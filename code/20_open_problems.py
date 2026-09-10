#!/usr/bin/env python3
"""Section 20: Open Problems -- summary visualization."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def generate_figure():
    print("\nGenerating Figure 20.1: Open Problems Landscape...")
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    problems = [
        (5, 9.2, "Lattice-Native\nRMSNorm", "#e74c3c", "Hard", "60% error"),
        (2, 8.0, "Optimal\nResolution k", "#f39c12", "Medium", "k=896 dip"),
        (8, 8.0, "Lattice-Native\nTraining", "#e74c3c", "Hard", "No gradients"),
        (5, 7.0, "Template →\nTetrix Dissolution", "#3498db", "Medium", "Geo. select"),
        (8, 6.5, "Unified Human +\nLearned Structure", "#e74c3c", "Hard", "3 universals"),
        (2, 5.5, "Chirality →\nT⁴ Topology", "#3498db", "Medium", "Isoclinic rot."),
        (5, 5.0, "Causal Zipf:\nln(φ) Explanation", "#2ecc71", "Easier", "Testable"),
        (8, 4.5, "Continuous\nPascal Dimension", "#9b59b6", "Speculative", "d=2.5+"),
        (2, 3.5, "Feigenbaum\nConnection", "#9b59b6", "Speculative", "δ≈4.669"),
        (5, 3.0, "k > 256:\nHigher Resolution", "#f39c12", "Medium", "k=2048 works"),
        (8, 2.0, "Multi-Model\nφ-Interoperability", "#2ecc71", "Easier", "φ-score=1.0"),
        (5, 1.0, "Hardware\nImplementation", "#2ecc71", "Easier", "FPGA→ASIC"),
    ]

    for x, y, label, color, difficulty, note in problems:
        rect = plt.Rectangle((x-1.5, y-0.4), 3, 0.8, fill=True,
                             facecolor=color, alpha=0.15,
                             edgecolor=color, linewidth=2,
                             linestyle="-" if difficulty == "Hard" else
                                       "--" if difficulty == "Medium" else ":")
        ax.add_patch(rect)
        ax.text(x, y, label, ha="center", va="center", fontsize=8,
                fontweight="bold", color=color)
        ax.text(x + 1.6, y, f"[{difficulty}]\n{note}", fontsize=6,
                color="gray", va="center")

    # Legend
    ax.text(0.5, 9.7, "Difficulty:", fontsize=9, fontweight="bold")
    for i, (label, color, ls) in enumerate([
        ("Hard", "#e74c3c", "-"), ("Medium", "#f39c12", "--"),
        ("Easier", "#2ecc71", ":"), ("Speculative", "#9b59b6", "-.")]):
        ax.plot([1.5 + i*1.8, 1.8 + i*1.8], [9.7, 9.7], color=color,
                linewidth=2, linestyle=ls)
        ax.text(1.9 + i*1.8, 9.7, label, fontsize=8, color=color, va="center")

    ax.set_title("Open Problems: The Research Frontier",
                 fontsize=15, fontweight="bold", y=1.02)

    plt.tight_layout()
    out = FIGURES_DIR / "20_open_problems.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def main():
    print("Section 20: Open Problems and Future Directions\n")
    print("=" * 60)
    print("""
The φ-lattice research program has mapped a complete theory:
  - φ-lattice representation (Section 01)
  - Integer arithmetic for all operations (Section 09)
  - Pure integer transformer running Qwen2-0.5B (Section 09)
  - Coherent text generation from XOR, ADD, LUT (Section 09)
  - 24x energy efficiency via φ-FPU (Section 19)

12 open problems define the frontier:
  1. Lattice-native RMSNorm (Hard — 60% of remaining error)
  2. Optimal resolution k (Medium — k=896 cancelation dip)
  3. Lattice-native training (Hard — no φ-gradient descent yet)
  4. Template dissolution into tetrix (Medium — geometric selection exists)
  5. Unified human + learned structure (Hard — 3 universals)
  6. Chirality → T⁴ topology (Medium — isoclinic rotation catalog)
  7. Causal Zipf: does ln(φ) explain Zipf's law? (Easier — testable)
  8. Continuous Pascal dimension (Speculative — d=2.5+)
  9. Feigenbaum connection (Speculative — φ≈4.854 vs δ=4.669)
  10. k > 256: higher resolution (Medium — k=2048 works, needs speed)
  11. Multi-model φ-interoperability (Easier — φ-score=1.0 on 4 models)
  12. Hardware implementation (Easier — FPGA→ASIC path clear)

The springboard has been built. The dive is next.
""")
    print("=" * 60)

    # Figure
    generate_figure()

    print(f"\n{'=' * 60}")
    print("Done. Figure generated.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
