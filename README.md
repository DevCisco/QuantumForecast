# Quantum Sensor Placement — QAOA for Optimal Weather Station Placement

Solving a small instance of the **Maximum Coverage Problem** — where to place a limited number
of weather sensors to maximize monitoring coverage — with the **Quantum Approximate Optimization
Algorithm (QAOA)**, benchmarked against exact and classical baselines and reported as an
**approximation ratio**, first on a single case study and then across a small ensemble of random
instances.

## Overview

Given a set of candidate locations for weather stations and a set of zones that need monitoring,
the goal is to select *k* stations that maximize the number of zones covered — the NP-hard
Maximum Coverage Problem, solved here several ways:

1. **Exact** — brute-force enumeration (ground truth) and an exact eigensolver on the QUBO.
2. **Classical baselines** — greedy (the textbook $(1-1/e)$-approximation algorithm), LP
   relaxation + rounding, and simulated annealing on the identical QUBO QAOA solves.
3. **Penalty-based QAOA** — the budget constraint folded into the cost function as a quadratic
   penalty, at circuit depths p = 1, 2, 3, each with several independent random restarts.
4. **Constraint-native QAOA** — the same problem, but a ring XY-mixer (Quantum Alternating
   Operator Ansatz, Hadfield et al. 2019) enforces the budget constraint structurally, so every
   sampled bitstring is feasible by construction — no penalty, no $\lambda$ to tune.
5. **Trainability** — gradient-variance scaling of both mixers vs. problem size and circuit
   depth (McClean et al. 2018-style diagnostic), the direct measurement motivating and following
   up on the depth-dependence observed in (4).
6. **Statistical robustness** — the penalty-based comparison repeated across a small ensemble of
   random problem instances, so no method's number rests on a single lucky or unlucky map.

## Problem formulation

The textbook Maximum Coverage ILP needs one binary "covered" variable per zone plus inequality
constraints linking it to the station variables. Once converted to a QUBO, each inequality needs
slack variables — with 15-25 zones this blows up the qubit count far beyond what's practical on a
simulator (confirmed empirically: it reliably ran out of memory during development).

This project uses a compact quadratic proxy over the station variables only:

