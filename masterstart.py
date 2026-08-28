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

def print_ml_evaluation():
    import sqlite3
    import pandas as pd
    try:
        from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, confusion_matrix
    except ImportError:
        print("\n[EVAL] scikit-learn is not installed. Run 'pip install scikit-learn' to view advanced metrics.")
        return

    try:
        conn = sqlite3.connect("factory_state.db")
        df = pd.read_sql("SELECT * FROM ml_eval_logs", conn)
        conn.close()
        
        if df.empty:
            print("\n[EVAL] No ML evaluation data collected yet.")
            return

        print("\n===========================================")
        print("     I-DENDEF ML EVALUATION METRICS        ")
        print("===========================================")

        # --- VIBRATION EVALUATION ---
        print("\n[ VIBRATION TCN-AE MODEL ]")
        y_true_vib = df['anomaly_type'].isin(['Bearing Degradation', 'Catastrophic Collision']).astype(int)
        y_pred_vib = df['defect_vib'].astype(int)
        y_score_vib = df['vib_mse']
        
        if len(y_true_vib.unique()) > 1:
            roc_auc_v = roc_auc_score(y_true_vib, y_score_vib)
            pr_auc_v = average_precision_score(y_true_vib, y_score_vib)
            f1_v = f1_score(y_true_vib, y_pred_vib)
            tn, fp, fn, tp = confusion_matrix(y_true_vib, y_pred_vib).ravel()
            
            print(f"ROC-AUC: {roc_auc_v:.4f}  |  PR-AUC: {pr_auc_v:.4f}  |  F1-Score: {f1_v:.4f}")
            print(f"True Positives (Caught): {tp}  |  False Negatives (Unnoticed): {fn}")
            print(f"True Negatives (Ideal):  {tn}  |  False Positives (False Alarms): {fp}")
            print(f"Avg MSE (Normal): {y_score_vib[y_true_vib==0].mean():.4f} | Avg MSE (Anomaly): {y_score_vib[y_true_vib==1].mean():.4f}")
        else:
            print("Not enough varied data to compute AUC (need both normal and anomalies).")

        # --- PLC EVALUATION ---
        print("\n[ PLC 3D COORDINATE TCN-AE MODEL ]")
        y_true_plc = df['anomaly_type'].isin(['Tool Miscalibration', 'Catastrophic Collision']).astype(int)
        y_pred_plc = df['defect_plc'].astype(int)
        y_score_plc = df['plc_mse']

        if len(y_true_plc.unique()) > 1:
            roc_auc_p = roc_auc_score(y_true_plc, y_score_plc)
            pr_auc_p = average_precision_score(y_true_plc, y_score_plc)
            f1_p = f1_score(y_true_plc, y_pred_plc)
            tn, fp, fn, tp = confusion_matrix(y_true_plc, y_pred_plc).ravel()
            
            print(f"ROC-AUC: {roc_auc_p:.4f}  |  PR-AUC: {pr_auc_p:.4f}  |  F1-Score: {f1_p:.4f}")
            print(f"True Positives (Caught): {tp}  |  False Negatives (Unnoticed): {fn}")
            print(f"True Negatives (Ideal):  {tn}  |  False Positives (False Alarms): {fp}")
            print(f"Avg MSE (Normal): {y_score_plc[y_true_plc==0].mean():.4f} | Avg MSE (Anomaly): {y_score_plc[y_true_plc==1].mean():.4f}")
        else:
            print("Not enough varied data to compute AUC (need both normal and anomalies).")
            
        print("===========================================\n")
    except Exception as e:
        print(f"\n[EVAL] Could not compute metrics: {e}")

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
        
        # 6. Print ML Evaluation Metrics
        print_ml_evaluation()

if __name__ == "__main__":
    main()
