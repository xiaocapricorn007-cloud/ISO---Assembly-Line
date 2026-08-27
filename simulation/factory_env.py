import simpy
import random
import time
from core.statecon import StateconEngine
from core.idendef import IdendefEngine
from core.optineck import OptineckEngine
from simulation.operators import Operator

class FactorySimulation:
    def __init__(self, env):
        self.env = env
        self.statecon = StateconEngine()
        self.idendef = IdendefEngine()
        self.optineck = OptineckEngine()
        
        self.stations = ['Station_A', 'Station_B', 'Station_C_Dark', 'Station_D', 'Station_E']
        self.base_cycle_time = 60.0
        
        self.operators = [
            Operator("Op_1", 1.0),
            Operator("Op_2", 1.1),
            Operator("Op_3", 0.9)
        ]
        
    def run_station(self, station_id):
        """Simulates a single station's operations over time."""
        while True:
            # Shift time in hours (simulation time / 3600)
            shift_hours = self.env.now / 3600.0
            
            # 1. I-DENDEF: Calculate Fatigue (slows down cycle time over time)
            fatigue_mult = self.idendef.calculate_fatigue_multiplier(shift_hours)
            actual_cycle_time = self.base_cycle_time * fatigue_mult * random.uniform(0.9, 1.2)
            
            # 2. I-DENDEF: Simulate telemetry & AI Anomaly detection
            # Generate random heat/vib. Occasionally inject an anomaly to cause a breakdown.
            is_anomaly = False
            if random.random() < 0.05: # 5% chance of breakdown event
                heat = random.uniform(70, 100)
                vib = random.uniform(3.0, 5.0)
            else:
                heat = random.uniform(45, 55)
                vib = random.uniform(1.5, 2.5)
                
            if self.idendef.detect_mechanical_anomaly(heat, vib):
                is_anomaly = True
                print(f"[{self.env.now:.1f}s] I-DENDEF ANOMALY DETECTED at {station_id}!")
                
            # 3. S-TATECON: Update live state
            status = 'BROKEN' if is_anomaly else 'RUNNING'
            self.statecon.update_machine_state(station_id, status, actual_cycle_time)
            
            # Phantom State Check simulation:
            if is_anomaly and random.random() < 0.5:
                # Human accidentally clicks "RUNNING" while machine is broken
                self.statecon.process_human_input(station_id, 'RUNNING')
            
            # 4. O-PTINECK: Calculate DEY
            dey, bottleneck = self.optineck.calculate_dey()
            
            # If bottleneck is severe, attempt rebalance (mocked)
            if bottleneck == station_id and actual_cycle_time > self.base_cycle_time * 1.3:
                # O-PTINECK evaluates moving someone (mocked 150s saved)
                self.optineck.evaluate_rebalance_veto(projected_time_saved_sec=150)
                
            event_log = f"Status: {status}, Anomaly: {is_anomaly}"
            self.optineck.log_metrics(dey, actual_cycle_time, bottleneck, event_log)
            
            # Simulate time taken for this cycle or downtime
            delay = actual_cycle_time if not is_anomaly else 300.0 # 5 min downtime
            yield self.env.timeout(delay)

def start_simulation():
    env = simpy.Environment()
    sim = FactorySimulation(env)
    
    # Start processes for all stations
    for station in sim.stations:
        env.process(sim.run_station(station))
        
    print("Starting SimPy Factory Simulation...")
    # Run indefinitely (or for a long shift)
    # We use a real-time equivalent loop so it doesn't instantly finish.
    # Actually, to integrate with Streamlit, we step the environment slowly.
    while True:
        env.step()
        time.sleep(0.1) # Slow down simulation to watch it live on dashboard
