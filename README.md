"This is independent work by a student; it is not an official publication of the University of Salerno."
# Constraint-native vs. penalty QAOA for budgeted sensor placement

A small, fully reproducible study of one question: **for a budget-constrained maximum-coverage
problem, should QAOA enforce the budget in the mixer or with a penalty?** The problem is the
placement of $k$ weather stations among $n$ candidates to cover as many zones as possible. The
two encodings are compared on solution quality, trainability, and cost on IBM hardware after
routing.

Everything in this README is taken from one end-to-end execution of
[`quantum_sensor_placement.ipynb`](quantum_sensor_placement.ipynb) (files in `results/`).

## Abstract

**Question.** Enforce $\sum_i x_i = k$ structurally with a ring XY mixer (Hadfield et al. 2019),
or with a quadratic penalty $P(\sum_i x_i - k)^2$ in standard transverse-field QAOA? Criteria:
(i) solution quality at fixed depth, (ii) trainability (variance of the cost and of its exact
gradient over random parameters), (iii) two-qubit-gate count after routing to `ibm_marrakesh`.

**Setup.** Exact statevector simulation, $n = 8$–$14$, $p = 1$–$3$, 72 random
instances plus 12 instances selected because greedy *and* LP rounding miss the optimum;
seeded, single run, no shot noise in simulator results.

**Main results.**

- **Quality (family R, n = 12, p = 3; mean [95% CI] over 20 instances).** Expected true-coverage ratio of a feasible shot: XY mixer 0.81 [0.76, 0.86] (basis-state start) and 0.79 [0.77, 0.82] (Dicke start); penalty QAOA 0.66 [0.63, 0.68] with $P_\text{tight}$ and 0.65 [0.63, 0.68] with qiskit's default $P$; uniformly random $k$-subsets 0.65 [0.63, 0.68]. Probability that one shot is optimal: 0.073 (XY, Dicke), 0.007 (penalty), 0.011 (random). Penalty QAOA also wastes 45% of its shots on infeasible strings. Across all sizes (n = 8–14) and depths (p = 1–3), the Dicke-start XY mixer beats penalty QAOA on 252 of 252 paired instance comparisons; the basis-start version is better on average in every setting and significantly so (Wilcoxon p < 0.05) in 13 of 15.
- **Classically hard instances (family H, n = 12, p = 3)**, where greedy and LP rounding both miss the optimum: XY mixer (Dicke) 0.83 [0.80, 0.85], penalty 0.73 [0.72, 0.75], random 0.73 [0.71, 0.75].
- **The previous version's metrics hid this.** Scored by the best of ~1000 shots (what `MinimumEigenOptimizer` returns), uniformly random subsets already reach 0.999 and penalty QAOA 0.996; scored by its single most probable bitstring, penalty QAOA looks near-optimal (0.99 at p = 1) although its output is barely biased away from uniform.
- **Trainability.** Slope of ln Var$_\theta$[E] per qubit (n = 6–14, p = 2, 95% CI): penalty -0.15 [-0.21, -0.08], XY mixer -0.18 [-0.29, -0.08] (basis) and -0.15 [-0.23, -0.09] (Dicke), hardware-efficient ansatz -0.18 [-0.20, -0.15]: overlapping intervals, all far from the $-\ln 2 \approx -0.69$ of a unitary 2-design. No difference in cost concentration between the encodings is detectable at these sizes, so it does not explain the quality gap. The range of n is short; these are descriptive slopes, not asymptotic rates.
- **Hardware cost.** After routing to `ibm_marrakesh`'s heavy-hex coupling map, penalty QAOA needs 2.3× (p = 1) to 2.1× (p = 3) the two-qubit gates of the XY mixer at n = 12, although its idealised all-to-all circuit is shallower.
- **The October hardware run is not evidence either way.** The statistic it reported (best of the 10 most frequent feasible bitstrings) averages 11.5/13 for uniformly random bitstrings (95% range 10–13); the observed values, 9–13/13, are within or below that range. A noisy emulation with the device calibration keeps 43%–76% of XY-mixer shots feasible (uniform: 12%), so the circuits are not fully depolarised, but that statistic cannot separate them from noise.

