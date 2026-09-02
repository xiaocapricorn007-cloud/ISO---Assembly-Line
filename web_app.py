from flask import Flask, render_template, jsonify, request
import sqlite3
import pandas as pd
import json
import os
import logging
from db import get_connection

app = Flask(__name__)

# Suppress Werkzeug HTTP request logging (the continuous GET prints)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

TOPOLOGY = {
    'Pressing': 3, 'Welding': 2, 'Painting': 5,
    'PowerTrain': 4, 'Final_Assembly': 2
}

@app.route('/')
def index():
    return render_template('index.html', topology=TOPOLOGY)

@app.route('/api/state')
def get_state():
    conn = None
    try:
        conn = get_connection()
        
        # Metrics
        df_metrics = pd.read_sql("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1", conn)
        dey = df_metrics['dey'].iloc[0] if not df_metrics.empty else 0.0
        bottleneck = df_metrics['bottleneck_station'].iloc[0] if not df_metrics.empty else "--"
        
        # Machines
        df_machines = pd.read_sql("SELECT station_id, status, current_cycle_time, target_cycle_time FROM machines", conn)
        machines = df_machines.to_dict(orient='records')
        
        # Veto Logs
        df_phantom = pd.read_sql("SELECT * FROM phantom_logs ORDER BY timestamp DESC LIMIT 5", conn)
        logs = df_phantom.to_dict(orient='records')
        
        # Units Produced
        df_units = pd.read_sql("SELECT value FROM system_config WHERE key='units_produced'", conn)
        units = int(df_units['value'].iloc[0]) if not df_units.empty else 0
        
        return jsonify({"dey": dey, "bottleneck": bottleneck, "machines": machines, "logs": logs, "units": units})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/parts')
def get_parts():
    conn = None
    try:
        conn = get_connection()
        query = "SELECT part_id, current_location, status FROM parts WHERE current_location != 'Completed' "
        df_parts = pd.read_sql(query, conn)
        return jsonify(df_parts.to_dict(orient='records'))
    except Exception as e:
        return jsonify([])
    finally:
        if conn: conn.close()

