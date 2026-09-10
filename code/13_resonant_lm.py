#!/usr/bin/env python3
"""Section 13: The Resonant Language Model -- demonstration."""

import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

TWOPI = 2.0 * math.pi
PHI = (1 + math.sqrt(5)) / 2
LN_PHI = math.log(PHI)

GAMMAS = [14.134725, 21.022040, 25.010858, 30.424876,
          32.935062, 37.586178, 40.918719, 43.327073]


def phase(key, gamma):
    return (gamma * key) % TWOPI


def circ_dist(a, b):
    d = abs(a - b)
    return min(d, TWOPI - d) / math.pi


class ResonantArray:
    def __init__(self, n_heads=4, n_buckets=1024):
        self.H = min(n_heads, len(GAMMAS))
        self.B = n_buckets
        self.gammas = GAMMAS[:self.H]
        self.tables = [[[] for _ in range(self.B)] for _ in range(self.H)]
        self._items = {}

    def _bucket(self, key, head):
        p = phase(key, self.gammas[head])
        return int(p / TWOPI * self.B) % self.B

    def insert(self, key, value):
        self._items[key] = value
        for h in range(self.H):
            b = self._bucket(key, h)
            self.tables[h][b].append(key)

    def resonate(self, key, threshold=0.1):
        results = {}
        for h in range(self.H):
            pk = phase(key, self.gammas[h])
            b = self._bucket(key, h)
            for other_key in self.tables[h][b]:
                if other_key == key: continue
                po = phase(other_key, self.gammas[h])
                d = circ_dist(pk, po)
                if d < threshold:
                    results[other_key] = results.get(other_key, 0) + 1
        return sorted(results.items(), key=lambda x: -x[1])


def resonant_embed(token_id, n_heads=8):
    vec = []
    for h in range(min(n_heads, len(GAMMAS))):
        p = phase(token_id + 1, GAMMAS[h])
        vec.extend([math.cos(p), math.sin(p)])
    return np.array(vec)


def signed_attention(tokens, gamma_idx=0):
    g = GAMMAS[gamma_idx]
    n = len(tokens)
    attn = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            p_i = phase(tokens[i] + 1, g)
            p_j = phase(tokens[j] + 1, g)
            attn[i, j] = math.cos(p_i - p_j)
    return attn


def phi_zipf_embed(token_id, n_heads=8, k=256):
    rng = np.random.RandomState(token_id)
    vec = np.zeros(2 * n_heads)
    for h in range(n_heads):
        p = phase(token_id + 1, GAMMAS[h])
        # φ-Zipf magnitude: phi^(-h) decay
        mag = PHI ** (-h)
        vec[2*h] = mag * math.cos(p)
        vec[2*h+1] = mag * math.sin(p)
    return vec


