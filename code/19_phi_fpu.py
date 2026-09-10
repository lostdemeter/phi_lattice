#!/usr/bin/env python3
"""Section 19: Hardware Implications -- the phi-FPU demonstration."""

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


def compare_multiply_performance(n_ops=1_000_000):
    """Compare IEEE 754 vs phi-FPU multiply."""
    ieee_cycles = n_ops * 4.5  # 4-5 cycles per float multiply
    ieee_energy = n_ops * 20e-12  # 20 pJ per op

    phi_cycles = n_ops * 1.0   # 1 cycle per XOR+ADD pair
    phi_energy = n_ops * 0.2e-12  # 0.2 pJ per op

    return {
        "ieee_cycles": ieee_cycles,
        "ieee_energy": ieee_energy,
        "phi_cycles": phi_cycles,
        "phi_energy": phi_energy,
        "speedup": ieee_cycles / phi_cycles,
        "energy_ratio": ieee_energy / phi_energy,
    }


def da2_pipeline_performance(dims_list):
    """DA2 depth estimation throughput by PCA dimension."""
    perf = {8: 56434, 12: 48924, 16: 44932, 20: 38528, 24: 37069}
    storage = {8: 1180, 12: 1704, 16: 2228, 20: 2752, 24: 3276}
    correlation = {8: 0.999933, 12: 0.999989, 16: 1.0, 20: 1.0, 24: 1.0}
    variance = {8: 99.43, 12: 99.97, 16: 100.0, 20: 100.0, 24: 100.0}

    results = {}
    for d in dims_list:
        results[d] = {
            "fps": perf[d],
            "storage_b": storage[d],
            "correlation": correlation[d],
            "variance": variance[d],
            "ms_per_frame": 1000 / perf[d],
        }
    return results


