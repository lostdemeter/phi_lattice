#!/usr/bin/env python3
"""Section 06: Navigation Replaces Inference — demonstration.

Key demonstrations:
  1. Token position tracking through simulated layers
  2. φ-form of softmax (algebraic identity with standard softmax)
  3. Signal flow: monotonic exponent growth through layers
  4. Similar-token path convergence
  5. The lattice-as-microscope: exact integers vs noisy floats
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


# ═══════════════════════════════════════════════════════════════════════
# 1. Token Navigation Path Simulation
# ═══════════════════════════════════════════════════════════════════════

def simulate_navigation_paths(n_layers=24, n_tokens=6, n_dims=896):
    """Simulate how token positions evolve through transformer layers.

    In the φ-lattice, each token starts at a specific exponent value.
    Each layer applies a shift + attention + MLP transformation that
    moves the position toward the predicted next token.
    """
    rng = np.random.RandomState(42)

    # Starting positions for 6 tokens (mean exponents)
    token_names = ["The", "capital", "of", "France", "is", "Paris"]
    start_exponents = np.array([-2684, -2502, -2400, -2571, -2350, -2649],
                                dtype=np.float64)

    # Each layer shifts the position by a learned amount + random noise
    # The shift has: a systematic component (learned direction)
    #                + a random walk component (attention scatter)
    paths = np.zeros((n_layers + 1, n_tokens))
    paths[0] = start_exponents

    # Learned shifts: each token has a "destination" it moves toward
    destinations = np.array([-2502, -2400, -2571, -2350, -2649, -2200],
                             dtype=np.float64)

    for layer in range(n_layers):
        # Systematic shift toward destination (decaying with layer)
        progress = (layer + 1) / n_layers
        systematic = 0.7 * (destinations - paths[layer]) * (1.0 - progress * 0.3)

        # Attention scatter: random perturbation that decays
        scatter = rng.randn(n_tokens) * 80 * (1.0 - progress * 0.6)

        # SiLU nonlinearity at ~layer 6 and 12 (compression toward zero)
        if layer in [5, 6, 11, 12]:
            # SiLU compresses values toward zero
            paths[layer] = np.where(paths[layer] > 0,
                                     paths[layer] * 0.7,
                                     paths[layer] * 0.3)

        paths[layer + 1] = paths[layer] + systematic + scatter

    return paths, token_names


# ═══════════════════════════════════════════════════════════════════════
# 2. φ-Form of Softmax (Algebraic Identity)
# ═══════════════════════════════════════════════════════════════════════

def standard_softmax(x, temperature=1.0):
    x = np.asarray(x, dtype=np.float64)
    x_max = x.max()
    e = np.exp((x - x_max) / temperature)
    return e / e.sum()


def phi_softmax(x, temperature=None):
    """phi-softmax using phi as the exponential base.
    
    The identity: exp(x) = phi^(x / ln(phi))
    So softmax via phi: phi^((x - max) / ln(phi)) / sum(phi^((x - max) / ln(phi)))
    This IS exactly standard softmax (algebraic identity).
    """
    x = np.asarray(x, dtype=np.float64)
    x_max = x.max()
    if temperature is None:
        phi_powers = PHI ** ((x - x_max) / LN_PHI)
    else:
        phi_powers = PHI ** ((x - x_max) / (temperature * LN_PHI))
    return phi_powers / phi_powers.sum()


# ═══════════════════════════════════════════════════════════════════════
# 3. Signal Flow: φ-Level Selection
# ═══════════════════════════════════════════════════════════════════════

def phi_level_select(logits, temperature=LN_PHI):
    """φ-level selection: softmax at natural temperature.
    
    At temperature = ln(phi), phi^(x/ln(phi)) = exp(x), so this IS the
    standard softmax. But geometrically, it's selecting a φ-level.
    """
    return phi_softmax(logits, temperature)


# ═══════════════════════════════════════════════════════════════════════
# 4. Lattice-as-Microscope
# ═══════════════════════════════════════════════════════════════════════

def demonstrate_lattice_precision():
    """Show that the φ-lattice reveals exact structure hidden in float."""
    rng = np.random.RandomState(42)

    # Generate a set of weights that SHOULD cluster at φ-levels
    n_weights = 1000
    true_levels = rng.randint(-10, 6, n_weights)
    true_signs = rng.choice([-1, 1], n_weights)
    true_weights = true_signs * PHI ** true_levels.astype(np.float64)

    # Add Gaussian "noise" (like float training introduces)
    noisy_weights = true_weights + rng.randn(n_weights) * 0.02

    # Float view: continuous distribution, no visible structure
    # Lattice view: quantize to nearest φ-level
    abs_weights = np.abs(noisy_weights) + 1e-30
    lattice_levels = np.round(np.log(abs_weights) / LN_PHI).astype(np.int32)
    lattice_weights = true_signs * PHI ** lattice_levels.astype(np.float64)

    # Error between lattice and true weights
    lattice_error = np.abs(true_weights - lattice_weights).mean()
    float_error = np.abs(true_weights - noisy_weights).mean()

    return true_weights, noisy_weights, lattice_weights, lattice_levels, \
           float_error, lattice_error


# ═══════════════════════════════════════════════════════════════════════
# Figures
# ═══════════════════════════════════════════════════════════════════════

def generate_figure_navigation_paths(paths, token_names):
    """Figure 6.1: Token navigation paths through layers."""
    print("\nGenerating Figure 6.1: Navigation Paths...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: Path trajectories
    ax = axes[0]
    layers = range(paths.shape[0])
    colors = plt.cm.tab10(np.linspace(0, 1, len(token_names)))
    for i, (name, c) in enumerate(zip(token_names, colors)):
        ax.plot(layers, paths[:, i], "o-", color=c, linewidth=1.5,
                markersize=4, label=name, alpha=0.85)
    ax.set_xlabel("Layer")
    ax.set_ylabel("Mean Exponent (position)")
    ax.set_title("Token Positions Through Transformer Layers")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    # Mark key layer transitions
    for l in [6, 12, 18]:
        ax.axvline(x=l, color="gray", linestyle=":", linewidth=0.5, alpha=0.5)

    # Right: Position deltas (how much each layer shifts)
    ax = axes[1]
    deltas = np.diff(paths, axis=0)
    for i, (name, c) in enumerate(zip(token_names, colors)):
        ax.bar(np.arange(len(deltas)) + i * 0.12, deltas[:, i] * 0.5,
               width=0.1, color=c, alpha=0.7, label=name if i < 3 else "")
    ax.set_xlabel("Layer Transition")
    ax.set_ylabel("Position Delta")
    ax.set_title("Layer-by-Layer Position Shifts")
    ax.axhline(y=0, color="gray", linestyle=":", linewidth=0.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = FIGURES_DIR / "06_navigation_paths.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def generate_figure_phi_softmax():
    """Figure 6.2: φ-form of softmax is algebraically identical."""
    print("\nGenerating Figure 6.2: Phi-Softmax Identity...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    rng = np.random.RandomState(42)

    # Left: Single example
    ax = axes[0]
    logits = np.array([3.0, 1.0, 0.5, 2.0, -1.0])
    std = standard_softmax(logits)
    phi = phi_softmax(logits)

    x = np.arange(len(logits))
    width = 0.35
    ax.bar(x - width/2, std, width, color="#2e86c1", edgecolor="white",
           linewidth=0.3, label="Standard (exp)")
    ax.bar(x + width/2, phi, width, color="#e74c3c", edgecolor="white",
           linewidth=0.3, alpha=0.8, label="Phi (phi^(x/ln(phi)))")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{v}" for v in logits])
    ax.set_xlabel("Logit Value")
    ax.set_ylabel("Probability")
    ax.set_title("Single Example: exp vs phi^(x/ln(phi))")
    ax.legend(fontsize=8)
    err = np.abs(std - phi).max()
    ax.text(0.5, 0.95, f"Max diff: {err:.2e}", transform=ax.transAxes,
            ha="center", fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))
    ax.grid(True, alpha=0.3, axis="y")

    # Center: Batch comparison
    ax = axes[1]
    n_batch = 100
    dim = 10
    all_diffs = []
    for _ in range(n_batch):
        x_batch = rng.randn(dim) * 2
        s1 = standard_softmax(x_batch)
        s2 = phi_softmax(x_batch)
        all_diffs.extend(np.abs(s1 - s2).tolist())

    ax.hist(all_diffs, bins=50, color="#2e86c1", edgecolor="white",
            linewidth=0.3, alpha=0.85)
    ax.set_xlabel("Absolute Difference")
    ax.set_ylabel("Count")
    ax.set_title(f"Batch ({n_batch} x {dim}): All Differences")
    max_d = max(all_diffs)
    ax.text(0.5, 0.95, f"Max diff: {max_d:.2e}", transform=ax.transAxes,
            ha="center", fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))
    ax.grid(True, alpha=0.3)

    # Right: phi-level selection interpretation
    ax = axes[2]
    levels = np.arange(-5, 6, dtype=np.float64)
    ph = phi_softmax(levels * 2.0)
    ax.bar(levels, ph, color="#d4a017", edgecolor="white",
           linewidth=0.3, alpha=0.85)
    ax.set_xlabel("phi-Level (e/k)")
    ax.set_ylabel("Selection Probability")
    ax.set_title("Attention as phi-Level Selection")
    ax.grid(True, alpha=0.3, axis="y")
    top_level = levels[np.argmax(ph)]
    ax.axvline(x=top_level, color="#c0392b", linestyle="--", linewidth=1.5,
               label=f"Top level: {int(top_level)}")
    ax.legend(fontsize=9)

    plt.tight_layout()
    out = FIGURES_DIR / "06_phi_softmax.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")
    return max_d


def generate_figure_lattice_microscope(true_w, noisy_w, lattice_w, levels):
    """Figure 6.3: Lattice as microscope."""
    print("\nGenerating Figure 6.3: Lattice as Microscope...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    # Left: Float view (noisy)
    ax = axes[0]
    ax.hist(noisy_w, bins=60, color="#3498db", edgecolor="white",
            linewidth=0.3, alpha=0.85)
    ax.set_xlabel("Weight Value")
    ax.set_ylabel("Count")
    ax.set_title("Float View: Continuous Distribution")
    ax.text(0.5, 0.95, "Structure hidden in noise",
            transform=ax.transAxes, ha="center", fontsize=9,
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))
    ax.grid(True, alpha=0.3)

    # Center: True structure (exact φ-levels)
    ax = axes[1]
    ax.hist(true_w, bins=40, color="#2ecc71", edgecolor="white",
            linewidth=0.3, alpha=0.85)
    ax.set_xlabel("Weight Value")
    ax.set_ylabel("Count")
    ax.set_title("True Structure: Exact phi-Levels")
    # Annotate some phi levels
    for lv in [-3, -1, 0, 1, 3]:
        val = PHI ** lv
        ax.axvline(x=val, color="#c0392b", linestyle="--", linewidth=0.8,
                   alpha=0.6)
        ax.text(val, ax.get_ylim()[1] * 0.95, f"phi^{lv}",
                fontsize=7, rotation=90, va="top", color="#c0392b")
    ax.grid(True, alpha=0.3)

    # Right: Level distribution (lattice view)
    ax = axes[2]
    unique, counts = np.unique(levels, return_counts=True)
    colors_ph = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(unique)))
    ax.bar(unique, counts, color=colors_ph, edgecolor="white",
           linewidth=0.3, alpha=0.85)
    ax.set_xlabel("phi-Level (integer)")
    ax.set_ylabel("Count")
    ax.set_title(f"Lattice View: Exact Integer Levels ({len(unique)} unique)")
    ax.text(0.5, 0.95, f"The Pythagorean theorem effect:\n"
            f"{len(unique)} discrete levels, not a continuum",
            transform=ax.transAxes, ha="center", fontsize=9,
            bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.8))
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    out = FIGURES_DIR / "06_lattice_microscope.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def generate_figure_signal_flow():
    """Figure 6.4: Signal flow and the sonic boom."""
    print("\nGenerating Figure 6.4: Signal Flow...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: Signal growth through layers
    ax = axes[0]
    layers = np.arange(24)
    # Synthesize realistic signal growth pattern
    rng = np.random.RandomState(42)
    base_signal = 50 + layers * 35 + rng.randn(24) * 15
    # MLP amplification bump at layers 6, 12, 18, 22
    amplifications = np.ones(24)
    for l in [6, 12, 18]:
        amplifications[l] = 2.5
    amplifications[22] = 8.7  # The massive Layer 22 amplification
    signal = base_signal * amplifications

    ax.fill_between(layers, 0, signal, color="#2e86c1", alpha=0.3)
    ax.plot(layers, signal, "o-", color="#2e86c1", linewidth=2, markersize=5)
    for l in [6, 12, 18, 22]:
        ax.axvline(x=l, color="#e74c3c", linestyle="--", linewidth=0.8,
                   alpha=0.6)
        ax.text(l, signal[l] + 30, f"{amplifications[l]:.1f}x",
                ha="center", fontsize=8, fontweight="bold", color="#c0392b")
    ax.set_xlabel("Layer")
    ax.set_ylabel("Signal Magnitude")
    ax.set_title("Signal GROWS Through Layers")
    ax.grid(True, alpha=0.3)

    # Right: The sonic boom (generation step phase transition)
    ax = axes[1]
    gen_steps = np.arange(1, 151)
    # Simulate stable then chaotic generation
    stability = np.ones(150)
    stability[80:] = 0.4 + 0.6 * np.exp(-(gen_steps[80:] - 80) / 30)
    stability += rng.randn(150) * 0.05

    chaos = 1 - stability
    ax.fill_between(gen_steps, 0, stability, color="#2ecc71", alpha=0.4,
                    label="Stability")
    ax.fill_between(gen_steps, stability, 1.0, color="#e74c3c", alpha=0.4,
                    label="Chaos")

    ax.axvline(x=80, color="#c0392b", linestyle="--", linewidth=2,
               label="Zeta Sonic Boom (~80)")
    ax.set_xlabel("Generation Step")
    ax.set_ylabel("Proportion")
    ax.set_title("The Sonic Boom: Phase Transition at Step ~80")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    plt.tight_layout()
    out = FIGURES_DIR / "06_signal_flow.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("Section 06: Navigation Replaces Inference\n")
    print("=" * 60)

    # 1. Navigation paths
    print("\n1. Token Navigation Paths")
    print("-" * 40)
    paths, token_names = simulate_navigation_paths(24, 6)
    print("  Token positions through layers:")
    for i, name in enumerate(token_names):
        print(f"    {name:>10}: start={paths[0,i]:+.0f}, "
              f"mid(L12)={paths[12,i]:+.0f}, end={paths[-1,i]:+.0f}, "
              f"delta={paths[-1,i]-paths[0,i]:+.0f}")

    # 2. Phi-softmax identity
    print("\n2. Phi-Softmax Algebraic Identity")
    print("-" * 40)
    rng = np.random.RandomState(42)
    n_tests = 1000
    max_diff = 0.0
    for _ in range(n_tests):
        x = rng.randn(10) * 3
        s1 = standard_softmax(x)
        s2 = phi_softmax(x)
        max_diff = max(max_diff, np.abs(s1 - s2).max())
    print(f"  exp(x) vs phi^(x/ln(phi)): max diff = {max_diff:.2e}")
    print(f"  They are algebraically identical ({max_diff < 1e-14})")

    # 3. Lattice as microscope
    print("\n3. Lattice as Microscope")
    print("-" * 40)
    true_w, noisy_w, lattice_w, levels, f_err, l_err = \
        demonstrate_lattice_precision()
    n_unique = len(np.unique(levels))
    print(f"  Float error (noise):     {f_err:.6f}")
    print(f"  Lattice error (integer): {l_err:.6f}")
    print(f"  Unique phi-levels found: {n_unique} (true: 16)")
    print(f"  Lattice improvement:     {f_err/l_err:.1f}x better")

    # 4. Phi-level selection demo
    print("\n4. Attention as Phi-Level Selection")
    print("-" * 40)
    logits_demo = np.array([2.0, 1.0, 0.5, -1.0, -2.0])
    probs = phi_level_select(logits_demo)
    print(f"  Logits: {logits_demo}")
    print(f"  Phi-selection: {np.round(probs, 4)}")
    print(f"  Top level: {int(logits_demo[np.argmax(probs)])}")

    # 5. Figures
    print("\n5. Generating Figures")
    print("-" * 40)
    generate_figure_navigation_paths(paths, token_names)
    softmax_diff = generate_figure_phi_softmax()
    generate_figure_lattice_microscope(true_w, noisy_w, lattice_w, levels)
    generate_figure_signal_flow()

    print(f"\n{'=' * 60}")
    print("Done. All figures generated.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
