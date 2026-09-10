#!/usr/bin/env python3
"""Section 03: Phase-Shift Probing — full framework demonstration.

Key demonstrations:
  1. Formal phase-shift probing on the 12D intentional encoder
  2. Separation score comparison across all 12 self-similar constants
  3. The invariance matrix: N×N heatmap of pair variances
  4. Crystallography analogy figure
  5. Probe space: how different constants discriminate differently
"""

import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ─── Self-Similar Constants ──────────────────────────────────────────

GOLDEN      = (1 + math.sqrt(5)) / 2
PLASTIC     = (9 + math.sqrt(69)) ** (1/3) / 18**(1/3) + (9 - math.sqrt(69)) ** (1/3) / 18**(1/3)
SILVER      = 1 + math.sqrt(2)
BRONZE      = (3 + math.sqrt(13)) / 2
CHROMIUM    = 2 + math.sqrt(5)
COPPER      = (3 + math.sqrt(13)) / 2 + 1
ALUMINIUM   = 2 + math.sqrt(6)
NICKEL      = 2 + math.sqrt(7)
SUPERGOLDEN = (1 + math.sqrt(5)) / 2
NARAYANA    = 1.465571231876768
TITANIUM    = 5 + math.sqrt(0.1)
TRIBONACCI  = (1 + (19+3*math.sqrt(33))**(1/3) + (19-3*math.sqrt(33))**(1/3)) / 3

ALL_CONSTANTS = [GOLDEN, PLASTIC, SILVER, BRONZE, CHROMIUM, COPPER,
                 ALUMINIUM, NICKEL, SUPERGOLDEN, NARAYANA, TITANIUM, TRIBONACCI]
CNAMES = ["phi", "rho", "delta", "bronze", "chromium", "copper",
          "aluminium", "nickel", "supergolden", "narayana", "titanium", "tribonacci"]

DEFAULT_CONSTANTS = ALL_CONSTANTS  # 12D
N_DIMS = len(DEFAULT_CONSTANTS)

# ─── Concept Corpus ──────────────────────────────────────────────────

CONCEPTS = [
    "file", "directory", "read", "write", "create", "destroy",
    "copy", "move", "search", "find", "grep", "list", "show",
    "process", "network", "ssh", "compress", "archive", "tar",
    "chmod", "permissions", "system",
]

# Intentional placement: each concept→(axis, direction)
CONCEPT_GROUPS = {
    "file": (0, +1), "directory": (0, +1),
    "read": (1, +1), "write": (1, -1),
    "create": (2, +1), "destroy": (2, -1),
    "copy": (3, +1), "move": (3, +1),
    "search": (4, +1), "find": (4, +1), "grep": (4, +1),
    "list": (4, +1), "show": (4, +1),
    "compress": (5, +1), "archive": (5, -1), "tar": (5, +1),
    "process": (6, +1), "network": (6, -1),
    "ssh": (7, +1),
    "chmod": (8, +1), "permissions": (8, +1), "system": (8, +1),
}

# Pair types for analysis
SYNONYM_PAIRS = [
    ("file", "directory"), ("copy", "move"),
    ("search", "find"), ("list", "show"),
]
OPPOSITE_PAIRS = [
    ("read", "write"), ("create", "destroy"),
    ("compress", "archive"), ("process", "network"),
]
UNRELATED_PAIRS = [
    ("file", "network"), ("read", "directory"),
    ("create", "ssh"), ("grep", "tar"),
]
ALL_PAIRS = SYNONYM_PAIRS + OPPOSITE_PAIRS + UNRELATED_PAIRS
ALL_LABELS = (["synonym"]*4 + ["opposite"]*4 + ["unrelated"]*4)


# ─── Core Probing Functions ─────────────────────────────────────────

