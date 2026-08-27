import tkinter as tk
from tkinter import ttk
import pandas as pd
from db import get_connection

class IsoDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ISO Digital Twin - Real-Time Dashboard")
        self.geometry("1000x600")
        self.configure(bg="#1e1e1e")
        
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Helvetica", 12))
        self.style.configure("Header.TLabel", font=("Helvetica", 16, "bold"))
        self.style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b")
        
        # --- TOP KPI FRAME ---
        self.kpi_frame = tk.Frame(self, bg="#1e1e1e")
        self.kpi_frame.pack(fill="x", pady=20, padx=20)
        
        self.dey_label = ttk.Label(self.kpi_frame, text="DEY: -- units/hr", style="Header.TLabel")
        self.dey_label.pack(side="left", padx=20)
        
        self.bottleneck_label = ttk.Label(self.kpi_frame, text="Bottleneck: --", style="Header.TLabel")
        self.bottleneck_label.pack(side="left", padx=20)
        
        # --- DATA FRAME ---
        self.data_frame = tk.Frame(self, bg="#1e1e1e")
        self.data_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ttk.Label(self.data_frame, text="Live Station States (S-TATECON)").pack(anchor="w")
        
        columns = ("Station", "Status", "Cycle Time", "Target", "Updated")
        self.tree = ttk.Treeview(self.data_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(fill="x", pady=10)
        
        # --- LOG FRAME ---
        ttk.Label(self.data_frame, text="Phantom Veto / Fault Logs").pack(anchor="w")
        self.log_text = tk.Text(self.data_frame, height=10, bg="#2b2b2b", fg="#ff4c4c", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, pady=5)
        
        # Start update loop
        self.update_dashboard()

    def update_dashboard(self):
        try:
            conn = get_connection()
            # 1. Update KPIs
            df_metrics = pd.read_sql("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1", conn)
            if not df_metrics.empty:
                dey = df_metrics['dey'].iloc[0]
                btl = df_metrics['bottleneck_station'].iloc[0]
                self.dey_label.config(text=f"DEY: {dey:.2f} units/hr")
                self.bottleneck_label.config(text=f"Bottleneck: {btl}")
                
            # 2. Update Treeview
            df_machines = pd.read_sql("SELECT station_id, status, current_cycle_time, target_cycle_time, last_updated FROM machines", conn)
            for row in self.tree.get_children():
                self.tree.delete(row)
            for _, r in df_machines.iterrows():
                self.tree.insert("", "end", values=(r['station_id'], r['status'], round(r['current_cycle_time'], 1), r['target_cycle_time'], r['last_updated']))
                
            # 3. Update Logs
            df_phantom = pd.read_sql("SELECT * FROM phantom_logs ORDER BY timestamp DESC LIMIT 5", conn)
            self.log_text.delete(1.0, tk.END)
            for _, r in df_phantom.iterrows():
                self.log_text.insert(tk.END, f"[{r['timestamp']}] VETO: Human '{r['human_input']}' vs PLC '{r['plc_truth']}' -> {r['action_taken']}\n")
                
            conn.close()
        except Exception as e:
            print("Error updating dashboard:", e)
            
        # Refresh every 1000ms (1 sec)
        self.after(1000, self.update_dashboard)

if __name__ == "__main__":
    app = IsoDashboard()
    app.mainloop()
