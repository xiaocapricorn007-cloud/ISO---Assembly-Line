import subprocess
import sys
import time
import threading
from db import init_db

def stream_output(pipe, prefix):
    """Reads lines from a subprocess pipe and prints them with a prefix."""
    with pipe:
        for line in iter(pipe.readline, b''):
            try:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line:
                    print(f"{prefix} {decoded_line}")
            except Exception:
                pass

def main():
    print("===========================================")
    print(" ISO DIGITAL TWIN - MASTER STARTUP SCRIPT  ")
    print("===========================================")
    
    # 1. Initialize S-TATECON Database
    print("[MASTER] Initializing S-TATECON Database...")
    init_db()
    print("[MASTER] Database ready.")
    
    processes = []
    
    try:
        # 2. Launch Web Server Dashboard
        print("[MASTER] Launching Flask Web Server...")
        gui_proc = subprocess.Popen(
            [sys.executable, "web_app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        processes.append(gui_proc)
        
        # Start background thread to stream GUI output
        threading.Thread(target=stream_output, args=(gui_proc.stdout, "[WEB]"), daemon=True).start()
        
        # Wait for Server to boot
        time.sleep(2.0)
        
        # 3. Launch Main Simulation
        print("[MASTER] Launching Factory Simulation...")
        sim_proc = subprocess.Popen(
            [sys.executable, "main_sim.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        processes.append(sim_proc)
        
        # Start background thread to stream Sim output
        threading.Thread(target=stream_output, args=(sim_proc.stdout, "[SIM]"), daemon=True).start()
        
        print("===========================================")
        print(" SYSTEM ONLINE. Press Ctrl+C to force exit.")
        print("===========================================")
        
        # 4. Block and wait until user stops the script
        while True:
            time.sleep(1)
            # If both processes died on their own, exit
            if all(p.poll() is not None for p in processes):
                print("[MASTER] All child processes have exited.")
                break
                
    except KeyboardInterrupt:
        print("\n[MASTER] Force exit requested. Terminating all processes...")
    finally:
        # 5. Graceful Cleanup
        for p in processes:
            if p.poll() is None: # If process is still running
                p.terminate()
                p.wait(timeout=3)
        print("[MASTER] ISO Digital Twin safely shut down.")

if __name__ == "__main__":
    main()
