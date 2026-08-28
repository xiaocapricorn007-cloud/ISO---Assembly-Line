# Runner Log

**Purpose:** 
This file serves as a continuous, chronological log of all architectural decisions, code implementations, and modifications made to the `ISO---Assembly-Line` repository. 

Every time a major design decision is finalized or a significant change is committed to the codebase, this log will be updated to ensure a transparent, auditable trail of the project's evolution.

---

## Log Entries

**[2026-08-27] - Initialization & Documentation Setup**
- Cloned the repository from GitHub.
- Created `README.md` to establish the architectural overview of the ISO Digital Twin.
- Created core module documentation in the `docs/` folder (`S-TATECON.md`, `I-DENDEF.md`, `O-PTINECK.md`).
- Created `docs/EntireFlow.md` to map out the complete data lifecycle and interdependencies between the modules.
- Created this `Runner.md` file to track future progress.

**[2026-08-27] - Added Reference Materials**
- Created docs/References directory.
- Copied challenge PDFs from local Downloads folder into the repository.
- Committed and pushed PDFs to GitHub.

**[2026-08-27] - Scaffolded Core Architecture**
- Created plan.md to track implementation.
- Scaffolded db.py for SQLite setup.
- Implemented core/statecon.py, core/idendef.py, and core/optineck.py with mock logic.
- Set up SimPy environment in simulation/factory_env.py.
- Built Streamlit dashboard entry point in pp.py.
- Added equirements.txt.

**[2026-08-27] - Added Additional Reference Materials**
- Copied new files (e.g., Flowchart.png) from local Downloads/AIC into docs/References.
- Committed and pushed updates to GitHub.

**[2026-08-27] - Architecture V2 Pivot (Flowchart Alignment)**
- Conducted /grill-me session to align with the new Flowchart.png.
- Decided to implement real PyTorch/TensorFlow LSTMs for I-DENDEF fatigue prediction.
- Decided to centralize constraints into a new \core/veto_engine.py\.
- Decided to refactor SimPy to include inter-station Buffers and \simpy.Container\ for inventory.
- Updated \plan.md\ to reflect Phase 6/V2 remodel.

**[2026-08-27] - V2 Implementation Phase 1 & 2**
- Added PyTorch/Torchvision/OpenCV to requirements.txt.
- Rewrote \core/idendef.py\ into three dedicated models (PyTorch CNN for Vision, Isolation Forest for Vibration, Deterministic Logic for PLC) trained on synthetic data.
- Created \core/veto_engine.py\ to house the sequential Constraint Verification Logic.

**[2026-08-27] - O-PTINECK and GUI Update**
- Rewrote \core/statecon.py\ as a Singleton memory hub to serve global variables directly to other modules.
- Rewrote \core/optineck.py\ to rely on strict threshold time-based checks (too early/too late).
- Scrapped Streamlit \pp.py\ in favor of a native \	kinter\ GUI window (\gui_dashboard.py\).

**[2026-08-27] - SimPy V2 Buffer & Inventory Upgrade**
- Rewrote \simulation/factory_env.py\ to use \simpy.Store\ for sequential inter-station buffering.
- Implemented \simpy.Container\ for Raw Materials inventory.
- Wired SimPy physics directly into the new \IdendefEngine\ (passing synthetic tensors) and \VetoEngine\ (triggering checks per part).
- Phase 4 Complete.

**[2026-08-27] - Advanced I-DENDEF Parameter Tuning**
- Configured Vision CNN for \3x224x224\ RGB images (YOLO/Mask R-CNN mock).
- Configured Vibration model for 500-step windows with FFT processing to train Isolation Forest on frequency domain.
- Upgraded PLC logic to strictly enforce 3D Euclidean spatial coordinates (X, Y, Z) with a 2.0mm tolerance.
- Tightened S-TATECON/O-PTINECK thresholds to [Min: 58s, Max: 65s] to force Veto Engine triggers.

**[2026-08-27] - Advanced Interactive GUI Dashboard**
- Added \	elemetry_logs\ table to SQLite schema (\db.py\) to track vibration strings.
- Configured \actory_env.py\ to serialize and log vibration tensors to the DB per cycle.
- Upgraded \gui_dashboard.py\ to use \	tk.Notebook\ for modular tabs.
- Integrated \matplotlib.backends.backend_tkagg\ to plot live, dynamic vibration waves directly inside the I-DENDEF tab, triggering red alerts upon anomaly detection.

**[2026-08-27] - Master Orchestrator Script**
- Implemented \masterstart.py\ to natively orchestrate the startup sequence (DB -> GUI -> Sim).
- Configured child process stdout/stderr capture to prefix logs with \[GUI]\ and \[SIM]\ in a unified master terminal.
- Added graceful shutdown handling on \Ctrl+C\.

**[2026-08-27] - Machine Granularity & Pre-Trained TCN Pipeline**
- Expanded stations into 16 distinct machines (Station A: 3, B: 2, C: 5, D: 4, E: 2).
- Created \	rain_vibration.py\ to generate unique datasets per machine and pre-train 16 distinct PyTorch TCN-AutoEncoders.
- Refactored \idendef.py\ to load pre-trained weights from \models/pretrained/\ instead of training in-memory.
- Refactored SimPy environment to use \simpy.Resource\ to model parallel machines with independent cycle times and telemetry streams.

**[2026-08-27] - Interactive Multi-Line GUI Dashboard**
- Redesigned the I-DENDEF tab layout with a \	tk.PanedWindow\.
- Added an interactive \	tk.Treeview\ sidebar to display the hierarchical 16-machine topology.
- If a specific Machine is clicked, the Matplotlib canvas dynamically renders only its telemetry.
- If a parent Station is clicked, the canvas overlays the telemetry of all its child machines concurrently using multi-colored plots.

