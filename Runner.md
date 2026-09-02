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

**[2026-08-29] - Single Car Test Mode & Synchronization Fixes**
- Overhauled simulation/factory_env.py to support a granular 'Single Car' sequential test flow, replacing continuous generation.
- Dynamically tied the inter-station conveyor transit wait time to the master conveyor_belt_speed variable from S-TATECON.
- Refactored un_station_cycle to trigger and await all parallel machines within a station simultaneously, allowing parallel telemetry generation.
- Fixed a critical synchronization bug where BOM starvation previously blocked only the M1 machine while allowing M2/M3 to blindly proceed. The entire station now halts and replenishes in unison.
- Optimized performance by hoisting heavy json imports out of cycle loops and stripping unused simpy.Resource allocations.


**[2026-08-29] - Realtime Environment Migration**
- Replaced the custom 	ime.sleep(0.05) simulation loop with simpy.rt.RealtimeEnvironment(factor=1.0). This forces the single-car test to execute in genuine real-time seconds, preventing the simulation from skipping idle wait periods instantly and flattening the dashboard prematurely.


**[2026-08-29] - Frontend Animation Syncing**
- Stripped the hardcoded frontend startFakeFlowAnimation() mockup loop in index.html.
- Rewrote the animation logic to actively poll the SQLite parts table via a new /api/parts endpoint. 
- The tracking dot is now precisely synchronized with the backend. It glows Emerald when docked inside a station for 4 seconds, and turns Blue when physically translating across the conveyor belts for 10 seconds.


**[2026-08-29] - Global Run/Pause Control Integration**
- Added a \simulation_running\ global flag to the SQLite \system_config\ table, defaulting to 0.0 (Paused) on startup.
- Rewrote SimPy's native \env.timeout\ calls into a custom \pausable_timeout\ generator that evaluates time in 0.1s increments, allowing the real-time simulation to completely freeze mid-cycle if the global flag is set to 0.0.
- Updated \web_app.py\ to expose an \/api/toggle_sim\ endpoint.
- Injected a master \START SIMULATION\ / \PAUSE\ toggle button into the top-left header of \index.html\.
- Linked the frontend animation logic to freeze CSS transitions immediately when the system is paused, perfectly syncing the visual flowchart, live telemetry graphs, and backend database lock.


**[2026-08-29] - Animation & Timing Synchronization Fixes**
- Fixed a bug in \index.html\ where \syncPartAnimation()\ was omitted from the main Javascript \setInterval\ loop, preventing the dot from spawning dynamically.
- Rescaled the physics engine timings: Target station cycle times (e.g. 60s) now accurately map to **10 seconds** of real-world processing wait time. 
- Inter-station conveyor transit wait time is now explicitly calculated as **5 seconds**, dynamically coupled to the master \conveyor_belt_speed\ S-TATECON variable.


**[2026-08-29] - Multi-Car Pipeline Scaling & Station Locks**
- Upgraded the backend from a single-car flow to a continuous, staggered assembly pipeline ('N' cars). 
- Implemented \simpy.Resource(capacity=1)\ locks for each station to enforce strict queueing physics, preventing overlapping telemetry if a station breaks down.
- Implemented a \part_generator\ that dynamically spaces incoming cars by exactly \(target_ct / 6.0) + transit_time\. This ensures that exactly when Car1 arrives at Station B, Car2 spawns into Station A.
- Re-verified frontend tracking logic to handle concurrent spawning, tracking, and deletion of multiple independent vehicle dots simultaneously.


**[2026-08-29] - Global Production Counter Integration**
- Added \units_produced\ tracking to the S-TATECON global parameter configuration.
- The physics engine now precisely increments this global database counter exactly when a vehicle passes the Final Assembly cell and reaches 'Completed' status.
- Injected a live \Units Prod.\ neon counter to the top-right header of the web dashboard, automatically synced with the DB via the \/api/state\ JSON payload.


**[2026-08-29] - Shutdown Error Prevention**
- Moved heavy ML library imports (like \scikit-learn\) to the global scope of \masterstart.py\ to prevent \importlib._bootstrap_external\ Tracebacks when users forcefully kill the simulation during the shutdown evaluation phase.


**[2026-08-29] - Rigid Pulsed Synchronous Assembly Line**
- Completely restructured the asynchronous SimPy physics engine into a single, master-controlled synchronous loop (\master_line_loop\).
- The line now operates on strict 'Pulsed' mechanics: All cars shift simultaneously, and all stations process simultaneously.
- Introduced a global 'Transit Phase' (5s): All machines go \IDLE\, all telemetry flatlines, and no ML models evaluate while cars are translating across the physical conveyor belts.
- If any station breaks down or starves, the \yield simpy.events.AllOf()\ lock enforces that the entire global factory pipeline halts and waits for the bottleneck to resolve before allowing the next pulse.


