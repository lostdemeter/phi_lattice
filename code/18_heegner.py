#!/usr/bin/env python3
"""Section 18: The Heegner Subspace -- demonstration."""

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

HEEGNER_NUMBERS = [1, 2, 3, 7, 11, 19, 43, 67, 163]


def heegner_weights(d, n_dims=512):
    w = 1.0 + (d - 1.0) * np.cos(np.pi * np.arange(n_dims) / d) ** 2
    return w


def ramanujan_constant(d):
    return math.exp(math.pi * math.sqrt(d))


def energy_fraction(weights, top_n):
    """Fraction of total weight energy in top N dimensions."""
    total = np.sum(weights ** 2)
    sorted_w = np.sort(weights)[::-1]
    return float(np.sum(sorted_w[:top_n] ** 2) / total)


def simulate_subspace_accuracy(n_dims=512, d=163, n_tests=100):
    """Simulate accuracy of projecting to Heegner subspace."""
    rng = np.random.RandomState(42)
    weights = heegner_weights(d, n_dims)
    top_dims = np.argsort(weights)[::-1]

    results = {}
    for n_keep in [1, 3, 8, 16, 32, 64, 128, 256]:
        corrs = []
        for _ in range(n_tests):
            coeffs = rng.randn(n_dims).astype(np.float64) * weights
            full = coeffs.copy()
            # Project: keep only top n_keep Heegner dimensions
            proj = np.zeros(n_dims, dtype=np.float64)
            proj[top_dims[:n_keep]] = coeffs[top_dims[:n_keep]]
            corr = float(np.corrcoef(full, proj)[0, 1]) if np.std(full) > 1e-30 and np.std(proj) > 1e-30 else 0.0
            corrs.append(corr)
        results[n_keep] = {"mean_corr": np.mean(corrs), "energy": energy_fraction(weights, n_keep)}
    return results


