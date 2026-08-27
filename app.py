import streamlit as st
import pandas as pd
from db import get_connection
import time

st.set_page_config(layout="wide", page_title="ISO Digital Twin")

st.title("ISO Digital Twin: Assembly Line Dashboard")
st.markdown("Monitoring the Dynamic Equilibrium Yield (DEY) and Constraint-Aware AI Pipelines in Real-Time.")

# Placeholder for real-time data
placeholder = st.empty()

def load_data():
    conn = get_connection()
    df_machines = pd.read_sql("SELECT * FROM machines", conn)
    df_metrics = pd.read_sql("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 50", conn)
    df_phantom = pd.read_sql("SELECT * FROM phantom_logs ORDER BY timestamp DESC LIMIT 5", conn)
    conn.close()
    return df_machines, df_metrics, df_phantom

while True:
    df_machines, df_metrics, df_phantom = load_data()
    
    with placeholder.container():
        # Top KPI row
        col1, col2, col3 = st.columns(3)
        if not df_metrics.empty:
            current_dey = df_metrics['dey'].iloc[0]
            bottleneck = df_metrics['bottleneck_station'].iloc[0]
            col1.metric("Dynamic Equilibrium Yield (DEY)", f"{current_dey:.2f} units/hr")
            col2.metric("Current Bottleneck", bottleneck)
        else:
            col1.metric("Dynamic Equilibrium Yield (DEY)", "Calculating...")
            col2.metric("Current Bottleneck", "Calculating...")
            
        col3.metric("Phantom State Vetoes", len(df_phantom) if not df_phantom.empty else 0)
        
        st.markdown("---")
        
        # Two columns for Layout
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("Machine States (S-TATECON)")
            st.dataframe(df_machines, use_container_width=True)
            
            st.subheader("DEY Trend Over Time")
            if not df_metrics.empty:
                st.line_chart(df_metrics.set_index('timestamp')['dey'])
                
        with col_right:
            st.subheader("I-DENDEF & O-PTINECK Alerts")
            if not df_phantom.empty:
                st.error("Phantom State Intercepted!")
                st.dataframe(df_phantom[['human_input', 'plc_truth', 'action_taken']])
                
            st.info("O-PTINECK GA Rebalancer Active")
            st.write("Evaluating switching costs to prevent cognitive whiplash...")

    time.sleep(1.0)