**Limits.** At $n \le 14$ exhaustive enumeration is instantaneous ($\binom{14}{5} = 2002$ subsets) and
every instance is solved exactly by simple classical methods, so nothing here concerns quantum
advantage: the study compares two encodings of the same problem. QAOA optimises a quadratic
proxy of coverage (exact unless a zone is covered three or more times). Variance slopes are
fitted over a short range of $n$. The hardware evidence is one job whose raw counts were not
kept.

## Contents

| File | |
|---|---|
| `quantum_sensor_placement.ipynb` | the study, executed end to end in one pass (about an hour on a 2-core machine) |
| `qaoa_ai_extensions.ipynb` | follow-up E1–E4: QAOA samples as warm starts for annealing and for a generative model, learned parameters (GNN), exact beyond-QUBO cost (≈45 min) |
| `report/` | 6-page article-style report (`report.pdf`) and its LaTeX sources |
| `requirements.txt` | pinned versions of the reference run |
| `results/`, `results_ext/` | every table behind the figures and this README (`summary.json`, per-instance CSVs) — written by the notebook |
| `data/` | archived summary of the October 2026 hardware job — written by the notebook |

Notebook structure: 0 reproducibility · 1 problem and QUBO proxy · 2 Vienna case study ·
3 methods and validation · 4 instance ensembles · 5–7 results (quality, trainability, hardware
cost) · 8 re-analysis of the hardware run · 9 computed summary · 10 technical notes ·
Appendices A–D (NFT vs COBYLA, learned initialiser, multi-angle QAOA, LP warm start).

