"""Plot the on-time rate per day for each policy from results/summary.csv.

Usage: python3 plot_results.py   (needs matplotlib; writes results/on_time_per_day.png)
Run `python3 summarise.py` first to refresh results/summary.csv.
"""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
POLICIES = [
    ("baseline", "Baseline (FIFO)", "#7f7f7f", "o"),
    ("urgency_first", "Urgency-first", "#d55e00", "s"),
    ("location_grouping", "Location grouping", "#0072b2", "^"),
    ("heuristic_best", "Combined", "#009e73", "D"),
    ("heuristic_timed", "Timed (Policy 4)", "#cc79a7", "v"),
]


def main() -> None:
    rates = {key: {} for key, *_ in POLICIES}
    with (ROOT / "results" / "summary.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["policy"] in rates:
                rates[row["policy"]][int(row["day"].split("_")[1])] = 100 * float(row["on_time_rate"])

    fig, ax = plt.subplots(figsize=(6.5, 2.7), dpi=200)
    for key, label, colour, marker in POLICIES:
        days = sorted(rates[key])
        ax.plot(days, [rates[key][d] for d in days], label=label, color=colour,
                marker=marker, markersize=3.5, linewidth=1.4)
    ax.set_xlabel("Day")
    ax.set_ylabel("On-time rate (%)")
    ax.set_xticks(range(1, 21))
    ax.set_ylim(0, 100)
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.2), frameon=False, fontsize=7,
              columnspacing=1.0, handlelength=1.6)
    ax.tick_params(labelsize=8)
    ax.xaxis.label.set_size(9)
    ax.yaxis.label.set_size(9)
    fig.tight_layout()
    out = ROOT / "results" / "on_time_per_day.png"
    fig.savefig(out, bbox_inches="tight")
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