**[2026-08-29] - Outbound Transit Animation & Counter Delay**
- Modified the master loop so that cars finishing \Final_Assembly\ now enter a formal 5-second \Conveyor (To Completed)\ transit state.
- Updated the frontend CSS tracking system to map this state to an 'Outbound' trajectory, allowing the dot to smoothly glide off-screen to the right.
- The global \units_produced\ counter is now strictly incremented *after* this 5-second outbound transit finishes, rather than instantaneously, providing a more realistic visual conclusion to the vehicle's lifecycle.


**[2026-08-29] - Visual Fidelity & CSS Animation Timing**
- Cleaned up the frontend UI by stripping out the static BOM inventory numbers from underneath the station boxes, reducing flowchart clutter.
- Dynamically mapped the CSS \	ransition\ durations to the exact physics states: Dots now smoothly glide for a full 5.0s during \Outbound\ and transit states, and quickly snap (1.0s) when docking into stations. 
- The newly updated \Buffer_Raw\ inbound transit perfectly mimics a slow 5.0s roll-on from the left side of the screen, and the \Outbound\ transit maps to a complete roll-off on the right before the global \units_produced\ counter ticks.


**[2026-08-29] - Visual Glide Smoothing & Animation Bugfixes**
- Fixed a string matching typo where \Conveyor (To Final_Assembly)\ from the backend was dropped by the frontend map, preventing the animation from tracking cars entering the final cell.
- Rewrote the CSS \	argetLeft\ calculation: Transit animations now target the final destination box directly instead of stopping at the geometric midpoint. This allows the 5.0s CSS transition to perfectly match the 5.0s backend transit timer, creating a flawlessly smooth glide from station to station with zero jitter.


**[2026-08-29] - Global Machine State Synchronization**
- Removed the 'Conveyor Belt Speed' UI slider and its associated config logic entirely, as it broke synchronization between the hardcoded frontend CSS animations and the dynamic backend simulator. The global transit time is now strictly fixed at 5.0 seconds.
- Re-architected machine \IDLE\ transitions. Individual \machine_tasks\ no longer set themselves to \IDLE\ when finishing their cycles early. Instead, the \master_line_loop\ globally forces all machines to \IDLE\ exactly at the millisecond the Transit Phase begins. This guarantees the dashboard accurately highlights machines as active for the entire duration the car is docked in the station, and flawlessly drops them to IDLE exactly when the dot hits the conveyor.


**[2026-08-29] - Exact Cycle Time Synchronization**
- Redefined the global \	arget_cycle_time\ from 60.0s to 10.0s in the S-TATECON architecture.
- Removed the \/ 6.0\ artificial speed-up factor in the physics engine. The simulator now accurately generates telemetry for a true 10-second physical window.
- Updated the frontend Chart.js configurations to explicitly render the X-axis labels from \ .0s\ to \10.0s\ to accurately reflect the new cycle time bounds.


**[2026-08-30] - Removed Legacy Station Overrides**
- Traced a critical flaw where cars were taking 60+ seconds to move between stations despite the global \	arget_cycle_time\ being set to 10.0s. 
- Discovered legacy hardcoded overrides in \self.station_cycle_times\ inside \statecon.py\ (e.g., \Painting: 65.0\) that were silently hijacking the global configuration.
- Replaced all legacy overrides with 10.0s to perfectly sync every station to the new pulsed 10s timeframe.
 
 
**[2026-09-02] - Final Logic Streamlining (Scrapped Features)**
- **Scrapped UI Flowchart Inventory Bindings**: Decided to permanently abandon binding the SimPy BOM inventory numbers to the visual flowchart DOM elements (originally planned for Phase 6). The UI flowchart is cleaner without the text clutter, and inventory remains accurately tracked and displayed in the dedicated "Real-Time BOM Inventory Tracking" table below it.
- **Scrapped 50s Repair Mechanic**: Dropped the legacy 50s sim-time shutdown repair loop (originally planned for Phase 4) in favor of the new V2 rigid pulsed simulation loop. Anomalous machines now naturally delay the global line synchronization (by a smaller multiplier) rather than entering a forced, extended offline state, creating a smoother and more realistic continuous assembly pipeline.

**[2026-09-02] - Documentation & Proposal Preparation**
- Drafted a comprehensive `Technical_Evaluation.md` breaking down the core stack, synchronized pulsed physics mechanics, 16-machine granular ML pipelines, and Scikit-Learn evaluation matrix.
- Created placeholder `Business_Proposal.md` pending future requirements.
- Updated `README.md` to ensure perfectly clean startup instructions for new clones of the repository.
