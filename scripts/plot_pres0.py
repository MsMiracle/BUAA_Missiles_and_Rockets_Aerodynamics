#!/usr/bin/env python3
"""
plot_pres0.py

Plot pres[0] vs time using all snapshot CSVs under build/.
Each CSV produced by main.c has columns: time,idx,rho,vel,pres.
We extract the row with idx==0 from each file and collect (time, pres).

Usage examples:
  python scripts/plot_pres0.py
  python scripts/plot_pres0.py --build-dir build --save pres0.png --no-show
  python scripts/plot_pres0.py --ylim-min 1.012e5 --ylim-max 1.014e5

Dependencies: matplotlib, numpy (install with `pip install matplotlib numpy`).
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
from typing import List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt

DEFAULT_BUILD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build')


def list_snapshot_files(build_dir: str) -> List[str]:
    files = glob.glob(os.path.join(build_dir, 'snapshot_*.csv'))
    files.sort()  # lexicographic by name; filenames contain scientific notation time, but we'll sort by time later
    return files


def read_pres0_from_csv(path: str) -> Optional[Tuple[float, float]]:
    """Return (time, pres_at_idx0) for a given snapshot CSV. None if idx 0 not found."""
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not {'time', 'idx', 'rho', 'vel', 'pres'}.issubset(reader.fieldnames):
            raise ValueError(f"CSV {path} missing required columns: {reader.fieldnames}")
        for row in reader:
            try:
                idx = int(row['idx'])
            except Exception:
                continue
            if idx == 0:
                t = float(row['time'])
                p0 = float(row['pres'])
                return (t, p0)
    return None


def collect_series(build_dir: str) -> Tuple[np.ndarray, np.ndarray]:
    ts: List[float] = []
    ps: List[float] = []
    for fp in list_snapshot_files(build_dir):
        res = read_pres0_from_csv(fp)
        if res is None:
            # If idx==0 isn't present (e.g., due to sampling stride), skip
            continue
        t, p0 = res
        ts.append(t)
        ps.append(p0)
    if not ts:
        raise SystemExit(f"No pres[0] data found in {build_dir}. Ensure snapshots exist and include idx==0.")
    # Sort by time
    arr = np.array(list(zip(ts, ps)), dtype=float)
    arr = arr[np.argsort(arr[:, 0])]
    return arr[:, 0], arr[:, 1]


def plot_series(t: np.ndarray, p: np.ndarray, save: Optional[str] = None, show: bool = True,
                title: Optional[str] = None, ylim_min: Optional[float] = None, ylim_max: Optional[float] = None) -> None:
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(t, p, marker='o', markersize=2, linewidth=1.2, color='C3', label='pres[0]')
    ax.set_xlabel('time (s)')
    ax.set_ylabel('pressure at x=0 (Pa)')
    if title:
        ax.set_title(title)
    else:
        ax.set_title('pres[0] vs time')
    if ylim_min is not None or ylim_max is not None:
        ax.set_ylim(ylim_min if ylim_min is not None else ax.get_ylim()[0],
                    ylim_max if ylim_max is not None else ax.get_ylim()[1])
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend()
    fig.tight_layout()
    if save:
        os.makedirs(os.path.dirname(save) or '.', exist_ok=True)
        fig.savefig(save, dpi=150)
        print(f"[INFO] Saved plot to {save}")
    if show:
        plt.show()
    else:
        plt.close(fig)


def parse_args():
    p = argparse.ArgumentParser(description='Plot pres[0] vs time from snapshot CSVs under build/.')
    p.add_argument('--build-dir', type=str, default=DEFAULT_BUILD_DIR, help='Directory containing snapshot CSVs (default: ./build)')
    p.add_argument('--save', type=str, default=None, help='Path to save the figure (PNG)')
    p.add_argument('--no-show', action='store_true', help='Do not display the window (use with --save)')
    p.add_argument('--title', type=str, default=None, help='Custom plot title')
    p.add_argument('--ylim-min', type=float, default=None, help='Lower limit for y-axis')
    p.add_argument('--ylim-max', type=float, default=None, help='Upper limit for y-axis')
    return p.parse_args()


def main():
    args = parse_args()
    t, p0 = collect_series(args.build_dir)
    plot_series(t, p0, save=args.save, show=not args.no_show, title=args.title,
                ylim_min=args.ylim_min, ylim_max=args.ylim_max)


if __name__ == '__main__':
    main()
