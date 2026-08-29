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
        Runs a heuristic Genetic Algorithm to balance the line.
        Objective: Minimize max(CT_i) (the bottleneck) while keeping total work content W constant.
        Passes proposed solution to VetoEngine. If approved, applies it to DB.
        """
        from core.veto_engine import VetoEngine
        veto = VetoEngine()
        
        # 1. Fetch current times
        self.statecon.refresh_config()
        current_times = self.statecon.station_cycle_times
        stations = list(current_times.keys())
        total_work = sum(current_times.values())
        current_bottleneck = max(current_times.values())
        
        # 2. GA heuristic (for simplicity, targets perfect average balance +/- 0.5s variance)
        import random
        target_avg = total_work / len(stations)
        
        proposed_times = {}
        remaining_work = total_work
        for i, st in enumerate(stations):
            if i == len(stations) - 1:
                proposed_times[st] = round(remaining_work, 1)
            else:
                # Add slight random mutation around the average
                val = round(target_avg + random.uniform(-0.5, 0.5), 1)
                proposed_times[st] = val
                remaining_work -= val
                
        proposed_bottleneck = max(proposed_times.values())
        
        # 3. Calculate metrics
        time_saved_per_cycle = current_bottleneck - proposed_bottleneck
        shift_N = self.statecon.get_global_var("shift_quantity_N")
        projected_time_saved = time_saved_per_cycle * shift_N
        
        # 4. Check Veto
        veto_flag, veto_msg = veto.check_whiplash(projected_time_saved)
        
        if veto_flag:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO phantom_logs (timestamp, human_input, plc_truth, action_taken)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now(), "O-PTINECK Optimize", f"Projected {projected_time_saved}s saved", f"VETO: {veto_msg}"))
            cursor.execute('''
                INSERT INTO global_alerts (timestamp, source, message, severity)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now(), "O-PTINECK", f"Optimization Vetoed: {veto_msg}", "WARNING"))
            self.conn.commit()
            return {"status": "rejected", "reason": veto_msg, "time_saved": projected_time_saved}
            
        # 5. Apply to DB
        cursor = self.conn.cursor()
        for st, new_ct in proposed_times.items():
            cursor.execute('''
                UPDATE system_config SET value = ? 
                WHERE config_group = 'station' AND key = ?
            ''', (new_ct, st))
        self.conn.commit()
        
        # Update metrics
        old_dey = (3600.0 / current_bottleneck) * self.statecon.get_global_var("structural_efficiency_eta")
        new_dey = (3600.0 / proposed_bottleneck) * self.statecon.get_global_var("structural_efficiency_eta")
        
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

    def log_metrics(self, dey, max_ct, bottleneck, event_log=""):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO metrics (timestamp, dey, max_ct, bottleneck_station, event_log)
        VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now(), dey, max_ct, bottleneck, event_log))
        self.conn.commit()
