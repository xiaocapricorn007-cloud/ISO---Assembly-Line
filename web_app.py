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
    'Station_A': 3, 'Station_B': 2, 'Station_C_Dark': 5,
    'Station_D': 4, 'Station_E': 2
}

@app.route('/')
def index():
    return render_template('index.html', topology=TOPOLOGY)

@app.route('/api/state')
def get_state():
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
        
        conn.close()
        return jsonify({"dey": dey, "bottleneck": bottleneck, "machines": machines, "logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/parts')
def get_parts():
    try:
        conn = get_connection()
        query = "SELECT part_id, current_location, status FROM parts WHERE current_location != 'Completed' AND current_location != 'Buffer_Raw'"
        df_parts = pd.read_sql(query, conn)
        conn.close()
        return jsonify(df_parts.to_dict(orient='records'))
    except Exception as e:
        return jsonify([])

@app.route('/api/inventory')
def get_inventory():
    try:
        conn = get_connection()
        query = "SELECT station_id, part_id, on_hand FROM inventory"
        df_inv = pd.read_sql(query, conn)
        conn.close()
        
        inv_dict = {}
        for _, row in df_inv.iterrows():
            inv_dict[row['station_id']] = {
                "part_id": row['part_id'],
                "on_hand": row['on_hand']
            }
        return jsonify(inv_dict)
    except Exception as e:
        return jsonify({})

@app.route('/api/telemetry')
def get_telemetry():
    node = request.args.get('node', '')
    if not node:
        return jsonify([])
        
    try:
        conn = get_connection()
        machines = []
        if node in TOPOLOGY:
            machines = [f"{node}_M{i}" for i in range(1, TOPOLOGY[node] + 1)]
        else:
            machines = [node]
            
        data = []
        for m_id in machines:
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
                    "timestamp": df_tel['timestamp'].iloc[0]
                })
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alarms')
def get_alarms():
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
        conn.close()
        return jsonify(df_alarms.to_dict(orient='records'))
    except Exception as e:
        return jsonify([])

if __name__ == '__main__':
    # Disable reloader so it doesn't double-start in masterstart
    app.run(host='127.0.0.1', port=5000, debug=False)
