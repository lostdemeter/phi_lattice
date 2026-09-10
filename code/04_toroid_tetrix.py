#!/usr/bin/env python3
"""Section 04: The 16D Toroid-Tetrix -- REAL language data from Austen.

Loads the actual Austen tetrix (7,243 words, 2,217 cells) built from
Pride and Prejudice. Computes gate statistics, cell transitions, and
fractal properties from real language data.
"""

import json
import math
import os
import pickle
from pathlib import Path
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

PHI = (1 + math.sqrt(5)) / 2
LN_PHI = math.log(PHI)
TWOPI = 2.0 * math.pi
GAMMA = 14.134725141734693

WORKSPACE = Path(__file__).resolve().parent.parent.parent.parent / "rlm_springboard"
if not WORKSPACE.exists():
    WORKSPACE = Path(os.environ.get("RLM_WORKSPACE", Path.home() / "Documents" / "OpenCode" / "rlm_springboard"))
TETRIX_PKL = WORKSPACE / "phase_coherence/language_tetrix/austen_tetrix.pkl"


def load_austen_tetrix():
    if not TETRIX_PKL.exists():
        return None
    return pickle.load(open(TETRIX_PKL, "rb"))


def compute_gate_statistics(tetrix):
    """Compute gate distribution from real cell transitions.

    Cell keys are tuples (POS_str, cluster_int, topic_int).
    We compute a deterministic numerical index from the tuple components:
      index = pos_idx * 5000 + cluster * 50 + topic
    using the mixed-radix encoding (201, 8, 3) scaled to fit."""
    cell_transitions = tetrix["cell_transitions"]

    POS_MAP = {"NOUN": 0, "VERB": 1, "ADJ": 2, "ADV": 3,
               "PREP": 4, "CONJ": 5, "PRON": 6, "DET": 7, "OTHER": 8}

    def cell_index(cell_key):
        if isinstance(cell_key, tuple) and len(cell_key) >= 3:
            pos = POS_MAP.get(str(cell_key[0]), 8)
            cluster = int(cell_key[1]) if cell_key[1] is not None else 0
            topic = int(cell_key[2]) if cell_key[2] is not None else 0
            return pos * 5000 + cluster * 50 + topic
        return hash(str(cell_key)) & 0x7FFFFFFF  # fallback for non-tuple

    gate_counts = {+1: 0, +2: 0, -2: 0, -1: 0}
    total_transitions = 0

    for cell_a, transitions in cell_transitions.items():
        ka = cell_index(cell_a)
        for cell_b_raw, count in transitions.items():
            kb = cell_index(cell_b_raw)
            c = int(count)
            c = int(count)
            dtheta = (GAMMA * (kb - ka)) % TWOPI
            if dtheta > math.pi:
                dtheta -= TWOPI
            if dtheta > LN_PHI:
                gate_counts[+1] += c
            elif dtheta > 0:
                gate_counts[+2] += c
            elif dtheta > -LN_PHI:
                gate_counts[-2] += c
            else:
                gate_counts[-1] += c
            total_transitions += c

    return gate_counts, total_transitions


def compute_fractal_dimension(tetrix):
    """Estimate fractal dimension of cell space via box-counting."""
    word_cell = tetrix["word_cell"]
    word_cluster = tetrix["word_cluster"]

    # Cell keys are tuples (POS, cluster, topic)
    pts = []
    for word, cell_key in word_cell.items():
        cluster = word_cluster.get(word, 0)
        if isinstance(cell_key, tuple) and len(cell_key) >= 3:
            pos_str = cell_key[0]
            pos_idx = {"NOUN": 0, "VERB": 1, "ADJ": 2, "ADV": 3,
                       "PREP": 4, "CONJ": 5, "PRON": 6, "DET": 7, "OTHER": 8}
            pos = pos_idx.get(str(pos_str), 8)
            sem = int(cell_key[1]) if cell_key[1] is not None else 0
            top = int(cell_key[2]) if cell_key[2] is not None else 0
            pts.append([pos / 9, sem / 50, top / 20])
        else:
            pts.append([cluster / 30, hash(str(cell_key)) % 25 / 25, 0.5])
    pts = np.array(pts)

    resolutions = [2, 4, 8, 16, 32]
    dims = []
    for r in resolutions:
        grid = np.floor(pts * r).astype(np.int32)
        unique = set(tuple(g) for g in grid)
        dims.append(len(unique))

    # Log-log fit
    log_r = np.log(resolutions)
    log_n = np.log(dims)
    slope, _ = np.polyfit(log_r, log_n, 1)

    return float(slope), dims, resolutions


def compute_cell_fill_rate(tetrix):
    """Compute cell occupancy statistics."""
    cell_words = tetrix["cell_words"]
    occupied = len(cell_words)
    word_cell = tetrix["word_cell"]
    n_words = len(word_cell)

    # Words per cell distribution
    words_per_cell = [len(words) for words in cell_words.values()]

    return {
        "n_cells": occupied,
        "n_words": n_words,
        "fill_rate": occupied / max(19924, 1),  # Theoretical max 201×25×4
        "avg_words_per_cell": np.mean(words_per_cell) if words_per_cell else 0,
        "cells_with_1_word": sum(1 for w in words_per_cell if w == 1),
    }


