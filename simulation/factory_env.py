import simpy
import random
import time
import torch
from core.statecon import StateconEngine
from core.idendef import IdendefEngine
from core.optineck import OptineckEngine
from core.veto_engine import VetoEngine

class FactorySimulation:
    def __init__(self, env):
        self.env = env
        self.statecon = StateconEngine()
        self.idendef = IdendefEngine()
        self.optineck = OptineckEngine()
        self.veto_engine = VetoEngine()
        
        self.stations = ['Station_A', 'Station_B', 'Station_C_Dark', 'Station_D', 'Station_E']
        
        # SimPy Inventory & Buffers
        # Raw materials container. Starts with 100 parts.
        self.raw_inventory = simpy.Container(env, capacity=1000, init=100) 
        
        # Inter-station buffers (capacity 5 parts)
        self.buffers = {
            'Buffer_A_B': simpy.Store(env, capacity=5),
            'Buffer_B_C': simpy.Store(env, capacity=5),
            'Buffer_C_D': simpy.Store(env, capacity=5),
            'Buffer_D_E': simpy.Store(env, capacity=5)
        }

    def generate_synthetic_telemetry(self, station_id, is_faulty):
        """Generates dummy tensors and arrays for the 3 I-DENDEF models."""
        # 1. Vision CNN (1, 1, 28, 28)
        img = torch.randn(1, 1, 28, 28)
        
        # 2. Vibration Isolation Forest (10 time steps)
        if is_faulty:
            vib = [random.uniform(5.0, 10.0) for _ in range(10)] # Anomalous
        else:
            vib = [random.uniform(-1.0, 1.0) for _ in range(10)] # Normal
            
        # 3. PLC Logic Position (expected vs actual)
        exp_pos = 100.0
        act_pos = 100.0 if not is_faulty else random.uniform(80.0, 90.0)
        
        return img, vib, exp_pos, act_pos

    def run_station(self, station_id, upstream_buffer, downstream_buffer):
        """Simulates a single station's operations on a part."""
        while True:
            # 1. Retrieve part
            if station_id == 'Station_A':
                # Station A pulls from Raw Inventory
                yield self.raw_inventory.get(1)
                part_id = f"Part_{int(self.env.now)}"
            else:
                part_id = yield upstream_buffer.get()

            # 2. Simulate Work (Cycle Time)
            target_ct = self.statecon.get_global_var("target_cycle_time")
            
            # Inject a random fault occasionally
            is_faulty = random.random() < 0.05
            
            if is_faulty:
                actual_ct = target_ct * random.uniform(1.5, 2.5) # Took way too long
            else:
                actual_ct = target_ct * random.uniform(0.9, 1.1) # Normal variance
                
            yield self.env.timeout(actual_ct)

            # 3. I-DENDEF Check
            img, vib, exp_pos, act_pos = self.generate_synthetic_telemetry(station_id, is_faulty)
            is_defect, reasons = self.idendef.evaluate_station(img, vib, exp_pos, act_pos)
            
            status = 'BROKEN' if is_defect else 'RUNNING'
            self.statecon.update_machine_state(station_id, status, actual_ct)

            # 4. O-PTINECK Time-Check
            time_flag = self.optineck.check_time_thresholds(station_id, actual_ct)
            
            # 5. Veto Engine Check (Before moving to next station)
            # Evaluate constraints (mocking inputs for the check)
            dep_rate = 1.0 # 1 part per cycle
            veto_result = self.veto_engine.evaluate_all(
                max_ct=actual_ct, target_ct=target_ct, 
                inv=self.raw_inventory.level, dep_rate=dep_rate,
                time_saved=0, exp_v=1.0, act_v=1.0
            )
            
            # Log metrics
            dey, bottleneck = self.optineck.calculate_dey()
            event_log = f"Veto: {veto_result} | I-DENDEF: {reasons} | O-PTINECK: {time_flag}"
            self.optineck.log_metrics(dey, actual_ct, bottleneck, event_log)

            # 6. Push to downstream buffer
            if downstream_buffer:
                try:
                    yield downstream_buffer.put(part_id)
                except simpy.Interrupt:
                    print(f"[{station_id}] Buffer full! Jamming...")

def start_simulation():
    env = simpy.Environment()
    sim = FactorySimulation(env)
    
    # Wire up the stations with their respective buffers
    env.process(sim.run_station('Station_A', None, sim.buffers['Buffer_A_B']))
    env.process(sim.run_station('Station_B', sim.buffers['Buffer_A_B'], sim.buffers['Buffer_B_C']))
    env.process(sim.run_station('Station_C_Dark', sim.buffers['Buffer_B_C'], sim.buffers['Buffer_C_D']))
    env.process(sim.run_station('Station_D', sim.buffers['Buffer_C_D'], sim.buffers['Buffer_D_E']))
    env.process(sim.run_station('Station_E', sim.buffers['Buffer_D_E'], None)) # Last station exits system
        
    print("Starting V2 SimPy Factory Simulation with Buffers...")
    
    # Step simulation slowly for live dashboard tracking
    while True:
        env.step()
        time.sleep(0.05) 
