import simpy
import random
import time
import torch
import numpy as np
from core.statecon import StateconEngine
from core.idendef import IdendefEngine
from core.optineck import OptineckEngine
from core.veto_engine import VetoEngine

MACHINE_TOPOLOGY = {
    'Station_A': 3,
    'Station_B': 2,
    'Station_C_Dark': 5,
    'Station_D': 4,
    'Station_E': 2
}

class FactorySimulation:
    def __init__(self, env):
        self.env = env
        self.statecon = StateconEngine()
        self.idendef = IdendefEngine()
        self.optineck = OptineckEngine()
        self.veto_engine = VetoEngine()
        
        # Parallel machines per station (using simpy.Resource)
        self.station_resources = {
            station: simpy.Resource(env, capacity=count)
            for station, count in MACHINE_TOPOLOGY.items()
        }
        
        # SimPy Inventory & Buffers
        self.raw_inventory = simpy.Container(env, capacity=1000, init=100) 
        self.buffers = {
            'Buffer_A_B': simpy.Store(env, capacity=self.statecon.get_buffer_capacity('Buffer_A_B')),
            'Buffer_B_C': simpy.Store(env, capacity=self.statecon.get_buffer_capacity('Buffer_B_C')),
            'Buffer_C_D': simpy.Store(env, capacity=self.statecon.get_buffer_capacity('Buffer_C_D')),
            'Buffer_D_E': simpy.Store(env, capacity=self.statecon.get_buffer_capacity('Buffer_D_E'))
        }

    def update_part_location(self, part_id, location, status="In Progress"):
        cursor = self.statecon.conn.cursor()
        curr_time = time.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO parts (part_id, current_location, status, last_updated)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(part_id) DO UPDATE SET current_location=excluded.current_location, status=excluded.status, last_updated=excluded.last_updated
        ''', (part_id, location, status, curr_time))
        self.statecon.conn.commit()

    def generate_synthetic_telemetry(self, machine_id, anomaly_type):
        # 1. Vibration
        vib_model = self.idendef.vibration_model
        base_freq = vib_model.base_freqs.get(machine_id, 10.0) 
            
        t_vib = np.linspace(0, 2, 500)
        
        # Base ideal vibration
        vib = np.sin(2 * np.pi * base_freq * t_vib) + 0.5 * np.sin(2 * np.pi * (base_freq * 2.5) * t_vib) + np.random.normal(0, 0.15, 500)
        
        if anomaly_type == "Bearing Degradation" or anomaly_type == "Catastrophic Collision":
            # Add an 80Hz rattle anomaly or massive spike
            vib += 2.0 * np.sin(2 * np.pi * 80 * t_vib) + np.random.normal(0, 0.5, 500)
            
        # 2. PLC 3D Trajectory
        plc_model = getattr(self.idendef, 'plc_model', None)
        seq_len = plc_model.seq_lens.get(machine_id, 200) if plc_model else 200
        L1, L2 = plc_model.kinematics.get(machine_id, (150.0, 100.0)) if plc_model else (150.0, 100.0)
        
        t_plc = np.linspace(0, 1, seq_len)
        theta1 = np.pi * np.sin(2 * np.pi * t_plc) 
        theta2 = 0.5 * np.pi * np.cos(4 * np.pi * t_plc) 
        
        x = L1 * np.cos(theta1) + L2 * np.cos(theta1 + theta2)
        y = L1 * np.sin(theta1) + L2 * np.sin(theta1 + theta2)
        z = 100.0 + 50.0 * np.sin(2 * np.pi * t_plc)
        
        # Base ideal PLC variance
        x += np.random.normal(0, 1.0, seq_len)
        y += np.random.normal(0, 1.0, seq_len)
        z += np.random.normal(0, 1.0, seq_len)
        
        if anomaly_type == "Tool Miscalibration":
            # Progressive spatial drift + sudden mechanical slippage mid-cycle
            drift = np.linspace(0, 45.0, seq_len)
            x += drift
            y -= drift
            # Slippage jump
            mid = seq_len // 2
            z[mid:] -= 30.0
        elif anomaly_type == "Catastrophic Collision":
            # Massive structural deviation
            x += np.random.normal(50.0, 10.0, seq_len)
            y -= np.random.normal(50.0, 10.0, seq_len)
            z += np.random.normal(20.0, 5.0, seq_len)
            
        plc_series = np.vstack((x, y, z)).tolist()
        
        return vib.tolist(), plc_series

    def process_part(self, part_id):
        """A single part flows through all stations."""
        self.update_part_location(part_id, 'Buffer_Raw')
        yield self.env.timeout(2.0)
        
        # --- STATION A ---
        yield self.env.process(self.run_machine_cycle('Station_A', part_id, self.raw_inventory, self.buffers['Buffer_A_B']))
        self.update_part_location(part_id, 'Buffer_A_B')
        yield self.env.timeout(3.0) # Transit time on conveyor
        
        # --- STATION B ---
        yield self.env.process(self.run_machine_cycle('Station_B', part_id, self.buffers['Buffer_A_B'], self.buffers['Buffer_B_C']))
        self.update_part_location(part_id, 'Buffer_B_C')
        yield self.env.timeout(3.0)
        
        # --- STATION C ---
        yield self.env.process(self.run_machine_cycle('Station_C_Dark', part_id, self.buffers['Buffer_B_C'], self.buffers['Buffer_C_D']))
        self.update_part_location(part_id, 'Buffer_C_D')
        yield self.env.timeout(3.0)
        
        # --- STATION D ---
        yield self.env.process(self.run_machine_cycle('Station_D', part_id, self.buffers['Buffer_C_D'], self.buffers['Buffer_D_E']))
        self.update_part_location(part_id, 'Buffer_D_E')
        yield self.env.timeout(3.0)
        
        # --- STATION E ---
        yield self.env.process(self.run_machine_cycle('Station_E', part_id, self.buffers['Buffer_D_E'], None))
        self.update_part_location(part_id, 'Completed', status="Finished")

    def run_machine_cycle(self, station_id, part_id, upstream, downstream):
        """Requests a machine in the station, processes, and pushes to downstream."""
        # 1. Retrieve part
        if station_id == 'Station_A':
            yield upstream.get(1) # Get from raw inventory
        else:
            _ = yield upstream.get() # Get from buffer

        # 2. Request an available machine in this station
        resource = self.station_resources[station_id]
        with resource.request() as req:
            yield req
            
            machine_num = random.randint(1, MACHINE_TOPOLOGY[station_id])
            machine_id = f"{station_id}_M{machine_num}"
            
            # Record that the part is now actively inside this station
            self.update_part_location(part_id, station_id)
            
            # Check BOM Starvation
            if not self.statecon.consume_inventory(station_id):
                print(f"[{machine_id}] BOM STARVATION! Waiting for {station_id} materials.")
                self.statecon.update_machine_state(machine_id, 'STARVED', 0.0)
                yield self.env.timeout(10.0) # Simulating emergency replenishment (Forklift transit)
                print(f"[{machine_id}] FORKLIFT ARRIVED! Replenishing 100 units.")
                self.statecon.replenish_inventory(station_id, 100)
                self.statecon.consume_inventory(station_id)
            
            # Simulate Work using real architectural cycle times
            target_ct = self.statecon.get_station_cycle_time(station_id)
            
            # Randomly trigger distinct anomaly classes
            rand_val = random.random()
            anomaly_type = None
            if rand_val < 0.02:
                anomaly_type = "Bearing Degradation"
            elif rand_val < 0.04:
                anomaly_type = "Tool Miscalibration"
            elif rand_val < 0.05:
                anomaly_type = "Catastrophic Collision"
                
            actual_ct = target_ct * random.uniform(1.5, 2.5) if anomaly_type else target_ct * random.uniform(0.95, 1.05)
            
            # Scale simulation timeout so we don't literally wait 60 seconds (15x speedup)
            yield self.env.timeout(actual_ct / 15.0)

            # 3. I-DENDEF Check
            vib, plc_series = self.generate_synthetic_telemetry(machine_id, anomaly_type)
            is_defect, reasons, vib_mse, plc_mse = self.idendef.evaluate_station(machine_id, vib, plc_series)
            
            # Extract independent flags strictly from ML model predictions
            defect_vib = any("Vib-TCN" in r for r in reasons)
            defect_plc = any("PLC-TCN" in r for r in reasons)
            
            import json
            cursor = self.statecon.conn.cursor()
            curr_time = time.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
            INSERT INTO telemetry_logs (timestamp, station_id, vibration_data, is_anomaly)
            VALUES (?, ?, ?, ?)
            ''', (curr_time, machine_id, json.dumps(vib), defect_vib))
            
            cursor.execute('''
            INSERT INTO plc_logs (timestamp, station_id, plc_x, plc_y, plc_z, is_anomaly)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (curr_time, machine_id, json.dumps(plc_series[0]), json.dumps(plc_series[1]), json.dumps(plc_series[2]), defect_plc))
            
            ground_truth_type = anomaly_type if anomaly_type else "Ideal"
            cursor.execute('''
            INSERT INTO ml_eval_logs (timestamp, machine_id, anomaly_type, defect_vib, defect_plc, vib_mse, plc_mse)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (curr_time, machine_id, ground_truth_type, defect_vib, defect_plc, vib_mse, plc_mse))
            
            self.statecon.conn.commit()
            
            status = 'BROKEN' if is_defect else 'RUNNING'
            self.statecon.update_machine_state(machine_id, status, actual_ct)
            
            # If broken, simulate repair downtime
            if is_defect:
                print(f"[{machine_id}] OFFLINE for repair...")
                yield self.env.timeout(20.0) # Scaled repair time
                self.statecon.update_machine_state(machine_id, 'RUNNING', actual_ct)
                print(f"[{machine_id}] REPAIRED. Back online.")

            # 4. O-PTINECK & Veto Check
            time_flag = self.optineck.check_time_thresholds(machine_id, actual_ct)
            veto_result = self.veto_engine.evaluate_all(
                max_ct=actual_ct, target_ct=target_ct, 
                inv=self.raw_inventory.level, dep_rate=1.0,
                time_saved=0, exp_v=1.0, act_v=1.0
            )
            
            dey, bottleneck = self.optineck.calculate_dey()
            event_log = f"[{machine_id}] Veto: {veto_result} | I-DENDEF: {reasons}"
            self.optineck.log_metrics(dey, actual_ct, bottleneck, event_log)

            # 5. Push to downstream buffer (Will automatically block if Buffer is at B_max!)
            if downstream:
                if len(downstream.items) >= downstream.capacity:
                    print(f"[{machine_id}] BLOCKED! Downstream buffer is full.")
                    self.statecon.update_machine_state(machine_id, 'BLOCKED', actual_ct)
                yield downstream.put(part_id)
                # Once unblocked (or if it wasn't), ensure it's marked running
                self.statecon.update_machine_state(machine_id, 'RUNNING', actual_ct)

def part_generator(env, sim):
    """Generates new parts entering the factory continuously based on Takt Time."""
    part_count = 0
    takt_time = sim.statecon.get_global_var("takt_time_TT")
    scaled_takt = takt_time / 15.0
    while True:
        part_count += 1
        part_id = f"Part_{part_count}"
        env.process(sim.process_part(part_id))
        yield env.timeout(scaled_takt)

def start_simulation():
    env = simpy.Environment()
    sim = FactorySimulation(env)
    
    # Start the continuous flow of parts
    env.process(part_generator(env, sim))
        
    print("Starting V2 SimPy Factory Simulation with Granular Machines...")
    while True:
        env.step()
        time.sleep(0.05) 
