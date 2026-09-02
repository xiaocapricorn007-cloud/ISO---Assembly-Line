# ISO Digital Twin: Assembly Line

A predictive, closed-loop Digital Twin designed specifically for mixed-model automotive assembly lines. Moving beyond reactive dashboards, the ISO ecosystem acts as a paranoid, constraint-aware prediction engine. It anticipates failures, models physical constraints, and optimizes flow before physical execution breaks down on the factory floor.

## Architecture

The architecture is divided into three interdependent pillars, governed by a unifying output metric: the **Dynamic Equilibrium Yield (DEY)**.

1. **[S-TATECON (Central State Management)](docs/S-TATECON.md)**: The digital ontology and single source of truth. Functioning as a singleton database layer, it serves global variables and machine states directly to other modules.
2. **[I-DENDEF (Predictive Quality & Defect Detection)](docs/I-DENDEF.md)**: The predictive quality guard. Expanded to 16 distinct granular machines, it utilizes dual pre-trained PyTorch 1D-Convolution AutoEncoders (TCNs):
    - **Vibration Models**: Evaluates high-frequency spectral reconstruction to detect mechanical bearing degradation.
    - **PLC Kinematics Models**: Evaluates 3D spatial trajectories (`X`, `Y`, `Z`) using `AdaptiveAvgPool1d` to detect progressive tool miscalibration and sudden mechanical slippages.
3. **[O-PTINECK (Proactive Flow & Bottleneck Optimizer)](docs/O-PTINECK.md)**: The bottleneck optimizer. Relies on strict threshold time-based boundary checks (too early/too late) to govern flow.
4. **Veto Engine**: The centralized constraint verification hub (`core/veto_engine.py`) that executes sequential checks including Severity Override, Material Check (Starvation Risk), Whiplash Veto (Cooldown), and Physics Check (Conveyor Speed).

## Simulation Environment & Evaluation

The underlying environment leverages `SimPy` to model parallel machines with independent cycle times and telemetry streams. It features sequential inter-station buffering (`simpy.Store`) and physical raw material inventory (`simpy.Container`), operating on a strict, synchronous pulsed master loop architecture.

Upon interrupting the master orchestrator (`Ctrl+C`), the simulation dumps a comprehensive **Scikit-Learn Evaluation Matrix** (ROC-AUC, PR-AUC, F1-Scores) comparing the hidden simulation Ground Truth anomalies strictly against the independent ML Model predictions.

## Getting Started

The Python-based simulation is powered by a modern **Flask + Chart.js / Tailwind CSS** web dashboard, replacing legacy Streamlit/Tkinter interfaces. It enables:
- 60FPS multi-line overlaid telemetry charts (Vibration and PLC Kinematics).
- Live global alarms and historical timelogs.
- A decoupled, CSS-driven **Animated Flowchart** that seamlessly renders multiple staggered stock units physically moving across the factory lines in real-time.

To run the full simulation, orchestrate the startup sequence (Database wiping -> Web Server -> SimPy Environment) natively using the master orchestrator script:

```bash
pip install -r requirements.txt
python masterstart.py
```