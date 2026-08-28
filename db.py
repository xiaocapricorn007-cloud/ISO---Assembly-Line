import sqlite3
import os
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "factory_state.db")

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Machine States
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS machines (
        station_id TEXT PRIMARY KEY,
        status TEXT,
        current_cycle_time REAL,
        target_cycle_time REAL,
        operator_id TEXT,
        last_updated TIMESTAMP
    )
    ''')
    
    # System Metrics (DEY)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS metrics (
        timestamp TIMESTAMP,
        dey REAL,
        max_ct REAL,
        bottleneck_station TEXT,
        event_log TEXT
    )
    ''')
    
    # Operator States
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS operators (
        operator_id TEXT PRIMARY KEY,
        current_station TEXT,
        fatigue_level REAL,
        status TEXT
    )
    ''')

    # Phantom State Logs (S-TATECON Vetoes)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS phantom_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP,
        human_input TEXT,
        plc_truth TEXT,
        action_taken TEXT
    )
    ''')
    
    # I-DENDEF Telemetry Logs (Vibration arrays)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS telemetry_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP,
        station_id TEXT,
        vibration_data TEXT,
        is_anomaly BOOLEAN
    )
    ''')
    
    # I-DENDEF PLC Telemetry Logs (X, Y, Z arrays)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS plc_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP,
        station_id TEXT,
        plc_x TEXT,
        plc_y TEXT,
        plc_z TEXT,
        is_anomaly BOOLEAN
    )
    ''')
    
    # Parts Tracking (Inventory)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parts (
        part_id TEXT PRIMARY KEY,
        current_location TEXT,
        status TEXT,
        last_updated TIMESTAMP
    )
    ''')
    
    # ML Evaluation Tracker
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ml_eval_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP,
        machine_id TEXT,
        anomaly_type TEXT,
        defect_vib BOOLEAN,
        defect_plc BOOLEAN,
        vib_mse REAL,
        plc_mse REAL
    )
    ''')
    
    # Clear ghost data from previous runs
    cursor.execute('DELETE FROM machines')
    cursor.execute('DELETE FROM telemetry_logs')
    cursor.execute('DELETE FROM plc_logs')
    cursor.execute('DELETE FROM metrics')
    cursor.execute('DELETE FROM phantom_logs')
    cursor.execute('DELETE FROM ml_eval_logs')
    cursor.execute('DELETE FROM parts')
    conn.commit()
    
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized at:", DB_PATH)
