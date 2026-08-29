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
            "Pressing": 62.0,
            "Welding": 58.0,
            "Painting": 65.0,  # Bottleneck
            "PowerTrain": 59.0,
            "Final_Assembly": 61.0
        }
        
        # Buffer Capacities (Group 3)
        self.buffer_capacities = {
            "Buffer_Pressing_Welding": 5,
            "Buffer_Welding_Painting": 5,
            "Buffer_Painting_PowerTrain": 5,
            "Buffer_PowerTrain_FinalAssembly": 5
        }
        
        self.bom_inventory = {
            "Pressing": [
                {"part_id": "Steel_Coils", "qty_per_car": 1, "on_hand": 500, "category": "Raw Materials & Body Components"},
                {"part_id": "Stamped_Body_Panels", "qty_per_car": 4, "on_hand": 2000, "category": "Raw Materials & Body Components"},
                {"part_id": "Structural_Frame_Rails", "qty_per_car": 2, "on_hand": 1000, "category": "Raw Materials & Body Components"},
                {"part_id": "Acoustic_Dampening_Pads", "qty_per_car": 6, "on_hand": 3000, "category": "Raw Materials & Body Components"}
            ],
            "Welding": [
                {"part_id": "Welding_Wire_and_Gases", "qty_per_car": 5, "on_hand": 2500, "category": "Consumable Fasteners & Joining"},
                {"part_id": "Structural_Adhesives", "qty_per_car": 2, "on_hand": 1000, "category": "Consumable Fasteners & Joining"},
                {"part_id": "Rivets_and_Clinches", "qty_per_car": 50, "on_hand": 25000, "category": "Consumable Fasteners & Joining"},
                {"part_id": "Bolts_and_Nuts", "qty_per_car": 120, "on_hand": 60000, "category": "Consumable Fasteners & Joining"}
            ],
            "Painting": [
                {"part_id": "Pre-treatment_Chemicals", "qty_per_car": 1, "on_hand": 500, "category": "Paint & Coating Consumables"},
                {"part_id": "E-coat_Resin", "qty_per_car": 1, "on_hand": 500, "category": "Paint & Coating Consumables"},
                {"part_id": "Primers_and_Basecoats", "qty_per_car": 2, "on_hand": 1000, "category": "Paint & Coating Consumables"},
                {"part_id": "Paint_Thinners_and_Solvents", "qty_per_car": 1, "on_hand": 500, "category": "Paint & Coating Consumables"},
                {"part_id": "Masking_Tapes", "qty_per_car": 3, "on_hand": 1500, "category": "Paint & Coating Consumables"},
                {"part_id": "Cavity_Wax", "qty_per_car": 1, "on_hand": 500, "category": "Paint & Coating Consumables"}
            ],
            "PowerTrain": [
                {"part_id": "Engine_Assemblies", "qty_per_car": 1, "on_hand": 5, "category": "Powertrain & Mechanical Components"},
                {"part_id": "Transmissions", "qty_per_car": 1, "on_hand": 500, "category": "Powertrain & Mechanical Components"},
                {"part_id": "High-voltage_Battery_Packs", "qty_per_car": 1, "on_hand": 500, "category": "Powertrain & Mechanical Components"},
                {"part_id": "Exhaust_Systems", "qty_per_car": 1, "on_hand": 500, "category": "Powertrain & Mechanical Components"},
                {"part_id": "Drive_Shafts", "qty_per_car": 2, "on_hand": 1000, "category": "Powertrain & Mechanical Components"},
                {"part_id": "Suspension_Components", "qty_per_car": 4, "on_hand": 2000, "category": "Powertrain & Mechanical Components"},
                {"part_id": "Brake_Assemblies", "qty_per_car": 4, "on_hand": 2000, "category": "Powertrain & Mechanical Components"}
            ],
            "Final_Assembly": [
                {"part_id": "Wiring_Harnesses", "qty_per_car": 3, "on_hand": 1500, "category": "Electrical & Electronics"},
                {"part_id": "Electronic_Control_Units", "qty_per_car": 5, "on_hand": 2500, "category": "Electrical & Electronics"},
                {"part_id": "Sensors_and_Cameras", "qty_per_car": 10, "on_hand": 5000, "category": "Electrical & Electronics"},
                {"part_id": "Infotainment_Screens", "qty_per_car": 1, "on_hand": 500, "category": "Electrical & Electronics"},
                {"part_id": "Headlights_and_Taillights", "qty_per_car": 4, "on_hand": 2000, "category": "Electrical & Electronics"},
                {"part_id": "Dashboard_Modules", "qty_per_car": 1, "on_hand": 500, "category": "Interior & Exterior Trim"},
                {"part_id": "Front_and_Rear_Seats", "qty_per_car": 2, "on_hand": 1000, "category": "Interior & Exterior Trim"},
                {"part_id": "Steering_Wheels", "qty_per_car": 1, "on_hand": 500, "category": "Interior & Exterior Trim"},
                {"part_id": "Plastic_Trim_Clips", "qty_per_car": 40, "on_hand": 20000, "category": "Consumable Fasteners & Joining"},
                {"part_id": "Windshields_and_Glass", "qty_per_car": 4, "on_hand": 2000, "category": "Glass & Weatherstripping"},
                {"part_id": "Rubber_Door_Seals", "qty_per_car": 4, "on_hand": 2000, "category": "Glass & Weatherstripping"},
                {"part_id": "Operational_Fluids", "qty_per_car": 5, "on_hand": 2500, "category": "Operational Fluids & Gases"},
                {"part_id": "Alloy_Wheels", "qty_per_car": 4, "on_hand": 2000, "category": "Wheel & Tire Assemblies"},
                {"part_id": "Tires", "qty_per_car": 4, "on_hand": 2000, "category": "Wheel & Tire Assemblies"},
                {"part_id": "Packaging_Consumables", "qty_per_car": 10, "on_hand": 5000, "category": "Packaging & Logistics Consumables"}
            ]
        }
        
        # Sync Initial Inventory to DB
        cursor = self.conn.cursor()
        for station_id, parts in self.bom_inventory.items():
            for inv in parts:
                cursor.execute('''
                INSERT INTO inventory (station_id, part_id, category, on_hand)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(station_id, part_id) DO UPDATE SET on_hand=excluded.on_hand
                ''', (station_id, inv["part_id"], inv.get("category", "Uncategorized"), inv["on_hand"]))
            
        # Sync Initial Config to DB
        for k, v in self.global_vars.items():
            cursor.execute('INSERT INTO system_config (config_group, key, value) VALUES (?, ?, ?)', ('global', k, v))
        for k, v in self.station_cycle_times.items():
            cursor.execute('INSERT INTO system_config (config_group, key, value) VALUES (?, ?, ?)', ('station', k, v))
        for k, v in self.buffer_capacities.items():
            cursor.execute('INSERT INTO system_config (config_group, key, value) VALUES (?, ?, ?)', ('buffer', k, v))
        for st, parts in self.bom_inventory.items():
            for inv in parts:
                cursor.execute('INSERT INTO system_config (config_group, key, value) VALUES (?, ?, ?)', ('bom_qty', f"{st}_{inv['part_id']}_qty_per_car", inv["qty_per_car"]))
                cursor.execute('INSERT INTO system_config (config_group, key, value) VALUES (?, ?, ?)', ('bom_onhand', f"{st}_{inv['part_id']}_on_hand", inv["on_hand"]))
        self.conn.commit()

    def refresh_config(self):
        """Pulls dynamic overrides from DB (set by Web Dashboard)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT config_group, key, value FROM system_config")
        rows = cursor.fetchall()
        for cg, k, v in rows:
            if cg == 'global':
                self.global_vars[k] = v
            elif cg == 'station':
                self.station_cycle_times[k] = v
            elif cg == 'buffer':
                self.buffer_capacities[k] = int(v)
            elif cg == 'bom_qty':
                # key format: StationName_PartName_qty_per_car
                # Actually it's easier to find it by splitting from right.
                parts = k.split('_')
                if len(parts) >= 4: # e.g. Final_Assembly_Wiring_Harnesses_qty_per_car or Pressing_Steel_Coils_qty_per_car
                    # Instead of parsing the string, let's just find the part in the inventory structure that matches
                    for st, items in self.bom_inventory.items():
                        for item in items:
                            expected_key = f"{st}_{item['part_id']}_qty_per_car"
                            if k == expected_key:
                                item["qty_per_car"] = int(v)
            elif cg == 'bom_onhand':
                for st, items in self.bom_inventory.items():
                        for item in items:
                            expected_key = f"{st}_{item['part_id']}_on_hand"
                            if k == expected_key:
                                item["on_hand"] = int(v)

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
        parts = self.bom_inventory.get(station_id)
        if not parts:
            return True # No BOM requirement
            
        # First check if ALL parts have enough inventory
        for inv in parts:
            if inv["on_hand"] < inv["qty_per_car"]:
                return False # Starvation!
                
        # If we reach here, we have enough of everything. Consume it.
        cursor = self.conn.cursor()
        for inv in parts:
            inv["on_hand"] -= inv["qty_per_car"]
            
            # Persist to DB for the Web Server to read
            cursor.execute('''
            INSERT INTO inventory (station_id, part_id, category, on_hand)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(station_id, part_id) DO UPDATE SET on_hand=excluded.on_hand
            ''', (station_id, inv["part_id"], inv.get("category", "Uncategorized"), inv["on_hand"]))
        self.conn.commit()
        return True
        
    def replenish_inventory(self, station_id, amount):
        """Simulates a forklift arriving to drop off stock."""
        parts = self.bom_inventory.get(station_id)
        if parts:
            cursor = self.conn.cursor()
            for inv in parts:
                # Proportional replenishment: a "pallet" contains enough parts for 'amount' cars
                inv["on_hand"] += (amount * inv["qty_per_car"])
                cursor.execute('''
                UPDATE inventory SET on_hand = ? WHERE station_id = ? AND part_id = ?
                ''', (inv["on_hand"], station_id, inv["part_id"]))
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
