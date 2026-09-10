#!/usr/bin/env python3
"""Section 08: The T Transformation -- demonstration.

Key demonstrations:
  1. Three softmax variants: float, naive lattice, T-transformed
  2. Algebraic derivation of T: T(x) = round(k*x / ln(phi))
  3. Taylor series for exp with range reduction
  4. Correlation measurement across sequence lengths
"""

import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

PHI = (1 + math.sqrt(5)) / 2
LN_PHI = math.log(PHI)
K = 256


def float_softmax(x):
    x = np.asarray(x, dtype=np.float64)
    x_max = x.max(axis=-1, keepdims=True)
    e = np.exp(x - x_max)
    return e / e.sum(axis=-1, keepdims=True)


def naive_lattice_softmax(x):
    x = np.asarray(x, dtype=np.float64)
    x_max = x.max(axis=-1, keepdims=True)
    phi_pow = PHI ** (x - x_max)
    return phi_pow / phi_pow.sum(axis=-1, keepdims=True)


def t_transform(x):
    return np.round(K * x / LN_PHI).astype(np.int32)


def t_transformed_softmax(x):
    x = np.asarray(x, dtype=np.float64)
    x_max = x.max(axis=-1, keepdims=True)
    x_shifted = x - x_max
    exponents = t_transform(x_shifted)
    phi_pow = PHI ** (exponents.astype(np.float64) / K)
    return phi_pow / phi_pow.sum(axis=-1, keepdims=True)


def exp_taylor(z, n_terms=8):
    result = np.ones_like(z, dtype=np.float64)
    term = np.ones_like(z, dtype=np.float64)
    for m in range(1, n_terms + 1):
        term = term * z / m
        result = result + term
    return result


def taylor_range_reduced_softmax(x, n_terms=8):
    x = np.asarray(x, dtype=np.float64)
    x_max = x.max(axis=-1, keepdims=True)
    x_shifted = x - x_max
    ln2 = math.log(2.0)
    n = np.floor(x_shifted / ln2)
    remainder = x_shifted - n * ln2
    exp_rem = exp_taylor(remainder, n_terms)
    exp_full = exp_rem * (2.0 ** n)
    return exp_full / exp_full.sum(axis=-1, keepdims=True)


def correlation(a, b):
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    return float(np.corrcoef(a, b)[0, 1])


def run_softmax_comparison(n_tests=500, seq_len=8):
    rng = np.random.RandomState(42)
    naive_corr = []; t_corr = []; taylor_corr = []
    for _ in range(n_tests):
        x = rng.randn(seq_len) * 2.0
        ref = float_softmax(x)
        naive_corr.append(correlation(ref, naive_lattice_softmax(x)))
        t_corr.append(correlation(ref, t_transformed_softmax(x)))
        taylor_corr.append(correlation(ref, taylor_range_reduced_softmax(x, 8)))
    return {
        "naive_mean": np.mean(naive_corr), "naive_std": np.std(naive_corr),
        "t_mean": np.mean(t_corr), "t_std": np.std(t_corr),
        "taylor_mean": np.mean(taylor_corr), "taylor_std": np.std(taylor_corr),
    }


# Figures

