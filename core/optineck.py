from datetime import datetime
from db import get_connection

class OptineckEngine:
    """
    O-PTINECK: Bottleneck Optimizer
    Calculates Dynamic Equilibrium Yield (DEY) and handles GA Rebalancing logic.
    """
    def __init__(self):
        self.conn = get_connection()
        self.structural_efficiency_eta = 0.90 # 90% buffer
        self.switching_cost_penalty_sec = 300 # 5 minutes to change stations

    def calculate_dey(self):
        """
        Calculates DEY = (3600 / max(CT_i)) * eta
        Reads live cycle times from S-TATECON's database.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(current_cycle_time) FROM machines WHERE status != 'BROKEN'")
        max_ct = cursor.fetchone()[0]
        
        if max_ct is None or max_ct == 0:
            return 0.0, None
            
        dey = (3600.0 / max_ct) * self.structural_efficiency_eta
        
        # Find the bottleneck station
        cursor.execute("SELECT station_id FROM machines WHERE current_cycle_time = ?", (max_ct,))
        bottleneck = cursor.fetchone()[0]
        
        return dey, bottleneck

    def evaluate_rebalance_veto(self, projected_time_saved_sec):
        """
        Switching Cost Hysteresis Veto.
        Vetoes moving an operator if the transition penalty is greater than the time saved.
        """
        if projected_time_saved_sec < self.switching_cost_penalty_sec:
            print(f"[O-PTINECK VETO] GA Rebalance vetoed. Saved {projected_time_saved_sec}s < Penalty {self.switching_cost_penalty_sec}s")
            return True # Veto applied
        return False # Approved

    def log_metrics(self, dey, max_ct, bottleneck, event_log=""):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO metrics (timestamp, dey, max_ct, bottleneck_station, event_log)
        VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now(), dey, max_ct, bottleneck, event_log))
        self.conn.commit()
