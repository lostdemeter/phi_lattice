#!/usr/bin/env python3
"""Section 01: φ-Lattice Foundation — Demonstration and Figure Generation.

A self-contained implementation of the φ-lattice:
  - encode/decide with midpoint correction
  - lattice-native multiplication (XOR + ADD)
  - shift-and-sum accumulation
  - quantization error analysis
  - generates Figure 1.1: φ-lattice structure

Usage:
    python3 code/01_lattice_demo.py
"""

import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ─── Constants ──────────────────────────────────────────────────────────

PHI = (1 + math.sqrt(5)) / 2       # Golden ratio
LN_PHI = math.log(PHI)              # ln(φ) ≈ 0.48121182505960347
K = 256                             # Default lattice resolution

# Ensure output directory
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# ─── Core φ-Lattice Operations ─────────────────────────────────────────

def phi_encode(x: np.ndarray, k: int = K):
    """Encode float array → (signs, exponents) on the φ-lattice.

    Uses arithmetic convention: signs are +1 or -1.
    Midpoint correction ensures correct nearest-lattice-point selection
    for geometric spacing (the arithmetic midpoint is NOT at half-exponent).
    """
    x = np.asarray(x, dtype=np.float64)
    signs = np.where(x >= 0, 1, -1).astype(np.int8)
    mag = np.abs(x) + 1e-300
    exps = np.round(k * np.log(mag) / LN_PHI).astype(np.int64)

    # Midpoint correction
    mag_clip = np.maximum(mag, 1e-300)
    ratio = mag_clip * PHI ** (-exps.astype(np.float64) / k)
    phi_1overk = PHI ** (1.0 / k)
    hi_thresh = (1.0 + phi_1overk) / 2.0
    lo_thresh = (1.0 + 1.0 / phi_1overk) / 2.0
    exps = np.where(ratio > hi_thresh, exps + 1,
                    np.where(ratio < lo_thresh, exps - 1, exps)).astype(np.int32)
    return signs, exps


def phi_decode(signs: np.ndarray, exps: np.ndarray, k: int = K):
    """Decode (signs, exponents) → float64."""
    return signs.astype(np.float64) * PHI ** (exps.astype(np.float64) / k)


def phi_mul(signs_a, exps_a, signs_b, exps_b):
    """Multiply two φ-lattice values.

    Returns (signs, exps) — exact, zero error.
    """
    s = (signs_a * signs_b).astype(np.int8)
    e = (exps_a.astype(np.int32) + exps_b.astype(np.int32)).astype(np.int32)
    return s, e


def phi_accumulate(signs, exps, k=K):
    """Accumulate (sum) φ-lattice values along last axis.

    Uses shift-and-sum in float64 to avoid underflow.
    This is the "approximate" operation — introduces ~0.09% error.
    """
    signs = np.asarray(signs, dtype=np.float64)
    exps = np.asarray(exps, dtype=np.float64)
    e_min = exps.min(axis=-1, keepdims=True)
    shifted = exps - e_min
    vals = signs * PHI ** (shifted / k)
    total = vals.sum(axis=-1)
    # Re-apply shift: total * φ^(e_min/k)
    result = total * PHI ** (np.squeeze(e_min, axis=-1) / k)
    s_out, e_out = phi_encode(result, k=k)
    return s_out, e_out


# ─── Single-Precision Helper (no midpoint correction) ───────────────────

def phi_encode_simple(x: np.ndarray, k: int = K):
    """Encode without midpoint correction — for comparison."""
    x = np.asarray(x, dtype=np.float64)
    signs = np.where(x >= 0, 1, -1).astype(np.int8)
    mag = np.abs(x) + 1e-300
    exps = np.round(k * np.log(mag) / LN_PHI).astype(np.int32)
    return signs, exps


# ─── Validation Functions ───────────────────────────────────────────────

def correlation(a, b):
    """Pearson correlation between two flat arrays."""
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    return np.corrcoef(a, b)[0, 1]


def max_relative_error(original, reconstructed):
    """Maximum relative error."""
    original = np.asarray(original, dtype=np.float64).ravel()
    reconstructed = np.asarray(reconstructed, dtype=np.float64).ravel()
    mask = np.abs(original) > 1e-30
    errors = np.abs(original[mask] - reconstructed[mask]) / np.abs(original[mask])
    return errors.max()


# ─── Tests ──────────────────────────────────────────────────────────────