def generate_figure_softmax_comparison():
    print("\nGenerating Figure 8.1: Softmax Comparison...")
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5))
    rng = np.random.RandomState(42)
    x = rng.randn(6) * 2.0
    ref = float_softmax(x)
    naive = naive_lattice_softmax(x)
    t_out = t_transformed_softmax(x)
    x_pos = np.arange(len(x))
    width = 0.25
    for ax, data, title, color in [
        (axes[0], ref, "Float (reference)", "#2e86c1"),
        (axes[1], naive, f"Naive lattice\n(corr={correlation(ref,naive):.3f})",
         "#e74c3c"),
        (axes[2], t_out, f"T-transformed\n(corr={correlation(ref,t_out):.6f})",
         "#2ecc71"),
    ]:
        ax.bar(x_pos, data, width, color=color, edgecolor="white", linewidth=0.3)
        ax.set_title(title)
        ax.set_xticks(x_pos); ax.set_xticklabels([f"{v:.1f}" for v in x], fontsize=8)
        ax.set_ylim(0, 1); ax.grid(True, alpha=0.3, axis="y")
    ax = axes[3]
    ax.bar(x_pos - width, ref, width, color="#2e86c1", edgecolor="white",
           linewidth=0.3, label="Float", alpha=0.8)
    ax.bar(x_pos, t_out, width, color="#2ecc71", edgecolor="white",
           linewidth=0.3, label="T-transformed", alpha=0.8)
    ax.bar(x_pos + width, naive, width, color="#e74c3c", edgecolor="white",
           linewidth=0.3, label="Naive", alpha=0.8)
    ax.set_title("Overlay"); ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{v:.1f}" for v in x], fontsize=8)
    ax.set_ylim(0, 1); ax.legend(fontsize=7); ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    out = FIGURES_DIR / "08_softmax_comparison.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def generate_figure_t_mapping():
    print("\nGenerating Figure 8.2: T Mapping...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    ax = axes[0]
    x_vals = np.linspace(-5, 5, 500)
    ax.plot(x_vals, K * x_vals / LN_PHI, color="#2e86c1", linewidth=2,
            label=f"T(x) = {K:.0f}/ln(phi) * x")
    for ex in [-3, -1, 0, 1, 3]:
        ey = K * ex / LN_PHI
        ax.plot(ex, ey, "o", color="#e74c3c", markersize=8,
                markeredgecolor="white", markeredgewidth=0.5)
        ax.annotate(f"({ex}, {ey:.0f})", (ex, ey), xytext=(10, 10),
                    textcoords="offset points", fontsize=8, color="#c0392b")
    ax.axhline(y=0, color="gray", ls=":", lw=0.5)
    ax.axvline(x=0, color="gray", ls=":", lw=0.5)
    ax.set_xlabel("Float Score x"); ax.set_ylabel("Phi-Exponent e")
    ax.set_title("T: e = k/ln(phi) * x"); ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    rng = np.random.RandomState(42)
    errors = []
    for _ in range(200):
        x = rng.randn(8) * 3.0
        ref = float_softmax(x)
        t_out = t_transformed_softmax(x)
        errors.extend(np.abs(ref - t_out).ravel().tolist())
    ax.hist(errors, bins=60, color="#2ecc71", edgecolor="white",
            linewidth=0.3, alpha=0.85)
    ax.set_xlabel("Absolute Error"); ax.set_ylabel("Count")
    ax.set_title(f"T-Softmax Errors (n={len(errors)})")
    me = max(errors)
    ax.text(0.5, 0.95, f"Max error: {me:.6f}", transform=ax.transAxes,
            ha="center", fontsize=10, fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.8))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = FIGURES_DIR / "08_t_mapping.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def generate_figure_taylor_convergence():
    print("\nGenerating Figure 8.3: Taylor Convergence...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    rng = np.random.RandomState(42)
    ax = axes[0]
    n_range = [2, 3, 4, 5, 6, 7, 8, 10, 12]
    corrs = []
    for n in n_range:
        c = []
        for _ in range(100):
            x = rng.randn(8) * 2.0
            c.append(correlation(float_softmax(x), taylor_range_reduced_softmax(x, n)))
        corrs.append(np.mean(c))
    ax.plot(n_range, corrs, "o-", color="#2e86c1", linewidth=2, markersize=8,
            markeredgecolor="white", markeredgewidth=0.5)
    ax.axhline(y=0.9999, color="#2ecc71", ls="--", lw=1, alpha=0.5,
               label="0.9999 threshold")
    ax.axvline(x=8, color="#e74c3c", ls="--", lw=1, alpha=0.5, label="8 terms")
    ax.set_xlabel("Taylor Terms"); ax.set_ylabel("Correlation")
    ax.set_title("Convergence vs Terms"); ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    x_test = rng.randn(50) * 8.0
    xm = x_test.max()
    xs = x_test - xm
    direct = exp_taylor(xs, 8)
    ln2 = math.log(2.0)
    nf = np.floor(xs / ln2)
    reduced = exp_taylor(xs - nf * ln2, 8) * (2.0 ** nf)
    true = np.exp(xs)
    de = np.abs(direct - true) / np.maximum(true, 1e-30)
    re = np.abs(reduced - true) / np.maximum(true, 1e-30)
    ax.hist(de[de < 5], bins=40, color="#e74c3c", edgecolor="white",
            linewidth=0.3, alpha=0.6, label="Direct Taylor")
    ax.hist(re[re < 5], bins=40, color="#2ecc71", edgecolor="white",
            linewidth=0.3, alpha=0.6, label="With range reduction")
    ax.set_xlabel("Relative Error"); ax.set_ylabel("Count")
    ax.set_title("Range Reduction Benefit"); ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.text(0.95, 0.95, f"Direct err: {np.mean(de):.4f}\nReduced err: {np.mean(re):.6f}",
            transform=ax.transAxes, ha="right", va="top", fontsize=9,
            fontweight="bold", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))
    plt.tight_layout()
    out = FIGURES_DIR / "08_taylor_convergence.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def main():
    print("Section 08: The T Transformation (Softmax Geometry)\n")
    print("=" * 60)

    rng = np.random.RandomState(42)

    print("\n1. T Derivation")
    print("-" * 40)
    print(f"  phi^(e_i/k) = C * exp(x_i)")
    print(f"  e_i/k = log_phi(C) + x_i / ln(phi)")
    print(f"  e_i = k * x_i / ln(phi) + const")
    print(f"  T(x) = round({K:.0f} / {LN_PHI:.4f} * x) = round({K/LN_PHI:.1f} * x)")

    print("\n2. Softmax Comparison")
    print("-" * 40)
    stats = run_softmax_comparison(500, 8)
    print(f"  Naive lattice:  corr = {stats['naive_mean']:.4f} +/- {stats['naive_std']:.4f}")
    print(f"  T-transformed:  corr = {stats['t_mean']:.6f} +/- {stats['t_std']:.6f}")
    print(f"  Taylor 8-term:  corr = {stats['taylor_mean']:.6f} +/- {stats['taylor_std']:.6f}")

    # Cross-validate with a single example
    x = rng.randn(6) * 2.0
    ref = float_softmax(x)
    t_out = t_transformed_softmax(x)
    naive = naive_lattice_softmax(x)
    print(f"\n  Example: x = {np.round(x, 2)}")
    print(f"  Float:      {np.round(ref, 4)}")
    print(f"  T-trans:    {np.round(t_out, 4)}")
    print(f"  Naive:      {np.round(naive, 4)}")
    print(f"  Corr(F,T):  {correlation(ref, t_out):.8f}")
    print(f"  Corr(F,N):  {correlation(ref, naive):.4f}")

    # Taylor convergence
    print("\n3. Taylor Series Convergence")
    print("-" * 40)
    for n in [2, 4, 6, 8, 10, 12]:
        corrs = []
        for _ in range(100):
            x = rng.randn(8) * 2.0
            corrs.append(correlation(float_softmax(x),
                                     taylor_range_reduced_softmax(x, n)))
        print(f"  {n:>2} terms: mean corr = {np.mean(corrs):.6f}")

    print("\n4. Generating Figures")
    print("-" * 40)
    generate_figure_softmax_comparison()
    generate_figure_t_mapping()
    generate_figure_taylor_convergence()

    print(f"\n{'=' * 60}")
    print("Done. All figures generated.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