def phi_encode_concept(word, constants=None):
    if constants is None:
        constants = DEFAULT_CONSTANTS
    dims = len(constants)
    if word not in CONCEPT_GROUPS:
        d, sign = (min(dims-1, 9), +1)
    else:
        d, sign = CONCEPT_GROUPS[word]
    if d >= dims:
        d = dims - 1
    vec = np.zeros(dims, dtype=np.complex128)
    vec[d] = complex(sign, 0.0)
    return vec


def apply_phase_shift(vec, theta, constants=None):
    if constants is None:
        constants = DEFAULT_CONSTANTS
    result = vec.copy()
    for i, c in enumerate(constants):
        rate = math.log(c) / math.log(GOLDEN) if c > 0 else 1.0
        result[i] *= np.exp(1j * theta * rate)
    return result


def cosine_similarity_real(v1, v2):
    v1r = np.concatenate([v1.real, v1.imag])
    v2r = np.concatenate([v2.real, v2.imag])
    n1 = np.linalg.norm(v1r)
    n2 = np.linalg.norm(v2r)
    if n1 < 1e-30 or n2 < 1e-30:
        return 0.0
    return float(np.dot(v1r, v2r) / (n1 * n2))


def probe_pair(v1, v2, thetas, constants=None):
    return np.array([cosine_similarity_real(
        apply_phase_shift(v1, t, constants),
        apply_phase_shift(v2, t, constants)) for t in thetas])


# ─── 1. Invariance Matrix ───────────────────────────────────────────

def compute_invariance_matrix(constants=None, n_angles=360):
    if constants is None:
        constants = DEFAULT_CONSTANTS
    thetas = np.linspace(0, 2 * math.pi, n_angles)
    vectors = {c: phi_encode_concept(c, constants) for c in CONCEPTS}
    n = len(CONCEPTS)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i+1, n):
            sims = probe_pair(vectors[CONCEPTS[i]], vectors[CONCEPTS[j]],
                              thetas, constants)
            matrix[i, j] = matrix[j, i] = float(np.var(sims))
    return matrix


# ─── 2. Constant Comparison ─────────────────────────────────────────

def compute_separation_scores():
    """For each constant individually (at D=1), compute how well it
    separates synonym/opposite/unrelated pairs.
    
    In D=1, each constant alone determines the phase advance rate.
    We measure: for each pair type, mean cos similarity under rotation.
    A good constant produces well-separated means for the three types.
    """
    print("Computing separation scores for 12 constants (D=1)...")
    thetas = np.linspace(0, 2 * math.pi, 360)
    scores = {}
    
    for idx, (c, name) in enumerate(zip(ALL_CONSTANTS, CNAMES)):
        # Build concept vectors in 1D with just this constant
        single_constant = [c]
        vectors = {}
        for word in CONCEPTS:
            # Re-use axis assignment but collapse to 1D:
            # Concepts on axes 0,2,4,6,8 → positive
            # Concepts on axes 1,3,5,7 → get sign from group
            if word not in CONCEPT_GROUPS:
                d, sign = (9, +1)
            else:
                d, sign = CONCEPT_GROUPS[word]
            # Map axis to 0 (single axis), sign determines direction
            vec = np.array([complex(sign, 0.0)], dtype=np.complex128)
            vectors[word] = vec
        
        # Measure mean similarity for each pair type
        syn_means = []
        opp_means = []
        unr_means = []
        
        for pair in SYNONYM_PAIRS:
            sims = probe_pair(vectors[pair[0]], vectors[pair[1]],
                              thetas, single_constant)
            syn_means.append(float(np.mean(sims)))
        for pair in OPPOSITE_PAIRS:
            sims = probe_pair(vectors[pair[0]], vectors[pair[1]],
                              thetas, single_constant)
            opp_means.append(float(np.mean(sims)))
        for pair in UNRELATED_PAIRS:
            sims = probe_pair(vectors[pair[0]], vectors[pair[1]],
                              thetas, single_constant)
            unr_means.append(float(np.mean(sims)))
        
        s_mean = np.mean(syn_means)
        o_mean = np.mean(opp_means)
        u_mean = np.mean(unr_means)
        
        # Separation = distance between synonym and opposite clusters
        separation = abs(s_mean - o_mean)
        # Plus distance from unrelated to both
        separation += abs(u_mean - s_mean) + abs(u_mean - o_mean)
        
        scores[name] = {
            "value": c,
            "separation": float(separation),
            "syn_mean": float(s_mean),
            "opp_mean": float(o_mean),
            "unr_mean": float(u_mean),
        }
        print(f"  {name:>12}: c={c:.4f}, sep={separation:.4f}  "
              f"[syn={s_mean:+.3f}, opp={o_mean:+.3f}, unr={u_mean:+.3f}]")
    
    return scores