def run_tests():
    """Verify all φ-lattice operations and print metrics."""
    print("=" * 60)
    print("φ-Lattice Foundation — Validation Tests")
    print("=" * 60)

    rng = np.random.RandomState(42)
    x_vals = np.exp(rng.uniform(-20, 20, 1000)) * rng.choice([-1, 1], 1000)

    # Test 1: Round-trip encode/decode
    signs, exps = phi_encode(x_vals)
    decoded = phi_decode(signs, exps)
    corr = correlation(x_vals, decoded)
    max_err = max_relative_error(x_vals, decoded)
    print(f"\nTest 1 — Encode/Decode Round-Trip:")
    print(f"  Correlation:       {corr:.8f}")
    print(f"  Max relative error: {max_err:.6f}  ({max_err*100:.4f}%)")
    assert corr > 0.9999, f"Correlation too low: {corr}"

    # Test 2: Multiplication accuracy
    a = rng.uniform(-100, 100, 500).astype(np.float64)
    b = rng.uniform(-100, 100, 500).astype(np.float64)
    sa, ea = phi_encode(a)
    sb, eb = phi_encode(b)
    sm, em = phi_mul(sa, ea, sb, eb)
    lattice_prod = phi_decode(sm, em)
    float_prod = a * b
    corr_mul = correlation(float_prod, lattice_prod)
    print(f"\nTest 2 — Lattice-Native Multiplication (XOR + ADD):")
    print(f"  Correlation:       {corr_mul:.8f}")
    assert corr_mul > 0.9999, f"Multiplication correlation too low: {corr_mul}"

    # Test 3: Accumulation
    x_batch = rng.uniform(-10, 10, (100, 32)).astype(np.float64)
    s, e = phi_encode(x_batch)
    sa, ea = phi_accumulate(s, e)
    decoded_sum = phi_decode(sa, ea)
    float_sum = x_batch.sum(axis=-1)
    corr_acc = correlation(float_sum, decoded_sum)
    print(f"\nTest 3 — Accumulation (Shift-and-Sum):")
    print(f"  Correlation:       {corr_acc:.8f}")
    assert corr_acc > 0.9999, f"Accumulation correlation too low: {corr_acc}"

    # Test 4: Lattice spacing
    print(f"\nTest 4 — Lattice Properties:")
    points_per_octave = K * math.log2(PHI)
    relative_spacing = PHI ** (1.0 / K) - 1.0
    print(f"  Resolution k:      {K}")
    print(f"  Points per octave: {points_per_octave:.1f}")
    print(f"  Relative spacing:  {relative_spacing:.6f}  ({relative_spacing*100:.4f}%)")

    # Test 5: Quantization error bound
    theoretical_bound = LN_PHI / (2 * K)
    print(f"\nTest 5 — Quantization Error Bound:")
    print(f"  Theoretical bound: {theoretical_bound:.6f}  ({theoretical_bound*100:.4f}%)")
    print(f"  Measured max:      {max_err:.6f}  ({max_err*100:.4f}%)")
    print(f"  Within bound?      {'YES' if max_err <= 1.01*theoretical_bound else 'NO'}")

    # Test 6: Midpoint correction matters
    s_simple, e_simple = phi_encode_simple(x_vals)
    decoded_simple = phi_decode(s_simple, e_simple)
    corr_simple = correlation(x_vals, decoded_simple)
    corr_corrected = correlation(x_vals, decoded)
    print(f"\nTest 6 — Midpoint Correction Impact:")
    print(f"  Without correction: {corr_simple:.8f}")
    print(f"  With correction:    {corr_corrected:.8f}")
    print(f"  Improvement:        {corr_corrected - corr_simple:.8f}")

    # Test 7: Sign convention (the XOR/AND distinction)
    print(f"\nTest 7 — Sign Convention:")
    # Using 1/-1 arithmetic convention: XOR behavior
    pairs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for sa, sb in pairs:
        result = sa * sb
        print(f"  {sa:2d} * {sb:2d} = {result:2d}   (expected: {1 if sa == sb else -1:2d})")

    print(f"\n{'=' * 60}")
    print("All tests passed.")
    print(f"{'=' * 60}")
    return True


# ─── Figure 1.1: φ-Lattice Structure ────────────────────────────────────