def generate_figure():
    print("\nGenerating Figure 18.1: Heegner Subspace...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Top-left: Heegner weights across 512D (d=163)
    ax = axes[0, 0]
    w163 = heegner_weights(163, 512)
    ax.plot(w163, color="#2e86c1", linewidth=0.8, alpha=0.8)
    # Highlight tight dimensions
    tight = [0, 163, 326]
    for t in tight:
        ax.scatter(t, w163[t], color="#e74c3c", s=50, zorder=5,
                   edgecolors="white", linewidth=0.5)
        ax.annotate(f"i={t}\nw={w163[t]:.0f}", (t, w163[t]),
                    xytext=(t+20, w163[t]-30),
                    arrowprops=dict(arrowstyle="->", color="#c0392b"),
                    fontsize=8, fontweight="bold", color="#c0392b")
    ax.set_xlabel("Dimension index i")
    ax.set_ylabel("Heegner Weight w[i]")
    ax.set_title(f"Heegner Weights (d=163) across 512D")
    ax.grid(True, alpha=0.3)

    # Top-right: Ramanujan constant for each Heegner number
    ax = axes[0, 1]
    rc = [ramanujan_constant(d) for d in HEEGNER_NUMBERS]
    ax.bar(range(len(HEEGNER_NUMBERS)), [math.log10(r) for r in rc],
           color="#d4a017", edgecolor="white", linewidth=0.3)
    ax.set_xticks(range(len(HEEGNER_NUMBERS)))
    ax.set_xticklabels([f"d={d}" for d in HEEGNER_NUMBERS], fontsize=8)
    ax.set_ylabel("log10(e^(pi sqrt(d)))")
    ax.set_title("Ramanujan Constant Magnitude by Heegner Number")
    ax.grid(True, alpha=0.3, axis="y")
    # Annotate d=163
    ax.text(8, 14, f"d=163:\ne^(pi sqrt(163))\n≈ 2.6e17",
            fontsize=8, color="#c0392b", fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

    # Bottom-left: Energy concentration
    ax = axes[1, 0]
    acc = simulate_subspace_accuracy(512, 163, 50)
    n_keeps = sorted(acc.keys())
    energies = [acc[n]["energy"] * 100 for n in n_keeps]
    corrs = [max(0, acc[n]["mean_corr"]) * 100 for n in n_keeps]

    ax.plot(n_keeps, energies, "o-", color="#2e86c1", linewidth=2, markersize=8,
            markeredgecolor="white", markeredgewidth=0.5, label="Energy retained")
    ax.plot(n_keeps, corrs, "s-", color="#e74c3c", linewidth=2, markersize=8,
            markeredgecolor="white", markeredgewidth=0.5, label="Correlation")
    ax.axvline(x=3, color="#2ecc71", linestyle="--", linewidth=1.5, alpha=0.7,
               label="3D Heegner subspace")
    ax.axhline(y=99, color="gray", linestyle=":", linewidth=0.8, alpha=0.5)
    ax.set_xscale("log")
    ax.set_xlabel("Dimensions Kept (top-N Heegner)")
    ax.set_ylabel("Percentage")
    ax.set_title("Subspace Accuracy vs Dimensions")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Bottom-right: Heegner number comparison
    ax = axes[1, 1]
    comp_data = []
    for d in HEEGNER_NUMBERS:
        w = heegner_weights(d, 512)
        e3 = energy_fraction(w, 3) * 100
        top_idx = np.argsort(w)[::-1][:3]
        comp_data.append((d, e3, top_idx))

    xs = np.arange(len(HEEGNER_NUMBERS))
    e3s = [d[1] for d in comp_data]
    colors_h = ["#2ecc71" if e > 99 else "#f39c12" if e > 95 else "#e74c3c"
                for e in e3s]
    ax.bar(xs, e3s, color=colors_h, edgecolor="white", linewidth=0.3)
    ax.axhline(y=99, color="#2ecc71", linestyle="--", linewidth=1, alpha=0.5,
               label="99% energy threshold")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"d={d}" for d in HEEGNER_NUMBERS], fontsize=8)
    ax.set_ylabel("Energy in Top-3 (%)")
    ax.set_title("Energy Concentration by Heegner Number")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    plt.suptitle("The Heegner Subspace: 512D -> 3D at 170x Compression",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "18_heegner_subspace.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def main():
    print("Section 18: The Heegner Subspace\n")
    print("=" * 60)

    # 1. Heegner weights
    print("\n1. Heegner Weights (d=163, 512D)")
    print("-" * 40)
    w163 = heegner_weights(163, 512)
    top3 = np.argsort(w163)[::-1][:3]
    print(f"  Weight range: [{w163.min():.1f}, {w163.max():.1f}]")
    print(f"  Top-3 dimensions: {top3.tolist()} (weights: {w163[top3].tolist()})")
    e3 = energy_fraction(w163, 3) * 100
    e1 = energy_fraction(w163, 1) * 100
    print(f"  Energy in top-1 dim: {e1:.1f}%")
    print(f"  Energy in top-3 dims: {e3:.1f}%")
    print(f"  Compression ratio: {512/3:.0f}x")

    # 2. Ramanujan constant
    print("\n2. Ramanujan Constants e^(pi sqrt(d))")
    print("-" * 40)
    for d in HEEGNER_NUMBERS:
        rc = ramanujan_constant(d)
        if d == 163:
            # Check the famous almost-integer
            diff_to_int = abs(rc - round(rc))
            print(f"  d={d:>3}: e^(pi sqrt({d})) = {rc:.2f} "
                  f"(diff to int: {diff_to_int:.6e})")
        else:
            print(f"  d={d:>3}: e^(pi sqrt({d})) = {rc:.2f}")

    # 3. Subspace accuracy
    print("\n3. Subspace Projection Accuracy")
    print("-" * 40)
    results = simulate_subspace_accuracy(512, 163, 50)
    for n in [1, 3, 8, 16, 32, 64]:
        r = results[n]
        print(f"  {n:>3}D: energy={r['energy']*100:.1f}%, "
              f"corr={r['mean_corr']:.4f}, compression={512/n:.0f}x")

    # 4. Heegner number comparison
    print("\n4. Energy Concentration by Heegner Number")
    print("-" * 40)
    for d in HEEGNER_NUMBERS:
        w = heegner_weights(d, 512)
        e3 = energy_fraction(w, 3) * 100
        print(f"  d={d:>3}: top-3 energy = {e3:.1f}%")

    # Figures
    generate_figure()

    print(f"\n{'=' * 60}")
    print("Done. Figure generated.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
