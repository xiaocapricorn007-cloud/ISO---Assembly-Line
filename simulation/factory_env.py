import simpy
import random
import time
from datetime import datetime
import torch
import numpy as np
import json
from core.statecon import StateconEngine
from core.idendef import IdendefEngine
from core.optineck import OptineckEngine
from core.veto_engine import VetoEngine

MACHINE_TOPOLOGY = {
    'Pressing': 3,
    'Welding': 2,
    'Painting': 5,
    'PowerTrain': 4,
    'Final_Assembly': 2
}

class FactorySimulation:
    def __init__(self, env):
        self.env = env
        self.statecon = StateconEngine()
        self.idendef = IdendefEngine()
        self.optineck = OptineckEngine()
        self.veto_engine = VetoEngine(self.statecon)
        

        
        # SimPy Inventory & Buffers
        self.station_locks = {st: simpy.Resource(env, capacity=1) for st in MACHINE_TOPOLOGY.keys()}
        self.raw_inventory = simpy.Container(env, capacity=1000, init=100) 
        self.buffers = {
            'Buffer_Pressing_Welding': simpy.Store(env, capacity=self.statecon.get_buffer_capacity('Buffer_Pressing_Welding')),
            'Buffer_Welding_Painting': simpy.Store(env, capacity=self.statecon.get_buffer_capacity('Buffer_Welding_Painting')),
            'Buffer_Painting_PowerTrain': simpy.Store(env, capacity=self.statecon.get_buffer_capacity('Buffer_Painting_PowerTrain')),
            'Buffer_PowerTrain_FinalAssembly': simpy.Store(env, capacity=self.statecon.get_buffer_capacity('Buffer_PowerTrain_FinalAssembly'))
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


    def pausable_timeout(self, duration):
        """Yields in small increments, freezing if the system is paused."""
        elapsed = 0.0
        step = 0.1
        while elapsed < duration:
            self.statecon.refresh_config()
            status = self.statecon.get_global_var("simulation_running")
            if status > 0.5:
                yield self.env.timeout(step)
                elapsed += step
            else:
                yield self.env.timeout(step)

    def get_transit_time(self):
        # Enforced strict 5.0s transit time to perfectly sync with CSS animation
        return 5.0


    def master_line_loop(self):
        # Wait until RUN is pressed before starting the shift
        while True:
            self.statecon.refresh_config()
            if self.statecon.get_global_var("simulation_running") > 0.5:
                break
            yield self.env.timeout(0.5)
            
        car_idx = 1
        stations = ['Pressing', 'Welding', 'Painting', 'PowerTrain', 'Final_Assembly']
        line_state = {st: None for st in stations}
        finishing_car = None
        
        while True:
            # --- GLOBAL TRANSIT PHASE ---
            # Set all machines to IDLE exactly during transit phase
            for st, count in MACHINE_TOPOLOGY.items():
                for i in range(1, count + 1):
                    self.statecon.update_machine_state(f"{st}_M{i}", 'IDLE', 0.0)
                    
            if finishing_car:
                self.update_part_location(finishing_car, 'Completed', status="Finished")
                
                # Increment Units Produced
                self.statecon.refresh_config()
                units = self.statecon.get_global_var("units_produced") + 1.0
                self.statecon.set_global_var("units_produced", units)
                cursor = self.statecon.conn.cursor()
                cursor.execute("UPDATE system_config SET value=? WHERE key='units_produced'", (units,))
                self.statecon.conn.commit()
                finishing_car = None

            if line_state['Final_Assembly']:
                finishing_car = line_state['Final_Assembly']
                self.update_part_location(finishing_car, 'Conveyor (To Completed)')

            # Shift cars forward logically and visually
            next_state = {st: None for st in stations}
            for i in range(len(stations) - 1, 0, -1):
                curr_st = stations[i-1]
                next_st = stations[i]
                part = line_state[curr_st]
                if part:
                    next_state[next_st] = part
                    self.update_part_location(part, f'Conveyor (To {next_st})')
            
            # Introduce new car
            new_car = f"Car{car_idx}"
            car_idx += 1
            next_state['Pressing'] = new_car
            self.update_part_location(new_car, 'Buffer_Raw')
            
            # Wait exactly 5s (scaled by conveyor speed) for ALL cars to transit together
            yield self.env.process(self.pausable_timeout(self.get_transit_time()))
            
            # --- GLOBAL PROCESSING PHASE ---
            line_state = next_state
            
            processing_tasks = []
            for st in stations:
                part = line_state[st]
                if part:
                    self.update_part_location(part, st)
                    processing_tasks.append(self.env.process(self.run_station_cycle(st, part)))
                    
            # Wait for ALL stations to finish processing simultaneously (Bottleneck sync)
            if processing_tasks:
                yield simpy.events.AllOf(self.env, processing_tasks)

    def run_station_cycle(self, station_id, part_id):
        """Runs ALL machines in the station simultaneously, no locks needed in global transit."""
        # Check BOM Starvation for the entire station
        if not self.statecon.consume_inventory(station_id):
            print(f"[{station_id}] BOM STARVATION! Waiting for {station_id} materials.")
            self.statecon.update_machine_state(f"{station_id}_M1", 'STARVED', 0.0)
            yield self.env.process(self.pausable_timeout(10.0)) 
            print(f"[{station_id}] FORKLIFT ARRIVED! Replenishing 100 units.")
            self.statecon.replenish_inventory(station_id, 100)
            self.statecon.consume_inventory(station_id)
        
        # Run all machines in parallel
        machine_count = MACHINE_TOPOLOGY[station_id]
        machine_tasks = []
        for i in range(1, machine_count + 1):
            machine_id = f"{station_id}_M{i}"
            machine_tasks.append(self.env.process(self.machine_task(station_id, machine_id)))
            
        yield simpy.events.AllOf(self.env, machine_tasks)

    def machine_task(self, station_id, machine_id):
        target_ct = self.statecon.get_station_cycle_time(station_id)
        
        # Set to RUNNING immediately so UI doesn't hang on IDLE during ML inference
        self.statecon.update_machine_state(machine_id, 'RUNNING', target_ct)
        
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
        
        # 3. I-DENDEF Check
        vib, plc_series = self.generate_synthetic_telemetry(machine_id, anomaly_type)
        is_defect, reasons, vib_mse, plc_mse = self.idendef.evaluate_station(machine_id, vib, plc_series)
        
        defect_vib = any("Vib-TCN" in r for r in reasons)
        defect_plc = any("PLC-TCN" in r for r in reasons)
        
        cursor = self.statecon.conn.cursor()
        curr_time = time.strftime('%Y-%m-%d %H:%M:%S')
        
        if is_defect:
            cursor.execute('''
            INSERT INTO global_alerts (timestamp, source, message, severity)
            VALUES (?, ?, ?, ?)
            ''', (datetime.now(), "I-DENDEF", f"Anomaly detected at {machine_id}: {', '.join(reasons)}", "CRITICAL"))
        
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
        
        # Wait for the physical cycle time so UI can plot the active data
        yield self.env.process(self.pausable_timeout(actual_ct))

        


        # 4. O-PTINECK & Veto Check
        time_flag = self.optineck.check_time_thresholds(machine_id, actual_ct)
        veto_result = "N/A"
        
        dey, bottleneck = self.optineck.calculate_dey()
        event_log = f"[{machine_id}] Veto: {veto_result} | I-DENDEF: {reasons}"
        self.optineck.log_metrics(dey, actual_ct, bottleneck, event_log)
        


def start_simulation():
    import simpy.rt
    env = simpy.rt.RealtimeEnvironment(factor=1.0, strict=False)
    sim = FactorySimulation(env)
    
    env.process(sim.master_line_loop())
        
    print("Starting V2 SimPy Factory Simulation with Single Car Test in REAL-TIME...")
    try:
        env.run()
    except Exception as e:
        print("Simulation error:", e)
        
    print("Simulation for Car1 finished. Keeping process alive for GUI...")
    while True:
        time.sleep(1)
