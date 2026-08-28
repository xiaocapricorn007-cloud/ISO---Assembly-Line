# ISO Digital Twin: Assembly Line

A predictive, closed-loop Digital Twin designed specifically for mixed-model automotive assembly lines. Moving beyond reactive dashboards, the ISO ecosystem acts as a paranoid, constraint-aware prediction engine. It anticipates failures, models physical constraints, and optimizes flow before physical execution breaks down on the factory floor.

## Architecture

The architecture is divided into three interdependent pillars, governed by a unifying output metric: the **Dynamic Equilibrium Yield (DEY)**.

1. **[S-TATECON (Central State Management)](docs/S-TATECON.md)**: The digital ontology and single source of truth. Functioning as a singleton database layer, it serves global variables and machine states directly to other modules.
2. **[I-DENDEF (Predictive Quality & Defect Detection)](docs/I-DENDEF.md)**: The predictive quality guard. Expanded to 16 distinct granular machines, it utilizes pre-trained PyTorch 1D-Convolution AutoEncoders (TCN) to dynamically evaluate high-frequency vibration sequence reconstruction and detect anomalies.
3. **[O-PTINECK (Proactive Flow & Bottleneck Optimizer)](docs/O-PTINECK.md)**: The bottleneck optimizer. Relies on strict threshold time-based boundary checks (too early/too late) to govern flow.
4. **Veto Engine**: The centralized constraint verification hub (`core/veto_engine.py`) that executes sequential checks including Severity Override, Material Check (Starvation Risk), Whiplash Veto (Cooldown), and Physics Check (Conveyor Speed).

## Simulation Environment

The underlying environment leverages `SimPy` to model parallel machines with independent cycle times and telemetry streams. It features sequential inter-station buffering (`simpy.Store`), physical raw material inventory (`simpy.Container`), and dynamic repair loops (50s simulation-time shutdowns upon anomaly detection).

## Getting Started

The Python-based simulation is powered by a modern **Flask + Chart.js / Tailwind CSS** web dashboard, replacing legacy Streamlit/Tkinter interfaces. It enables 60FPS multi-line overlaid vibration charts and live global alarms.

To run the full simulation, orchestrate the startup sequence (Database wiping -> Web Server -> SimPy Environment) natively using the master orchestrator script:

```bash
pip install -r requirements.txt
python masterstart.py
```