def generate_figure():
    """Generate three-panel figure showing φ-lattice structure."""
    print("\nGenerating Figure 1.1: φ-Lattice Structure...")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    rng = np.random.RandomState(42)

    # ── Panel 1: Exponential spacing of φ^(n/k) ──
    ax = axes[0]
    n_vals = np.arange(-1024, 1024, dtype=np.float64)
    # Sample every 32nd point for visual clarity
    step = 32
    n_sample = n_vals[::step]
    y_sample = PHI ** (n_sample / K)

    # Full range
    y_full = PHI ** (n_vals / K)
    ax.semilogy(n_vals / K, y_full, color="#2a2a2a", linewidth=0.6, alpha=0.5,
                label=f"φ^(n/{K})")
    ax.scatter(n_sample / K, y_sample, color="#d4a017", s=5, zorder=5,
               label=f"Lattice points (every {step}th)")

    # Highlight key powers
    for power in [-3, -2, -1, 0, 1, 2, 3]:
        idx = np.argmin(np.abs(n_vals - power * K))
        ax.axhline(y=PHI**power, color="#c0392b", linestyle=":", linewidth=0.8, alpha=0.7)
        ax.text(n_vals[0]/K, PHI**power * 1.05, f"φ^{power}", fontsize=8,
                color="#c0392b", va="bottom")

    ax.set_xlabel("Exponent / k")
    ax.set_ylabel("Value (log scale)")
    ax.set_title("Exponential Spacing")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

    # ── Panel 2: Quantization error distribution ──
    ax = axes[1]
    x_test = PHI ** rng.uniform(-16, 16, 10000) * rng.choice([-1, 1], 10000)
    s, e = phi_encode(x_test)
    decoded = phi_decode(s, e)
    rel_error = np.abs(x_test - decoded) / np.maximum(np.abs(x_test), 1e-30)

    ax.hist(rel_error * 100, bins=80, color="#2e86c1", edgecolor="white",
            alpha=0.85, linewidth=0.3)
    bound = LN_PHI / (2 * K) * 100
    ax.axvline(x=bound, color="#c0392b", linestyle="--", linewidth=1.5,
               label=f"Theoretical bound: {bound:.3f}%")
    ax.set_xlabel("Relative Error (%)")
    ax.set_ylabel("Count")
    ax.set_title("Quantization Error Distribution")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # ── Panel 3: Points per octave ──
    ax = axes[2]
    # Count lattice points in each octave
    octaves = np.arange(-16, 17)
    counts = []
    for o in octaves:
        lower = PHI ** (o - 0.5)
        upper = PHI ** (o + 0.5)
        count = K * math.log(upper / lower) / LN_PHI
        counts.append(count)

    bars = ax.bar(octaves, counts, color="#27ae60", edgecolor="white",
                  linewidth=0.3, alpha=0.85)
    ax.axhline(y=K * math.log2(PHI), color="#c0392b", linestyle="--",
               linewidth=1.5,
               label=f"k·log₂(φ) = {K * math.log2(PHI):.1f} pts/octave")
    ax.set_xlabel("Octave (power of φ)")
    ax.set_ylabel("Lattice Points")
    ax.set_title("Lattice Point Density per Octave")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout(pad=2.0)
    out_path = FIGURES_DIR / "01_phi_lattice_structure.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")
    return out_path


# ─── Figure 1.2: Self-Similarity ────────────────────────────────────────

