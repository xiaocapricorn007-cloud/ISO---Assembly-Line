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
    
    conn.commit()
    
    # Initialize basic stations
    stations = ['Station_A', 'Station_B', 'Station_C_Dark', 'Station_D', 'Station_E']
    for st in stations:
        cursor.execute('''
        INSERT OR IGNORE INTO machines (station_id, status, current_cycle_time, target_cycle_time, operator_id, last_updated)
        VALUES (?, 'IDLE', 0.0, 60.0, 'NONE', ?)
        ''', (st, datetime.now()))
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized at:", DB_PATH)
