#!/usr/bin/env python3
"""Section 16: The Wall-Breaking Protocol -- demonstration."""

import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

PHI = (1 + math.sqrt(5)) / 2


def resfrac_score(data, order=5):
    """AR(k) predictability score. rho -> 0 = structured, rho -> 1 = ergodic."""
    data = np.asarray(data, dtype=np.float64)
    n = len(data)
    if n <= order + 1:
        return 1.0
    predictions = np.zeros_like(data)
    for t in range(order, n):
        window = data[t - order:t]
        coeffs = np.polyfit(np.arange(order), window, min(order - 1, 3))
        predictions[t] = np.polyval(coeffs, order)
    residuals = data[order:] - predictions[order:]
    var_residual = np.var(residuals)
    var_data = np.var(data[order:])
    if var_data < 1e-30:
        return 0.0
    return float(min(1.0, var_residual / var_data))


def fractal_peel(data, max_layers=5, order=5):
    """Recursively peel structured layers from the signal."""
    layers = []
    residual = data.copy()
    rhos = []
    for layer in range(max_layers):
        rho = resfrac_score(residual, order)
        rhos.append(rho)
        if rho > 0.9:
            break
        # Extract AR structure
        coeffs = np.polyfit(np.arange(order), residual[:order], min(order - 1, 3))
        structured = np.polyval(coeffs, np.arange(len(residual)))
        layers.append(structured)
        residual = residual - structured
    return layers, residual, rhos


def chaos_injection(residual, frequency):
    """Inject an irrational harmonic into the residual."""
    n = len(residual)
    t = np.arange(n, dtype=np.float64)
    harmonic = np.sin(2 * math.pi * frequency * t)
    injected = residual + harmonic * np.std(residual) * 0.5
    return injected


def pslq_search(value, candidates, tol=1e-8, max_coeff=20):
    """Simplified integer-relation search (brute-force small coefficients)."""
    best = None
    best_err = float("inf")
    for a0 in range(-max_coeff, max_coeff + 1):
        if a0 == 0:
            continue
        target = -a0 * value
        for a1 in range(-max_coeff, max_coeff + 1):
            remaining = target - a1 * candidates[0]
            for a2 in range(-max_coeff, max_coeff + 1):
                err = abs(remaining - a2 * candidates[1])
                if err < best_err:
                    best_err = err
                    best = (a0, a1, a2)
    return best, best_err


def holographic_bound(scores):
    """Detect holographic bound: convergence_ratio = std/mean."""
    scores = np.array(scores)
    return float(np.std(scores) / np.mean(scores)) if np.mean(scores) > 1e-30 else 1.0


