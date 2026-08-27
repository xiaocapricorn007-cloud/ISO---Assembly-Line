# O-PTINECK (Bottleneck Optimizer)

O-PTINECK is the proactive flow optimizer. It predicts flow interruptions and continuously calculates the line's resilient output metric: the **Dynamic Equilibrium Yield (DEY)**.

## Core Directives

1. **Dark Zone Inference**
   - **Problem:** Assembly lines have uneven sensor coverage, leaving uninstrumented "Dark Zones" (e.g., Station B is blind, but Stations A and C have sensors).
   - **Solution:** Uses Hidden Markov Models (HMMs) or Gradient Boosted Regressors to calculate transit-time deltas between instrumented checkpoints. By factoring in the live BOM from S-TATECON, it deduces delays at the blind stations.

2. **Balance Delay Tracking**
   - Monitors line efficiency by tracking the target cycle time ($c = T/N$) against actual average times ($\bar{c}$).
   - **Formula:** $d = \frac{c - \bar{c}}{c}$

3. **Constraint-Aware Rebalancing (Switching Cost Hysteresis)**
   - **Problem:** Standard GA (Genetic Algorithm) optimizers reallocate flexible operators at every micro-delay, causing cognitive whiplash.
   - **Solution:** O-PTINECK enforces a *Switching Cost Hysteresis*. A rebalance is mathematically vetoed unless the projected time saved exceeds the physical transition penalty (walking, tooling) and passes a maximum-moves-per-shift limit.

4. **Dynamic Equilibrium Yield (DEY)**
   - **Formula:** $\text{DEY} = \frac{3600}{\max(CT_i)} \times \eta$
   - Where $\max(CT_i)$ is the current slowest cycle time across all stations (including degraded machines), and $\eta$ is the structural efficiency buffer.
   - When a machine breaks, S-TATECON raises $\max(CT_i)$, O-PTINECK drops the DEY, and automatically throttles inbound logistics to prevent a parts pile-up, rejecting the delusion of 100% ideal maximization.