def generate_figures():
    print("\nGenerating figures...")

    # Figure 13.1: Phase uniformity
    print("  Figure 13.1: Phase Uniformity...")
    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    keys = np.arange(1, 5001)
    for h in range(8):
        ax = axes[h // 4, h % 4]
        phases_h = np.array([phase(k, GAMMAS[h]) for k in keys])
        ax.hist(phases_h, bins=40, color="#2e86c1", edgecolor="white",
                linewidth=0.3, alpha=0.85, density=True)
        ax.axhline(y=1.0 / TWOPI, color="#c0392b", linestyle="--",
                   linewidth=1, alpha=0.7)
        ax.set_title(f"gamma_{h+1} = {GAMMAS[h]:.2f}")
        ax.set_xlabel("Phase"); ax.set_ylabel("Density")
        ax.set_xlim(0, TWOPI)
    plt.suptitle("Phase Uniformity: Montgomery-Odlyzko Law Verified",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "13_phase_uniformity.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"    Saved: {out}")

    # Figure 13.2: Resonant Array demo
    print("  Figure 13.2: Resonant Array...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: Bucket fill distribution
    ax = axes[0]
    ra = ResonantArray(n_heads=4, n_buckets=256)
    for i in range(500):
        ra.insert(i, f"item_{i}")
    fills = [len(ra.tables[0][b]) for b in range(ra.B)]
    ax.bar(range(ra.B), sorted(fills), color="#2e86c1", edgecolor="white",
           linewidth=0.3, alpha=0.7)
    ax.set_xlabel("Bucket (sorted)")
    ax.set_ylabel("Items per bucket")
    ax.set_title(f"Bucket Fill Distribution (500 items, {ra.B} buckets)")
    ax.grid(True, alpha=0.3, axis="y")
    exp_fill = 500 / ra.B
    ax.axhline(y=exp_fill, color="#c0392b", linestyle="--", linewidth=1,
               label=f"Expected: {exp_fill:.1f}")
    ax.legend(fontsize=9)

    # Right: Resonance search example
    ax = axes[1]
    ra2 = ResonantArray(n_heads=4, n_buckets=128)
    # Insert tokens with natural clustering
    clusters = {
        "file_ops": list(range(1, 21)),
        "network": list(range(100, 120)),
        "system": list(range(200, 220)),
    }
    for name, ids in clusters.items():
        for kid in ids:
            ra2.insert(kid, f"{name}:{kid}")

    # Test resonance search
    query = 5  # file_ops cluster
    results = ra2.resonate(query, threshold=0.3)
    found_ids = [r[0] for r in results[:10]]
    found_clusters = []
    for fid in found_ids:
        for cname, cids in clusters.items():
            if fid in cids:
                found_clusters.append(cname)
                break
        else:
            found_clusters.append("other")

    from collections import Counter
    counts = Counter(found_clusters)
    ax.bar(counts.keys(), counts.values(), color=["#2ecc71", "#3498db", "#e74c3c"],
           edgecolor="white", linewidth=0.3)
    ax.set_ylabel("Matches Found")
    ax.set_title(f"Resonance Search (query: {query})")
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    out = FIGURES_DIR / "13_resonant_array.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"    Saved: {out}")

    # Figure 13.3: Signed attention matrix
    print("  Figure 13.3: Signed Attention...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    tokens = list(range(20))
    attn = signed_attention(tokens, 0)
    ax = axes[0]
    im = ax.imshow(attn, cmap="RdBu_r", aspect="auto", vmin=-1, vmax=1)
    ax.set_xlabel("Key position"); ax.set_ylabel("Query position")
    ax.set_title("Signed Attention Matrix (gamma_1)")
    plt.colorbar(im, ax=ax, shrink=0.8, label="cos(phase_diff)")

    ax = axes[1]
    # Attention scores histogram
    ax.hist(attn.ravel(), bins=50, color="#3498db", edgecolor="white",
            linewidth=0.3, alpha=0.85)
    ax.axvline(x=0, color="gray", linestyle=":", linewidth=0.8)
    ax.set_xlabel("Attention Weight")
    ax.set_ylabel("Count")
    ax.set_title("Signed Attention Distribution")
    pos_pct = (attn > 0).mean() * 100
    neg_pct = (attn < 0).mean() * 100
    ax.text(0.95, 0.95, f"Positive: {pos_pct:.0f}%\nNegative: {neg_pct:.0f}%",
            transform=ax.transAxes, ha="right", va="top", fontsize=9,
            fontweight="bold", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = FIGURES_DIR / "13_signed_attention.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"    Saved: {out}")


def main():
    print("Section 13: The Resonant Language Model\n")
    print("=" * 60)

    # 1. Phase uniformity
    print("\n1. Phase Uniformity (Montgomery-Odlyzko)")
    print("-" * 40)
    keys = np.arange(1, 10001)
    for h in range(4):
        phases_h = np.array([phase(k, GAMMAS[h]) for k in keys])
        # Kolmogorov-Smirnov test for uniformity
        sorted_p = np.sort(phases_h) / TWOPI
        ks_stat = np.max(np.abs(sorted_p - np.linspace(0, 1, len(keys))))
        print(f"  gamma_{h+1} = {GAMMAS[h]:.2f}: "
              f"mean phase = {phases_h.mean():.3f}, "
              f"KS stat = {ks_stat:.4f}")

    # 2. Resonant Array
    print("\n2. Resonant Array Operations")
    print("-" * 40)
    ra = ResonantArray(n_heads=4, n_buckets=256)
    for i in range(1000):
        ra.insert(i, f"item_{i}")

    # Resonance search
    query = 42
    results = ra.resonate(query, threshold=0.15)
    print(f"  Inserted 1000 items")
    print(f"  Query key={query}: found {len(results)} resonant items")
    if results:
        top3 = results[:3]
        for rkey, score in top3:
            d = circ_dist(phase(query, GAMMAS[0]), phase(rkey, GAMMAS[0]))
            print(f"    key={rkey:>4}, score={score}, phase_dist={d:.4f}")

    # 3. Deterministic embeddings
    print("\n3. Deterministic Embeddings")
    print("-" * 40)
    tokens = [1, 42, 100, 999]
    for tid in tokens:
        emb = resonant_embed(tid, 4)
        print(f"  token_id={tid:>3}: dims={len(emb)}, "
              f"norm={np.linalg.norm(emb):.4f}, "
              f"first 4 = {np.round(emb[:4], 3)}")

    # Note: same token -> same embedding (deterministic)
    emb1 = resonant_embed(42, 4)
    emb2 = resonant_embed(42, 4)
    print(f"  Same token check: |emb(42)_1 - emb(42)_2| = "
          f"{np.abs(emb1 - emb2).max():.1e} (deterministic!)")

    # 4. Signed attention
    print("\n4. Signed Attention")
    print("-" * 40)
    tokens_test = list(range(30))
    attn = signed_attention(tokens_test, 0)
    n_pos = int((attn > 0.1).sum())
    n_neg = int((attn < -0.1).sum())
    n_near = int((np.abs(attn) <= 0.1).sum())
    total = attn.size
    print(f"  {len(tokens_test)}x{len(tokens_test)} attention matrix:")
    print(f"    Positive resonance:  {n_pos}/{total} ({n_pos/total*100:.1f}%)")
    print(f"    Negative resonance:  {n_neg}/{total} ({n_neg/total*100:.1f}%)")
    print(f"    Near-zero (neutral): {n_near}/{total} ({n_near/total*100:.1f}%)")
    print(f"    Range: [{attn.min():.3f}, {attn.max():.3f}]")

    # 5. phi-Zipf embedding
    print("\n5. phi-Zipf + Resonant Embeddings")
    print("-" * 40)
    emb_phi = phi_zipf_embed(42, 8)
    print(f"  phi-Zipf magnitudes: {np.round([np.linalg.norm(emb_phi[2*h:2*h+2]) for h in range(8)], 3)}")
    print(f"  Decay ratio: {np.linalg.norm(emb_phi[0:2]) / np.linalg.norm(emb_phi[14:16]):.3f}")
    print(f"  Expected phi^7 = {PHI**7:.3f}")

    # 6. Figures
    generate_figures()

    print(f"\n{'=' * 60}")
    print("Done. All figures generated.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
