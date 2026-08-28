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
        # Global Parameters (Group 1)
        self.global_vars = {
            "shift_quantity_N": 400,
            "shift_time_T_min": 450,
            "target_cycle_time": 60.0,
            "takt_time_TT": 67.5,
            "structural_efficiency_eta": 0.90,
            "conveyor_belt_speed": 1.0,
            "min_time_threshold": 58.0, 
            "max_time_threshold": 65.0
        }
        
        # Station Timing (Group 2)
        self.station_cycle_times = {
            "Station_A": 62.0,
            "Station_B": 58.0,
            "Station_C_Dark": 65.0,  # Bottleneck
            "Station_D": 59.0,
            "Station_E": 61.0
        }
        
        # Buffer Capacities (Group 3)
        self.buffer_capacities = {
            "Buffer_A_B": 5,
            "Buffer_B_C": 5,
            "Buffer_C_D": 5,
            "Buffer_D_E": 5
        }
        
        # Single-Model BOM & Inventory (Group 5)
        self.bom_inventory = {
            "Station_A": {"part_id": "Sheet_Metal", "qty_per_car": 1, "on_hand": 500},
            "Station_B": {"part_id": "Welding_Wire", "qty_per_car": 1, "on_hand": 500},
            "Station_C_Dark": {"part_id": "Paint_Gallons", "qty_per_car": 2, "on_hand": 1000},
            "Station_D": {"part_id": "Engine_Block", "qty_per_car": 1, "on_hand": 5}, # Deliberately low to trigger starvation!
            "Station_E": {"part_id": "Tires", "qty_per_car": 4, "on_hand": 2000}
        }
        
        # Sync Initial Inventory to DB
        cursor = self.conn.cursor()
        for station_id, inv in self.bom_inventory.items():
            cursor.execute('''
            INSERT INTO inventory (station_id, part_id, on_hand)
            VALUES (?, ?, ?)
            ON CONFLICT(station_id) DO UPDATE SET on_hand=excluded.on_hand
            ''', (station_id, inv["part_id"], inv["on_hand"]))
        self.conn.commit()

    def get_global_var(self, key):
        """Allows I-DENDEF and O-PTINECK to retrieve parameters."""
        return self.global_vars.get(key)
        
    def set_global_var(self, key, value):
        """Allows updating global parameters dynamically."""
        self.global_vars[key] = value
        
    def get_station_cycle_time(self, station_id):
        return self.station_cycle_times.get(station_id, self.global_vars["target_cycle_time"])
        
    def get_buffer_capacity(self, buffer_id):
        return self.buffer_capacities.get(buffer_id, 5)
        
    def get_bom_inventory(self, station_id):
        return self.bom_inventory.get(station_id)
        
    def consume_inventory(self, station_id):
        """Consumes BOM items per car. Returns False if starved."""
        inv = self.bom_inventory.get(station_id)
        if not inv:
            return True # No BOM requirement
            
        if inv["on_hand"] >= inv["qty_per_car"]:
            inv["on_hand"] -= inv["qty_per_car"]
            
            # Persist to DB for the Web Server to read
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO inventory (station_id, part_id, on_hand)
            VALUES (?, ?, ?)
            ON CONFLICT(station_id) DO UPDATE SET on_hand=excluded.on_hand
            ''', (station_id, inv["part_id"], inv["on_hand"]))
            self.conn.commit()
            
            return True
        return False # Starvation!
        
    def replenish_inventory(self, station_id, amount):
        """Simulates a forklift arriving to drop off stock."""
        inv = self.bom_inventory.get(station_id)
        if inv:
            inv["on_hand"] += amount
            cursor = self.conn.cursor()
            cursor.execute('''
            UPDATE inventory SET on_hand = ? WHERE station_id = ?
            ''', (inv["on_hand"], station_id))
            self.conn.commit()
        
    def update_machine_state(self, station_id, status, current_cycle_time):
        cursor = self.conn.cursor()
        # Check if exists
        cursor.execute("SELECT 1 FROM machines WHERE station_id = ?", (station_id,))
        if cursor.fetchone():
            cursor.execute('''
            UPDATE machines 
            SET status = ?, current_cycle_time = ?, last_updated = ?
            WHERE station_id = ?
            ''', (status, current_cycle_time, datetime.now(), station_id))
        else:
            cursor.execute('''
            INSERT INTO machines (station_id, status, current_cycle_time, target_cycle_time, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ''', (station_id, status, current_cycle_time, self.global_vars["target_cycle_time"], datetime.now()))
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