@app.route('/api/inventory', methods=['GET', 'POST'])
def get_inventory():
    conn = None
    try:
        conn = get_connection()
        if request.method == 'POST':
            data = request.json
            cursor = conn.cursor()
            for key, val in data.items():
                st, part = key.split('_', 1)
                cursor.execute("UPDATE inventory SET on_hand=? WHERE station_id=? AND part_id=?", (int(val), st, part))
                cursor.execute("UPDATE system_config SET value=? WHERE config_group='bom_onhand' AND key=?", (float(val), f"{key}_on_hand"))
            conn.commit()
            return jsonify({"status": "success"})
        query = "SELECT station_id, part_id, category, on_hand FROM inventory"
        query = "SELECT station_id, part_id, category, on_hand FROM inventory"
        df_inv = pd.read_sql(query, conn)
        
        # Also fetch qty_per_car from config to calculate starvation
        df_cfg = pd.read_sql("SELECT key, value FROM system_config WHERE config_group='bom_qty'", conn)
        
        qty_map = {}
        for _, row in df_cfg.iterrows():
            # row['key'] is e.g. "Pressing_Steel_Coils_qty_per_car"
            st_part = row['key'].replace("_qty_per_car", "")
            qty_map[st_part] = int(row['value'])
            
        inv_dict = {}
        for _, row in df_inv.iterrows():
            st = row['station_id']
            part_id = row['part_id']
            composite_key = f"{st}_{part_id}"
            inv_dict[composite_key] = {
                "station_id": st,
                "part_id": part_id,
                "category": row['category'],
                "on_hand": row['on_hand'],
                "qty_per_car": qty_map.get(composite_key, 1)
            }
        return jsonify(inv_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/config', methods=['GET', 'POST'])
def config_manager():
    conn = None
    try:
        conn = get_connection()
        if request.method == 'POST':
            data = request.json
            cursor = conn.cursor()
            for key, val in data.items():
                cursor.execute("UPDATE system_config SET value=? WHERE key=?", (float(val), key))
            conn.commit()
            return jsonify({"status": "success"})
        else:
            df = pd.read_sql("SELECT config_group, key, value FROM system_config", conn)
            config_dict = {}
            for _, row in df.iterrows():
                cg = row['config_group']
                if cg not in config_dict:
                    config_dict[cg] = {}
                config_dict[cg][row['key']] = row['value']
            return jsonify(config_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/optimize', methods=['POST'])
def run_optimizer():
    try:
        from core.optineck import OptineckEngine
        engine = OptineckEngine()
        result = engine.run_genetic_optimizer()
        engine.conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts', methods=['GET', 'POST'])
def handle_alerts():
    conn = None
    try:
        conn = get_connection()
        if request.method == 'POST':
            # Mark all as read
            conn.execute("UPDATE global_alerts SET is_read = 1")
            conn.commit()
            return jsonify({"status": "success"})
        else:
            df = pd.read_sql("SELECT * FROM global_alerts ORDER BY timestamp DESC LIMIT 50", conn)
            alerts = []
            for _, row in df.iterrows():
                alerts.append({
                    "timestamp": row['timestamp'],
                    "source": row['source'],
                    "message": row['message'],
                    "severity": row['severity'],
                    "is_read": bool(row['is_read'])
                })
            return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/telemetry')
def get_telemetry():
    node = request.args.get('node', '')
    if not node:
        return jsonify([])
        
    conn = None
    try:
        conn = get_connection()
        machines = []
        if node in TOPOLOGY:
            machines = [f"{node}_M{i}" for i in range(1, TOPOLOGY[node] + 1)]
        else:
            machines = [node]
            
        # Fetch statuses to check if machines are idle
        df_status_all = pd.read_sql("SELECT station_id, status FROM machines", conn)
        status_dict = dict(zip(df_status_all['station_id'], df_status_all['status']))
        
        # Check if simulation is paused
        df_sim = pd.read_sql("SELECT value FROM system_config WHERE key='simulation_running'", conn)
        sim_running = float(df_sim['value'].iloc[0]) > 0.5 if not df_sim.empty else False
            
        data = []
        for m_id in machines:
            status = status_dict.get(m_id)
            if status == 'IDLE' or status is None or not sim_running:
                # Machine is dead/idle, hasn't started yet, or simulation is paused -> flatline the data
                data.append({
                    "machine_id": m_id,
                    "vibration": [0.0] * 500,
                    "plc_x": [0.0] * 200,
                    "plc_y": [0.0] * 200,
                    "plc_z": [0.0] * 200,
                    "is_anomaly": False,
                    "timestamp": "",
                    "status": "IDLE"
                })
                continue

            query = f"SELECT * FROM telemetry_logs WHERE station_id='{m_id}' ORDER BY id DESC LIMIT 1"
            df_tel = pd.read_sql(query, conn)
            
            plc_query = f"SELECT * FROM plc_logs WHERE station_id='{m_id}' ORDER BY id DESC LIMIT 1"
            df_plc = pd.read_sql(plc_query, conn)
            
            if not df_tel.empty and not df_plc.empty:
                data.append({
                    "machine_id": m_id,
                    "vibration": json.loads(df_tel['vibration_data'].iloc[0]),
                    "plc_x": json.loads(df_plc['plc_x'].iloc[0]),
                    "plc_y": json.loads(df_plc['plc_y'].iloc[0]),
                    "plc_z": json.loads(df_plc['plc_z'].iloc[0]),
                    "is_anomaly": bool(df_tel['is_anomaly'].iloc[0]) or bool(df_plc['is_anomaly'].iloc[0]),
                    "timestamp": df_tel['timestamp'].iloc[0],
                    "status": status
                })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/alarms')
def get_alarms():
    conn = None
    try:
        conn = get_connection()
        # Fetch the last 20 anomalies triggered across any machine from both ML models
        query = """
        SELECT timestamp, station_id, 'Vibration Anomaly (e.g. Bearing Degradation)' as type FROM telemetry_logs WHERE is_anomaly=1
        UNION
        SELECT timestamp, station_id, 'PLC Anomaly (e.g. Tool Miscalibration)' as type FROM plc_logs WHERE is_anomaly=1
        ORDER BY timestamp DESC LIMIT 20
        """
        df_alarms = pd.read_sql(query, conn)
        return jsonify(df_alarms.to_dict(orient='records'))
    except Exception as e:
        return jsonify([])
    finally:
        if conn: conn.close()

@app.route('/api/toggle_sim', methods=['POST'])
def toggle_sim():
    conn = None
    try:
        data = request.json
        state = float(data.get('state', 0.0))
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE system_config SET value=? WHERE key='simulation_running'", (state,))
        conn.commit()
        return jsonify({"status": "success", "state": state})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    # Disable reloader so it doesn't double-start in masterstart
    app.run(host='127.0.0.1', port=5000, debug=False)
