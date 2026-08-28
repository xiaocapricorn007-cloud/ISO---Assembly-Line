# Single-Model Assembly Line Architecture & Parameters

When narrowing the system scope down to **one car model moving sequentially across multiple stations** (a single-model assembly line), the variable list simplifies significantly because mixed-model job sequencing ($j$), option variant probability matrices ($P(f, k)$), and multi-model feature usage vectors ($u_{ej}$) drop out.

However, because **each station has its own distinct process timing and machine assets**, several critical variables must be preserved and expanded to model station-by-station line balancing, bottleneck mechanics, buffering, and physical constraints.

---

### Group 1: Global Shift & Production Target Parameters

*Macro parameters governing the overall shift duration and baseline pacing.*

* **$N$**: Shift schedule quantity (target total units to build during the shift).
* **$T$**: Total productive working time available in the shift (e.g., $450\text{ min}$).
* **$c$** / **$c_0$**: Target baseline cycle time ($c = \frac{T}{N}$).
* **$TT$**: Target Takt Time demanded by downstream throughput ($TT = \frac{\text{Available Time}}{\text{Demand}}$).
* **$\eta$**: Line efficiency buffer factor (e.g., $90\%$).
* **$\text{DEY}$**: Dynamic Equilibrium Yield ($DEY = \frac{3600}{\max(CT_i)} \times \eta$).

---

### Group 2: Station & Elemental Task Timing

Variables capturing the individual station process times and balancing mechanics across the multi-station layout.

* **$N_i$ / $n$**: Total number of workstations along the line.
* **$i$**: Station index ($i \in \{1, 2, \dots, N_i\}$).
* **$e$**: Elemental work task identifier ($e \in \{1, \dots, N_e\}$).
* **$t_e$**: Standard baseline duration for work element $e$.
* **$p(e)$**: Immediate predecessor work elements required before element $e$ can begin (precedence constraints).
* **$CT_i$ / $c_i$**: Total assigned station cycle time for station $i$, computed as the sum of its allocated element times:
  $$CT_i = \sum_{e \in \text{Station } i} t_e$$
* **$\max(CT_i)$**: Bottleneck cycle time (the maximum station time across all stations), dictating line throughput:
  $$\text{Effective Cycle Time} = \max_{i}(CT_i)$$
* **$\bar{c}$**: Average station cycle time across the entire line ($\bar{c} = \frac{\sum t_e}{n}$).
* **$d$**: Line balance delay (fraction of idle/wasted time due to unequal station process times):
  $$d = \frac{\max(CT_i) - \bar{c}}{\max(CT_i)}$$

---

### Group 3: Physical Station Kinematics & Inter-Station Buffering

Variables governing unit movement, station length, and buffers between stations with unequal times.

* **$w_i$**: Physical station length / unit spacing at station $i$.
* **$v$**: Master conveyor velocity ($v = \frac{w}{c_0}$).
* **$B_i(t)$**: Dynamic buffer occupancy between station $i$ and station $i+1$ (crucial for isolating stations whose cycle time exceeds Takt Time).
* **$B_{i,\max}$**: Maximum physical capacity of the intermediate buffer decoupling station $i$ and station $i+1$.
* **$\text{Parallel\_Count}_i$**: Number of parallel stations at bottleneck point $i$ (used if an elemental task standard time exceeds the required cycle time).

---

### Group 4: Machine Telemetry & Asset-Level State Variables

Station-level machine parameters tracking nominal speeds, degradation, and operational state.

* **$m$**: Active machine asset identifier at station $i$ (e.g., Press $M_{A1}$, Spot Welder $M_{C1}$, Multi-Spindle Torquer $M_{D2}$).
* **$T_{\text{nom}, m}$**: Nominal machine operation time for asset $m$.
* **$T_{m}$**: Actual stochastic cycle time duration of machine $m$ for the current vehicle:
  $$T_{m} = T_{\text{nom}, m} \cdot \exp(\mu_m + \epsilon_m)$$
* **$f_{0, m}$**: Base harmonic operational frequency of machine $m$.
* **$\text{PLC\_RUN}_m$**: Binary machine status flag ($1 = \text{Running}$, $0 = \text{Halted/Starved/Blocked}$).
* **$\mathcal{S}_m(t)$**: Real-time anomaly score calculated by edge detectors on machine telemetry.
* **$\theta_m$**: Anomaly alarm threshold for machine asset $m$.

---

### Group 5: Single-Model Bill of Materials (BOM) & Station-Side Inventory

Station-specific component stocking parameters to prevent line starvation for the single model.

* **$h$**: Part / component item identifier.
* **$b_h$**: Quantity of part $h$ required per car.
* **$e(h)$**: Work element (and therefore station $i$) where part $h$ is installed.
* **$R_{hi}$**: Shift inventory requirement for part $h$ at station $i$ ($R_{hi} = N \cdot b_h$).
* **$OH_{hi}(t)$**: Live on-hand inventory count of part $h$ remaining at station $i$.
* **$ds_{hi}$**: Days-Supply / replenishment buffer metric for part $h$ at station $i$.

---

### Structural Comparison: Multi-Model vs. Single-Model Variable Footprint

| Variable Category | Multi-Model Architecture | Single-Model / Multi-Station Architecture |
| --- | --- | --- |
| **Model Variants** | $j \in \{1 \dots M\}$ (Multiple active models) | Single baseline configuration ($j=1$) |
| **Sequencing** | Daily job sequences, variant spacing ($MSSA/MOSA$) | First-In, First-Out (FIFO) continuous stream |
| **Feature Usage** | Binary usage index $u_{ej}$, option probabilities $P(f,k)$ | Fixed BOM ($b_h$) and constant work elements ($t_e$) |
| **Station Timing** | Variable model-dependent cycle time $c_{ij}$ | Static station standard time $CT_i = \sum_{e \in i} t_e$ |
| **Primary Risk** | Sequence clumping & option overload | Static station bottlenecks ($\max(CT_i) > TT$) & machine faults |

---

### Critical Loophole & Failure Scenario to Guard Against

Because you have a **single vehicle type with fixed, non-identical station timings**, the major operational failure mode shifts from *sequencing complexity* to **permanent line starvation and blocking**:

* If Station 1 has a cycle time of $114\text{ s}$ and Station 2 has $77\text{ s}$ while the Takt Time is $89\text{ s}$, Station 1 is an unchangeable hard bottleneck that will starve Station 2 on every single cycle unless intermediate buffer capacity $B_i(t)$ or parallel station logic ($\text{Parallel\_Count}_1 = 2$) is explicitly configured in S-TATECON.
