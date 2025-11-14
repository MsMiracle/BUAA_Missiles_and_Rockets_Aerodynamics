#!/usr/bin/env python3
"""
plot_field_xt.py

从 build/ 目录下的所有快照 CSV（snapshot_*.csv）中读取流场数据，
绘制流速 vel、密度 rho、压强 pres 随时间 t 和位置 x 的分布曲面。

每个 CSV 的列格式为：time,idx,rho,vel,pres
- time: 当前快照时刻（对文件内所有行相同）
- idx: 空间网格索引 i
- rho, vel, pres: 对应物理量

本脚本将：
1. 扫描 build/ 下所有 snapshot_*.csv，按 time 排序
2. 构建二维数组：
   - t 轴：所有快照时刻
   - x 轴：通过 idx * DX（从 include/constants.h 中读取）得到
   - 每个物理量形成一个 (nt, nx) 的二维矩阵
3. 使用 imshow 绘制三个 x-t 色彩图（rho/vel/pres），可选插值和保存

示例：
  python scripts/plot_field_xt.py --field rho
  python scripts/plot_field_xt.py --field vel --save vel_xt.png --no-show
  python scripts/plot_field_xt.py --field pres --interpolate

依赖：numpy, matplotlib
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import re
from typing import List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  # 激活 3D 投影

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BUILD_DIR = os.path.join(ROOT_DIR, 'build')
DEFAULT_CONSTANTS = os.path.join(ROOT_DIR, 'include', 'constants.h')


def parse_constants(constants_path: str = DEFAULT_CONSTANTS) -> Tuple[int, float]:
    """从 constants.h 中解析 NX, DX"""
    if not os.path.isfile(constants_path):
        raise FileNotFoundError(f"constants.h not found at: {constants_path}")
    with open(constants_path, 'r', encoding='utf-8') as f:
        text = f.read()
    nx_match = re.search(r"#\s*define\s+NX\s+([0-9]+)", text)
    dx_match = re.search(r"#\s*define\s+DX\s+([0-9.eE+\-]+)", text)
    if not nx_match or not dx_match:
        raise ValueError("Failed to parse NX/DX from constants.h. Ensure '#define NX <int>' and '#define DX <float>'.")
    NX = int(nx_match.group(1))
    DX = float(dx_match.group(1))
    return NX, DX


def list_snapshot_files(build_dir: str) -> List[str]:
    pattern = os.path.join(build_dir, 'snapshot_*.csv')
    files = glob.glob(pattern)
    # 先按修改时间排序，后续按 time 再精排
    files.sort(key=lambda p: os.path.getmtime(p))
    return files


def read_snapshot(path: str) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """读取单个快照文件，返回 (time, idx_array, rho, vel, pres)。"""
    times: List[float] = []
    idxs: List[int] = []
    rhos: List[float] = []
    vels: List[float] = []
    press: List[float] = []

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required = {'time', 'idx', 'rho', 'vel', 'pres'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV {path} missing required columns: {reader.fieldnames}")
        for row in reader:
            times.append(float(row['time']))
            idxs.append(int(row['idx']))
            rhos.append(float(row['rho']))
            vels.append(float(row['vel']))
            press.append(float(row['pres']))

    if not times:
        raise ValueError(f"CSV {path} has no data rows")

    # 该快照时刻对所有行相同，取最后一个即可
    t = times[-1]
    idx_arr = np.asarray(idxs, dtype=int)
    rho_arr = np.asarray(rhos, dtype=float)
    vel_arr = np.asarray(vels, dtype=float)
    pres_arr = np.asarray(press, dtype=float)

    # 按 idx 排序，保证空间顺序一致
    order = np.argsort(idx_arr)
    idx_arr = idx_arr[order]
    rho_arr = rho_arr[order]
    vel_arr = vel_arr[order]
    pres_arr = pres_arr[order]
    return t, idx_arr, rho_arr, vel_arr, pres_arr


def build_xt_field(build_dir: str, field: str, NX: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """构建指定 field 的 (t, x_idx, values) 网格。

    返回：
      times: shape (nt,)
      x_idx: shape (nx,)  —— 假定所有快照覆盖相同的 idx 集合
      F:     shape (nt, nx) 对应 field 值
    """
    files = list_snapshot_files(build_dir)
    if not files:
        raise SystemExit(f"No snapshot CSV found under {build_dir}")

    snapshots: List[Tuple[float, np.ndarray]] = []
    x_idx_ref: Optional[np.ndarray] = None

    for path in files:
        t, idx_arr, rho_arr, vel_arr, pres_arr = read_snapshot(path)
        if x_idx_ref is None:
            x_idx_ref = idx_arr
        else:
            # 若采样点集合不一致，可根据需要做插值；这里简单要求一致
            if len(idx_arr) != len(x_idx_ref) or not np.array_equal(idx_arr, x_idx_ref):
                raise SystemExit(
                    f"Snapshot {path} has different spatial sampling (idx set) than previous files; "
                    "consider resampling or adjusting output stride in main.c.")
        if field == 'rho':
            snapshots.append((t, rho_arr))
        elif field == 'vel':
            snapshots.append((t, vel_arr))
        elif field == 'pres':
            snapshots.append((t, pres_arr))
        else:
            raise ValueError("field must be one of 'rho', 'vel', 'pres'")

    # 按时间排序
    snapshots.sort(key=lambda item: item[0])
    times = np.array([s[0] for s in snapshots], dtype=float)
    F = np.vstack([s[1] for s in snapshots])  # (nt, nx)
    x_idx = x_idx_ref.copy()

    return times, x_idx, F


def plot_xt_heatmap(times: np.ndarray, x_idx: np.ndarray, F: np.ndarray, field: str, DX: float,
                     save: Optional[str] = None, show: bool = True,
                     interpolate: bool = False) -> None:
    """绘制 x-t 色彩图（将值视为 z 维度）。"""
    # 转为物理坐标
    x = x_idx * DX
    T_min, T_max = float(times.min()), float(times.max())

    # 构造网格
    # imshow 只需 extent，因此不必构造 full meshgrid
    extent = [float(x.min()), float(x.max()), T_min, T_max]

    # 根据 field 选择色标标签
    if field == 'rho':
        label = 'density (kg/m^3)'
    elif field == 'vel':
        label = 'velocity (m/s)'
    else:
        label = 'pressure (Pa)'

    fig, ax = plt.subplots(figsize=(8, 5))
    # 注意 imshow 默认 y 轴向下，这里 origin='lower' 让时间向上增长
    if interpolate:
        # 使用双线性插值（默认）
        im = ax.imshow(F, aspect='auto', origin='lower', extent=extent, cmap='viridis')
    else:
        # 关闭插值，保留网格感
        im = ax.imshow(F, aspect='auto', origin='lower', extent=extent, cmap='viridis', interpolation='nearest')

    ax.set_xlabel('x (m)')
    ax.set_ylabel('time (s)')
    ax.set_title(f"{field} field: value(t, x)")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(label)

    fig.tight_layout()
    if save:
        os.makedirs(os.path.dirname(save) or '.', exist_ok=True)
        fig.savefig(save, dpi=150)
        print(f"[INFO] Saved figure to {save}")
    if show:
        plt.show()
    else:
        plt.close(fig)

def plot_xt_surface3d(times: np.ndarray, x_idx: np.ndarray, F: np.ndarray, field: str, DX: float,
                      save: Optional[str] = None, show: bool = True) -> None:
    """绘制真正的 3D 曲面：横轴 x，纵轴 time，高度为 field 值。"""
    # 物理坐标
    x = x_idx * DX
    t = times

    # 构造网格：F 形状是 (nt, nx)，所以用 ij 索引保证对齐
    T_grid, X_grid = np.meshgrid(t, x, indexing='ij')  # both (nt, nx)

    # 选择标签
    if field == 'rho':
        zlabel = 'density (kg/m^3)'
    elif field == 'vel':
        zlabel = 'velocity (m/s)'
    else:
        zlabel = 'pressure (Pa)'

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')

    # 画曲面
    surf = ax.plot_surface(X_grid, T_grid, F,
                           cmap='viridis',
                           linewidth=0,
                           antialiased=True)

    ax.set_xlabel('x (m)')
    ax.set_ylabel('time (s)')
    ax.set_zlabel(zlabel)
    ax.set_title(f"{field} field surface: value(t, x)")

    fig.colorbar(surf, ax=ax, shrink=0.6, aspect=10, pad=0.1, label=zlabel)

    # 视角可以按喜好调整
    ax.view_init(elev=30, azim=-135)

    fig.tight_layout()
    if save:
        os.makedirs(os.path.dirname(save) or '.', exist_ok=True)
        fig.savefig(save, dpi=150)
        print(f"[INFO] Saved 3D surface to {save}")
    if show:
        plt.show()
    else:
        plt.close(fig)
def parse_args():
    p = argparse.ArgumentParser(
        description='Plot rho/vel/pres as x-t fields from snapshot CSVs (2D heatmap or 3D surface).'
    )
    p.add_argument('--field', type=str, choices=['rho', 'vel', 'pres'], required=True,
                   help='Which field to plot: rho, vel, pres')
    p.add_argument('--build-dir', type=str, default=DEFAULT_BUILD_DIR,
                   help='Directory containing snapshot CSVs')
    p.add_argument('--constants', type=str, default=DEFAULT_CONSTANTS,
                   help='Path to include/constants.h')
    p.add_argument('--save', type=str, default=None,
                   help='Path to save figure')
    p.add_argument('--no-show', action='store_true',
                   help='Do not show window (useful on servers or when saving only)')
    p.add_argument('--interpolate', action='store_true',
                   help='Use bilinear interpolation for smoother 2D heatmap (ignored for 3D surface)')
    p.add_argument('--mode', type=str, choices=['heatmap', 'surface'], default='surface',
                   help="Visualization mode: 'heatmap' for 2D x-t colormap, 'surface' for 3D surface (default).")
    return p.parse_args()


def main():
    args = parse_args()
    NX, DX = parse_constants(args.constants)
    times, x_idx, F = build_xt_field(args.build_dir, args.field, NX)

    if args.mode == 'heatmap':
        # 2D 色彩图
        plot_xt_heatmap(times, x_idx, F,
                        field=args.field,
                        DX=DX,
                        save=args.save,
                        show=not args.no_show,
                        interpolate=args.interpolate)
    else:
        # 3D 曲面
        if args.interpolate:
            print("[WARN] --interpolate is ignored in 3D surface mode.")
        plot_xt_surface3d(times, x_idx, F,
                          field=args.field,
                          DX=DX,
                          save=args.save,
                          show=not args.no_show)


if __name__ == '__main__':
    main()