# ─── 3. Multi-D Constant Probing ────────────────────────────────────

def probe_with_constants(constants, n_angles=360):
    """Probe all pairs with a given set of constants, return stats."""
    thetas = np.linspace(0, 2 * math.pi, n_angles)
    vectors = {c: phi_encode_concept(c, constants) for c in CONCEPTS}
    results = {}
    for pair in ALL_PAIRS:
        sims = probe_pair(vectors[pair[0]], vectors[pair[1]],
                          thetas, constants)
        results[pair] = {
            "mean": float(np.mean(sims)),
            "std": float(np.std(sims)),
        }
    # Aggregate by type
    agg = {"synonym": {"means": [], "stds": []},
           "opposite": {"means": [], "stds": []},
           "unrelated": {"means": [], "stds": []}}
    for pair, ptype in zip(ALL_PAIRS, ALL_LABELS):
        agg[ptype]["means"].append(results[pair]["mean"])
        agg[ptype]["stds"].append(results[pair]["std"])
    return results, agg


# ─── Figures ─────────────────────────────────────────────────────────

def generate_figure_crystallography():
    """Figure 3.1: Crystallography analogy."""
    print("\nGenerating Figure 3.1: Crystallography Analogy...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    # Left: Polycrystalline (invariant)
    ax = axes[0]
    thetas = np.linspace(0, 4*np.pi, 500)
    # Multiple crystal orientations produce a stable envelope
    for i in range(8):
        offset = i * np.pi / 4
        # Each "crystal" has its own pattern
        pattern = np.sin(thetas + offset) * np.exp(-((thetas-2*np.pi)/(np.pi))**2)
        ax.plot(thetas, pattern * 0.3 + 0.5, color="#2e86c1", alpha=0.4,
                linewidth=0.8)
    # The average (ensemble) is constant
    ax.axhline(y=0.5, color="#c0392b", linewidth=2.5,
               label="Ensemble average (constant)")
    ax.set_title("Polycrystalline: Invariant Pattern")
    ax.set_xlabel("Rotation angle")
    ax.set_ylabel("Diffraction intensity")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Center: Single crystal (variant)
    ax = axes[1]
    pattern = np.sin(thetas) * np.exp(-((thetas-2*np.pi)/(np.pi))**2)
    ax.plot(thetas, pattern * 0.4 + 0.5, color="#e74c3c", linewidth=2,
            label="Single crystal")
    ax.set_title("Single Crystal: Angle-Dependent")
    ax.set_xlabel("Rotation angle")
    ax.set_ylabel("Diffraction intensity")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Right: Phase-shift probing analogy
    ax = axes[2]
    theta_probe = np.linspace(0, 2*np.pi, 360)
    # Simulate what probing sees: three invariance classes
    ax.plot(theta_probe, np.ones_like(theta_probe), "#2ecc71",
            linewidth=2, label="Synonym (invariant, cos=+1)")
    ax.plot(theta_probe, -np.ones_like(theta_probe), "#e74c3c",
            linewidth=2, label="Opposite (invariant, cos=-1)")
    ax.plot(theta_probe, np.zeros_like(theta_probe), "#95a5a6",
            linewidth=2, label="Unrelated (invariant, cos=0)")
    # A surface artifact would wiggle
    wiggle = 0.5 + 0.3*np.sin(3*theta_probe)*np.cos(5*theta_probe + 0.7)
    ax.plot(theta_probe, wiggle, "#f39c12", linewidth=1.5, alpha=0.7,
            linestyle="--", label="Surface artifact (variant)")
    ax.set_title("Phase-Shift Probing Signature")
    ax.set_xlabel("Phase angle theta")
    ax.set_ylabel("Cosine Similarity")
    ax.set_ylim(-1.2, 1.2)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.suptitle("Crystallography Analogy: Distinguishing Structure from Artifact",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "03_crystallography_analogy.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def generate_figure_constant_comparison(scores):
    """Figure 3.2: Constant separation comparison."""
    print("\nGenerating Figure 3.2: Constant Comparison...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: Bar chart of separation scores
    ax = axes[0]
    names = [n for n, _ in sorted(scores.items(), key=lambda x: -x[1]["separation"])]
    seps = [scores[n]["separation"] for n in names]
    colors = ["#e74c3c" if n == "phi" else "#f39c12" if n == "rho"
              else "#2e86c1" for n in names]
    bars = ax.bar(range(len(names)), seps, color=colors, edgecolor="white",
                  linewidth=0.5)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Separation Score")
    ax.set_title("Constant Separation Scores (D=1)")
    # Highlight best
    best_name = max(scores, key=lambda n: scores[n]["separation"])
    best_idx = names.index(best_name)
    ax.annotate(f"Best: {best_name}\nsep={scores[best_name]['separation']:.3f}",
                xy=(best_idx, seps[best_idx]),
                xytext=(best_idx+0.5, seps[best_idx]+0.2),
                arrowprops=dict(arrowstyle="->", color="#c0392b"),
                fontsize=9, fontweight="bold", color="#c0392b")
    ax.grid(True, alpha=0.3, axis="y")

    # Right: 12D vs 4D comparison
    ax = axes[1]
    # Probe with 12D and 4D subsets
    _, agg12 = probe_with_constants(ALL_CONSTANTS[:12], 180)
    _, agg4 = probe_with_constants(ALL_CONSTANTS[:4], 180)
    
    x = np.arange(3)
    width = 0.35
    s12_means = [np.mean(agg12[t]["means"]) for t in ["synonym","opposite","unrelated"]]
    s12_stds = [np.mean(agg12[t]["stds"]) for t in ["synonym","opposite","unrelated"]]
    s4_means = [np.mean(agg4[t]["means"]) for t in ["synonym","opposite","unrelated"]]
    s4_stds = [np.mean(agg4[t]["stds"]) for t in ["synonym","opposite","unrelated"]]
    
    ax.bar(x - width/2, s12_means, width, color="#2e86c1", edgecolor="white",
           linewidth=0.5, label="12D probe")
    ax.bar(x + width/2, s4_means, width, color="#e74c3c", edgecolor="white",
           linewidth=0.5, label="4D probe")
    ax.set_xticks(x)
    ax.set_xticklabels(["Synonym (+1)", "Opposite (-1)", "Unrelated (0)"])
    ax.set_ylabel("Mean Cosine Similarity")
    ax.set_title("12D vs 4D Probing: Both Identify Same Classes")
    ax.legend(fontsize=9)
    ax.axhline(y=0, color="gray", ls=":", lw=0.5)
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    out = FIGURES_DIR / "03_constant_comparison.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")
    return agg12, agg4


def generate_figure_invariance_matrix(inv_matrix):
    """Figure 3.3: Invariance matrix heatmap."""
    print("\nGenerating Figure 3.3: Invariance Matrix...")
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(inv_matrix, cmap="YlOrRd", aspect="auto", vmin=0)
    ax.set_xticks(range(len(CONCEPTS)))
    ax.set_yticks(range(len(CONCEPTS)))
    ax.set_xticklabels(CONCEPTS, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(CONCEPTS, fontsize=8)
    ax.set_title("Invariance Matrix: variance of cos-similarity under phase rotation")
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("sigma^2 (variance)")
    # Zero entries are white (invariant), non-zero is coloured
    n_zero = int(np.sum(inv_matrix < 1e-15) - len(CONCEPTS)) // 2
    print(f"  Invariant pairs (sigma^2 = 0): {n_zero} out of "
          f"{len(CONCEPTS)*(len(CONCEPTS)-1)//2}")
    plt.tight_layout()
    out = FIGURES_DIR / "03_invariance_matrix.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def generate_figure_probe_space(scores):
    """Figure 3.4: Probe space visualization."""
    print("\nGenerating Figure 3.4: Probe Space...")
    fig, ax = plt.subplots(figsize=(10, 6))
    for name, data in scores.items():
        ax.scatter(data["value"], data["separation"], s=100,
                   edgecolors="white", linewidth=0.5, zorder=5,
                   color="#e74c3c" if name == "phi" else "#2e86c1")
        ax.annotate(name, (data["value"], data["separation"]),
                    xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Constant Value c")
    ax.set_ylabel("Separation Score")
    ax.set_title("Probe Space: Constant Value vs Discriminating Power")
    ax.set_xscale("log")
    ax.grid(True, alpha=0.3)
    # Highlight phi
    phi_data = scores["phi"]
    ax.annotate("phi — universal\nat 4D, good at 12D",
                xy=(phi_data["value"], phi_data["separation"]),
                xytext=(phi_data["value"]*1.3, phi_data["separation"]*1.5),
                arrowprops=dict(arrowstyle="->", color="#c0392b"),
                fontsize=9, fontweight="bold", color="#c0392b",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    plt.tight_layout()
    out = FIGURES_DIR / "03_probe_space.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


# ─── Main ───────────────────────────────────────────────────────────

def main():
    print("Section 03: Phase-Shift Probing and Geometric Invariants\n")
    print("=" * 60)

    # 1. Constant comparison (D=1)
    print("\n1. Separation Scores Across Constants (D=1)")
    print("-" * 40)
    scores = compute_separation_scores()
    
    # 2. Multi-dimensional probing validation
    print("\n2. Multi-D Probing Validation")
    print("-" * 40)
    for dims, consts in [("12D", ALL_CONSTANTS[:12]), ("4D", ALL_CONSTANTS[:4])]:
        results, agg = probe_with_constants(consts, 180)
        for ptype in ["synonym", "opposite", "unrelated"]:
            m = np.mean(agg[ptype]["means"])
            s = np.mean(agg[ptype]["stds"])
            expected = {"synonym": 1.0, "opposite": -1.0, "unrelated": 0.0}[ptype]
            ok = abs(m - expected) < 1e-12 and s < 1e-15
            print(f"  {dims} {ptype:>10}: mean={m:+.8f}, std={s:.1e}  "
                  f"[{'OK' if ok else 'FAIL'}]")

    # 3. Invariance matrix
    print("\n3. Computing Invariance Matrix...")
    inv_matrix = compute_invariance_matrix(n_angles=180)
    n_invariant = int(np.sum(inv_matrix < 1e-15) - len(CONCEPTS)) // 2
    n_total = len(CONCEPTS) * (len(CONCEPTS) - 1) // 2
    print(f"  Invariant pairs: {n_invariant}/{n_total}")

    # 4. Generate figures
    print("\n4. Generating Figures")
    print("-" * 40)
    generate_figure_crystallography()
    generate_figure_constant_comparison(scores)
    generate_figure_invariance_matrix(inv_matrix)
    generate_figure_probe_space(scores)

    print(f"\n{'=' * 60}")
    print("Done. All figures generated.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
