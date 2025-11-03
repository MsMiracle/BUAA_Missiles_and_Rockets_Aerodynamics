#!/usr/bin/env python3
"""
visualizations.py

Render heatmaps for 1D CFD snapshots saved as CSV by main.c.

Usage examples:
  # Show latest snapshot, density heatmap
  python vispy/visualizations.py --field rho

  # Specify a snapshot file and repeat y 80 rows
  python vispy/visualizations.py --field vel --file build/snapshot_1.000000e-03.csv --y-repeat 80

  # Save the image instead of showing
  python vispy/visualizations.py --field pres --save out.png

Notes:
- The script parses include/constants.h to read NX and DX.
- Since the simulation is 1D, we replicate the 1D profile along a fake y-axis to form a heatmap.
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import re
import time
from dataclasses import dataclass
from typing import Optional, Tuple, List

import numpy as np
import matplotlib.pyplot as plt


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONSTANTS = os.path.join(ROOT_DIR, 'include', 'constants.h')
DEFAULT_BUILD_DIR = os.path.join(ROOT_DIR, 'build')


@dataclass
class SimConstants:
    NX: int
    DX: float


def parse_constants(constants_path: str = DEFAULT_CONSTANTS) -> SimConstants:
    """Parse NX and DX from constants.h.
    Accepts formats like: #define NX 100000, #define DX 1e-5
    """
    if not os.path.isfile(constants_path):
        raise FileNotFoundError(f"constants.h not found at: {constants_path}")

    with open(constants_path, 'r', encoding='utf-8') as f:
        text = f.read()

    nx_match = re.search(r"#\s*define\s+NX\s+([0-9]+)", text)
    dx_match = re.search(r"#\s*define\s+DX\s+([0-9.eE+\-]+)", text)

    if not nx_match or not dx_match:
        raise ValueError("Failed to parse NX/DX from constants.h. Ensure they are defined like '#define NX 100000' and '#define DX 1e-5'.")

    NX = int(nx_match.group(1))
    DX = float(dx_match.group(1))
    return SimConstants(NX=NX, DX=DX)


def find_latest_snapshot(build_dir: str = DEFAULT_BUILD_DIR) -> Optional[str]:
    pattern = os.path.join(build_dir, 'snapshot_*.csv')
    files = glob.glob(pattern)
    if not files:
        return None
    # Pick the most recently modified
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files[0]


def list_snapshots_sorted(build_dir: str = DEFAULT_BUILD_DIR) -> List[Tuple[str, float]]:
    """Return list of (path, time_value) sorted by time ascending.
    Prefer time parsed from filename 'snapshot_<time>.csv'; fallback to mtime.
    """
    pattern = os.path.join(build_dir, 'snapshot_*.csv')
    files = glob.glob(pattern)
    out: List[Tuple[str, float]] = []
    for p in files:
        m = re.search(r"snapshot_([0-9.eE+\-]+)\.csv$", os.path.basename(p))
        if m:
            try:
                tval = float(m.group(1))
            except ValueError:
                tval = os.path.getmtime(p)
        else:
            tval = os.path.getmtime(p)
        out.append((p, tval))
    out.sort(key=lambda it: it[1])
    return out


def compute_minmax_over_files(files: List[Tuple[str, float]], field: str) -> Tuple[Optional[float], Optional[float]]:
    """Compute global min/max for a field across given snapshot files.
    Returns (vmin, vmax) or (None, None) if no data.
    """
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    for path, _ in files:
        snap = load_snapshot(path)
        data = getattr(snap, field)
        if data.size == 0:
            continue
        dmin = float(np.nanmin(data))
        dmax = float(np.nanmax(data))
        vmin = dmin if vmin is None else min(vmin, dmin)
        vmax = dmax if vmax is None else max(vmax, dmax)
    return vmin, vmax


@dataclass
class Snapshot:
    time: float
    idx: np.ndarray  # integer indices along x
    rho: np.ndarray
    vel: np.ndarray
    pres: np.ndarray


def load_snapshot(csv_path: str) -> Snapshot:
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Snapshot CSV not found: {csv_path}")

    times: List[float] = []
    idxs: List[int] = []
    rhos: List[float] = []
    vels: List[float] = []
    press: List[float] = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        expected = {'time', 'idx', 'rho', 'vel', 'pres'}
        if set(reader.fieldnames or []) != expected:
            # Be lenient: only require the expected fields to be present
            if not expected.issubset(set(reader.fieldnames or [])):
                raise ValueError(f"CSV header must include {expected}, got {reader.fieldnames}")
        for row in reader:
            times.append(float(row['time']))
            idxs.append(int(row['idx']))
            rhos.append(float(row['rho']))
            vels.append(float(row['vel']))
            press.append(float(row['pres']))

    # Time is constant per snapshot; take last value
    t = times[-1] if times else 0.0
    return Snapshot(
        time=t,
        idx=np.asarray(idxs, dtype=int),
        rho=np.asarray(rhos, dtype=float),
        vel=np.asarray(vels, dtype=float),
        pres=np.asarray(press, dtype=float),
    )


def make_heatmap_2d(values_1d: np.ndarray, y_repeat: int) -> np.ndarray:
    values_1d = np.asarray(values_1d, dtype=float)
    # Shape: (y_repeat, nx_samples)
    return np.tile(values_1d[np.newaxis, :], (y_repeat, 1))


def plot_heatmap(snapshot: Snapshot, consts: SimConstants, field: str, y_repeat: int = 50,
                 cmap: str = 'viridis', save: Optional[str] = None, show: bool = True,
                 vmin: Optional[float] = None, vmax: Optional[float] = None) -> None:
    field = field.lower()
    if field not in ('rho', 'vel', 'pres'):
        raise ValueError("--field must be one of: rho, vel, pres")

    data = getattr(snapshot, field)

    # x positions in meters using constants
    x = snapshot.idx * consts.DX

    # Build heatmap by repeating along y
    H = make_heatmap_2d(data, y_repeat=y_repeat)

    fig, ax = plt.subplots(figsize=(10, 3.2))

    # extent: [x_min, x_max, y_min, y_max]
    extent = [float(x.min()), float(x.max()), 0.0, 1.0]
    im = ax.imshow(H, aspect='auto', origin='lower', cmap=cmap,
                   extent=extent, vmin=vmin, vmax=vmax)

    ax.set_xlabel('x (m)')
    ax.set_ylabel('artificial y')
    ax.set_title(f"{field} heatmap at t={snapshot.time:.6f}s  (samples={len(x)})")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label({'rho': 'density (kg/m^3)', 'vel': 'velocity (m/s)', 'pres': 'pressure (Pa)'}[field])

    fig.tight_layout()

    if save:
        os.makedirs(os.path.dirname(save) or '.', exist_ok=True)
        fig.savefig(save, dpi=150)
        print(f"[INFO] Saved heatmap to {save}")
    if show:
        plt.show()
    else:
        plt.close(fig)


def watch_heatmap(consts: SimConstants, field: str, build_dir: str = DEFAULT_BUILD_DIR,
                  y_repeat: int = 50, cmap: str = 'viridis', interval: float = 0.5,
                  vmin: Optional[float] = None, vmax: Optional[float] = None,
                  lock_scale: bool = True) -> None:
    """Continuously watch the build directory and refresh the heatmap with the latest snapshot."""
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 3.2))
    im = None
    cbar = None
    last_path = None
    last_mtime = 0.0

    # If locking scale and user didn't provide bounds, compute once from current files
    if lock_scale and (vmin is None or vmax is None):
        files_now = list_snapshots_sorted(build_dir)
        vmin_auto, vmax_auto = compute_minmax_over_files(files_now, field)
        if vmin is None:
            vmin = vmin_auto
        if vmax is None:
            vmax = vmax_auto

    try:
        while True:
            path = find_latest_snapshot(build_dir)
            if path:
                mtime = os.path.getmtime(path)
                if path != last_path or mtime > last_mtime:
                    snap = load_snapshot(path)
                    data = getattr(snap, field)
                    x = snap.idx * consts.DX
                    H = make_heatmap_2d(data, y_repeat=y_repeat)
                    extent = [float(x.min()), float(x.max()), 0.0, 1.0]

                    # Initialize or update plot
                    if im is None or im.get_array().shape[1] != H.shape[1]:
                        ax.clear()
                        im = ax.imshow(H, aspect='auto', origin='lower', cmap=cmap,
                                       extent=extent, vmin=vmin, vmax=vmax)
                        if cbar is not None:
                            cbar.remove()
                        cbar = fig.colorbar(im, ax=ax)
                        cbar.set_label({'rho': 'density (kg/m^3)', 'vel': 'velocity (m/s)', 'pres': 'pressure (Pa)'}[field])
                        ax.set_xlabel('x (m)')
                        ax.set_ylabel('artificial y')
                    else:
                        im.set_data(H)
                        im.set_extent(extent)
                        if lock_scale and (vmin is not None and vmax is not None):
                            im.set_clim(vmin=vmin, vmax=vmax)
                        elif not lock_scale and (vmin is None or vmax is None):
                            # Only autoscale when not locking scale
                            im.autoscale()

                    ax.set_title(f"{field} heatmap at t={snap.time:.6f}s  (samples={len(x)})\n{os.path.basename(path)}")
                    fig.canvas.draw_idle()
                    last_path, last_mtime = path, mtime
            else:
                ax.set_title("Waiting for snapshot CSVs in build/ ...")
                fig.canvas.draw_idle()

            plt.pause(0.001)
            time.sleep(max(0.0, interval))
    except KeyboardInterrupt:
        pass
    finally:
        plt.ioff()
        if plt.get_fignums():
            plt.show()


def play_all_snapshots(consts: SimConstants, field: str, build_dir: str = DEFAULT_BUILD_DIR,
                       y_repeat: int = 50, cmap: str = 'viridis', interval: float = 0.2,
                       vmin: Optional[float] = None, vmax: Optional[float] = None,
                       loop: bool = False, lock_scale: bool = True) -> None:
    """Load all CSVs under build/ and render from the beginning sequentially."""
    files = list_snapshots_sorted(build_dir)
    if not files:
        raise SystemExit("No snapshot CSVs found under build/. Run the simulation to generate snapshots.")

    # If locking scale and user didn't provide bounds, compute global min/max across files
    if lock_scale and (vmin is None or vmax is None):
        vmin_auto, vmax_auto = compute_minmax_over_files(files, field)
        if vmin is None:
            vmin = vmin_auto
        if vmax is None:
            vmax = vmax_auto

    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 3.2))
    im = None
    cbar = None

    try:
        while True:
            for path, tval in files:
                snap = load_snapshot(path)
                data = getattr(snap, field)
                x = snap.idx * consts.DX
                H = make_heatmap_2d(data, y_repeat=y_repeat)
                extent = [float(x.min()), float(x.max()), 0.0, 1.0]

                if im is None or im.get_array().shape[1] != H.shape[1]:
                    ax.clear()
                    im = ax.imshow(H, aspect='auto', origin='lower', cmap=cmap,
                                   extent=extent, vmin=vmin, vmax=vmax)
                    if cbar is not None:
                        cbar.remove()
                    cbar = fig.colorbar(im, ax=ax)
                    cbar.set_label({'rho': 'density (kg/m^3)', 'vel': 'velocity (m/s)', 'pres': 'pressure (Pa)'}[field])
                    ax.set_xlabel('x (m)')
                    ax.set_ylabel('artificial y')
                else:
                    im.set_data(H)
                    im.set_extent(extent)
                    if lock_scale and (vmin is not None and vmax is not None):
                        im.set_clim(vmin=vmin, vmax=vmax)
                    elif not lock_scale and (vmin is None or vmax is None):
                        im.autoscale()

                ax.set_title(f"{field} heatmap at t={snap.time:.6f}s  (samples={len(x)})\n{os.path.basename(path)}")
                fig.canvas.draw_idle()
                plt.pause(0.001)
                time.sleep(max(0.0, interval))

            if not loop:
                break
    except KeyboardInterrupt:
        pass
    finally:
        plt.ioff()
        if plt.get_fignums():
            plt.show()


def main():
    parser = argparse.ArgumentParser(description='Render heatmap for 1D CFD snapshot CSV.')
    parser.add_argument('--field', required=True, choices=['rho', 'vel', 'pres'], help='Field to visualize')
    parser.add_argument('--file', default=None, help='Path to snapshot CSV; default is the latest under build/')
    parser.add_argument('--constants', default=DEFAULT_CONSTANTS, help='Path to include/constants.h')
    parser.add_argument('--y-repeat', type=int, default=50, help='Rows to replicate along y for heatmap aesthetics')
    parser.add_argument('--cmap', default='viridis', help='Matplotlib colormap')
    parser.add_argument('--save', default=None, help='Output image path (PNG). If not set, show interactively.')
    parser.add_argument('--watch', action='store_true', help='Continuously watch build/ and refresh latest snapshot')
    parser.add_argument('--interval', type=float, default=0.5, help='Refresh interval (seconds) when --watch is used')
    parser.add_argument('--vmin', type=float, default=None, help='Fix colormap lower bound (optional)')
    parser.add_argument('--vmax', type=float, default=None, help='Fix colormap upper bound (optional)')
    parser.add_argument('--play-all', action='store_true', help='Load all CSVs in build/ and render sequentially from the beginning')
    parser.add_argument('--loop', action='store_true', help='Loop playback when used with --play-all')
    parser.add_argument('--no-lock-scale', action='store_true', help='Do not lock colormap scale globally; allow autoscale per frame')
    parser.add_argument('--no-show', action='store_true', help='Do not open a window (useful with --save)')

    args = parser.parse_args()

    consts = parse_constants(args.constants)

    lock_scale = not args.no_lock_scale

    if args.play_all and args.file is None:
        print(f"[INFO] Playing all snapshots from {DEFAULT_BUILD_DIR} ...")
        print(f"[INFO] Constants: NX={consts.NX}, DX={consts.DX}")
        play_all_snapshots(consts, field=args.field, build_dir=DEFAULT_BUILD_DIR,
                           y_repeat=args.y_repeat, cmap=args.cmap, interval=args.interval,
                           vmin=args.vmin, vmax=args.vmax, loop=args.loop, lock_scale=lock_scale)
    elif args.watch and args.file is None:
        print(f"[INFO] Watching {DEFAULT_BUILD_DIR} for latest snapshots ...")
        print(f"[INFO] Constants: NX={consts.NX}, DX={consts.DX}")
        watch_heatmap(consts, field=args.field, build_dir=DEFAULT_BUILD_DIR,
                      y_repeat=args.y_repeat, cmap=args.cmap, interval=args.interval,
                      vmin=args.vmin, vmax=args.vmax, lock_scale=lock_scale)
    else:
        csv_path = args.file or find_latest_snapshot(DEFAULT_BUILD_DIR)
        if not csv_path:
            raise SystemExit("No snapshot CSV found under build/. Run the simulation until it writes a snapshot.")

        snap = load_snapshot(csv_path)
        print(f"[INFO] Loaded snapshot: {csv_path} (t={snap.time:.6f}s, samples={len(snap.idx)})")
        print(f"[INFO] Constants: NX={consts.NX}, DX={consts.DX}")

        plot_heatmap(snap, consts, field=args.field, y_repeat=args.y_repeat,
                     cmap=args.cmap, save=args.save, show=not args.no_show,
                     vmin=args.vmin, vmax=args.vmax)


if __name__ == '__main__':
    main()
