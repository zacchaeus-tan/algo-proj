# IS115 Project: Last-Mile Delivery Dispatch

We improve the **on-time delivery rate** (parcels delivered inside their preferred window, divided by all parcels that arrive that day) over the supplied FIFO baseline. Results below are means over `day_001` to `day_020`.

| Policy | File | On-time rate |
|---|---|---|
| Baseline (FIFO, supplied) | `solution/policies/baseline.py` | 27.4% |
| Urgency-first (min-heap, earliest deadline first) | `solution/policies/urgency_first.py` | 39.7% |
| Location grouping (hash map, nearest neighbour) | `solution/policies/location_grouping.py` | 63.0% |
| Combined (hash map, heap, nearest neighbour) | `solution/policies/heuristic_best.py` | 81.9% |
| Variation of Combined: no late filler | `solution/policies/heuristic_nofiller.py` | 81.9% (fewer parcels delivered) |
| Variation of Combined: arrival-order loading (no heap) | `solution/policies/heuristic_noheap.py` | 82.8% |
| Variation of Combined: nearest first stop | `solution/policies/heuristic_nearfirst.py` | 81.8% |
| Variation of Combined: most urgent next stop | `solution/policies/heuristic_urgentnext.py` | 82.9% |
| **Timed dispatch (recommended)** | `solution/policies/heuristic_timed.py` | **95.8%** |
| Ablation of Timed: no fleet reservation | `solution/policies/heuristic_timed_noreserve.py` | 95.6% |
| Ablation of Timed: no cluster limit | `solution/policies/heuristic_timed_noradius.py` | 90.5% |
| Ablation of Timed: no fill trigger | `solution/policies/heuristic_timed_nofill.py` | 68.3% |
| Sensitivity of Timed: fill at 24 / 30 units | `heuristic_timed_fill24.py`, `heuristic_timed_fill30.py` | 95.4% / 95.4% |
| Sensitivity of Timed: margin 10 / 30 minutes | `heuristic_timed_margin10.py`, `heuristic_timed_margin30.py` | 95.6% / 95.3% |

Shared helper functions are in `solution/policies/helpers.py`. The metric is implemented in `solution/performance_monitor.py`. The report discusses the design and results.

## Requirements

- Python 3.9 or later, standard library only. The simulator, policies, performance monitor and `summarise.py` need nothing else.
- `matplotlib`, only for the optional chart (`plot_results.py`).

All commands run from the project root.

## Reproduce one day (baseline example)

```bash
python3 -m simulator --policy solution.policies.baseline --data data --day day_001 --output results/baseline/day_001
```

```bash
python3 -m solution.performance_monitor --data data --day day_001 --log results/baseline/day_001/log.txt
```

The first command writes `log.txt`. The second writes `metrics.json` next to it. For another policy, replace `baseline` with the policy's module name (see the table above), in both the `--policy` argument and the output folder.

## Reproduce all 20 days for a policy

`run_all.sh` runs the simulator and the performance monitor for `day_001` to `day_020`:

```bash
bash run_all.sh baseline
bash run_all.sh urgency_first
bash run_all.sh location_grouping
bash run_all.sh heuristic_best
bash run_all.sh heuristic_nofiller
bash run_all.sh heuristic_noheap
bash run_all.sh heuristic_nearfirst
bash run_all.sh heuristic_urgentnext
bash run_all.sh heuristic_timed
bash run_all.sh heuristic_timed_noreserve
bash run_all.sh heuristic_timed_noradius
bash run_all.sh heuristic_timed_nofill
bash run_all.sh heuristic_timed_fill24
bash run_all.sh heuristic_timed_fill30
bash run_all.sh heuristic_timed_margin10
bash run_all.sh heuristic_timed_margin30
```

Each run writes `results/<policy>/<day>/log.txt` and `metrics.json`. The runs are deterministic, so they reproduce the committed results exactly. One policy takes about 4 to 20 seconds for all 20 days.

## Summarise and plot

```bash
python3 summarise.py
```

This writes `results/summary.csv` (one row per policy and day) and prints each policy's mean for every metric. The metrics are on-time rate, delivery rate, average lateness of late parcels, parcel counts (on time, early, late, undelivered) and trips.

```bash
pip install matplotlib
python3 plot_results.py
```

This writes `results/on_time_per_day.png` (Figure 1 in the report) from `results/summary.csv`.

## Metrics in `metrics.json`

| Field | Meaning |
|---|---|
| `on_time_rate` | Delivered inside the window (edges included) divided by all parcels that arrived. Early, late and undelivered parcels all count as failures. |
| `delivery_rate` | Delivered parcels divided by all parcels. |
| `avg_lateness_min` | Mean minutes late, over late parcels only. |
| `total_parcels`, `delivered`, `on_time`, `early`, `late`, `undelivered` | Parcel counts for the day. |
| `trips` | Number of trips (hub departures). |

## Folder structure

```
simulator/            supplied framework (not modified)
data/                 supplied inputs (not modified)
solution/
  performance_monitor.py   our metric
  policies/
    baseline.py            supplied FIFO policy (not modified)
    helpers.py             shared helpers
    urgency_first.py       Policy 1
    location_grouping.py   Policy 2
    heuristic_best.py      Policy 3 (combined)
    heuristic_nofiller.py, heuristic_noheap.py,
    heuristic_nearfirst.py, heuristic_urgentnext.py   one-rule variations of Policy 3
    heuristic_timed.py     Policy 4 (timed dispatch, recommended)
    heuristic_timed_noreserve.py, heuristic_timed_noradius.py,
    heuristic_timed_nofill.py   ablations of Policy 4 (one rule removed each)
    heuristic_timed_fill24.py, heuristic_timed_fill30.py,
    heuristic_timed_margin10.py, heuristic_timed_margin30.py   sensitivity runs of Policy 4
results/<policy>/<day>/    log.txt and metrics.json for every policy and day
results/summary.csv        all metrics, one row per policy and day
results/on_time_per_day.png  Figure 1
run_all.sh, summarise.py, plot_results.py   helper scripts
```