$$\max \sum_i c_i x_i \;-\; \lambda \sum_{i<i'} o_{i,i'}\, x_i x_{i'} \qquad \text{s.t.} \quad \sum_i x_i = k$$

where $c_i$ is the number of zones station $i$ covers, and $o_{i,i'}$ is the number of zones
covered by *both* $i$ and $i'$. The exact optimum of this proxy is checked against the true
brute-force optimum on every run.

## Classical baselines, precisely

- **Greedy** is the one with an actual proven worst-case guarantee here: $(1-1/e)$ for Maximum
  Coverage (Cornuéjols, Fisher & Nemhauser, 1977).
- **LP relaxation + rounding** solves the exact (non-proxy) ILP relaxed to continuous $[0,1]$,
  then rounds via top-$k$-by-LP-value plus a randomized-rounding-with-repair search. This is
  LP-*informed* but heuristic in its rounding — the formal $(1-1/e)$ guarantee for LP-based
  algorithms needs more careful (pipage/dependent) rounding than implemented here, and the
  notebook says so rather than overclaiming a theorem that doesn't quite apply to this
  simplified version.
- **Simulated annealing** runs on the *identical* QUBO proxy objective QAOA solves, via a
  swap-based local search that always stays feasible. This isolates the real question: does QAOA
  do anything a generic classical optimizer couldn't do on the same objective?

## Regions

The candidate-station generator (`REGION` in the config cell) supports ten areas, used for the
single-instance case study — the notebook is delivered executed with **Vienna** as the active
region:

| Region | Verified real anchors | Source |
|---|---|---|
| Milano | 12 well-known locations (Duomo, Stazione Centrale, San Siro, Bicocca, ...) | general geographic knowledge, not individually cited |
| Salerno | Stazione di Salerno; Fisciano (Unisa campus) | Wikipedia |
| Lamezia Terme – Gizzeria | Aeroporto SUF; Stazione di Lamezia Terme Centrale; Nicastro; Gizzeria; Lago La Vota | Wikipedia |
| Foligno | Stazione di Foligno; Piazza della Repubblica | Wikipedia / Wikidata |
| Rimini | Stazione di Rimini; Rimini Viserba | Wikipedia / Wikidata |
| Reggio Calabria | Reggio Calabria centro (Piazza Garibaldi); Stazione Santa Caterina | Wikipedia |
| **Vienna (active)** | Wien Hauptbahnhof; Stephansplatz; Wien Westbahnhof; Karlsplatz | Wikipedia / Wikidata |
| Gstaad | Gstaad (centro); Gsteig bei Gstaad; Rinderberg (ski area) | Wikipedia |
| Zurigo | Zürich Hauptbahnhof; ETH Zürich (Hauptgebäude); Aeroporto di Zurigo (ZRH) | Wikipedia / Wikidata |
| Losanna | Losanna, Gare CFF; EPFL (Ecublens) | Wikipedia / Wikidata |

Each region tops up its candidate pool to `N_STATIONS` with reproducible synthetic points inside
the same bounding box when it doesn't have enough verified anchors on its own — the `source`
column always says which is which, and the map plot marks them with different symbols. Coverage
density for each new region was sanity-checked (per-zone/per-station coverage counts, non-zero
and non-degenerate) before being added — the abstract multi-instance study earlier in development
caught a miscalibrated radius exactly this way, so every new region gets the same check. Lausanne
needed a wider bounding box than initially chosen for this reason (the first attempt was too
dense — every zone covered 3+ times, making the problem trivially easy).

The separate **multi-instance statistical study** (Section 9) deliberately uses abstract random
instances instead — the point there is to characterize algorithm behavior over a distribution of
problems, decoupled from any specific city, not to produce another map.

## What's in the notebook

| Section | Content |
|---|---|
| 1-8 | Candidate stations (region anchors + synthetic infill, or a real CSV), zones, coverage matrix, QUBO formulation, classical baselines, penalty-based QAOA with random restarts, visualizations |
| 9 | Constraint-native mixer — ring XY-mixer QAOA, validated against the direct QUBO objective, compared honestly against the penalty method |
| 10 | Multi-instance statistical study — same methods across 8 random abstract instances |
| 11 | Trainability — gradient-variance scaling vs. problem size and circuit depth, across penalty QAOA, native-mixer QAOA, RealAmplitudes, and EfficientSU2 |
| 12 | Optimizer choice — NFT vs. COBYLA on the two hardware-efficient ansätze, matched evaluation budget |
| 13 | A learned parameter predictor — ridge regression trained to warm-start QAOA, evaluated against a fixed cold start and random restarts |
| 14 | Multi-angle QAOA (ma-QAOA) — decouples circuit depth from parameter count, validated as a strict generalization of standard QAOA |
| 15 | LP-relaxation warm-starting — the same LP solution from Section 6b used as a structural bias on QAOA's initial state and mixer |
| 16 | Real-hardware run — offline transpilation check on `FakeMarrakesh`, then one batch of 6 circuits executed on `ibm_marrakesh` (156 qubits) |
| 17 | Summary table and roadmap |

## Results (illustrative run, Vienna, default config)

Single case study — this instance is more discriminating than Milano's: greedy, despite its
proven worst-case guarantee, doesn't reach the optimum here, while the QUBO-based methods do:

| Method | Coverage (/25) | Approximation ratio |
|---|---|---|
| Optimum (brute force) | 21 | 1.00 |
| Random baseline (exact average) | 15.7 ± 1.9 | 0.75 |
| Greedy | 19 | 0.90 |
| LP relaxation + rounding | 21 | 1.00 |
| Simulated annealing (same QUBO) | 21 | 1.00 |
| QUBO solved exactly (proxy) | 21 | 1.00 |
| QAOA p = 1 / 2 / 3 (best of 6 restarts) | 21 | 1.00 |

Across the 8-instance ensemble, a more interesting picture emerges — mean ± std approximation
ratio:

| Method | Mean | Std | Min |
|---|---|---|---|
| Random baseline | 0.626 | 0.043 | 0.541 |
| Greedy | 1.000 | 0.000 | 1.000 |
| LP relaxation + rounding | 1.000 | 0.000 | 1.000 |
| Simulated annealing | 1.000 | 0.000 | 1.000 |
| QAOA p = 1 | 0.991 | 0.025 | 0.929 |
| QAOA p = 2 | 0.983 | 0.031 | 0.929 |
| QAOA p = 3 | 0.983 | 0.031 | 0.929 |

Every classical baseline hits the optimum on every instance at this problem size; QAOA is the
only method that sometimes doesn't. Going deeper does **not** help: p = 2 and p = 3 are slightly
*worse* on average than p = 1 (0.983 vs. 0.991), with the same worst case (0.929). That's
consistent with deeper circuits being harder to optimize (a larger, more rugged parameter
landscape) even with random restarts — but with 8 instances and differences well inside one
standard deviation, it's a weak hint, not a conclusion (an earlier run of this ensemble showed a
cleaner p = 1 > p = 3 gap that did not reproduce exactly). See Roadmap below.

## Constraint-native mixer (no penalty term)

The Quantum Alternating Operator Ansatz (Hadfield et al., 2019) replaces the standard transverse
mixer with one whose generator commutes with $\sum_i Z_i$, so it only ever moves probability
*within* the subspace of bitstrings with exactly $k$ ones. Implemented here as a **ring XY-mixer**,
$H_M = \sum_i \tfrac12(X_iX_{i+1 \bmod n} + Y_iY_{i+1 \bmod n})$ — $O(n)$ terms, cheaper than a
fully-connected version. The cost operator is the same proxy objective as before, minus the
budget-constraint term (the mixer enforces it structurally instead), converted to Pauli-$Z$
operators and validated exhaustively against the direct QUBO evaluation (all $2^8$ bitstrings of
an 8-variable test slice; error $\approx 0$) before being trusted.

Reading it honestly, this is not a strictly-better replacement:

| Method | Coverage (/25) | Approximation ratio |
|---|---|---|
| Penalty QAOA p = 1 / 2 / 3 | 21 | 1.00 |
| Native-mixer QAOA p = 1 | 13 | 0.62 |
| Native-mixer QAOA p = 2 | 17 | 0.81 |
| Native-mixer QAOA p = 3 | 18 | 0.86 |

Feasibility is unconditional — every sampled bitstring from every restart has exactly $k$ ones,
checked directly, not assumed. But solution quality at shallow depth is worse than the penalty
method, and — unlike the penalty method, which is already at the optimum from p = 1 on this
instance — it **improves monotonically with circuit depth** (0.62 → 0.81 → 0.86). That pattern is
consistent with a connectivity/expressibility limitation: reaching a specific far-apart-in-the-ring
combination from a fixed initial state takes more "hops" than a generic mixer needs. Circuit depth
at p = 2 confirms the mixer isn't free either: 104 (penalty method, transpiled) vs. 309 (native
mixer, transpiled) — roughly 3× deeper for the same p.