def generate_figure(layers, residual, rhos):
    print("\nGenerating Figure 16.1: Wall-Breaking Protocol...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Fractal peel
    ax = axes[0, 0]
    data = layers[0] + residual if layers else residual
    ax.plot(data, color="gray", alpha=0.5, linewidth=0.8, label="Original")
    for i, layer in enumerate(layers):
        ax.plot(layer, linewidth=1.5, alpha=0.8, label=f"Layer {i+1}")
    ax.plot(residual, color="#e74c3c", linewidth=1, alpha=0.7, label="Residual")
    ax.set_title("Fractal Peel (GOP Phase 1)")
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # Resfrac scores
    ax = axes[0, 1]
    ax.plot(rhos, "o-", color="#2e86c1", linewidth=2, markersize=8,
            markeredgecolor="white", markeredgewidth=0.5)
    ax.axhline(y=0.9, color="#e74c3c", linestyle="--", linewidth=1, alpha=0.5,
               label="Ergodic threshold")
    ax.axhline(y=0.5, color="#f39c12", linestyle="--", linewidth=1, alpha=0.5,
               label="Mixed threshold")
    ax.set_xlabel("Peel Layer")
    ax.set_ylabel("resfrac_score rho")
    ax.set_title("Resfrac Score per Layer")
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)

    # Chaos injection
    ax = axes[1, 0]
    t = np.arange(500)
    signal = np.sin(2 * math.pi * 0.05 * t) * np.exp(-t / 200) + np.random.randn(500) * 0.3
    rho_before = resfrac_score(signal, 5)

    # Inject golden ratio harmonic
    injected = chaos_injection(signal, 1 / PHI)
    rho_after_phi = resfrac_score(injected, 5)

    ax.plot(signal[:200], color="gray", linewidth=0.8, alpha=0.7, label=f"Original (rho={rho_before:.3f})")
    ax.plot(injected[:200], color="#e74c3c", linewidth=1, alpha=0.8,
            label=f"+ 1/phi harmonic (rho={rho_after_phi:.3f})")
    ax.set_title(f"Chaos Injection: rho {rho_before:.3f} -> {rho_after_phi:.3f}")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Holographic bound
    ax = axes[1, 1]
    # Simulate projections approaching a holographic bound
    n_projections = 20
    scores = []
    ratios = []
    for i in range(1, n_projections + 1):
        s = 0.95 + 0.05 * np.exp(-i / 3) + np.random.randn(10) * 0.01
        scores.append(np.mean(s))
        ratios.append(holographic_bound(s))

    ax.plot(range(1, n_projections + 1), ratios, "o-", color="#9b59b6",
            linewidth=2, markersize=8, markeredgecolor="white", markeredgewidth=0.5)
    ax.axhline(y=0.01, color="#c0392b", linestyle="--", linewidth=1.5,
               label="HOLOGRAPHIC BOUND (0.01)")
    ax.axhline(y=0.05, color="#f39c12", linestyle="--", linewidth=1.5,
               label="New structure (0.05)")
    ax.set_xlabel("Projection #")
    ax.set_ylabel("Convergence Ratio")
    ax.set_title("Holographic Bound Detection (MGOP Phase 5)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.suptitle("The Wall-Breaking Protocol: Four Sub-Protocols",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "16_wbp.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def main():
    print("Section 16: The Wall-Breaking Protocol\n")
    print("=" * 60)

    # 1. Fractal peeling
    print("\n1. GOP: Fractal Peeling")
    print("-" * 40)
    rng = np.random.RandomState(42)
    t = np.arange(200)
    signal = (np.sin(2 * math.pi * 0.03 * t) * 3.0 +
              np.sin(2 * math.pi * 0.07 * t) * 1.5 +
              np.sin(2 * math.pi * 0.15 * t) * 0.8 +
              rng.randn(200) * 0.3)

    print(f"  Signal: {len(signal)} points, 3 periodic components + noise")
    rho_init = resfrac_score(signal, 5)
    print(f"  Initial resfrac: rho = {rho_init:.3f}")

    layers, residual, rhos = fractal_peel(signal, max_layers=5, order=5)
    print(f"  Layers peeled: {len(layers)}")
    for i, rho in enumerate(rhos):
        status = "structured" if rho < 0.5 else "mixed" if rho < 0.9 else "ergodic"
        print(f"    Layer {i+1}: rho = {rho:.3f} ({status})")

    # 2. Chaos injection
    print("\n2. Chaos Injection")
    print("-" * 40)
    rng2 = np.random.RandomState(99)
    hidden_signal = np.sin(2 * math.pi * (1/PHI) * np.arange(300)) * 2.0 + rng2.randn(300) * 1.5
    rho_hidden = resfrac_score(hidden_signal, 5)
    print(f"  Hidden signal (1/phi): rho = {rho_hidden:.3f}")

    for freq, name in [(1/PHI, "1/phi"), (1/math.sqrt(5), "1/sqrt(5)"), (1/math.pi, "1/pi")]:
        injected = chaos_injection(hidden_signal, freq)
        rho_inj = resfrac_score(injected, 5)
        delta = rho_hidden - rho_inj
        tag = "STRUCTURE REVEALED!" if delta > 0.1 else "no change"
        print(f"    + {name}: rho = {rho_inj:.3f} (delta = {delta:+.3f}) [{tag}]")

    # 3. PSLQ search
    print("\n3. EDP: PSLQ Integer-Relation Search")
    print("-" * 40)
    # A mysterious value that is actually sqrt(phi^2 + e/pi) ~ 1.84
    mystery = math.sqrt(PHI**2 + math.e / math.pi)
    print(f"  Mystery value: {mystery:.8f}")

    candidates = [PHI, math.e, math.pi]
    coeffs, err = pslq_search(mystery, candidates, tol=1e-6, max_coeff=10)
    a0, a1, a2 = coeffs
    reconstructed = -(a1 * candidates[0] + a2 * candidates[1]) / a0
    print(f"  Best relation: {a0}*v + {a1}*phi + {a2}*e = 0")
    print(f"  Reconstructed v = {reconstructed:.8f}, error = {err:.2e}")

    # 4. Holographic bound
    print("\n4. MGOP: Holographic Bound Detection")
    print("-" * 40)
    ratios_sim = []
    for i in range(1, 21):
        scores = 0.95 + 0.05 * np.exp(-i / 3) + np.random.randn(10) * 0.01
        ratios_sim.append(holographic_bound(scores))
    final_ratio = ratios_sim[-1]
    if final_ratio < 0.01:
        verdict = "HOLOGRAPHIC BOUND REACHED (real limit)"
    elif final_ratio > 0.05:
        verdict = "NEW STRUCTURE AVAILABLE"
    else:
        verdict = "Intermediate"
    print(f"  Final convergence ratio: {final_ratio:.4f}")
    print(f"  Verdict: {verdict}")

    # 5. Figure
    generate_figure(layers, residual, rhos)

    print(f"\n{'=' * 60}")
    print("Done. Figure generated.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