## Reproducing

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 quantum_sensor_placement.ipynb
```

All randomness is seeded and simulator results are computed from exact output probabilities,
so a re-run with the pinned versions gives the same numbers. Two exceptions, both stated in
the notebook: routed circuit depths depend on the number of CPU cores (Qiskit's Sabre pass runs
one trial per core by default), and the noisy emulation uses Aer's own seeded sampling. The
last cell of Section 9 checks that the numbers quoted in the notebook's abstract equal those
computed in the run. The hardware cells need an IBM Quantum account and are skipped otherwise;
if the account that ran job `db1pramegvvc73bi0du0` is configured, the notebook downloads its raw
counts and repeats the analysis on them.

## Problem and QUBO proxy

Station $i$ covers the zone set $A_i$; maximise $|\bigcup_{i \in S} A_i|$ with $|S| = k$. QAOA sees the proxy

$g_\lambda(x) = \sum_i |A_i|\, x_i - \lambda \sum_{i<j} |A_i \cap A_j|\, x_i x_j ,$

inclusion–exclusion truncated at second order. A zone covered by $m$ selected stations counts
$m - \lambda\binom{m}{2}$: with $\lambda = 1$ this is exact for $m \le 2$, 0 for $m = 3$ and negative for $m \ge 4$, and $g_1$ is
a lower bound on coverage (Bonferroni). Over 200 instances per family ($n = 12$, $k = 4$), the
proxy's maximiser is a true optimum in 100.0% (sparse) and 98.5% (dense) of
cases at $\lambda = 1$, against 49%/28% at $\lambda = 0.5$, 76%/54% at $\lambda = 2$ and
4%/0% without the overlap term. It works here because zones covered three or more
times by an optimal selection are rare at these densities; it would degrade on denser instances.

Penalty QAOA minimises $-g_1(x) + P(\sum_i x_i - k)^2$ with two choices of $P$: qiskit-optimization's
default $P_\text{auto} = 1 + \sum$ |coefficients| (≈ 30–50 here), and
$P_\text{tight} = 1 + \lfloor\max_i \max(c_i, \lambda\sum_{j} o_{ij} - c_i)\rfloor$, the smallest value for which a one-line argument
(given in the notebook, and checked by brute force on every instance) guarantees that every
minimiser is feasible.

## Methods in brief

- **Ansätze.** Penalty QAOA from $|+\rangle^{\otimes n}$ with the transverse mixer; XY-mixer QAOA with
  the cost $-g_1$ only and a ring of $e^{-i\beta(XX+YY)/2}$ hops (one Trotter step, exactly
  weight-preserving), started from the basis state $|1^k0^{n-k}\rangle$ (as on hardware) or from the Dicke
  state (uniform over weight $k$; its preparation cost is not counted).
- **Simulation.** A small exact statevector simulator with adjoint gradients, validated against
  Qiskit (`Statevector` fidelities and `ReverseEstimatorGradient`, errors < $10^{-8}$).
- **Metrics,** from exact probabilities: probability of a feasible shot; expected true-coverage
  ratio of a feasible shot; probability that a shot is optimal; expected best of $S$ shots.
  All are compared with uniformly random $k$-subsets.
- **Optimisation.** COBYLA, identical budget for all methods (250 iterations × 4 seeded
  restarts), restart chosen by energy (never by coverage); the $\gamma$ scale of each method is
  calibrated on separate instances.
- **Instances.** Family R: radius 2.2, $n \in \{8, 10, 12, 14\}$, 20/20/20/12 instances. Family H:
  radius 3.0, $n = 12$, rejection-sampled so that greedy and LP top-$k$ rounding both fail
  (0.3% of draws qualify). Greedy misses the optimum on 4% of family R;
  the LP relaxation is integral on all of them.

## Results

### 1. Solution quality

Family R, $n = 12$ (mean and 95% bootstrap CI over 20 instances):

| Method | p | E[ratio \| feasible] | P(optimal shot) | P(feasible) | best of 10 shots |
|---|---|---|---|---|---|
| uniformly random k-subset | — | 0.653 [0.626, 0.678] | 0.011 [0.007, 0.016] | 1 | 0.869 [0.852, 0.885] |
| penalty QAOA, P auto | 1 | 0.653 [0.627, 0.679] | 0.005 [0.003, 0.007] | 0.44 | 0.802 [0.780, 0.821] |
| penalty QAOA, P auto | 3 | 0.653 [0.627, 0.679] | 0.006 [0.004, 0.009] | 0.57 | 0.826 [0.806, 0.844] |
| penalty QAOA, P tight | 1 | 0.659 [0.633, 0.684] | 0.005 [0.003, 0.008] | 0.43 | 0.803 [0.782, 0.823] |
| penalty QAOA, P tight | 3 | 0.659 [0.633, 0.685] | 0.007 [0.004, 0.010] | 0.55 | 0.828 [0.807, 0.847] |
| XY mixer, basis start | 1 | 0.748 [0.677, 0.820] | 0.000 [0.000, 0.000] | 1.00 | 0.793 [0.721, 0.858] |
| XY mixer, basis start | 3 | 0.811 [0.761, 0.859] | 0.029 [0.000, 0.075] | 1.00 | 0.880 [0.848, 0.911] |
| XY mixer, Dicke start | 1 | 0.767 [0.749, 0.785] | 0.044 [0.028, 0.064] | 1.00 | 0.937 [0.925, 0.948] |
| XY mixer, Dicke start | 3 | 0.795 [0.771, 0.816] | 0.073 [0.047, 0.102] | 1.00 | 0.951 [0.936, 0.965] |

Expected ratio of a feasible shot at $p = 3$ across sizes:

| n (k) | random | penalty, P tight | XY, basis start | XY, Dicke start |
|---|---|---|---|---|
| 8 (3) | 0.64 [0.61, 0.66] | 0.65 [0.62, 0.68] | 0.84 [0.80, 0.88] | 0.81 [0.78, 0.83] |
| 10 (3) | 0.63 [0.59, 0.66] | 0.64 [0.60, 0.67] | 0.81 [0.77, 0.85] | 0.80 [0.78, 0.83] |
| 12 (4) | 0.65 [0.63, 0.68] | 0.66 [0.63, 0.68] | 0.81 [0.76, 0.86] | 0.79 [0.77, 0.82] |
| 14 (5) | 0.66 [0.64, 0.68] | 0.67 [0.65, 0.69] | 0.78 [0.73, 0.84] | 0.77 [0.75, 0.79] |

Family H ($n = 12$, classically hard; greedy 0.945, LP top-$k$ 0.928 on average):

| Method | p | E[ratio \| feasible] | P(optimal shot) | P(feasible) | best of 10 shots |
|---|---|---|---|---|---|
| uniformly random k-subset | — | 0.726 [0.708, 0.746] | 0.010 [0.007, 0.016] | 1 | 0.909 [0.899, 0.918] |
| penalty QAOA, P auto | 3 | 0.727 [0.709, 0.746] | 0.006 [0.004, 0.008] | 0.56 | 0.873 [0.863, 0.883] |
| penalty QAOA, P tight | 3 | 0.734 [0.717, 0.752] | 0.006 [0.004, 0.009] | 0.56 | 0.878 [0.868, 0.888] |
| XY mixer, basis start | 3 | 0.837 [0.799, 0.872] | 0.014 [0.000, 0.041] | 1.00 | 0.876 [0.844, 0.909] |
| XY mixer, Dicke start | 3 | 0.826 [0.804, 0.847] | 0.042 [0.028, 0.057] | 1.00 | 0.957 [0.950, 0.965] |

Reading:
- Penalty QAOA at $p \le 3$ behaves almost like a uniform sampler: its expected ratio is within
  0.015 of random at every $n$, its probability of an optimal shot is *below* random, and
  35–57% of its shots are infeasible. The penalty occupies almost the whole spectrum of the cost
  operator, so the shallow circuit is spent raising feasibility. $P_\text{tight}$ is consistently but
  only marginally better than the default.
- The XY mixer is better on every $n$ and $p$ tested, by 0.05–0.20 in expected ratio; the
  Dicke-start variant beats penalty QAOA on every single instance. With the basis-state start
  the probability of an optimal shot falls to ≈0 at $n = 14$: amplitude stays within a few hops of
  an arbitrary initial selection.
- In absolute terms, no variant is competitive with greedy at this size, and with ≥ 100 shots
  random sampling closes most of the gap.
- **Correction to the previous version.** It reported penalty QAOA at ratio 1.00 and the native
  mixer at 0.62–0.86 on the Vienna map. The penalty number came from `MinimumEigenOptimizer`,
  which returns the best of ~1000 sampled bitstrings — a metric on which uniformly random subsets
  score 0.999 here — while the native mixer was scored on its single most frequent
  bitstring. On Vienna, with the metrics above, penalty QAOA ($P_\text{tight}$, $p = 3$) gives
  0.750, the XY mixer 0.856 (basis) / 0.822 (Dicke), random 0.747.

### 2. Trainability

Variance over uniformly random parameters (full periods of the un-rescaled circuit) of the
rescaled cost $E = C/\lVert C\rVert_1$ and of its exact gradient, $p = 2$, $n = 6$–$14$, 5 instances × 200
samples per point. Slope of the log-variance per qubit, 95% bootstrap CI:

| Ansatz | slope of ln Var[E] per qubit | slope of ln mean Var[∂E] per qubit |
|---|---|---|
| penalty QAOA, P auto | -0.15 [-0.22, -0.09] | 0.22 [0.15, 0.29] |
| penalty QAOA, P tight | -0.15 [-0.21, -0.08] | 0.06 [-0.05, 0.15] |
| XY mixer, basis start | -0.18 [-0.29, -0.08] | -0.16 [-0.25, -0.09] |
| XY mixer, Dicke start | -0.15 [-0.23, -0.09] | -0.10 [-0.20, -0.02] |
| RealAmplitudes (HEA), penalty cost | -0.18 [-0.20, -0.15] | -0.30 [-0.31, -0.28] |

Reading: the cost variance decreases with $n$ at about the same rate for every ansatz (slopes -0.18 to -0.15, overlapping intervals), several times more slowly than the $-\ln 2$ of a unitary 2-design: at $n \le 14$, $p = 2$ the two encodings do not differ detectably in trainability, so trainability does not explain the quality gap of Result 1. With depth ($n = 12$, $p = 1 \to 8$) the cost variance falls by a factor 10–45 for penalty QAOA, the Dicke-start XY mixer and the HEA, and stays nearly flat for the basis-start XY mixer, whose amplitude remains near the initial state. The gradient variance agrees for the XY mixer and the HEA, but grows with $n$ for penalty QAOA with $P_\text{auto}$: $\partial E/\partial\gamma$ carries a factor of the generator, whose spectrum is set by $P$, which grows with $n$. That is a matter of units, which is why the parametrisation-independent cost variance is the primary diagnostic (exponential cost concentration and vanishing gradients imply each other, Arrasmith et al. 2022).

### 3. Cost on hardware after routing

Two-qubit (CZ) gates after transpiling for `FakeMarrakesh` (heavy-hex coupling map of
`ibm_marrakesh`), optimisation level 1, mean ± std over 5 transpiler seeds:

| n | p | penalty: 2q gates | XY mixer: 2q gates | ratio |
|---|---|---|---|---|
| 8 | 1 | 123 ± 3 | 52 ± 1 | 2.34 |
| 8 | 2 | 249 ± 5 | 112 ± 0 | 2.23 |
| 8 | 3 | 379 ± 7 | 179 ± 3 | 2.11 |
| 10 | 1 | 209 ± 3 | 133 ± 5 | 1.57 |
| 10 | 2 | 424 ± 11 | 294 ± 12 | 1.44 |
| 10 | 3 | 634 ± 25 | 464 ± 14 | 1.37 |
| 12 | 1 | 310 ± 11 | 137 ± 5 | 2.27 |
| 12 | 2 | 625 ± 8 | 290 ± 15 | 2.15 |
| 12 | 3 | 948 ± 26 | 454 ± 28 | 2.09 |
| 14 | 1 | 429 ± 20 | 205 ± 8 | 2.09 |
| 14 | 2 | 875 ± 12 | 466 ± 10 | 1.88 |
| 14 | 3 | 1328 ± 27 | 717 ± 17 | 1.85 |

The penalty term couples every pair of qubits, which a heavy-hex device can only implement
with many SWAPs; the ring mixer and the (sparse) overlap terms route far more cheaply. In the
idealised all-to-all circuits the ranking is the opposite (the XY mixer is two to three times
deeper), which is why depth must be compared after routing.

### 4. The October 2026 hardware run, re-analysed

Job `db1pramegvvc73bi0du0` on `ibm_marrakesh`: six circuits (penalty and XY mixer, $p = 1, 2, 3$),
4000 shots each, on an $n = 12$ instance with optimum 13/25. It reported the best true coverage
among the 10 most frequent feasible bitstrings. The notebook rebuilds the same circuits (the
idealised depths match the recorded ones exactly) and applies the **same** statistic to the
noiseless simulator and to uniformly random bitstrings (Monte Carlo, 4000 shots):

| Circuit | hardware, best of top-10 | noiseless simulator, same extraction (mean, 95% range) | uniform bitstrings, same extraction (mean, 95% range) | P(uniform ≥ hardware) | emulated P(feasible) |
|---|---|---|---|---|---|
| penalty_p1 | 13 | 12.3 [11, 13] | 11.5 [10, 13] | 0.12 | 0.187 |
| native_p1 | 9 | 6.0 [6, 6] | 11.5 [10, 13] | 1.00 | 0.765 |
| penalty_p2 | 12 | 10.9 [8, 12] | 11.5 [10, 13] | 0.50 | 0.127 |
| native_p2 | 10 | 8.0 [8, 8] | 11.5 [10, 13] | 0.99 | 0.604 |
| penalty_p3 | 11 | 11.3 [11, 12] | 11.5 [10, 13] | 0.87 | 0.212 |
| native_p3 | 11 | 11.8 [10, 12] | 11.5 [10, 13] | 0.87 | 0.427 |

Uniformly random bitstrings score 11.5/13 on average on this statistic, so it cannot
separate a working circuit from noise; the hardware values are within or below the null
range. These circuits were also weak in noiseless simulation (one COBYLA run each; the XY
circuits used the basis start, E[ratio | feasible] = 0.46–0.62 against 0.65 for random), so a perfect
device would not have shown much either. A noisy emulation with the device's calibration
(Aer, 1000 shots) leaves 76.5%, 60.4% and 42.7% of XY-mixer shots feasible at $p = 1, 2, 3$ (uniform:
12%); tensored readout mitigation changes these rates by at most
0.06, so gate errors, not readout, dominate. The raw counts of the job were not saved; the
notebook now saves them and contains a ready (disabled) cell for a repeated run with an on-device
null circuit and measured readout calibration.

### Appendices (exploratory)

- **A. NFT vs COBYLA** on `RealAmplitudes`/`EfficientSU2` (where NFT's one-frequency assumption holds
  exactly), 10 paired starts, 150 evaluations: EfficientSU2: COBYLA -220.1 ± 6.1, NFT -235.9 ± 6.0 (NFT lower on 10/10 paired starts); RealAmplitudes: COBYLA -247.6 ± 5.9, NFT -265.9 ± 3.4 (NFT lower on 10/10 paired starts).
- **B. Learned initialiser** (ridge regression, 60 training / 30 test instances, penalty QAOA $p = 2$):
  learned start 0.650, fixed start 0.650, best of 3 random starts 0.650,
  uniformly random subsets 0.649. Negative result: with penalty QAOA this shallow there
  is little for a better initial point to improve.
- **C. Multi-angle QAOA**: standard QAOA's cost variance ($n = 12$, 5 instances) falls from 4.4e-03 at $p = 1$ to 2.1e-05 at $p = 10$ and 7.9e-06 at $p = 45$; ma-QAOA with 90 parameters is at 3.3e-06 already at $p = 1$. Giving every term its own angle makes the landscape as concentrated as a very deep standard circuit. The previous version's conclusion (deep-thin three orders of magnitude *less* barren than shallow-wide) came from comparing gradients whose parameters have different units.
- **D. LP warm start** (Egger et al. 2021), penalty QAOA $P_\text{tight}$, $p = 3$: E[ratio | feasible]
  0.834 vs 0.683 without warm start on family R (LP integral), 0.827 vs 0.733
  on family H (LP rounding wrong by construction). The earlier single-instance test had an
  integral LP solution, i.e. the warm start was the answer.

## Follow-up: learning and beyond QUBO (`qaoa_ai_extensions.ipynb`)

With the XY-mixer ansatz (Dicke start) as the encoding of choice, four follow-up questions, matching three themes of current quantum-optimisation research: quantum samples as warm starts for classical solvers (E1, E4), learned circuit parameters (E2), and QAOA beyond QUBO (E3). Same conventions as the main study (exact simulation, true coverage, seeded single run, bootstrap CIs, paired tests).

- **E1 — quantum samples for a classical solver.** Taking the best of 10 XY-QAOA samples as the start of a
  short simulated-annealing run raises the probability of ending at the optimum over 10 random subsets by
  +0.049 ($n=12$, 18 wins / 0 losses), +0.086 ($n=14$, 11/0) and +0.031 on classically hard instances (9/2).
  Penalty-QAOA samples are no better than random. Greedy is better still on easy instances, where it is
  usually already optimal, but on the hard family the XY warm start beats greedy by +0.077.
- **E2 — learned parameters.** QAOA parameters concentrate strongly: one fixed parameter vector (the training
  median) gives $E[f/f^\star\mid$feasible$]$ = 0.780 on unseen $n=12$ instances and 0.787 at $n=14$, *above* full
  per-instance optimisation with 4 random restarts (0.772, 0.775). A graph neural network trained only on the
  QAOA energy adds a small, consistent gain without any optimisation (0.786 and 0.796; +0.006 and +0.008,
  Wilcoxon $p \approx 0.03$–$0.04$) and transfers to the larger, unseen size; after 30 COBYLA iterations the two are equal.
- **E3 — beyond QUBO.** Using the exact high-order coverage Hamiltonian instead of the quadratic proxy helps
  only where the proxy is wrong: on instances where the proxy's maximiser is not optimal, the probability of
  an optimal shot rises by +0.096 at $p=2$ (11/1, $p=0.007$); elsewhere gains are within noise. The exact
  cost layer needs about 1.7× (sparse) to 13–17× (dense) the two-qubit gates of the proxy after routing.
- **E4 — quantum samples as pretraining data.** An autoregressive network pretrained on 50 XY-QAOA shots
  starts with a higher probability of sampling an optimum than one pretrained on 50 random subsets (+0.049
  at $n=12$, 19/1) and keeps the lead in early classical fine-tuning; after 300 steps of variational
  annealing all variants converge to similar quality. Quantum samples give a head start, not an
  unreachable advantage, at this size.

## Limits and next steps

- **Scale.** $n \le 14$. The next step is $n = 16$–$24$, simulating the XY mixer in its
  $\binom{n}{k}$-dimensional feasible subspace, to test whether the quality gap and the variance trends persist.
- **Hardness.** Even family H is solved by randomized LP rounding and simulated annealing; a
  meaningful benchmark needs sizes beyond enumeration and instances with a real LP integrality gap.
- **Objective.** A higher-order proxy (or the exact objective with cubic terms) would remove the
  proxy error at the price of more gates.
- **Hardware.** Repeat with raw counts, several jobs, an on-device uniform-superposition null
  circuit, measured readout calibration, and circuits that are good in simulation (Dicke start,
  several restarts). At several hundred two-qubit gates, error mitigation beyond readout or
  shallower circuits will be needed before a signal can be expected.
- **Learning.** Test parameter learning where concentration breaks down (heterogeneous instances, larger $p$), and a weight-3 truncation of the exact cost as a middle ground between proxy and exact Hamiltonian.
- Out of scope: weighting zones by historical weather risk; multi-objective formulations.

## What changed from the previous version

- One research question; the side studies became appendices.
- One clean seeded run, pinned environment, computed summary (the previous summary table was
  typed in by hand and README numbers had drifted from the notebook).
- Same metrics for all methods; this reversed the earlier penalty-vs-mixer conclusion.
- Exact gradients over all parameters and cost-variance diagnostics instead of a finite
  difference on one parameter; ma-QAOA over seven depths instead of two points.
- 72 + 12 instances with variable $n$ and bootstrap CIs, instead of 8.
- QUBO proxy justified and tested against $\lambda$; two penalty choices compared.
- Hardware run re-analysed with the same extraction for simulator and null model; noisy
  emulation with readout mitigation; raw counts now saved.

## Regions and data

The Vienna case study (Section 2) uses four individually sourced anchors (Wien Hauptbahnhof,
Stephansplatz, Westbahnhof, Karlsplatz; Wikipedia/Wikidata) plus reproducible synthetic infill,
labelled as such. Nine other regions are preset in the configuration cell (Milano, Salerno,
Lamezia Terme–Gizzeria, Foligno, Rimini, Reggio Calabria, Gstaad, Zurich, Lausanne); the Milano
anchors are from general knowledge and not individually verified. Setting `CSV_PATH` loads a
real station list instead.

## References

- E. Farhi, J. Goldstone, S. Gutmann, *A Quantum Approximate Optimization Algorithm*, arXiv:1411.4028 (2014).
- S. Hadfield et al., *From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz*, Algorithms 12, 34 (2019).
- A. Bärtschi, S. Eidenbenz, *Deterministic Preparation of Dicke States*, FCT 2019.
- J. R. McClean et al., *Barren plateaus in quantum neural network training landscapes*, Nat. Commun. 9, 4812 (2018).
- A. Arrasmith et al., *Equivalence of quantum barren plateaus to cost concentration and narrow gorges*, Quantum Sci. Technol. 7, 045015 (2022).
- K. M. Nakanishi, K. Fujii, S. Todo, *Sequential minimal optimization for quantum-classical hybrid algorithms*, Phys. Rev. Research 2, 043158 (2020).
- R. Herrman et al., *Multi-angle quantum approximate optimization algorithm*, Sci. Rep. 12, 6781 (2022).
- D. J. Egger, J. Mareček, S. Woerner, *Warm-starting quantum optimization*, Quantum 5, 479 (2021).
- G. Cornuéjols, M. L. Fisher, G. L. Nemhauser, *Location of bank accounts to optimize float*, Management Science 23, 789 (1977).
