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
