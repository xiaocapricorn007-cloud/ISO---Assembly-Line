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
        eta = self.statecon.get_global_var("structural_efficiency")
        
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

    def log_metrics(self, dey, max_ct, bottleneck, event_log=""):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO metrics (timestamp, dey, max_ct, bottleneck_station, event_log)
        VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now(), dey, max_ct, bottleneck, event_log))
        self.conn.commit()