**[2026-08-27] - Bugfix: ML Inference False Positives**
- Fixed a critical data mismatch where the SimPy environment was generating a generic 10Hz wave for all normal vibration data, instead of the specific unique frequencies (12.5Hz - 50Hz) the TCN models were trained on.
- Updated \idendef.py\ to load and store \ase_freq\ from the \.pth\ files and passed it to \actory_env.py\ to generate the correct baseline telemetry.
- Fixed the untrained PyTorch CNN which was randomly outputting defects due to uninitialized weights by mocking the final decision boundary based on tensor mean.

**[2026-08-27] - Memory Optimization (GUI Stutter Fix)**
- Temporarily disabled the PyTorch \VisualDefectModel\ (MockYOLOCNN) and stripped out the heavy \3x224x224\ image tensor generation per cycle from \actory_env.py\.
- This significantly reduces RAM and CPU overhead, dedicating full memory bandwidth to the 16 parallel TCN-AutoEncoders tracking vibrations.

**[2026-08-27] - Web Dashboard Pivot**
- Replaced the \Tkinter\ Python GUI with a \Flask\ web server (\web_app.py\).
- Designed a modern HTML/CSS frontend (\	emplates/index.html\) using Tailwind CSS and Chart.js.
- The web dashboard queries telemetry endpoints to render 60FPS multi-line overlaid vibration charts instantly in the browser, eliminating the Python GUI bottlenecks.

**[2026-08-27] - Global Alerts & Collapsible Sidebar**
- Added CSS toggles in \index.html\ to allow collapsing/expanding the Station folders in the Treeview without losing graph focus.
- Rewrote the alerting logic to run globally via the \etchState\ poll. If ANY machine across the 16 nodes triggers an anomaly, its name in the sidebar will instantly turn bold RED, and the top banner will trigger a Global Alarm, regardless of which graph is currently active.

**[2026-08-27] - Repair Mechanic & Dashboard Tabs**
- Fixed a database upsert bug where granular machines weren't properly registering their states in S-TATECON.
- Implemented a repair mechanic in the simulation: When an anomaly occurs, the machine goes OFFLINE for 50 simulated seconds (displaying RED), before rectifying itself back to normal (GREEN).
- Separated the web UI into multiple Tabs (Dashboard and S-TATECON) for a cleaner layout.
- Added a live Alarm Timelog to the Dashboard to track exactly when and where past anomalies occurred.

**[2026-08-27] - DB Wipe & Startup Stabilizer**
- Cleared a massive logic bug where old ghost records (from previous test runs) in SQLite were permanently triggering the UI dashboard alarm.
- Updated `db.py` to forcefully TRUNCATE/DELETE all telemetry, metric, and machine state tables upon a fresh `masterstart` boot.
- Implemented a 3-second 'Initializing Digital Twin' splash overlay on the frontend web dashboard to pause polling, allowing the backend to fully stabilize its data streams before rendering.

**[2026-08-28] - Documentation Update for V2 Architecture**
- Updated `README.md` to fully reflect the V2 remodel based on `Runner.md` and `plan.md`.
- Reflected the shift to a PyTorch TCN 16-machine granular architecture for I-DENDEF, the addition of the centralized Veto Engine, and the new Flask + Chart.js web dashboard.

**[2026-08-28] - PLC Logic Integration & Multi-Joint Modeling**
- Expanded I-DENDEF to evaluate 3D robotic tool coordinates (X, Y, Z).
- Created a PyTorch `PLC_TCNAutoEncoder` designed to dynamically handle varying sequence lengths.
- Implemented `train_plc.py` to generate unique synthetic multi-joint robotic kinematics for all 16 machines and pre-train specific anomaly thresholds.
- Updated the backend (`idendef.py`, `factory_env.py`, `db.py`) to process and log PLC deviations into a new `plc_logs` SQLite table.

**[2026-08-28] - Dashboard UI Overhaul & Optimization**
- Completely redesigned `index.html` to optimize the operator viewing experience.
- Implemented a side-by-side flexbox layout for the Vibration and PLC charts to eliminate vertical scrolling.
- Enhanced the UI with a refined dark mode palette, custom scrollbars, SVG iconography, status badges, and polished gradient borders.

**[2026-08-28] - Advanced Model Tuning & Ground-Truth Evaluation Matrix**
- Increased PyTorch PLC training dataset from 1000 to 3000 samples and deepened epochs from 15 to 60.
- Implemented rigorous Z-Score statistical thresholding (`mean + 4 * std`) to bound the False Positive rate.
- Tuned the `factory_env.py` anomaly generator to introduce sudden mechanical slippages in the Z-axis.
- Hooked `masterstart.py` to intercept `Ctrl+C` and output a fully automated Scikit-Learn evaluation matrix (ROC-AUC, PR-AUC, F1-Scores) comparing the hidden Ground Truths to the independent ML Predictions.

**[2026-08-28] - Animated S-TATECON Flowchart & Parts Tracking**
- Added a `parts` tracking table to the SQLite schema to log live inventory positions (Buffer vs Station).
- Integrated a physical conveyor-transit delay (`yield env.timeout(3.0)`) into the SimPy backend to accurately map to real-world physics.
- Replaced the boring static S-TATECON table with a visually stunning decoupled CSS-driven Assembly Line Flowchart UI.
- Programmed a custom JavaScript logic loop (`startFakeFlowAnimation()`) to generate, continuously track, and seamlessly animate multiple staggered neon blocks sliding through the factory stations at 60FPS.