def generate_self_similarity_figure():
    """Figure showing φ self-similarity: φ = 1 + 1/φ geometrically."""
    print("\nGenerating Figure 1.2: Self-Similarity...")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # ── Panel 1: φ = 1 + 1/φ geometric interpretation ──
    ax = axes[0]
    # Draw a golden rectangle
    rect = plt.Rectangle((0, 0), 1, 1/PHI, fill=False, edgecolor="#2c3e50",
                         linewidth=2, label=f"1 × 1/φ")
    ax.add_patch(rect)

    # The "1" part
    square = plt.Rectangle((0, 0), 1/PHI, 1/PHI, fill=True,
                           facecolor="#3498db", alpha=0.5, edgecolor="#2980b9",
                           linewidth=1.5, label="1/φ × 1/φ")
    ax.add_patch(square)

    # The "1/φ" part
    rect_small = plt.Rectangle((1/PHI, 0), 1 - 1/PHI, 1/PHI, fill=True,
                               facecolor="#e74c3c", alpha=0.5, edgecolor="#c0392b",
                               linewidth=1.5, label="1/φ² × 1/φ")
    ax.add_patch(rect_small)

    ax.set_xlim(-0.05, 1.1)
    ax.set_ylim(-0.05, 0.75)
    ax.set_aspect("equal")
    ax.set_title("φ = 1 + 1/φ\nφ × 1/φ Rectangle")
    ax.legend(fontsize=8, loc="upper right")
    ax.text(0.5/PHI, 0.5/PHI, "1/φ", ha="center", va="center", fontsize=10,
            fontweight="bold", color="white")
    ax.text(1/PHI + (1-1/PHI)/2, 0.5/PHI, "1/φ²", ha="center", va="center",
            fontsize=8, fontweight="bold", color="white")

    # ── Panel 2: Fibonacci spiral approximating φ ──
    ax = axes[1]
    fib = [1, 1]
    for _ in range(8):
        fib.append(fib[-1] + fib[-2])
    # fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    n_sq = 8  # use fib[0..7]

    # Tile squares: square 0 at the origin, then attach each new square
    # to the bounding box cycling right → down → left → up.
    # All coordinates are exact integers (sums of Fibonacci numbers).
    squares = [(0, 0, fib[0])]  # (xmin, ymin, size)
    xmin, ymin, xmax, ymax = 0, 0, 1, 1
    for i in range(1, n_sq):
        s = fib[i]
        d = (i - 1) % 4  # 0=right, 1=down, 2=left, 3=up
        if d == 0:
            sq = (xmax, ymax - s, s)
            xmax += s
        elif d == 1:
            sq = (xmin, ymin - s, s)
            ymin -= s
        elif d == 2:
            sq = (xmin - s, ymin, s)
            xmin -= s
        else:
            sq = (xmax - s, ymax, s)
            ymax += s
        squares.append(sq)

    def corner(sq, idx):
        # 0=BL, 1=BR, 2=TR, 3=TL
        x0, y0, s = sq
        return [(x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)][idx]

    def find_corner(sq, pt):
        for idx in range(4):
            if corner(sq, idx) == pt:
                return idx
        raise AssertionError(f"{pt} is not a corner of {sq}")

    # Draw the spiral: in each square, the arc joins the entry corner to
    # the diagonally opposite exit corner. The center is the corner whose
    # radius at the entry point is perpendicular to the travel direction,
    # which guarantees tangent-continuous joints between squares.
    entry = (0, 0)          # spiral starts at bottom-left of square 0...
    entry_idx = 0           # ...heading up
    t_in = (0, 1)           # incoming travel direction (axis-aligned unit)
    for i, sq in enumerate(squares):
        x0, y0, s = sq
        assert corner(sq, entry_idx) == entry
        exit_idx = entry_idx ^ 2            # diagonally opposite corner
        X = corner(sq, exit_idx)
        cands = [c for c in range(4) if c not in (entry_idx, exit_idx)]
        chosen = None
        for c in cands:
            C = corner(sq, c)
            r = (entry[0] - C[0], entry[1] - C[1])
            for sgn, rot in ((1, (-r[1], r[0])), (-1, (r[1], -r[0]))):
                if (rot[0] // s, rot[1] // s) == t_in:
                    chosen = (C, sgn)
                    break
            if chosen:
                break
        assert chosen, f"no smooth center for square {i}"
        C, sgn = chosen

        ax.add_patch(plt.Rectangle((x0, y0), s, s, fill=False,
                                   edgecolor="#8e44ad", linewidth=0.8, alpha=0.7))
        th_e = math.degrees(math.atan2(entry[1] - C[1], entry[0] - C[0]))
        th_x = math.degrees(math.atan2(X[1] - C[1], X[0] - C[0]))
        if sgn > 0:   # CCW sweep
            while th_x <= th_e:
                th_x += 360.0
            t1, t2 = th_e, th_x
        else:         # CW sweep
            while th_e <= th_x:
                th_e += 360.0
            t1, t2 = th_x, th_e
        ax.add_patch(plt.matplotlib.patches.Arc(
            C, 2 * s, 2 * s, angle=0, theta1=t1, theta2=t2,
            color="#d4a017", linewidth=1.4))

        # Outgoing tangent at X becomes the next square's incoming direction.
        rx, ry = X[0] - C[0], X[1] - C[1]
        t_in = ((-ry // s, rx // s) if sgn > 0 else ((ry // s, -rx // s)))
        if i + 1 < n_sq:
            entry = X
            entry_idx = find_corner(squares[i + 1], entry)

    pad = 2.0
    ax.set_xlim(xmin - pad, xmax + pad)
    ax.set_ylim(ymin - pad, ymax + pad)
    ax.set_aspect("equal")
    ax.set_title("Fibonacci Spiral → φ")
    ax.grid(True, alpha=0.2)

    # ── Panel 3: φ^n self-similar scaling ──
    ax = axes[2]
    ns = np.arange(-8, 9, dtype=np.float64)
    vals = PHI ** ns
    colors = plt.cm.viridis(np.linspace(0.15, 0.95, len(ns)))

    for n, v, c in zip(ns, vals, colors):
        ax.barh(n, v, 0.6, color=c, edgecolor="white", linewidth=0.3)
        ax.text(v + 0.2, n, f"φ^{int(n)}={v:.1f}", va="center", fontsize=7)

    ax.set_xscale("log")
    ax.set_xlabel("Value (log scale)")
    ax.set_ylabel("n")
    ax.set_title("φ^n Self-Similar Scaling")
    ax.grid(True, alpha=0.3, axis="x")

    plt.tight_layout(pad=2.0)
    out_path = FIGURES_DIR / "01_phi_self_similarity.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")
    return out_path


# ─── Main ───────────────────────────────────────────────────────────────

def main():
    print("φ-Lattice Foundation Demo\n")
    run_tests()
    generate_figure()
    generate_self_similarity_figure()
    print("\nDone. All figures generated successfully.")


if __name__ == "__main__":
    main()
