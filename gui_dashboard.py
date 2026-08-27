import tkinter as tk
from tkinter import ttk
import pandas as pd
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from db import get_connection

class IsoDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ISO Digital Twin - Real-Time Dashboard")
        self.geometry("1100x700")
        self.configure(bg="#1e1e1e")
        
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Helvetica", 12))
        self.style.configure("TFrame", background="#1e1e1e")
        self.style.configure("TNotebook", background="#1e1e1e", tabmargins=[2, 5, 2, 0])
        self.style.configure("TNotebook.Tab", background="#2b2b2b", foreground="white", padding=[10, 5], font=("Helvetica", 11, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", "#4a4a4a")])
        self.style.configure("Header.TLabel", font=("Helvetica", 16, "bold"))
        self.style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b")
        
        # NOTEBOOK (TABS)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- TAB 1: S-TATECON & O-PTINECK (Main KPI) ---
        self.tab_main = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_main, text="Global Overview (S-TATECON / O-PTINECK)")
        self.setup_main_tab()
        
        # --- TAB 2: I-DENDEF (Telemetry & Alerts) ---
        self.tab_idendef = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_idendef, text="I-DENDEF (Vibration Inference)")
        self.setup_idendef_tab()
        
        # Start update loop
        self.update_dashboard()

    def setup_main_tab(self):
        self.kpi_frame = tk.Frame(self.tab_main, bg="#1e1e1e")
        self.kpi_frame.pack(fill="x", pady=20, padx=20)
        
        self.dey_label = ttk.Label(self.kpi_frame, text="DEY: -- units/hr", style="Header.TLabel")
        self.dey_label.pack(side="left", padx=20)
        
        self.bottleneck_label = ttk.Label(self.kpi_frame, text="Bottleneck: --", style="Header.TLabel")
        self.bottleneck_label.pack(side="left", padx=20)
        
        ttk.Label(self.tab_main, text="Live Station States").pack(anchor="w", padx=20)
        
        columns = ("Station", "Status", "Cycle Time", "Target", "Updated")
        self.tree = ttk.Treeview(self.tab_main, columns=columns, show="headings", height=8)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(fill="x", padx=20, pady=10)
        
        ttk.Label(self.tab_main, text="Phantom Veto / Fault Logs").pack(anchor="w", padx=20)
        self.log_text = tk.Text(self.tab_main, height=10, bg="#2b2b2b", fg="#ff4c4c", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=20, pady=5)

    def setup_idendef_tab(self):
        # Alert banner
        self.alert_var = tk.StringVar()
        self.alert_var.set("I-DENDEF Status: NORMAL")
        self.alert_label = tk.Label(self.tab_idendef, textvariable=self.alert_var, font=("Helvetica", 16, "bold"), bg="#1e1e1e", fg="#00ff00")
        self.alert_label.pack(pady=10)
        
        # Matplotlib Figure
        self.fig, self.ax = plt.subplots(figsize=(8, 4), facecolor='#1e1e1e')
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.set_title("Live Vibration Telemetry (Time Domain)", color="white")
        self.ax.set_xlabel("Time Step", color="white")
        self.ax.set_ylabel("Amplitude", color="white")
        self.line, = self.ax.plot([], [], color="#00ff00", lw=2)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab_idendef)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)
        
        # Text log for inference details
        self.idendef_log = tk.Text(self.tab_idendef, height=5, bg="#2b2b2b", fg="white", font=("Consolas", 10))
        self.idendef_log.pack(fill="x", padx=20, pady=10)

    def update_dashboard(self):
        try:
            conn = get_connection()
            
            # --- Update Main Tab ---
            df_metrics = pd.read_sql("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1", conn)
            if not df_metrics.empty:
                dey = df_metrics['dey'].iloc[0]
                btl = df_metrics['bottleneck_station'].iloc[0]
                self.dey_label.config(text=f"DEY: {dey:.2f} units/hr")
                self.bottleneck_label.config(text=f"Bottleneck: {btl}")
                
            df_machines = pd.read_sql("SELECT station_id, status, current_cycle_time, target_cycle_time, last_updated FROM machines", conn)
            for row in self.tree.get_children():
                self.tree.delete(row)
            for _, r in df_machines.iterrows():
                self.tree.insert("", "end", values=(r['station_id'], r['status'], round(r['current_cycle_time'], 1), r['target_cycle_time'], r['last_updated']))
                
            df_phantom = pd.read_sql("SELECT * FROM phantom_logs ORDER BY timestamp DESC LIMIT 5", conn)
            self.log_text.delete(1.0, tk.END)
            for _, r in df_phantom.iterrows():
                self.log_text.insert(tk.END, f"[{r['timestamp']}] VETO: Human '{r['human_input']}' vs PLC '{r['plc_truth']}' -> {r['action_taken']}\n")
                
            # --- Update I-DENDEF Tab ---
            df_telemetry = pd.read_sql("SELECT * FROM telemetry_logs ORDER BY id DESC LIMIT 1", conn)
            if not df_telemetry.empty:
                vib_data = json.loads(df_telemetry['vibration_data'].iloc[0])
                is_anomaly = df_telemetry['is_anomaly'].iloc[0]
                station = df_telemetry['station_id'].iloc[0]
                timestamp = df_telemetry['timestamp'].iloc[0]
                
                # Update Plot
                self.line.set_xdata(range(len(vib_data)))
                self.line.set_ydata(vib_data)
                self.ax.relim()
                self.ax.autoscale_view()
                
                if is_anomaly:
                    self.line.set_color("#ff4c4c")
                    self.alert_var.set(f"I-DENDEF ALARM! Anomaly detected at {station}")
                    self.alert_label.config(fg="#ff4c4c")
                    self.idendef_log.insert(1.0, f"[{timestamp}] Anomaly triggered at {station}. Sub-line buffer engaged.\n")
                else:
                    self.line.set_color("#00ff00")
                    self.alert_var.set("I-DENDEF Status: NORMAL")
                    self.alert_label.config(fg="#00ff00")
                    
                self.canvas.draw()
                
            conn.close()
        except Exception as e:
            pass # Fail silently if DB is locked during read
            
        # Refresh every 1000ms
        self.after(1000, self.update_dashboard)

if __name__ == "__main__":
    app = IsoDashboard()
    app.mainloop()
