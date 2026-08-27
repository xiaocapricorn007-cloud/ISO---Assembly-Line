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
        # Top Alert banner
        self.alert_var = tk.StringVar()
        self.alert_var.set("I-DENDEF Status: NORMAL")
        self.alert_label = tk.Label(self.tab_idendef, textvariable=self.alert_var, font=("Helvetica", 16, "bold"), bg="#1e1e1e", fg="#00ff00")
        self.alert_label.pack(pady=5)
        
        # Split layout: Left for Graph, Right for Treeview
        self.paned = ttk.PanedWindow(self.tab_idendef, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True, padx=10, pady=5)
        
        # LEFT: Matplotlib Figure
        self.graph_frame = tk.Frame(self.paned, bg="#1e1e1e")
        self.paned.add(self.graph_frame, weight=3)
        
        self.fig, self.ax = plt.subplots(figsize=(6, 4), facecolor='#1e1e1e')
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.set_title("Live Vibration Telemetry", color="white")
        self.ax.set_xlabel("Time Step", color="white")
        self.ax.set_ylabel("Amplitude", color="white")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.idendef_log = tk.Text(self.graph_frame, height=4, bg="#2b2b2b", fg="white", font=("Consolas", 9))
        self.idendef_log.pack(fill="x", pady=5)
        
        # RIGHT: Treeview Sidebar
        self.sidebar_frame = tk.Frame(self.paned, bg="#1e1e1e")
        self.paned.add(self.sidebar_frame, weight=1)
        
        ttk.Label(self.sidebar_frame, text="Select Machine / Station:").pack(anchor="w")
        
        self.machine_tree = ttk.Treeview(self.sidebar_frame, show="tree")
        self.machine_tree.pack(fill="both", expand=True)
        self.machine_tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # Populate Treeview
        self.topology = {
            'Station_A': 3, 'Station_B': 2, 'Station_C_Dark': 5,
            'Station_D': 4, 'Station_E': 2
        }
        for station, count in self.topology.items():
            parent = self.machine_tree.insert("", "end", iid=station, text=station)
            for i in range(1, count + 1):
                self.machine_tree.insert(parent, "end", iid=f"{station}_M{i}", text=f"Machine {i}")
                
        self.selected_node = None # Can be a Station or a Machine

    def on_tree_select(self, event):
        selected = self.machine_tree.selection()
        if selected:
            self.selected_node = selected[0]

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
                
            # --- Update I-DENDEF Tab (Graphing) ---
            if self.selected_node:
                self.ax.clear()
                self.ax.set_title(f"Telemetry: {self.selected_node}", color="white")
                self.ax.set_xlabel("Time Step", color="white")
                self.ax.set_ylabel("Amplitude", color="white")
                
                # Determine if selected is a Station or Machine
                if self.selected_node in self.topology: # It's a Station
                    machines = [f"{self.selected_node}_M{i}" for i in range(1, self.topology[self.selected_node] + 1)]
                else: # It's a Machine
                    machines = [self.selected_node]
                    
                colors = ['#00ff00', '#00ccff', '#ff00ff', '#ffff00', '#ff9900']
                
                global_anomaly = False
                
                for idx, m_id in enumerate(machines):
                    # Get latest log for this specific machine
                    query = f"SELECT * FROM telemetry_logs WHERE station_id='{m_id}' ORDER BY id DESC LIMIT 1"
                    df_tel = pd.read_sql(query, conn)
                    
                    if not df_tel.empty:
                        vib_data = json.loads(df_tel['vibration_data'].iloc[0])
                        is_anomaly = df_tel['is_anomaly'].iloc[0]
                        timestamp = df_tel['timestamp'].iloc[0]
                        
                        color = "#ff4c4c" if is_anomaly else colors[idx % len(colors)]
                        self.ax.plot(vib_data, color=color, lw=1.5, label=m_id)
                        
                        if is_anomaly:
                            global_anomaly = True
                            # Prevent log spam, only insert if not already there
                            log_msg = f"[{timestamp}] ALARM! TCN Anomaly at {m_id}.\n"
                            if log_msg not in self.idendef_log.get(1.0, tk.END):
                                self.idendef_log.insert(1.0, log_msg)
                                
                if len(machines) > 1:
                    self.ax.legend(loc="upper right", fontsize='small')
                    
                if global_anomaly:
                    self.alert_var.set("I-DENDEF ALARM! Anomaly Detected!")
                    self.alert_label.config(fg="#ff4c4c")
                else:
                    self.alert_var.set("I-DENDEF Status: NORMAL")
                    self.alert_label.config(fg="#00ff00")
                    
                self.canvas.draw()
                
            conn.close()
        except Exception as e:
            pass # Fail silently if DB is locked
            
        self.after(1000, self.update_dashboard)

if __name__ == "__main__":
    app = IsoDashboard()
    app.mainloop()