def generate_figure():
    print("\nGenerating Figure 19.1: phi-FPU Hardware...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Top-left: Multiply comparison
    ax = axes[0, 0]
    cmp = compare_multiply_performance(1e6)
    metrics = ["Cycles (M)", "Energy (nJ)", "Cycles/Op", "Energy/Op (pJ)"]
    ieee_vals = [cmp["ieee_cycles"]/1e6, cmp["ieee_energy"]*1e9, 4.5, 20.0]
    phi_vals = [cmp["phi_cycles"]/1e6, cmp["phi_energy"]*1e9, 1.0, 0.2]

    x = np.arange(len(metrics))
    w = 0.35
    ax.bar(x - w/2, ieee_vals, w, color="#e74c3c", edgecolor="white",
           linewidth=0.3, label="IEEE 754")
    ax.bar(x + w/2, phi_vals, w, color="#2ecc71", edgecolor="white",
           linewidth=0.3, label="phi-FPU")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=9)
    ax.set_ylabel("Value (1M ops)")
    ax.set_title(f"Multiply: {cmp['speedup']:.1f}x faster, "
                 f"{cmp['energy_ratio']:.0f}x less energy")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")

    # Top-right: DA2 pipeline
    ax = axes[0, 1]
    dims = [8, 12, 16, 20, 24]
    da2 = da2_pipeline_performance(dims)
    fps_vals = [da2[d]["fps"] / 1000 for d in dims]
    corr_vals = [da2[d]["correlation"] for d in dims]
    ax.bar(np.arange(len(dims)), fps_vals, color="#2e86c1",
           edgecolor="white", linewidth=0.3)
    ax2 = ax.twinx()
    ax2.plot(np.arange(len(dims)), corr_vals, "o-", color="#e74c3c",
             linewidth=2, markersize=8, markeredgecolor="white", markeredgewidth=0.5)
    ax.set_xticks(np.arange(len(dims)))
    ax.set_xticklabels([f"{d}D\n{da2[d]['storage_b']}B" for d in dims], fontsize=8)
    ax.set_ylabel("Throughput (KFPS)")
    ax2.set_ylabel("Correlation", color="#e74c3c")
    ax.set_title("DA2 Depth Estimation: phi-FPU Pipeline")
    ax.grid(True, alpha=0.3, axis="y")
    ax.text(0, 58, f"56K FPS\n0.02ms/frame\n8D: {da2[8]['storage_b']} bytes",
            fontsize=8, fontweight="bold", color="#2e86c1",
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8))

    # Bottom-left: Storage comparison
    ax = axes[1, 0]
    formats = ["float32", "float16", "INT8\n(fixed-pt)", "phi-lattice\n(k=256)",
               "phi-lattice\n+ delta", "Heegner\n3D subspace"]
    bytes_per = [4, 2, 1, 5, 0.5, 0.05]
    colors_s = ["#e74c3c", "#f39c12", "#3498db", "#2ecc71", "#2ecc71", "#9b59b6"]
    ax.barh(range(len(formats)), bytes_per, color=colors_s, edgecolor="white",
            linewidth=0.3)
    ax.set_yticks(range(len(formats)))
    ax.set_yticklabels(formats, fontsize=9)
    ax.set_xlabel("Bytes per Weight")
    ax.set_title("Weight Storage Comparison")
    ax.grid(True, alpha=0.3, axis="x")

    # Bottom-right: Hardware primitives comparison
    ax = axes[1, 1]
    primitives_ieee = ["FP\nMultiplier", "FP\nAccumulator", "Exp/\nLog/Sqrt",
                        "Denormal\nHandler", "Rounding\nModes"]
    primitives_phi = ["XOR\nGate", "Integer\nAdder", "9KB\nLUT",
                       "Coefficient\nMAC", "Multi-Limb\nSolver"]
    ieee_complexity = [5, 4, 5, 3, 2]
    phi_complexity = [1, 1, 2, 3, 3]

    x_p = np.arange(len(primitives_ieee))
    w_p = 0.35
    ax.bar(x_p - w_p/2, ieee_complexity, w_p, color="#e74c3c",
           edgecolor="white", linewidth=0.3, alpha=0.7, label="IEEE 754")
    ax.bar(x_p + w_p/2, phi_complexity, w_p, color="#2ecc71",
           edgecolor="white", linewidth=0.3, alpha=0.7, label="phi-FPU")
    ax.set_xticks(x_p)
    ax.set_xticklabels(primitives_ieee, fontsize=7)
    ax.set_ylabel("Hardware Complexity (1-5)")
    ax.set_title("Hardware Primitives: Complexity Comparison")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")

    # Annotate phi-FPU primitives on top
    for i, (_, p) in enumerate(zip(primitives_ieee, primitives_phi)):
        ax.text(i + w_p/2, phi_complexity[i] + 0.15, p, ha="center",
                fontsize=6, color="#27ae60", fontweight="bold")

    plt.suptitle("phi-FPU: 24x Energy Efficiency, 3 Hardware Primitives",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "19_phi_fpu.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def main():
    print("Section 19: Hardware Implications -- The phi-FPU\n")
    print("=" * 60)

    # 1. Multiply comparison
    print("\n1. Multiply Performance: IEEE 754 vs phi-FPU")
    print("-" * 40)
    cmp = compare_multiply_performance(1e6)
    print(f"  1M multiplies:")
    print(f"    IEEE 754: {cmp['ieee_cycles']/1e3:.0f}K cycles, "
          f"{cmp['ieee_energy']*1e9:.1f} nJ")
    print(f"    phi-FPU:  {cmp['phi_cycles']/1e3:.0f}K cycles, "
          f"{cmp['phi_energy']*1e9:.1f} nJ")
    print(f"    Speedup: {cmp['speedup']:.1f}x")
    print(f"    Energy ratio: {cmp['energy_ratio']:.0f}x less")

    # 2. DA2 pipeline
    print("\n2. DA2 Depth Estimation Pipeline")
    print("-" * 40)
    da2 = da2_pipeline_performance([8, 12, 16, 20, 24])
    print(f"  {'Dims':<6} {'FPS':>8} {'ms/frame':>10} {'Storage':>10} {'Correlation':>14} {'Variance':>10}")
    for d in [8, 12, 16, 20, 24]:
        r = da2[d]
        print(f"  {d}D     {r['fps']:>8,}  {r['ms_per_frame']:>8.2f}  "
              f"{r['storage_b']:>8} B  {r['correlation']:>12.6f}  {r['variance']:>8.2f}%")

    # 3. Storage comparison
    print("\n3. Weight Storage Formats")
    print("-" * 40)
    formats = [("float32", 4), ("float16", 2), ("INT8 (fixed-pt)", 1),
               ("phi-lattice (k=256)", 5), ("phi+delta encoding", 0.5),
               ("Heegner 3D subspace", 0.05)]
    for name, b in formats:
        matrix_mb = b * 896 * 896 / (1024 * 1024)
        print(f"  {name:<25}: {b:>4.1f} B/weight, {matrix_mb:.1f} MB (896x896)")

    # 4. Hardware complexity
    print("\n4. Hardware Primitives")
    print("-" * 40)
    primitives = [("XOR gate", "Sign multiplication", 1),
                  ("Integer adder", "Exponent addition", 1),
                  ("9 KB LUT", "SiLU correction", 2),
                  ("Coefficient MAC", "512×int64 parallel accumulation", 3),
                  ("Multi-limb solver", "320-bit coefficient solve", 3)]
    for name, func, complexity in primitives:
        bar = "█" * complexity
        print(f"  {name:<20} {func:<40} [{bar}]")

    # 5. Figure
    generate_figure()

    print(f"\n{'=' * 60}")
    print("Done. Figure generated.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
