import threading
from db import init_db
from simulation.factory_env import start_simulation

def main():
    print("Initializing Database...")
    init_db()
    
    print("Starting background SimPy thread...")
    sim_thread = threading.Thread(target=start_simulation, daemon=True)
    sim_thread.start()
    
    # Keep main thread alive
    sim_thread.join()

if __name__ == "__main__":
    main()
