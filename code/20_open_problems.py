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
    from matplotlib.patches import FancyBboxPatch

    groups = [
        ("Hard", "#e74c3c", [
            ("Lattice-Native\nRMSNorm", "60% of remaining error"),
            ("Lattice-Native\nTraining", "No φ-gradient descent yet"),
            ("Unified Human +\nLearned Structure", "Bridging the 3 universals"),
        ]),
        ("Medium", "#e67e22", [
            ("Optimal\nResolution k", "k=896 cancellation dip"),
            ("Template →\nTetrix Dissolution", "Geometric selection exists"),
            ("Chirality →\nT⁴ Topology", "Isoclinic rotation catalog"),
            ("k > 256:\nHigher Resolution", "k=2048 works, needs speed"),
        ]),
        ("Easier", "#27ae60", [
            ("Causal Zipf:\nln(φ) Explanation", "Testable prediction"),
            ("Multi-Model\nφ-Interoperability", "φ-score = 1.0 on 4 models"),
            ("Hardware\nImplementation", "FPGA → ASIC path"),
        ]),
        ("Speculative", "#8e44ad", [
            ("Continuous\nPascal Dimension", "d = 2.5+ ?"),
            ("Feigenbaum\nConnection", "φ≈4.854 vs δ=4.669"),
        ]),
    ]

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")

    n_cols = len(groups)
    margin, gap = 0.3, 0.3
    col_w = (12 - 2 * margin - (n_cols - 1) * gap) / n_cols
    card_h, card_gap = 1.55, 0.22
    top = 8.55  # top edge of first card row

    for c, (difficulty, color, items) in enumerate(groups):
        x0 = margin + c * (col_w + gap)

        # Column header band
        ax.add_patch(FancyBboxPatch(
            (x0, 9.0), col_w, 0.7, boxstyle="round,pad=0.02",
            facecolor=color, edgecolor=color, alpha=0.9))
        ax.text(x0 + col_w / 2, 9.35,
                f"{difficulty} ({len(items)})",
                ha="center", va="center", fontsize=11,
                fontweight="bold", color="white")

        # Cards, stacked from the top
        for i, (title, note) in enumerate(items):
            y1 = top - i * (card_h + card_gap)
            y0 = y1 - card_h
            ax.add_patch(FancyBboxPatch(
                (x0, y0), col_w, card_h, boxstyle="round,pad=0.02",
                facecolor="white", edgecolor=color, linewidth=1.8))
            ax.text(x0 + col_w / 2, y0 + card_h - 0.42, title,
                    ha="center", va="top", fontsize=9,
                    fontweight="bold", color=color, linespacing=1.3)
            ax.text(x0 + col_w / 2, y0 + 0.18, note,
                    ha="center", va="bottom", fontsize=7.5, color="gray")

    ax.text(6, 0.35, "Grouped by expected difficulty — see Section 20 for details.",
            ha="center", va="center", fontsize=8, color="gray", style="italic")

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
