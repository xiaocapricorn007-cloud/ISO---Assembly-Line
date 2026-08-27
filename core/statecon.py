import sqlite3
import pandas as pd
from datetime import datetime
from db import get_connection

class StateconEngine:
    """
    S-TATECON: The Digital Ontology & State Hub
    Handles Auto-Validation (Phantom State Fix) and Live State.
    """
    def __init__(self):
        self.conn = get_connection()
        
    def update_machine_state(self, station_id, status, current_cycle_time):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE machines 
        SET status = ?, current_cycle_time = ?, last_updated = ?
        WHERE station_id = ?
        ''', (status, current_cycle_time, datetime.now(), station_id))
        self.conn.commit()

    def process_human_input(self, station_id, human_reported_status):
        """
        The Auto-Validation Layer: Prevent Phantom State.
        Checks human input against PLC (database).
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT status FROM machines WHERE station_id = ?', (station_id,))
        plc_status = cursor.fetchone()[0]
        
        # If PLC says BROKEN, but human says RUNNING -> VETO
        if plc_status == 'BROKEN' and human_reported_status == 'RUNNING':
            action = "VETO_FREEZE"
            self._log_phantom(human_reported_status, plc_status, action)
            return False # Input rejected
            
        return True # Input accepted

    def _log_phantom(self, human, plc, action):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO phantom_logs (timestamp, human_input, plc_truth, action_taken)
        VALUES (?, ?, ?, ?)
        ''', (datetime.now(), human, plc, action))
        self.conn.commit()
        print(f"[S-TATECON VETO] Blocked human input '{human}' contradicting PLC '{plc}'")
