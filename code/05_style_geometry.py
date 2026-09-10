#!/usr/bin/env python3
"""Section 05: Style Is Geometry — full demonstration.

Implements the generic Style Space framework with three domains:
  Ethics (16D), Text Style (6D), Image Style (16D).

Key demonstrations:
  1. StyleSpace, Component, StyleVector classes
  2. Three domain generators
  3. Style distance matrix
  4. Style interpolation (lerp)
  5. The Three Universals visualization
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════
# Generic Style Space Framework
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class Component:
    """A named group of semantically related dimensions."""
    name: str
    dimensions: int
    description: str = ""
    labels: Optional[List[str]] = None


class StyleSpace:
    """N-dimensional Euclidean space decomposed into components."""

    def __init__(self, components: List[Component], name: str = "style_space"):
        self.components = list(components)
        self.name = name
        self._offsets: Dict[str, tuple] = {}
        self._total_dims = 0
        for comp in self.components:
            self._offsets[comp.name] = (self._total_dims, comp.dimensions)
            self._total_dims += comp.dimensions

    @property
    def n_dims(self) -> int:
        return self._total_dims

    def component_range(self, name: str) -> tuple:
        return self._offsets[name]

    def from_dict(self, values: Dict[str, List[float]]) -> "StyleVector":
        v = np.zeros(self.n_dims, dtype=np.float64)
        for comp_name, vals in values.items():
            offset, ndim = self._offsets[comp_name]
            v[offset:offset + len(vals)] = vals[:ndim]
        return StyleVector(self, v)

    def sample(self, center: float = 0.5, spread: float = 0.3) -> "StyleVector":
        rng = np.random.RandomState()
        v = center + spread * rng.randn(self.n_dims)
        v = np.clip(v, 0.0, 1.0)
        return StyleVector(self, v)

    def zero(self) -> "StyleVector":
        return StyleVector(self, np.zeros(self.n_dims))

    def midpoint(self) -> "StyleVector":
        return StyleVector(self, np.full(self.n_dims, 0.5))


class StyleVector:
    """A point in a StyleSpace."""

    def __init__(self, space: StyleSpace, values: np.ndarray):
        self.space = space
        self.values = np.asarray(values, dtype=np.float64)

    def __getitem__(self, comp_name: str) -> np.ndarray:
        offset, ndim = self.space.component_range(comp_name)
        return self.values[offset:offset + ndim].copy()

    def distance(self, other: "StyleVector") -> float:
        return float(np.sqrt(np.sum((self.values - other.values) ** 2)))

    def lerp(self, other: "StyleVector", t: float) -> "StyleVector":
        t = np.clip(t, 0.0, 1.0)
        v = self.values + (other.values - self.values) * t
        return StyleVector(self.space, v)

    def to_dict(self) -> Dict[str, List[float]]:
        d = {}
        for comp in self.space.components:
            d[comp.name] = self[comp.name].tolist()
        return d

    def explain(self, generator=None) -> str:
        if generator:
            return generator.explain(self)
        parts = []
        for comp in self.space.components:
            vals = self[comp]
            top_idx = int(np.argmax(vals))
            label = (comp.labels[top_idx] if comp.labels
                     else f"dim_{top_idx}")
            parts.append(f"  {comp.name}: {label} ({vals[top_idx]:.2f})")
        return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════
# Domain: Ethics (16D)
# ═══════════════════════════════════════════════════════════════════════

ETHICS_SPACE = StyleSpace([
    Component("moral_frame", 4, "Ethical framework",
              ["deontological", "consequentialist", "virtue", "care"]),
    Component("scope", 4, "Scope of consideration",
              ["individual", "community", "society", "universal"]),
    Component("temporal", 4, "Time horizon",
              ["immediate", "short-term", "long-term", "eternal"]),
    Component("stakes", 4, "Risk tolerance",
              ["cautious", "moderate", "bold", "radical"]),
], name="ethics")

ETHICS_PRESETS = {
    "Kantian":        {"moral_frame": [1.0, 0.0, 0.0, 0.0],
                       "scope": [0.7, 0.2, 0.1, 0.0],
                       "temporal": [0.0, 0.2, 0.3, 0.5],
                       "stakes": [1.0, 0.0, 0.0, 0.0]},
    "Utilitarian":    {"moral_frame": [0.0, 1.0, 0.0, 0.0],
                       "scope": [0.0, 0.1, 0.3, 0.6],
                       "temporal": [0.3, 0.5, 0.2, 0.0],
                       "stakes": [0.0, 0.3, 0.5, 0.2]},
    "Virtue Ethics":  {"moral_frame": [0.0, 0.0, 1.0, 0.0],
                       "scope": [0.4, 0.4, 0.1, 0.1],
                       "temporal": [0.0, 0.1, 0.5, 0.4],
                       "stakes": [0.3, 0.5, 0.2, 0.0]},
    "Care Ethics":    {"moral_frame": [0.0, 0.0, 0.0, 1.0],
                       "scope": [0.3, 0.6, 0.1, 0.0],
                       "temporal": [0.5, 0.3, 0.2, 0.0],
                       "stakes": [0.5, 0.4, 0.1, 0.0]},
    "Nihilist":       {"moral_frame": [0.2, 0.2, 0.2, 0.2],
                       "scope": [1.0, 0.0, 0.0, 0.0],
                       "temporal": [1.0, 0.0, 0.0, 0.0],
                       "stakes": [0.0, 0.0, 0.0, 1.0]},
    "Stoic":          {"moral_frame": [0.0, 0.0, 0.8, 0.2],
                       "scope": [0.6, 0.3, 0.1, 0.0],
                       "temporal": [0.0, 0.0, 0.4, 0.6],
                       "stakes": [0.8, 0.2, 0.0, 0.0]},
}


class EthicsGenerator:
    """Generate ethical analysis from a style vector."""
    def __init__(self):
        self.space = ETHICS_SPACE
        self.presets = ETHICS_PRESETS

    def generate(self, style: StyleVector, dilemma: str) -> Dict[str, Any]:
        mf = style["moral_frame"]
        sc = style["scope"]
        top_frame = self.space.components[0].labels[int(np.argmax(mf))]
        top_scope = self.space.components[1].labels[int(np.argmax(sc))]
        return {
            "dilemma": dilemma,
            "framework": top_frame,
            "scope": top_scope,
            "recommendation": f"From a {top_frame} perspective at "
                              f"{top_scope} scope, ...",
            "vector": style.to_dict(),
        }

    def describe(self) -> Dict[str, str]:
        return {c.name: c.description for c in self.space.components}

    def explain(self, style: StyleVector) -> str:
        return style.explain(self)


# ═══════════════════════════════════════════════════════════════════════
# Domain: Text Style (6D)
# ═══════════════════════════════════════════════════════════════════════

TEXT_SPACE = StyleSpace([
    Component("emphasis", 6, "Content emphasis",
              ["identity", "possession", "action",
               "complexity", "repetition", "uniqueness"]),
], name="text_style")

TEXT_GENRES = {
    "Roman History":  [0.9, 0.3, 0.7, 0.4, 0.2, 0.3],
    "Gothic Novel":   [0.7, 0.8, 0.3, 0.9, 0.5, 0.6],
    "Satire":         [0.2, 0.2, 0.8, 0.3, 0.3, 0.9],
    "Philosophy":     [0.7, 0.8, 0.2, 0.9, 0.4, 0.5],
    "Poetry":         [0.8, 0.6, 0.4, 0.2, 0.9, 0.6],
    "Scientific":     [0.3, 0.2, 0.7, 0.8, 0.1, 0.2],
    "Comedy":         [0.3, 0.1, 0.9, 0.1, 0.2, 0.7],
    "Religious":      [0.8, 0.5, 0.5, 0.5, 0.8, 0.3],
}


class TextStyleGenerator:
    def __init__(self):
        self.space = TEXT_SPACE
        self.genres = TEXT_GENRES

    def generate(self, style: StyleVector, subject: str) -> str:
        # Find closest genre
        best_genre = None
        best_dist = float("inf")
        for name, vec in self.genres.items():
            sv = self.space.from_dict({"emphasis": vec})
            d = style.distance(sv)
            if d < best_dist:
                best_dist = d
                best_genre = name
        emphasis = style["emphasis"]
        emph_labels = self.space.components[0].labels
        top_emph = emph_labels[int(np.argmax(emphasis))]
        return (f"Subject: {subject}\n"
                f"Style: {best_genre} (distance: {best_dist:.2f})\n"
                f"Emphasis: {top_emph} ({emphasis.max():.2f})\n"
                f"Vector: {emphasis.tolist()}")

    def describe(self):
        return {c.name: c.description for c in self.space.components}

    def explain(self, style):
        return style.explain(self)


# ═══════════════════════════════════════════════════════════════════════
# Domain: Image Style (16D)
# ═══════════════════════════════════════════════════════════════════════

IMAGE_SPACE = StyleSpace([
    Component("detail", 4, "Visual detail level",
              ["minimal", "moderate", "rich", "hyperreal"]),
    Component("color", 4, "Color palette",
              ["monochrome", "muted", "vibrant", "saturated"]),
    Component("mood", 4, "Emotional atmosphere",
              ["serene", "dramatic", "melancholic", "chaotic"]),
    Component("composition", 4, "Visual arrangement",
              ["symmetric", "asymmetric", "dynamic", "chaotic"]),
], name="image_style")

IMAGE_PRESETS = {
    "Realist":       {"detail": [0.2, 0.5, 0.7, 0.8],
                      "color": [0.1, 0.5, 0.6, 0.4],
                      "mood": [0.7, 0.2, 0.1, 0.0],
                      "composition": [0.6, 0.3, 0.1, 0.0]},
    "Impressionist": {"detail": [0.1, 0.8, 0.6, 0.2],
                      "color": [0.1, 0.3, 0.7, 0.5],
                      "mood": [0.8, 0.1, 0.1, 0.0],
                      "composition": [0.3, 0.5, 0.2, 0.0]},
    "Noir":          {"detail": [0.6, 0.7, 0.8, 0.9],
                      "color": [0.9, 0.4, 0.1, 0.0],
                      "mood": [0.0, 0.8, 0.7, 0.2],
                      "composition": [0.1, 0.7, 0.6, 0.3]},
    "Abstract":      {"detail": [0.9, 0.5, 0.2, 0.0],
                      "color": [0.0, 0.2, 0.7, 0.9],
                      "mood": [0.3, 0.3, 0.3, 0.7],
                      "composition": [0.0, 0.1, 0.4, 0.9]},
    "Minimalist":    {"detail": [1.0, 0.2, 0.0, 0.0],
                      "color": [0.8, 0.3, 0.1, 0.0],
                      "mood": [0.9, 0.1, 0.0, 0.0],
                      "composition": [0.9, 0.1, 0.0, 0.0]},
}


class ImageStyleGenerator:
    def __init__(self):
        self.space = IMAGE_SPACE
        self.presets = IMAGE_PRESETS

    def generate(self, style: StyleVector, scene: str) -> Dict[str, Any]:
        best = None
        best_d = float("inf")
        for name, vec in self.presets.items():
            sv = self.space.from_dict(vec)
            d = style.distance(sv)
            if d < best_d:
                best_d = d
                best = name
        return {
            "scene": scene,
            "style": best,
            "distance": best_d,
            "recommendations": self._filters_for(style),
        }

    def _filters_for(self, style):
        recs = []
        d = style["detail"]
        c = style["color"]
        m = style["mood"]
        comp = style["composition"]
        if d[3] > 0.6: recs.append("Unsharp mask / detail enhancement")
        if c[2] > 0.5: recs.append("Vibrance boost")
        if c[0] > 0.7: recs.append("Desaturate to monochrome")
        if m[1] > 0.5: recs.append("High contrast")
        if comp[3] > 0.5: recs.append("Chaotic / generative composition")
        return recs[:3]

    def describe(self): 
        return {c.name: c.description for c in self.space.components}
    def explain(self, style): 
        return style.explain(self)


# ═══════════════════════════════════════════════════════════════════════
# Figures
# ═══════════════════════════════════════════════════════════════════════

def generate_figure_domains():
    """Figure 5.1: Three domains side by side."""
    print("\nGenerating Figure 5.1: Three Domains...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    # Ethics
    ax = axes[0]
    for i, (name, preset) in enumerate(ETHICS_PRESETS.items()):
        sv = ETHICS_SPACE.from_dict(preset)
        x = i
        mf = sv["moral_frame"]
        sc = sv["scope"]
        tp = sv["temporal"]
        st = sv["stakes"]
        y_offset = 0
        for label, vals, color in [
            ("MF", mf, "#2ecc71"), ("SC", sc, "#3498db"),
            ("TM", tp, "#e67e22"), ("ST", st, "#9b59b6")]:
            for j, v in enumerate(vals):
                ax.scatter(x, y_offset + v * 0.25, color=color, s=40,
                           alpha=0.7, edgecolors="white", linewidth=0.3)
            y_offset += 1
    ax.set_xticks(range(len(ETHICS_PRESETS)))
    ax.set_xticklabels(list(ETHICS_PRESETS.keys()), rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("Component Value")
    ax.set_title("Ethics (16D)")
    ax.grid(True, alpha=0.3, axis="y")

    # Text
    ax = axes[1]
    for i, (name, vec) in enumerate(TEXT_GENRES.items()):
        ax.scatter([i]*6, vec, s=60, alpha=0.8, edgecolors="white",
                   linewidth=0.3, zorder=5)
        # Connect with line
        ax.plot([i]*6, vec, color="gray", alpha=0.2, linewidth=0.5)
    ax.set_xticks(range(len(TEXT_GENRES)))
    ax.set_xticklabels(list(TEXT_GENRES.keys()), rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("Dimension Value (6D)")
    ax.set_title("Text Style (6D)")
    ax.grid(True, alpha=0.3, axis="y")

    # Image
    ax = axes[2]
    for i, (name, preset) in enumerate(IMAGE_PRESETS.items()):
        sv = IMAGE_SPACE.from_dict(preset)
        y_offset = 0
        for comp_name, color in [("detail", "#2e86c1"), ("color", "#e74c3c"),
                                  ("mood", "#2ecc71"), ("composition", "#f39c12")]:
            vals = sv[comp_name]
            for j, v in enumerate(vals):
                ax.scatter(x=i, y=y_offset + v * 0.25, color=color,
                           s=30, alpha=0.7, edgecolors="white",
                           linewidth=0.3)
            y_offset += 1
    ax.set_xticks(range(len(IMAGE_PRESETS)))
    ax.set_xticklabels(list(IMAGE_PRESETS.keys()), rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("Component Value")
    ax.set_title("Image Style (16D)")
    ax.grid(True, alpha=0.3, axis="y")

    plt.suptitle("Three Domains, One Mathematical Framework",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "05_three_domains.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def generate_figure_distance_matrix():
    """Figure 5.2: Style distance matrix."""
    print("\nGenerating Figure 5.2: Style Distance Matrix...")
    genres = list(TEXT_GENRES.keys())
    n = len(genres)
    vectors = [TEXT_SPACE.from_dict({"emphasis": TEXT_GENRES[name]})
               for name in genres]
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            matrix[i, j] = vectors[i].distance(vectors[j])

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(genres, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(genres, fontsize=8)
    ax.set_title("Style Distance Matrix (6D Text Space)")
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Euclidean Distance")
    # Annotate closest pair
    upper = matrix.copy()
    np.fill_diagonal(upper, 999)
    min_idx = np.unravel_index(upper.argmin(), upper.shape)
    print(f"  Closest: {genres[min_idx[0]]} <-> {genres[min_idx[1]]} "
          f"(dist={matrix[min_idx]:.3f})")
    max_idx = np.unravel_index(matrix.argmax(), matrix.shape)
    print(f"  Farthest: {genres[max_idx[0]]} <-> {genres[max_idx[1]]} "
          f"(dist={matrix[max_idx]:.3f})")
    plt.tight_layout()
    out = FIGURES_DIR / "05_style_distance.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def generate_figure_interpolation():
    """Figure 5.3: Style interpolation."""
    print("\nGenerating Figure 5.3: Style Interpolation...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: Ethics interpolation (Kantian -> Utilitarian)
    ax = axes[0]
    kantian = ETHICS_SPACE.from_dict(ETHICS_PRESETS["Kantian"])
    utilitarian = ETHICS_SPACE.from_dict(ETHICS_PRESETS["Utilitarian"])
    ts = np.linspace(0, 1, 11)
    for t in ts:
        interp = kantian.lerp(utilitarian, t)
        mf = interp["moral_frame"]
        for j, (v, label) in enumerate(zip(mf, interp.space.components[0].labels)):
            alpha = 0.2 + 0.8 * (1 - abs(t - v))
            ax.scatter(t, v, color=["#2ecc71","#3498db","#e67e22","#9b59b6"][j],
                       s=80, alpha=alpha, edgecolors="white", linewidth=0.3)
    ax.set_xlabel("Interpolation t (0=Kantian, 1=Utilitarian)")
    ax.set_ylabel("Moral Frame Value")
    ax.set_title("Ethics: Kantian -> Utilitarian")
    ax.grid(True, alpha=0.3)
    ax.legend(["deontological", "consequentialist", "virtue", "care"],
              fontsize=8, loc="center right")

    # Right: Text interpolation
    ax = axes[1]
    roman = TEXT_SPACE.from_dict({"emphasis": TEXT_GENRES["Roman History"]})
    comedy = TEXT_SPACE.from_dict({"emphasis": TEXT_GENRES["Comedy"]})
    ts = np.linspace(0, 1, 11)
    emph_names = TEXT_SPACE.components[0].labels
    colors = ["#2ecc71", "#3498db", "#e74c3c", "#e67e22", "#9b59b6", "#f39c12"]
    for t in ts:
        interp = roman.lerp(comedy, t)
        emph = interp["emphasis"]
        for j, (v, label) in enumerate(zip(emph, emph_names)):
            ax.scatter(t, v, color=colors[j], s=80,
                       alpha=0.3 + 0.7 * abs(v - 0.5) * 2,
                       edgecolors="white", linewidth=0.3)
    ax.set_xlabel("Interpolation t (0=Roman, 1=Comedy)")
    ax.set_ylabel("Emphasis Value")
    ax.set_title("Text: Roman History -> Comedy")
    ax.grid(True, alpha=0.3)
    ax.legend(emph_names, fontsize=7, loc="center right")

    plt.tight_layout()
    out = FIGURES_DIR / "05_style_interpolation.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def generate_figure_three_universals():
    """Figure 5.4: Three Universals."""
    print("\nGenerating Figure 5.4: Three Universals...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    colors_u = {"phi": "#d4a017", "cognitive": "#2ecc71", "hardware": "#3498db"}

    # phi-universality
    ax = axes[0]
    ax.set_facecolor("#fafafa")
    ax.text(0.5, 0.75, "phi (golden ratio)", ha="center", fontsize=14,
            fontweight="bold", color=colors_u["phi"], transform=ax.transAxes)
    ax.text(0.5, 0.55, "Universal QUANTIZATION", ha="center", fontsize=11,
            transform=ax.transAxes)
    ax.text(0.5, 0.40, "value = sign x phi^(e/k)", ha="center", fontsize=10,
            fontfamily="monospace", transform=ax.transAxes)
    ax.text(0.5, 0.25, "Works for: ANY data\nEvidence: DA2, zeta zeros,"
            "phi-lattice", ha="center", fontsize=9,
            transform=ax.transAxes)
    ax.text(0.5, 0.10, "Most irrational number\nOptimal multiplicative "
            "coordinate", ha="center", fontsize=8, color="gray",
            transform=ax.transAxes)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # Cognitive universality
    ax = axes[1]
    ax.set_facecolor("#fafafa")
    ax.text(0.5, 0.75, "4 (quaternion)", ha="center", fontsize=14,
            fontweight="bold", color=colors_u["cognitive"], transform=ax.transAxes)
    ax.text(0.5, 0.55, "Universal HUMAN CATEGORIES", ha="center", fontsize=11,
            transform=ax.transAxes)
    ax.text(0.5, 0.40, "4 semantic components\ntext | ethics | images",
            ha="center", fontsize=10, transform=ax.transAxes)
    ax.text(0.5, 0.25, "Works for: Human-designed systems\nNOT for: "
            "Learned representations", ha="center", fontsize=9,
            transform=ax.transAxes)
    ax.text(0.5, 0.10, "Identity, possession, action, transition\n"
            "= 4 independent semantic axes", ha="center", fontsize=8,
            color="gray", transform=ax.transAxes)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # Hardware universality
    ax = axes[2]
    ax.set_facecolor("#fafafa")
    ax.text(0.5, 0.75, "2^n (powers of 2)", ha="center", fontsize=14,
            fontweight="bold", color=colors_u["hardware"], transform=ax.transAxes)
    ax.text(0.5, 0.55, "Universal HARDWARE", ha="center", fontsize=11,
            transform=ax.transAxes)
    ax.text(0.5, 0.40, "16D, 32D, 64D, 128D\nGPU SIMD alignment",
            ha="center", fontsize=10, transform=ax.transAxes)
    ax.text(0.5, 0.25, "Works for: ANY computation\nConstraint: "
            "Engineering, not math", ha="center", fontsize=9,
            transform=ax.transAxes)
    ax.text(0.5, 0.10, "Memory alignment, SIMD width\n"
            "Efficient, but not fundamental", ha="center", fontsize=8,
            color="gray", transform=ax.transAxes)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    plt.suptitle("The Three Universals: Different Kinds, Different Domains",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "05_three_universals.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("Section 05: Style Is Geometry\n")
    print("=" * 60)

    # 1. Three domains demo
    print("\n1. Domain Demonstrations")
    print("-" * 40)

    # Ethics
    eth_gen = EthicsGenerator()
    kantian = ETHICS_SPACE.from_dict(ETHICS_PRESETS["Kantian"])
    result = eth_gen.generate(kantian, "Trolley Problem")
    print(f"\n  Ethics: {result['framework']} ({result['scope']})")
    print(f"  {result['recommendation'][:80]}...")

    # Text
    text_gen = TextStyleGenerator()
    roman = TEXT_SPACE.from_dict({"emphasis": TEXT_GENRES["Roman History"]})
    print(f"\n  Text: {text_gen.generate(roman, 'Julius Caesar')}")

    # Lerp demo
    gothic = TEXT_SPACE.from_dict({"emphasis": TEXT_GENRES["Gothic Novel"]})
    philo = TEXT_SPACE.from_dict({"emphasis": TEXT_GENRES["Philosophy"]})
    d = gothic.distance(philo)
    print(f"  Gothic <-> Philosophy distance: {d:.3f}")
    mid = gothic.lerp(philo, 0.5)
    print(f"  Midpoint -> Gothic: {mid.distance(gothic):.3f}")
    print(f"  Midpoint -> Philosophy: {mid.distance(philo):.3f}")

    # Image
    img_gen = ImageStyleGenerator()
    noir = IMAGE_SPACE.from_dict(IMAGE_PRESETS["Noir"])
    result_img = img_gen.generate(noir, "City street at night")
    print(f"\n  Image: {result_img['style']} (dist={result_img['distance']:.2f})")
    print(f"  Filters: {result_img['recommendations']}")

    # 2. Distance matrix validation
    print("\n\n2. Style Distance Validation")
    print("-" * 40)
    genres = list(TEXT_GENRES.keys())
    for i, g1 in enumerate(genres):
        for j, g2 in enumerate(genres):
            if i < j:
                v1 = TEXT_SPACE.from_dict({"emphasis": TEXT_GENRES[g1]})
                v2 = TEXT_SPACE.from_dict({"emphasis": TEXT_GENRES[g2]})
                d = v1.distance(v2)
                if d < 1.5 or d > 3.0:
                    print(f"  {g1:>15} <-> {g2:<15}  dist={d:.3f}")

    # 3. Figures
    print("\n\n3. Generating Figures")
    print("-" * 40)
    generate_figure_domains()
    generate_figure_distance_matrix()
    generate_figure_interpolation()
    generate_figure_three_universals()

    print(f"\n{'=' * 60}")
    print("Done. All figures generated.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
