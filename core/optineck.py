from datetime import datetime
from db import get_connection
from core.statecon import StateconEngine

class OptineckEngine:
    """
    O-PTINECK: Bottleneck Optimizer
    Relies on time-based checking to identify bottlenecks and calculates DEY.
    """
    def __init__(self):
        self.conn = get_connection()
        self.statecon = StateconEngine() # Retrieve singleton
        
    def check_time_thresholds(self, station_id, actual_cycle_time):
        """
        Flags if a piece leaves too early or too late based on global variables.
        """
        min_thresh = self.statecon.get_global_var("min_time_threshold")
        max_thresh = self.statecon.get_global_var("max_time_threshold")
        
        if actual_cycle_time < min_thresh:
            print(f"[O-PTINECK FLAG] {station_id} finished TOO EARLY ({actual_cycle_time:.1f}s < {min_thresh}s). Possible fault!")
            return "TOO_EARLY_FAULT"
        elif actual_cycle_time > max_thresh:
            print(f"[O-PTINECK FLAG] {station_id} is TOO SLOW ({actual_cycle_time:.1f}s > {max_thresh}s). Bottleneck forming!")
            return "BOTTLENECK_FAULT"
            
        return "NORMAL"

    def calculate_dey(self):
        """
        Calculates DEY = (3600 / max(CT_i)) * eta
        Reads live cycle times from database, eta from S-TATECON.
        """
        eta = self.statecon.get_global_var("structural_efficiency_eta")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(current_cycle_time) FROM machines WHERE status != 'BROKEN'")
        max_ct = cursor.fetchone()[0]
        
        if max_ct is None or max_ct == 0:
            return 0.0, None
            
        dey = (3600.0 / max_ct) * eta
        
        cursor.execute("SELECT station_id FROM machines WHERE current_cycle_time = ?", (max_ct,))
        bottleneck_row = cursor.fetchone()
        bottleneck = bottleneck_row[0] if bottleneck_row else None
        
        return dey, bottleneck

    def run_genetic_optimizer(self):
        """
        Step 5: Dynamic Rebalancing & DEY Maximization
        """
        from core.veto_engine import VetoEngine
        veto = VetoEngine(self.statecon)
        
        # Step 1: Prerequisites & Baseline
        self.statecon.refresh_config()
        shift_N = self.statecon.get_global_var("shift_quantity_N")
        shift_T = self.statecon.get_global_var("shift_time_T_min") * 60.0
        c_baseline = shift_T / shift_N if shift_N > 0 else 60.0
        TT = self.statecon.get_global_var("target_cycle_time")
        eta = self.statecon.get_global_var("structural_efficiency_eta")
        
        # Step 3: Drift Detection
        current_times = self.statecon.station_cycle_times
        stations = list(current_times.keys())
        total_work = sum(current_times.values())
        n_workers = len(stations)
        c_bar = total_work / n_workers
        current_bottleneck = max(current_times.values())
        
        # Phase 3C: Takt Time Synchronization Trigger
        if current_bottleneck <= TT:
            return {"status": "rejected", "reason": f"No bottleneck detected. Max CT ({current_bottleneck}s) <= TT ({TT}s).", "time_saved": 0}
            
        # Step 5A: Genetic Algorithm (Heuristic)
        import random
        target_avg = total_work / n_workers
        proposed_times = {}
        remaining_work = total_work
        for i, st in enumerate(stations):
            if i == len(stations) - 1:
                proposed_times[st] = round(remaining_work, 1)
            else:
                val = round(target_avg + random.uniform(-0.5, 0.5), 1)
                proposed_times[st] = val
                remaining_work -= val
                
        proposed_bottleneck = max(proposed_times.values())
        
        # Calculate Time Saved
        time_saved_per_cycle = current_bottleneck - proposed_bottleneck
        projected_time_saved = time_saved_per_cycle * shift_N
        
        # Step 4: Veto Engine
        # 4D: Severity Override
        sev_flag, sev_msg = veto.check_severity_override(current_bottleneck, TT)
        is_override = sev_flag
        
        # 4A: Physics
        phys_flag, phys_msg = veto.check_physics(proposed_times, c_baseline)
        if phys_flag: return self._reject_veto(phys_msg, projected_time_saved)
        
        # 4B: Material Starvation
        mat_flag, mat_msg = veto.check_material_starvation(shift_N)
        if mat_flag: return self._reject_veto(mat_msg, projected_time_saved)
        
        # 4C: Whiplash
        whip_flag, whip_msg = veto.check_whiplash(current_bottleneck, proposed_bottleneck, is_override)
        if whip_flag: return self._reject_veto(whip_msg, projected_time_saved)
        
        # Step 5B & 5C: Apply and Output DEY
        cursor = self.conn.cursor()
        for st, new_ct in proposed_times.items():
            cursor.execute('''
                UPDATE system_config SET value = ? 
                WHERE config_group = 'station' AND key = ?
            ''', (new_ct, st))
        self.conn.commit()
        
        old_dey = (3600.0 / current_bottleneck) * eta
        new_dey = (3600.0 / proposed_bottleneck) * eta
        
        cursor.execute('''
            INSERT INTO phantom_logs (timestamp, human_input, plc_truth, action_taken)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now(), "O-PTINECK Optimize", f"Projected {projected_time_saved}s saved", "APPROVED"))
        
        cursor.execute('''
            INSERT INTO global_alerts (timestamp, source, message, severity)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now(), "O-PTINECK", f"Line Rebalanced. {projected_time_saved}s saved.", "SUCCESS"))
        self.conn.commit()
        
        return {
            "status": "applied",
            "old_bottleneck": current_bottleneck,
            "new_bottleneck": proposed_bottleneck,
            "old_dey": round(old_dey, 1),
            "new_dey": round(new_dey, 1),
            "projected_time_saved_sec": projected_time_saved,
            "new_times": proposed_times
        }

    def _reject_veto(self, reason, time_saved):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO phantom_logs (timestamp, human_input, plc_truth, action_taken)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now(), "O-PTINECK Optimize", f"Projected {time_saved}s saved", f"VETO: {reason}"))
        cursor.execute('''
            INSERT INTO global_alerts (timestamp, source, message, severity)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now(), "O-PTINECK", f"Optimization Vetoed: {reason}", "WARNING"))
        self.conn.commit()
        return {"status": "rejected", "reason": reason, "time_saved": time_saved}

    def log_metrics(self, dey, max_ct, bottleneck, event_log=""):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO metrics (timestamp, dey, max_ct, bottleneck_station, event_log)
        VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now(), dey, max_ct, bottleneck, event_log))
        self.conn.commit()
