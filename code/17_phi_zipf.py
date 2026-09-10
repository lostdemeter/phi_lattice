#!/usr/bin/env python3
"""Section 17: phi-Zipf and the Zipf Connection -- demonstration."""

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
GAMMAS = [14.134725, 21.022040, 25.010858, 30.424876,
          32.935062, 37.586178, 40.918719, 43.327073]


def phi_zipf_mag(rank):
    return rank ** (-LN_PHI)


def phi_zipf_embed(token_id, n_dims=8):
    scale = n_dims / 4.0
    vec = np.zeros(2 * n_dims)
    for h in range(n_dims):
        mag = PHI ** (-h / scale)
        p = (GAMMAS[h] * (token_id + 1)) % (2 * math.pi)
        vec[2*h] = mag * math.cos(p)
        vec[2*h+1] = mag * math.sin(p)
    return vec


def phi_rung_magnitudes(n_dims, mean_rung=111):
    mags = []
    for h in range(n_dims):
        r = max(0, min(255, int(mean_rung + 30 * math.sin(h * 1.7))))
        mags.append(PHI ** (-r * 20 / 255))
    return np.array(mags)


def demonstrate_duality():
    """Show that phi^(-ln f) = f^(-ln phi)."""
    freqs = np.array([0.001, 0.01, 0.1, 0.5, 1.0])
    phi_form = PHI ** (-np.log(freqs))
    freq_form = freqs ** (-LN_PHI)
    print("  f       phi^(-ln f)    f^(-ln phi)    match?")
    for f, pf, ff in zip(freqs, phi_form, freq_form):
        print(f"  {f:.3f}   {pf:.6f}     {ff:.6f}      {abs(pf-ff)<1e-12}")


