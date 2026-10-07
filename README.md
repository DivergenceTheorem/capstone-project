# Agent-Based Modeling in Network Formation

Code, data and paper for a capstone project that simulates decentralized network formation with agent-based modeling (ABM). This repository is the capstone component of a larger project, **Agent-Based Modeling in Social and Economic Networks**, which develops an ABM framework to study decentralized network formation.

Agents form and sever links to maximize a distance-based utility:

```
u_i(g) = Σ_{j ≠ i, d(i,j) ≤ r} δ^{d(i,j)}  −  c · deg(i)
```

- **δ** (decay): how fast the value of indirect connections falls with distance.
- **c** (link cost): cost per direct link.
- **r** (myopic radius): agents only see nodes within distance `r`.

Starting from an empty network of `n = 10` agents, a random agent proposes adding or removing one link at each step. The change is made only if it strictly increases utility (for both endpoints when adding a link). After 200 steps, the network is classified by its degree sequence. The results are compared with the analytical predictions of Jackson (2008): complete networks for low c, stars for moderate c, and empty networks for high c.

The parameter grid is 3 decay values × 10 costs × 4 radii = **120 settings**:

| Parameter | Values | Groups used in the tables |
|---|---|---|
| δ | 0.35, 0.65, 0.95 | low / intermediate / high |
| c | 0.1, 0.2, …, 1.0 | low {0.1–0.3} / intermediate {0.4–0.6} / high {0.7–1.0} |
| r | 3, 5, 8, 10 | each value separately |

Main results (counts of structure labels; Section 5.1.1 of the paper):

| Cost c | Complete | Star-like | Weakly star-like | Regular | Near-regular | Empty | Other |
|---|---|---|---|---|---|---|---|
| High | 0 | 4 | 7 | 0 | 5 | 36 | 0 |
| Intermediate | 0 | 5 | 10 | 0 | 10 | 12 | 6 |
| Low | 16 | 2 | 12 | 0 | 11 | 0 | 2 |

Cost is the main driver of connectivity: empty networks never appear at low cost, and complete networks never appear at high cost. Hub structures (star-like) appear only at high δ. The distribution barely changes with the radius r.

---

## Repository layout

```
.
├── requirements.txt                 # pinned Python dependencies
├── dbum_network_formation.py        # runs the simulation over the parameter grid (animated), writes the CSV
├── utils/
│   └── project_utils.py             # utility function, one ABM step, degree-based network classification
├── dbum_param_grid_results.csv      # simulation output: one row per (δ, c, r) setting
├── analyze_simulation.ipynb         # groups the results and rebuilds Tables 1–3 of the capstone
└── Meirzhan_Kurmanov_Capstone.pdf   # 
```

---

## 1. Environment setup

Developed on **Python 3.13**.

```bash
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# macOS / Linux:         source .venv/bin/activate

pip install -r requirements.txt
pip install jupyter               # only needed to run the notebook
```

| Package | Used for |
|---|---|
| networkx | graphs, shortest paths, drawing |
| pandas | results table, grouping and counts |
| matplotlib | animation of the network formation |

---

## 2. Reproduce the results

### Tables 1–3 (from the saved CSV)

Open `analyze_simulation.ipynb` and run all cells. The last section builds `table_1` (by radius), `table_2` (by δ) and `table_3` (by c), then checks them against the values in the paper.

### Rerun the simulation

```bash
python dbum_network_formation.py
```

This opens an animated window that plays every setting in turn: 200 steps plus a 100-frame pause per setting, at 100 ms per frame, so a full run takes about **1 hour**. Leave the window open until it closes by itself; it writes `dbum_param_grid_results.csv` on completion. With the fixed seeds, the rerun reproduces the committed CSV exactly.

Set `VIEW_MODE = "bars"` in the script to show node degrees as bars instead of drawing the network.

---

## 3. What the code does

### Simulation (`dbum_network_formation.py`)

For each `(δ, c, r)` setting, the network is reset to empty and seeded with `random.seed(1 + setting_index)`. Then `one_step` runs 200 times with link-addition probability `p = 0.6`. The final degree sequence is classified and appended as one row of the results.

If `δ ≤ c`, the setting is recorded as empty without simulating. No first link can pay off there: a link's benefit is at most δ and its cost is c.

### Model and classification (`utils/project_utils.py`)

- `utility_dbum`: distance-based utility of agent `i`, counting only nodes within radius `r`.
- `delta_u_add` / `delta_u_remove`: marginal utility of adding or removing link `(i, j)`.
- `one_step`: one ABM update (Algorithm 1 in the paper).
- `classify_network_from_degrees`: assigns degree-based labels. The run uses `near_regular_eps=2`, `weak_ratio=1.5`, `strong_ratio=3.3`.

| Label | Condition |
|---|---|
| empty | no edges |
| complete | all `n(n−1)/2` edges |
| star | one node of degree `n−1`, all others degree 1 |
| regular | `d_max − d_min = 0` |
| nearly_regular | `d_max − d_min ≤ 2` |
| star_like | `median > 0` and `d_max / median ≥ 3.3` |
| weakly_star_like | `median > 0` and `1.5 ≤ d_max / median < 3.3` |
| other | none of the above |

Labels can overlap (e.g. `nearly_regular|weakly_star_like`).

### Analysis (`analyze_simulation.ipynb`)

Tags each row with its δ and c group, then counts labels per group. Each label a network carries counts once, so a row of the tables can sum to more than the number of networks in it. Complete networks are also regular and near-regular, but they are counted only as `complete`. That is why the Regular column is 0.

---

## 4. Output data dictionary (`dbum_param_grid_results.csv`)

| Column | Content |
|---|---|
| `delta`, `c`, `radius` | parameter setting |
| `steps` | ABM steps run (0 for settings recorded as empty without simulating) |
| `edges` | number of edges in the final network |
| `mean_degree`, `deg_max`, `deg_min`, `deg_range`, `deg_median` | degree-sequence statistics |
| `labels` | structure labels, separated by `\|` |
| `is_empty`, `is_complete`, `is_regular`, `is_nearly_regular`, `is_star`, `is_weakly_star_like`, `is_star_like` | raw classification flags (empty for settings recorded as empty without simulating, apart from `is_empty`) |

---

## 5. Reproducibility notes

- Every setting is seeded with `random.seed(1 + setting_index)`, where the grid order is r radius, δ (decay), c (cost). Network layouts use `spring_layout(seed=42 + setting_index)`, which does not draw from Python's `random`, so the animation does not affect the results.
- The simulation is myopic and stops after a fixed 200 steps.

---

## Citation

> Kurmanov, M. (2026). *Agent-Based Modeling in Network Formation* (Capstone Project).

### References

- Jackson, M. O. (2008). *Social and Economic Networks*. Princeton University Press.
- Axtell, R. L., & Farmer, J. D. (2022). Agent-based modeling in economics and finance: Past, present, and future. *Journal of Economic Literature*.
