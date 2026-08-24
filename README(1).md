# Quantum Sensor Placement — QAOA for Optimal Weather Station Placement

Solving a small instance of the **Maximum Coverage Problem** — where to place a limited number
of weather sensors to maximize monitoring coverage — with the **Quantum Approximate Optimization
Algorithm (QAOA)**, benchmarked against exact and classical-heuristic baselines.

## Overview

Given a set of candidate locations for weather stations and a set of zones that need monitoring,
the goal is to select *k* stations that maximize the number of zones covered. This is an instance
of the NP-hard Maximum Coverage Problem, solved here three ways:

1. **Exact** — brute-force enumeration (ground truth) and an exact eigensolver on the QUBO.
2. **Classical heuristic** — greedy marginal-gain selection.
3. **Quantum** — QAOA on a statevector simulator, compared across circuit depths (p = 1, 2, 3).

The project is deliberately scoped as a small, from-scratch weekend build: no auxiliary
"zone covered" variables, no inequality constraints, no real-hardware run — see
[Scope & limitations](#scope--limitations) for why, and what's explicitly left out.

## Problem formulation

The textbook Maximum Coverage ILP needs one binary "covered" variable per zone plus inequality
constraints linking it to the station variables. Once converted to a QUBO, each inequality
constraint needs slack variables — with 15-25 zones this blows up the qubit count far beyond
what's practical on a simulator.

This project uses a compact quadratic proxy over the station variables only:

$$\max \sum_i c_i x_i \;-\; \lambda \sum_{i<i'} o_{i,i'}\, x_i x_{i'} \qquad \text{s.t.} \quad \sum_i x_i = k$$

where $c_i$ is the number of zones station $i$ covers, and $o_{i,i'}$ is the number of zones
covered by *both* $i$ and $i'$. It rewards individual coverage and penalizes overlap between
co-selected stations — a standard quadratic surrogate for submodular coverage problems. The
notebook checks this proxy against the true (brute-force) objective on every run.

## What's in the notebook

| Step | Content |
|---|---|
| 1 | Candidate stations — real CSV loader (auto-detects lat/lon columns), with a hand-picked fallback list of 16 well-known Milan locations |
| 2 | Zones to cover — regular grid over the bounding box |
| 3 | Coverage matrix — haversine distance between stations and zones |
| 4 | QUBO formulation — `qiskit_optimization.QuadraticProgram` |
| 5 | Classical baselines — brute force, greedy, exact QUBO solve |
| 6 | QAOA — `MinimumEigenOptimizer` + `QAOA`, compared at p = 1, 2, 3 |
| 7 | Visualizations — map of selected stations, coverage comparison bar chart, QAOA convergence trace |

## Results (illustrative run)

With the default 16-location Milan dataset, 25 zones, k = 4:

| Method | Zones covered (/25) |
|---|---|
| Brute force (true optimum) | 16 |
| Greedy | 14 |
| QUBO solved exactly (proxy) | 16 |
| QAOA, p = 1 | 13 |
| QAOA, p = 2 | 16 |
| QAOA, p = 3 | 14 |

Two things worth noting, left in rather than smoothed over:

- The exact QUBO solve matches the true optimum here — the proxy objective is a good surrogate
  on this instance, though that's not guaranteed in general.
- QAOA's coverage doesn't improve monotonically with circuit depth. That's expected: it's an
  approximate algorithm, and its classical optimizer (COBYLA) is prone to local minima — deeper
  circuits mean a larger, harder parameter landscape, not automatically a better answer.

## Scope & limitations

Explicitly out of scope for this version (kept separate on purpose, to avoid scope creep):
- weighting zones by real historical extreme-weather events
- running on real quantum hardware (noise analysis)
- benchmarking against simulated annealing / D-Wave on the same QUBO
- multi-objective formulation (coverage + installation/maintenance cost)

## Data

The default dataset (`MILANO_LANDMARKS` in the config cell) is a hand-written list of 16
well-known Milan locations with approximate coordinates — **not** downloaded from any open data
portal, just a realistic geographic stand-in. To use real weather-station data instead, set
`CSV_PATH` in the config cell to a CSV with latitude/longitude columns — e.g. from
[Regione Lombardia Open Data](https://www.dati.lombardia.it/Ambiente/Stazioni-Idro-Nivo-Meteorologiche/nf78-nj6b)
or [Comune di Milano Open Data](https://dati.comune.milano.it) — the loader auto-detects common
column names, or you can override them via `COLUMN_MAP`.

## Running it

The notebook is saved with all outputs already computed, so it renders fully on GitHub as-is —
no execution needed to read it. To reproduce or modify:

```bash
pip install qiskit qiskit-optimization qiskit-algorithms numpy pandas matplotlib
jupyter notebook quantum_sensor_placement.ipynb
```

Tested with `qiskit==2.5.2`, `qiskit-optimization==0.7.0`, `qiskit-algorithms==0.4.0`.