This trade-off — feasibility and no penalty tuning, against depth and (at shallow p) solution
quality — is exactly what motivates measuring gradient variance directly instead of continuing to
infer trainability indirectly from solution quality alone (see Roadmap).

## Trainability: gradient-variance scaling

The direct diagnostic for the depth-dependence found above (McClean et al. 2018; building on
Holmes et al.'s work connecting ansatz expressibility to gradient magnitude): sample the cost
gradient (finite difference, since the multi-Pauli-term operators here don't satisfy the
single-generator assumption behind the analytic parameter-shift rule) at many random parameter
points, and look at its variance. Every operator is rescaled to unit total Pauli weight before
comparing — the penalty method's raw gradient variance is otherwise ~4 orders of magnitude larger,
an artifact of its penalty coefficient's scale, not a trainability difference.

**Four ansätze, not two.** Alongside penalty-based and constraint-native QAOA, this compares two
**hardware-efficient ansätze** (`RealAmplitudes`, `EfficientSU2`, both shallow with linear
entanglement) evaluated against the same cost operator — problem-*agnostic* circuits with no
structural connection to the coverage objective, unlike QAOA. Two scans: gradient variance vs.
problem size $n$ (fixed depth p=2) and vs. depth $p$ (fixed $n=12$, this project's actual size),
40 random parameter draws per point.

**Honestly, the six-$n$/40-sample results are noisy, not textbook-clean**, but one pattern is
clear in both panels: **both HEA ansätze sit at markedly lower gradient variance than either QAOA
variant across nearly every point tested** — lower variance means a flatter landscape, so this is
the textbook-*expected* direction, not a surprise. `EfficientSU2` (double `RealAmplitudes`'
parameter count at the same `reps`) is consistently the most barren of the four, consistent with
the expressibility-trainability tradeoff.

**A confound worth stating rather than glossing over**: this isn't a matched-depth comparison
across families. At $n=12$, $p=2$: penalty QAOA has 4 parameters and transpiled depth 104; the
native mixer has 4 parameters and depth 309; `RealAmplitudes` has 36 parameters and depth 16;
`EfficientSU2` has 72 parameters and depth 19. The HEA ansätze are shallower but far wider. Since
the measured gradient is with respect to *one* fixed reference parameter, more total parameters
sharing influence over the same measurement can dilute that parameter's marginal effect on its
own — a distinct mechanism from the usual depth-driven barren-plateau story, and this sweep can't
cleanly separate the two. A rigorous version would hold parameter count fixed while varying depth,
and vice versa, rather than letting both vary at once by ansatz family. This is a first pass,
explicitly flagged as such — see Roadmap.

## Optimizer choice: NFT vs. COBYLA for the hardware-efficient ansätze

COBYLA is used everywhere else in this notebook, but **Nakanishi-Fujii-Todo (NFT)** is a better
theoretical fit specifically for `RealAmplitudes` and `EfficientSU2`: it assumes that, holding
every parameter but one fixed, the cost is a single-frequency sinusoid in that one — exactly true
when a parameter controls one single-qubit Pauli rotation in isolation, which is the structure of
these two ansätze (the same reasoning behind using NFT for shallow HEA circuits in unrelated
image-classification work). It does **not** carry over to either QAOA ansatz here — each QAOA
angle drives a multi-Pauli-term Hamiltonian at once, generally giving a multi-frequency dependence
that breaks NFT's core assumption (a generalized Rotosolve-type method exists for that case but
isn't implemented here) — so this comparison is scoped to where the theory actually applies.

Matched budget (COBYLA `maxiter=150`, NFT `maxfev=150`, same paired starting points, 5 restarts):

| Ansatz | COBYLA final cost | NFT final cost |
|---|---|---|
| RealAmplitudes | −246.5 ± 5.6 | **−265.9 ± 1.7** |
| EfficientSU2 | −218.5 ± 8.9 | **−236.6 ± 7.2** |

NFT reaches a better (more negative) mean cost on both ansätze at a matched evaluation budget —
a gap of roughly 2-3 standard deviations, not a marginal effect — and with lower spread across
restarts on both (1.7 vs. 5.6 for `RealAmplitudes`, 7.2 vs. 8.9 for `EfficientSU2`). The running-best convergence trace shows
why rather than just asserting it: NFT's sweep-based descent front-loads progress by exploiting
the ansatz's known single-rotation structure, where COBYLA's simplex search treats the same cost
function as a generic black box. A solid, if narrow, empirical confirmation that optimizer choice
should follow from ansatz structure rather than defaulting to one general-purpose method
everywhere.

## Learned parameter predictor ("Quantum x AI", literally)

Everything else uses AI/ML only by analogy. This is direct: a ridge regression model (closed-form,
implemented in plain numpy, no external ML library needed at this scale) trained to map a problem
instance's coverage profile to a good QAOA initial point, tested against a fixed cold start and
against random restarts — all three given the same per-run optimizer budget, so the comparison is
about the starting point, not extra compute.

**This result changed after fixing a real bug, and both numbers are worth showing.** The first
version of this evaluation had the learned warm start beating the cold start. It was wrong: the
bitstring-extraction step picked the most frequent sample regardless of whether it actually
selected exactly $k$ stations — and unlike the native mixer (which guarantees feasibility by
construction), the penalty-based ansatz used here does not, so infeasible samples that quietly
used *more* than the allowed budget were sometimes winning. The tell: one test instance's
"best of 3 random restarts" scored *higher* than that same instance's brute-force optimum, which
cannot happen in a genuine $k$-constrained comparison. After restricting to feasible samples only:

| Approach | Mean approximation ratio (5 test instances) |
|---|---|
| Cold fixed start (1 run) | 0.72 |
| Learned warm start (1 run) | **0.62** |
| Best of 3 random restarts | 0.73 |

The learned warm start does not beat the simple fixed baseline here — a genuine negative result,
not a disappointing writeup of a positive one. It ties the cold start on 2 of 5 instances, wins on
1, and loses badly on one (4/17 covered, ratio 0.24), which drags the mean down; three random
restarts barely beat a single fixed cold start (0.73 vs. 0.72). With 14 training instances, a linear model, and a
fixed-length coverage-count feature vector, there's little reason to expect strong generalization,
and there isn't any. The value of this section is validating the *pipeline* (train a regressor on
solved instances, deploy it as an initializer, evaluate honestly against matched-compute
baselines) rather than this particular model — see Roadmap for what a version with a real chance
of winning would need.

## Multi-angle QAOA (ma-QAOA), and decoupling depth from parameter count

Section 11's four-ansatz trainability comparison had an unresolved confound: HEA circuits were
shallower but far *wider* (many more parameters per layer) than either QAOA variant, so the
observed trainability gap could reflect depth, parameter count, or both. **Multi-angle QAOA**
(Herrman et al. 2022) resolves this within the QAOA family: every Pauli term in the cost gets its
own $\gamma_i$, every qubit its own $\beta_i$ in the mixer, instead of one shared angle each — a
strict generalization of standard QAOA (checked numerically: fidelity 1.0 between the two circuits
at matched parameters, not assumed).

This gives the same ansatz family a large parameter count at shallow depth (90 parameters at
$n=12$, $p=1$), enabling two matched comparisons instead of one confounded sweep:

| Comparison | Gradient variance |
|---|---|
| Standard QAOA, p=1 (2 params) | 5.08e-2 |
| ma-QAOA, p=1 (90 params) | 6.39e-7 |
| Standard QAOA, p=45 (90 params, depth 1738) | 5.35e-4 |

**Bars 1 vs. 2** (same depth, parameters vary): variance collapses ~5 orders of magnitude —
confirms Section 11's parameter-count effect within a single ansatz family, where depth is
genuinely fixed. **Bars 2 vs. 3** (same ~90 parameters, depth varies): variance *increases* by
~3 orders of magnitude going from shallow-wide to deep-thin — the opposite of the naive "more
depth is always more barren" expectation. A plausible reading: ma-QAOA spends its 90 parameters
giving every term an independent angle *simultaneously* in one layer, a qualitatively different
use of a parameter budget than spreading the same count across many repetitions of a 2-parameter
unit cell — a hypothesis, not a settled explanation. Together: parameter count did most of the
work in what Section 11 measured, not depth, a real correction worth taking forward.

## LP-relaxation warm-starting

The LP relaxation from Section 6b produces a fractional solution $x_i^\star \in [0,1]$, rounded to
a classical baseline there. **Warm-starting QAOA** (Egger, Marecek & Woerner, 2021) uses it
differently: each qubit starts in $R_Y(2\arcsin\sqrt{x_i^\star})|0\rangle$ instead of the uninformed
equal superposition, and the mixer is correspondingly tilted per qubit so it doesn't immediately
wash the bias back out. This reduces exactly to standard QAOA when $x^\star \equiv 0.5$
(uninformative) — checked numerically (fidelity 1.0), the same validation style used for ma-QAOA.

| Depth | Standard QAOA (5 restarts) | Warm-start QAOA (5 restarts) |
|---|---|---|
| p=1 | 0.38 | **1.00** |
| p=2 | 0.23 | **1.00** |
| p=3 | 0.62 | 0.62 |

Warm-start reaches the true optimum at p=1 and p=2, where standard QAOA does far worse (0.38,
0.23). At p=3 the advantage **disappears**: both end at 0.62 — the deeper, more-parameter
optimization apparently drifts away from the good initial state within the 150-iteration COBYLA
budget, so the warm start's benefit is not robust to depth. Why p=1-2 work so well is clear from
the LP solution: for this instance,
$x^\star \approx [1,0,0,0,0,0,1,0,1,0,1,0]$ — **already almost exactly integral**, and the four
LP-selected stations verified to achieve the true optimum on their own. The warm start begins
close to a computational-basis state encoding the optimum before any optimization runs — an
especially favorable case, not necessarily a representative one. A harder instance with a more
fractional $x^\star$ would be a fairer stress test of whether the advantage survives when the
relaxation is genuinely uncertain rather than effectively handing over the answer — see Roadmap.

## Real-hardware run

**Designed to fit IBM's free-tier budget (10 minutes of QPU time per 28-day window)**: no
optimization runs on hardware — that would need hundreds of circuit evaluations. Instead, 6
circuits (penalty QAOA and native-mixer QAOA at p=1,2,3, on an abstract $n=12$, $k=4$ instance
with optimum 13/25) are optimized locally on the noiseless simulator, then submitted **once, as a
single batch** of 4000 shots each to `ibm_marrakesh` (156 qubits, Heron). The delivered notebook
contains the executed job's output.

**Transpiled depth on real topology.** Same circuits, idealized all-to-all depth vs. ISA depth
after routing to the Marrakesh heavy-hex coupling map (offline `FakeMarrakesh`, seeded, and the
live backend):

| Circuit | Idealized depth | ISA depth, FakeMarrakesh | ISA depth, ibm_marrakesh |
|---|---|---|---|
| Penalty, p=1/2/3 | 66 / 104 / 142 | 446 / 710 / 958 | 550 / 699 / 998 |
| Native mixer, p=1/2/3 | 125 / 249 / 373 | 304 / 587 / 870 | 322 / 588 / 903 |

Section 9's idealized comparison has the native mixer 2-3× *deeper*; after real routing the
ranking **flips at every depth** — the native mixer comes out shallower (its ring mixer maps
naturally onto nearest-neighbour hardware, while the penalty method's dense all-to-all $ZZ$ terms
from the budget penalty need many SWAPs). An earlier version of this check, run against the
27-qubit `FakeAlgiers`, gave a mixed picture (native shallower only at p=1); the conclusion is
backend-dependent, so cite it with the device named.

**Hardware results** (simulator = most frequent feasible bitstring; hardware = best true coverage
among the 10 most frequent feasible bitstrings):

| Circuit | Simulator, top-1 (ratio) | Hardware, best of top-10 (ratio) |
|---|---|---|
| Penalty p=1 | 11/13 (0.85) | 13/13 (1.00) |
| Native p=1 | 6/13 (0.46) | 9/13 (0.69) |
| Penalty p=2 | 8/13 (0.62) | 12/13 (0.92) |
| Native p=2 | 8/13 (0.62) | 10/13 (0.77) |
| Penalty p=3 | 7/13 (0.54) | 11/13 (0.85) |
| Native p=3 | 8/13 (0.62) | 11/13 (0.85) |

Read with care — this is **not** an apples-to-apples comparison, and the hardware column being
*higher* than the noiseless simulator is the tell:

- the two columns use different post-processing: hardware gets a classical best-of-10 selection
  over candidate bitstrings, the simulator only top-1. Picking the best of 10 feasible 4-subsets
  out of $\binom{12}{4}=495$ would already score well even for uniformly random samples, so these
  numbers mostly measure the post-processing, not the circuit;
- **no circuit was 100% feasible on hardware — including the native mixer**, whose feasibility
  guarantee holds only in the noiseless model; gate errors leak probability out of the
  Hamming-weight-$k$ subspace, so feasible-only filtering is necessary for both ansätze on real
  devices;
- one job, one instance, no repetition — no error bars.

A fair version would apply the same top-10 extraction to the simulator (and to uniform random
sampling as a null baseline) before drawing any hardware-vs-simulator conclusion — see Roadmap.

## Roadmap

Left out of this version on purpose:
- a statistically tighter version of both trainability studies (Sections 11 and 14) — more
  samples, more instances, more points between the two matched comparisons in Section 14 rather
  than a single jump from p=1 to p=45;
- testing LP-relaxation warm-starting (Section 15) on an instance where the LP solution is
  genuinely fractional rather than nearly integral, to see whether the dramatic advantage found
  here survives a harder, more realistic case;
- a single-restart warm-start vs. multi-restart standard QAOA comparison (the fairer test of a
  warm start's actual value proposition) — not run here;
- a learned predictor that generalizes across problem size (this version fixes $n=12$) and uses a
  graph-based model over the coverage graph directly, instead of a fixed-length feature vector —
  with enough training instances (hundreds, not tens) to give a fair test;
- a fair hardware comparison (Section 16): same best-of-top-10 extraction on simulator, hardware
  and a uniform-random null baseline, plus feasibility rate per circuit and more than one job;
- weighting zones by real historical extreme-weather events;
- multi-objective formulation (coverage + installation/maintenance cost).

## Data

Set `CSV_PATH` in the config cell to override with a real downloaded dataset — the loader
auto-detects common lat/lon/name column names, or override via `COLUMN_MAP`. Takes precedence
over both the region's verified anchors and synthetic infill.

## Running it

The notebook is saved with all outputs already computed, so it renders fully on GitHub as-is —
no execution needed to read it. To reproduce or modify:

```bash
pip install qiskit qiskit-optimization qiskit-algorithms qiskit-ibm-runtime numpy pandas matplotlib scipy
jupyter notebook quantum_sensor_placement.ipynb
```

Tested with `qiskit==2.5.2`, `qiskit-optimization==0.7.0`, `qiskit-algorithms==0.4.0`. The
single case study takes a couple of minutes on a standard CPU; the whole notebook (ensemble,
trainability scans, ma-QAOA at p=45, warm-start) is closer to 15 minutes. The hardware
submission cell in Section 16 needs an IBM Quantum account (`IBM_QUANTUM_TOKEN` environment
variable or a saved `QiskitRuntimeService` account) and is skipped/raises otherwise.

Note: the notebook was executed in several passes (September–October 2026); the Section 17
summary table is built from hard-coded values carried forward from Sections 1-9 rather than
recomputed.