def generate_figures(tetrix, gate_counts, total_trans, frac_dim, fill):
    print("\nGenerating figures...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Panel 1: 4-state gate distribution from real data
    ax = axes[0, 0]
    names = ["+1 EXPAND", "+2 PRESERVE+", "-2 PRESERVE-", "-1 CONTRACT"]
    vals = [gate_counts.get(s, 0) / max(total_trans, 1) * 100 for s in [+1, +2, -2, -1]]
    theo = [(math.pi-LN_PHI)/TWOPI*100, LN_PHI/TWOPI*100,
            LN_PHI/TWOPI*100, (math.pi-LN_PHI)/TWOPI*100]
    colors = ["#27ae60", "#2980b9", "#e67e22", "#c0392b"]
    ax.bar(names, vals, color=colors, edgecolor="white", linewidth=0.3)
    for i, t in enumerate(theo):
        ax.axhline(y=t, color=colors[i], linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_ylabel("Percentage")
    ax.set_title(f"Gate Distribution (Austen, {total_trans:,} transitions)")
    ax.grid(True, alpha=0.3, axis="y")

    # Panel 2: Cell fill statistics
    ax = axes[0, 1]
    if fill:
        cell_words = tetrix["cell_words"]
        words_per_cell = [len(w) for w in cell_words.values()]
        ax.hist(words_per_cell, bins=30, color="#2e86c1", edgecolor="white",
                linewidth=0.3, alpha=0.85)
        ax.set_xlabel("Words per Cell")
        ax.set_ylabel("Number of Cells")
        ax.set_title(f"Cell Occupancy ({fill['n_cells']:,} cells, "
                     f"{fill['n_words']:,} words)")
        ax.axvline(x=fill["avg_words_per_cell"], color="#e74c3c",
                   linestyle="--", linewidth=1, label=f"Mean: {fill['avg_words_per_cell']:.1f}")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    # Panel 3: Box-counting dimension
    ax = axes[1, 0]
    if frac_dim:
        _, dims_vals, resolutions = compute_fractal_dimension(tetrix)
        ax.plot(resolutions, dims_vals, "o-", color="#2e86c1", linewidth=2, markersize=8,
                markeredgecolor="white", markeredgewidth=0.5)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("Resolution")
        ax.set_ylabel("Occupied Boxes")
        ax.set_title(f"Box-Counting Dimension: {frac_dim:.3f}")
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, "No fractal data", ha="center", transform=ax.transAxes)

    # Panel 4: Summary
    ax = axes[1, 1]
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    lines = [
        "AUSTEN TETRIX (Pride & Prejudice)",
        "=================================",
        f"Vocabulary: {len(tetrix['vocab_words']):,}",
        f"Unique cells: {len(tetrix['cell_words']):,}",
        f"Cell transitions tracked: {len(tetrix['cell_transitions']):,}",
        f"",
        f"Gate threshold: +/- ln(phi) = +/- {LN_PHI:.4f}",
        f"Gate distribution:",
    ]
    for s in [+1, +2, -2, -1]:
        pct = gate_counts.get(s, 0) / max(total_trans, 1) * 100
        names_g = {+1: "EXPAND", +2: "PRESERVE+", -2: "PRESERVE-", -1: "CONTRACT"}
        lines.append(f"  {names_g[s]:>12}: {pct:5.1f}%")
    lines += [
        f"",
        f"Fractal dim: {frac_dim:.3f}" if frac_dim else "",
        f"Words/cell: {fill['avg_words_per_cell']:.1f}" if fill else "",
    ]
    for i, line in enumerate(lines):
        y = 9.5 - i * 0.55
        ax.text(0.5, y, line, fontsize=8,
                fontweight="bold" if "AUSTEN" in line else "normal")

    plt.suptitle("16D Toroid-Tetrix: Real Language Data (Pride & Prejudice)",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "04_real_tetrix.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def main():
    print("Section 04: The 16D Toroid-Tetrix (REAL DATA: Austen)\n")
    print("=" * 60)

    tetrix = load_austen_tetrix()

    if tetrix is None:
        print("\n  Tetrix data not found.")
        print(f"  Expected: {TETRIX_PKL}")
        generate_figures(None, {}, 0, None, None)
        return

    n_vocab = len(tetrix["vocab_words"])
    n_cells = len(tetrix["cell_words"])
    n_trans = len(tetrix["cell_transitions"])

    print(f"\n  Austen Tetrix (Pride & Prejudice):")
    print(f"    Vocabulary:      {n_vocab:,} words")
    print(f"    Unique cells:    {n_cells:,}")
    print(f"    Cell transitions: {n_trans:,}")

    # Gate statistics
    print(f"\n  Gate Distribution (from real cell transitions):")
    gate_counts, total_trans = compute_gate_statistics(tetrix)
    print(f"    Total transitions: {total_trans:,}")
    for s in [+1, +2, -2, -1]:
        names = {+1: "+1 EXPAND", +2: "+2 PRESERVE+",
                 -2: "-2 PRESERVE-", -1: "-1 CONTRACT"}
        emp = gate_counts[s] / total_trans * 100
        theo = ((math.pi-LN_PHI)/TWOPI*100 if s in [+1, -1] else LN_PHI/TWOPI*100)
        print(f"      {names[s]:>20}: empirical={emp:.1f}%, theoretical={theo:.1f}%")

    # Fractal dimension
    print(f"\n  Fractal Properties:")
    frac_dim, _, _ = compute_fractal_dimension(tetrix)
    print(f"    Box-counting dimension: {frac_dim:.3f}")

    # Cell fill
    fill = compute_cell_fill_rate(tetrix)
    print(f"\n  Cell Occupancy:")
    print(f"    Occupied cells:     {fill['n_cells']:,}")
    print(f"    Avg words per cell: {fill['avg_words_per_cell']:.1f}")
    print(f"    Cells with 1 word:  {fill['cells_with_1_word']:,}")

    # Figures
    generate_figures(tetrix, gate_counts, total_trans, frac_dim, fill)

    print(f"\n{'=' * 60}")
    print("Done. Figure generated.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