def generate_figure():
    print("\nGenerating Figure 17.1: phi-Zipf Connection...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Top-left: Word frequency vs rank
    ax = axes[0, 0]
    ranks = np.arange(1, 10001)
    freq = phi_zipf_mag(ranks)
    ax.loglog(ranks, freq, color="#2e86c1", linewidth=2,
              label=f"phi-Zipf: rank^(-{LN_PHI:.3f})")
    # Standard Zipf (alpha=1.0)
    zipf1 = ranks ** (-1.0)
    ax.loglog(ranks, zipf1, color="#e74c3c", linewidth=1.5, linestyle="--",
              alpha=0.6, label="Standard Zipf: rank^(-1.0)")
    ax.set_xlabel("Rank")
    ax.set_ylabel("Relative Frequency")
    ax.set_title("phi-Zipf vs Standard Zipf")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Top-right: phi-Zipf embedding magnitudes (within-vector)
    ax = axes[0, 1]
    n_dims = 32
    dims = np.arange(n_dims)
    mags_zipf = np.array([PHI ** (-h / (n_dims/4)) for h in range(n_dims)])
    mags_rung = phi_rung_magnitudes(n_dims, 111)

    ax.bar(dims, mags_zipf, color="#2e86c1", alpha=0.6, label="phi-Zipf decay")
    ax.plot(dims, mags_zipf, "o-", color="#2e86c1", linewidth=1.5, markersize=3)
    ax.set_xlabel("Dimension h")
    ax.set_ylabel("Magnitude")
    ax.set_title(f"Within-Vector phi-Zipf Decay (32D)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")

    # Bottom-left: 5 appearances of ln(phi)
    ax = axes[1, 0]
    appearances = ["Gate\nthreshold", "phi-Zipf\nexponent", "Embedding\ndecay",
                   "Pareto\nsplit", "Zeta\nquantization"]
    values = [LN_PHI, LN_PHI, LN_PHI, 1 - 1/PHI, LN_PHI]
    colors_a = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12", "#9b59b6"]
    x = np.arange(len(appearances))
    ax.bar(x, values, color=colors_a, edgecolor="white", linewidth=0.3)
    ax.axhline(y=LN_PHI, color="#2ecc71", linestyle="--", linewidth=1, alpha=0.5,
               label=f"ln(phi) = {LN_PHI:.4f}")
    ax.set_xticks(x)
    ax.set_xticklabels(appearances, fontsize=8)
    ax.set_ylabel("Value")
    ax.set_title("Five Independent Appearances of ln(phi)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    # Bottom-right: phi-rung atlas
    ax = axes[1, 1]
    rungs = np.arange(256)
    values_r = PHI ** (-rungs * 20 / 255)
    # Color bands
    colors_r = []
    for r in rungs:
        if r < 90: colors_r.append("#e74c3c")
        elif r < 110: colors_r.append("#2ecc71")
        elif r < 130: colors_r.append("#3498db")
        elif r < 150: colors_r.append("#f39c12")
        else: colors_r.append("#9b59b6")
    ax.scatter(rungs[::4], values_r[::4], c=np.array(colors_r)[::4],
               s=15, alpha=0.8, edgecolors="none")
    ax.axvspan(90, 110, alpha=0.15, color="#2ecc71", label="ROUTE (func words)")
    ax.axvspan(110, 130, alpha=0.15, color="#3498db", label="CONTENT")
    ax.axvspan(130, 150, alpha=0.15, color="#f39c12", label="DETAIL (rare)")
    ax.set_yscale("log")
    ax.set_xlabel("Rung r")
    ax.set_ylabel("Value phi^(-r*20/255)")
    ax.set_title("phi-Rung Atlas (256 rungs)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.suptitle("phi-Zipf: The Golden Ratio in Word Frequency",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "17_phi_zipf.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def main():
    print("Section 17: phi-Zipf and the Zipf Connection\n")
    print("=" * 60)

    # 1. The duality
    print("\n1. phi-Zipf Duality")
    print("-" * 40)
    print(f"  phi^(-ln f) = f^(-ln phi) = f^(-{LN_PHI:.4f})")
    print(f"  ln(phi) = {LN_PHI:.10f}")
    demonstrate_duality()

    # 2. Embedding demo
    print("\n2. phi-Zipf + Resonant Embeddings")
    print("-" * 40)
    for tid in [1, 42, 100, 1000]:
        emb = phi_zipf_embed(tid, 8)
        mags = np.array([np.linalg.norm(emb[2*h:2*h+2]) for h in range(8)])
        print(f"  token={tid:>4}: norm={np.linalg.norm(emb):.4f}, "
              f"mags={np.round(mags[:4], 3)}...")

    # Same token = same embedding
    e1 = phi_zipf_embed(42, 8)
    e2 = phi_zipf_embed(42, 8)
    print(f"  Deterministic: max diff = {np.abs(e1-e2).max():.1e}")

    # 3. phi-Zipf vs Standard Zipf
    print("\n3. phi-Zipf Frequency Distribution")
    print("-" * 40)
    ranks_test = [1, 10, 100, 1000, 10000]
    for r in ranks_test:
        phiz = phi_zipf_mag(r)
        stdz = r ** (-1.0)
        print(f"  rank={r:>5}: phi-Zipf={phiz:.6f}, standard Zipf={stdz:.6f}, "
              f"ratio={phiz/stdz:.3f}")

    # 4. phi-Rung atlas
    print("\n4. phi-Rung Atlas")
    print("-" * 40)
    mags_r = phi_rung_magnitudes(16, 111)
    for band_name, lo, hi in [("ROUTE", 90, 110), ("CONTENT", 110, 130),
                                ("DETAIL", 130, 150)]:
        in_band = sum(1 for m in mags_r
                      if PHI ** (-hi * 20/255) <= m <= PHI ** (-lo * 20/255))
        print(f"  {band_name:>10} (rungs {lo}-{hi}): {in_band}/{len(mags_r)} dims")

    # 5. Five appearances
    print("\n5. Five Appearances of ln(phi)")
    print("-" * 40)
    apps = [("Gate threshold", LN_PHI, "Phase space division"),
            ("phi-Zipf exponent", LN_PHI, "Word frequency power law"),
            ("Embedding decay", LN_PHI, "Within-vector structure"),
            ("Pareto split", 1 - 1/PHI, "80/20 information distribution"),
            ("Zeta quantization", LN_PHI, "Riemann zero phase boundaries")]
    for name, val, desc in apps:
        print(f"  {name:<20}: {val:.6f} — {desc}")

    # Figures
    generate_figure()

    print(f"\n{'=' * 60}")
    print("Done. Figure generated.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
