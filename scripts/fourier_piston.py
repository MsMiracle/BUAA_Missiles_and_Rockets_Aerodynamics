#!/usr/bin/env python3
"""
fourier_piston.py

Compute the N-th order Fourier series coefficients for the piston acceleration a(t)
defined piecewise in the README:

  a(t) = 3          0 <= t < 10
         0         10 <= t < 30
         1         30 <= t < 40
         0         40 <= t < 60

We treat the function as periodic with period T=60.
Fourier series form (real):

  a(t) ~ a0/2 + sum_{n=1..N} [ a_n cos(2π n t / T) + b_n sin(2π n t / T) ]

Where:
  a_n = (2/T) ∫_0^T a(t) cos(2π n t / T) dt
  b_n = (2/T) ∫_0^T a(t) sin(2π n t / T) dt
  a0  = (2/T) ∫_0^T a(t) dt (so DC term is a0/2)

We integrate analytically over each constant piece.

Usage examples:
  python scripts/fourier_piston.py --order 20
  python scripts/fourier_piston.py --order 50 --export coeffs_50.csv
  python scripts/fourier_piston.py --order 30 --show-series

"""
from __future__ import annotations
import argparse
import math
import csv
from typing import List, Tuple

T = 60.0
# Piecewise segments: (start, end, value)
SEGMENTS = [
    (0.0, 10.0, 3.0),
    (10.0, 30.0, 0.0),
    (30.0, 40.0, 1.0),
    (40.0, 60.0, 0.0),
]

def piecewise_integral(value: float, t0: float, t1: float, func) -> float:
    """Integrate value * func(t) dt over [t0, t1] using analytic antiderivatives for sin/cos.
    func should be either ('cos', n) or ('sin', n) or ('const', None).
    """
    kind, n = func
    if kind == 'const':
        # ∫ value dt = value * (t1 - t0)
        return value * (t1 - t0)
    # Angular frequency
    w = 2.0 * math.pi * n / T
    if kind == 'cos':
        # ∫ value * cos(w t) dt = value * (sin(w t)/w)
        return value * (math.sin(w * t1) - math.sin(w * t0)) / w
    if kind == 'sin':
        # ∫ value * sin(w t) dt = - value * (cos(w t)/w)
        return -value * (math.cos(w * t1) - math.cos(w * t0)) / w
    raise ValueError(f"Unknown func kind: {kind}")

def compute_a0() -> float:
    total = 0.0
    for (t0, t1, v) in SEGMENTS:
        total += piecewise_integral(v, t0, t1, ('const', None))
    # a0 = (2/T) ∫_0^T a(t) dt; DC term is a0/2
    return (2.0 / T) * total

def compute_an_bn(N: int) -> Tuple[List[float], List[float]]:
    a_list: List[float] = []
    b_list: List[float] = []
    for n in range(1, N + 1):
        a_n = 0.0
        b_n = 0.0
        for (t0, t1, v) in SEGMENTS:
            a_n += piecewise_integral(v, t0, t1, ('cos', n))
            b_n += piecewise_integral(v, t0, t1, ('sin', n))
        a_n *= (2.0 / T)
        b_n *= (2.0 / T)
        a_list.append(a_n)
        b_list.append(b_n)
    return a_list, b_list

def reconstruct(t: float, a0: float, a_list: List[float], b_list: List[float]) -> float:
    # Clip t to [0,T) for periodicity
    t = t % T
    s = a0 / 2.0
    for n, (a_n, b_n) in enumerate(zip(a_list, b_list), start=1):
        w = 2.0 * math.pi * n / T
        s += a_n * math.cos(w * t) + b_n * math.sin(w * t)
    return s

def parse_args():
    p = argparse.ArgumentParser(description='Compute Fourier series coefficients for piston acceleration.')
    p.add_argument('--order', type=int, default=20, help='Highest harmonic order N')
    p.add_argument('--export', type=str, default=None, help='Optional CSV output path')
    p.add_argument('--show-series', action='store_true', help='Print reconstructed values at sample times')
    p.add_argument('--samples', type=int, default=13, help='Number of sample times to display when --show-series used')
    return p.parse_args()

def main():
    args = parse_args()
    N = args.order
    a0 = compute_a0()
    a_list, b_list = compute_an_bn(N)

    print(f"Period T = {T}")
    print(f"a0 (DC*2) = {a0:.10f}; DC term (a0/2) = {a0/2:.10f}")
    print(f"Computed harmonics up to n = {N}")
    print("n,a_n,b_n")
    for n, (a_n, b_n) in enumerate(zip(a_list, b_list), start=1):
        print(f"{n},{a_n:.10f},{b_n:.10f}")

    if args.export:
        with open(args.export, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['n', 'a_n', 'b_n'])
            for n, (a_n, b_n) in enumerate(zip(a_list, b_list), start=1):
                w.writerow([n, f"{a_n:.12e}", f"{b_n:.12e}"])
        print(f"[INFO] Coefficients exported to {args.export}")

    if args.show_series:
        print("\nSample reconstruction:")
        for i in range(args.samples):
            t = i * T / (args.samples - 1)
            val = reconstruct(t, a0, a_list, b_list)
            # Original piecewise value for comparison
            orig = None
            for (t0, t1, v) in SEGMENTS:
                if t0 <= t < t1:
                    orig = v
                    break
            if orig is None:  # t==T maps to 0
                orig = SEGMENTS[0][2]
            print(f"t={t:8.3f}  orig={orig:4.1f}  series≈{val:10.6f}")

if __name__ == '__main__':
    main()
