import sqlite3
import pandas as pd
from datetime import datetime
from db import get_connection

class StateconEngine:
    """
    S-TATECON: The Digital Ontology & State Hub
    The single source of truth. Holds global variables and live state.
    Both I-DENDEF and O-PTINECK must retrieve parameters from here.
    """
    _instance = None
    
    # Singleton pattern so GUI and SimPy share the exact same state object in memory
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateconEngine, cls).__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self.conn = get_connection()
        # Global Parameters
        self.global_vars = {
            "target_cycle_time": 60.0,
            "min_time_threshold": 58.0, # Aggressively tight: Too early
            "max_time_threshold": 65.0, # Aggressively tight: Too late (bottleneck)
            "structural_efficiency": 0.90
        }

    def get_global_var(self, key):
        """Allows I-DENDEF and O-PTINECK to retrieve parameters."""
        return self.global_vars.get(key)
        
    def update_machine_state(self, station_id, status, current_cycle_time):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE machines 
        SET status = ?, current_cycle_time = ?, last_updated = ?
        WHERE station_id = ?
        ''', (status, current_cycle_time, datetime.now(), station_id))
        self.conn.commit()

    def process_human_input(self, station_id, human_reported_status):
        """Auto-Validation Layer (Phantom State Check)."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT status FROM machines WHERE station_id = ?', (station_id,))
        plc_status = cursor.fetchone()[0]
        
        if plc_status == 'BROKEN' and human_reported_status == 'RUNNING':
            self._log_phantom(human_reported_status, plc_status, "VETO_FREEZE")
            return False 
        return True

    def _log_phantom(self, human, plc, action):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO phantom_logs (timestamp, human_input, plc_truth, action_taken)
        VALUES (?, ?, ?, ?)
        ''', (datetime.now(), human, plc, action))
        self.conn.commit()
