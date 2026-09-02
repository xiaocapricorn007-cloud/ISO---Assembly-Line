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

To run the ISO Digital Twin locally on your machine, follow these steps:

### 1. Installation
Clone the repository and install the necessary Python dependencies (including Flask, SimPy, PyTorch, and Scikit-Learn):

```bash
git clone https://github.com/xiaocapricorn007-cloud/ISO---Assembly-Line.git
cd ISO---Assembly-Line
pip install -r requirements.txt
```

### 2. Boot the Digital Twin
The system utilizes a master orchestrator script that safely wipes old database ghost records, boots the Flask web server, and launches the SimPy physical environment concurrently.

```bash
python masterstart.py
```

### 3. Open the Dashboard & Start Simulation
- Open your browser and navigate to **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)**.
- The simulation is **paused by default**. 
- Click the green **START SIMULATION** button in the top-left corner of the web UI to unfreeze the physics engine and begin the live pipeline.

### 4. Evaluate the Models
Let the cars run through a few cycles to generate live telemetry. When you are finished testing, return to your terminal and safely terminate the program:
- Press `Ctrl + C`
- The system will gracefully shut down the servers and output a complete **Scikit-Learn Evaluation Matrix** (ROC-AUC, PR-AUC, F1-Scores) comparing the simulation's ground truth defects to the ML predictions.