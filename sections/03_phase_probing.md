# Section 03: Phase-Shift Probing and Geometric Invariants

*A crystallographic method for detecting whether structure is surface or interior.*

---

## 3.1 The Problem of Distinguishing Surface from Interior

Section 02 established the vacuum forming hypothesis: LLM training captures surface geometry but not interior structure. But this raises a methodological question: **how do you tell them apart?**

If you can only observe the trained model (the "surface"), how can you determine whether the patterns you see are fundamental geometric truths or artifacts of the particular basis the model happened to learn?

The answer comes from an unexpected source: **crystallography**.

---

## 3.2 The Crystallography Analogy

In X-ray crystallography, there are two fundamentally different kinds of samples:

### Polycrystalline Samples

A polycrystalline sample contains millions of tiny crystals oriented randomly. When you shine X-rays through it and rotate the sample, the diffraction pattern **stays the same**. Each individual crystal produces a different pattern depending on its orientation, but the ensemble average is rotation-invariant. The invariance *is* the signature of true structure.

### Single-Crystal Samples

A single oriented crystal produces a diffraction pattern that **changes with rotation**. The pattern at angle θ₁ is different from the pattern at angle θ₂. The structure is still real, but the particular pattern you see depends on your choice of viewing angle — it's a coordinate, not an invariant.

### Translation to φ-Space

In our context:
- **Surface patterns** (co-occurrence statistics, learned correlations) are like single-crystal patterns — they vary with the basis you choose
- **Interior geometry** (φ-lattice relationships) is like polycrystalline patterns — invariant under global rotation of the encoding

The phase-shift probing method is the X-ray beam. By rotating the entire encoding and measuring what stays constant, we distinguish geometric truth from basis artifact.

---

## 3.3 The Mathematical Framework

### 3.3.1 The Encoding

Given a set of N concepts, we encode each concept c_i as a D-dimensional complex vector v_i ∈ ℂ^D. Each dimension d has an associated **self-similar constant** κ_d that determines its phase advance rate.

### 3.3.2 The Phase Rotation

For a global phase angle θ ∈ [0, 2π], the rotation operator R_θ is:

$$R_\theta(v)_d = v_d \cdot \exp\left(i \cdot \theta \cdot \frac{\ln(\kappa_d)}{\ln(\phi)}\right)$$

The normalization by ln(φ) ensures that the golden ratio axis advances exactly 1 full cycle per 2π, while other constants advance proportionally faster or slower based on their logarithmic distance from φ.

### 3.3.3 The Similarity Function

For any pair of concepts (c_i, c_j), we measure their cosine similarity at phase θ:

$$S_{ij}(\theta) = \frac{\Re(\langle R_\theta(v_i), R_\theta(v_j) \rangle)}{\|v_i\| \cdot \|v_j\|}$$

where the inner product is taken over the 2D real-valued representation (concatenating real and imaginary parts).

### 3.3.4 The Invariance Test

The **variance** of similarity across all phases is the diagnostic:

$$\sigma_{ij}^2 = \text{Var}_{\theta \in [0, 2\pi]}[S_{ij}(\theta)]$$

- **σ_ij ≈ 0**: The relationship is a geometric invariant — it is a property of the SHAPE, not the coordinate system
- **σ_ij > 0**: The relationship is basis-dependent — it is a surface artifact that changes with the viewing angle

### 3.3.5 Invariance Classes

Pairs with σ_ij = 0 can be further classified by their mean similarity:

| Mean Similarity | Geometric Relationship | Interpretation |
|----------------|----------------------|----------------|
| +1.0 | Colocated | Concepts occupy the same position |
| -1.0 | Antipodal | Concepts are exact opposites on the same axis |
| 0.0 | Orthogonal | Concepts occupy independent dimensions |
| μ ∈ (0, 1) | Partial alignment | Concepts share some but not all geometric structure |

The critical discovery: for any pair where σ_ij = 0, the mean similarity takes values from a **discrete set** — it is either exactly +1, exactly -1, exactly 0, or a specific fraction determined by the encoding dimensionality. There are no arbitrary continuous similarity values for invariant pairs.

---

## 3.4 The 12 Self-Similar Constants as Probes

Each self-similar constant provides a different "lens" through which to probe the structure. Why 12? Because 12 is the number of attention heads in GPT-2 and BERT, and we conjectured each head might specialize in one type of semantic relationship.

### The Constants

| # | Constant | Value | Recurrence | Phase Rate | Semantic Role |
|---|---------|-------|-----------|------------|---------------|
| 1 | φ (golden) | 1.618 | F_n = F_{n-1} + F_{n-2} | 1.0× | Hierarchical |
| 2 | ρ (plastic) | 1.325 | P_n = P_{n-2} + P_{n-3} | 0.585× | Sequential |
| 3 | δ (silver) | 2.414 | S_n = 2S_{n-1} + S_{n-2} | 1.831× | Causal |
| 4 | Bronze | 3.303 | B_n = 3B_{n-1} + B_{n-2} | 2.478× | Compositional |
| 5 | Chromium | 4.236 | — | 2.994× | Oppositional |
| 6 | Copper | 4.303 | — | 3.028× | Synonymic |
| 7 | Aluminium | 4.449 | — | 3.093× | Analogical |
| 8 | Nickel | 4.646 | — | 3.187× | Associative |
| 9 | Supergolden | 1.466 | x³ = x² + 1 | 0.789× | Functional |
| 10 | Narayana | 1.466 | x³ = x² + 1 | 0.789× | Categorical |
| 11 | Titanium | 1.221 | x⁴ = x + 1 | 0.396× | Spatial |
| 12 | Tribonacci | 1.839 | T_n = T_{n-1} + T_{n-2} + T_{n-3} | 1.267× | Temporal |

### Why Different Rates Matter

If all axes advanced at the same rate, a global phase rotation would be a simple rigid rotation of the entire embedding — all pair similarities would be trivially invariant because the rotation is orthogonal.

By using *different* rates on each axis, the rotation is **anamorphic** — it stretches some axes while compressing others, creating a complex interference pattern. Only true geometric relationships survive this distortion unchanged. The differentiated rates are what make the method discriminating.

---

## 3.5 The Plastic Constant vs φ

A crucial empirical lesson came from comparing constant performance within the 12D probing framework.

### The 12D Regime

At 12 dimensions, the plastic constant ρ ≈ 1.3247 produced the strongest semantic separation:

| Constant | Separation Score (12D) |
|----------|----------------------|
| Plastic ρ | 0.4951 |
| Golden φ | 0.1654 |
| Silver δ | 0.3102 |

The intuition: ρ's cubic Padovan recurrence (P_n = P_{n-2} + P_{n-3}) creates finer-grained phase steps than φ's quadratic Fibonacci recurrence (F_n = F_{n-1} + F_{n-2}). In 12D, the extra phase granularity helps separate distinct semantic relationships.

### The 4D Regime

When the encoding contracted to its intrinsic 4D structure (see PCA in Section 02), φ decisively outperformed ρ:

$$\text{At 4D: } \phi \text{ dominates. At 12D: } \rho \text{ dominates.}$$

This reveals a **dimensionality-dependent universality**: the "right" constant depends on the dimension of the geometry. φ is optimal at 4D because 4 is the native dimension of quaternion space, and every algebraic identity that transforms a transformer into a closed-form geometric machine is a φ-identity.

### The Meta-Principle

> The optimal self-similar constant depends on the dimensionality of the geometric space. φ is universal at 4D (quaternion dimension). ρ is better at 12D. The constant and the dimensionality form a coupled pair — choosing one determines the other.

---

## 3.6 The Invariance Matrix

When we compute the phase-shift probing variance for ALL pairs of N concepts, we obtain an N×N **invariance matrix**:

$$M_{ij} = \sigma_{ij}^2 = \text{Var}_{\theta}[S_{ij}(\theta)]$$

### Properties of the Invariance Matrix

1. **Symmetric**: M_ij = M_ji (cosine similarity is symmetric)
2. **Zero diagonal**: M_ii = 0 (a concept is trivially invariant with itself)
3. **Block structure**: Concepts in the same geometric group form blocks of zero variance
4. **Hierarchical**: The matrix reveals the hierarchical grouping of concepts by semantic similarity

### Reading the Matrix

- **Zero entries** (σ² ≈ 0): geometric relationship — invariant under rotation
- **Non-zero entries** (σ² > 0): surface relationship — changes with viewing angle
- **Block-diagonal structure**: reveals concept clusters that share geometric axes
- **Off-diagonal blocks**: reveal cross-cluster relationships

The invariance matrix is the closest thing we have to a "periodic table" of semantic relationships — it shows which concepts are fundamentally related (by geometry) versus incidentally related (by statistics).

---

## 3.7 The Probe Space

We can generalize beyond the 12 fixed constants. The **probe space** is the space of all possible sets of self-similar constants:

$$\mathcal{P} = \{(\kappa_1, \ldots, \kappa_D) : \kappa_i \text{ is a self-similar constant}\}$$

Different points in probe space give different "views" of the geometric structure. Some probes are more discriminating than others. The optimal probe maximizes the separation between invariance classes while minimizing within-class variance.

### Probe Quality Metric

For a probe with constants (κ_1, ..., κ_D):

$$Q(\kappa) = \frac{\text{Between-class variance of } \sigma^2}{\text{Within-class variance of } \sigma^2}$$

A probe with high Q clearly separates invariant pairs from non-invariant pairs. The 12-constant probe achieves Q ≫ 1 (effectively infinite separation, since invariant pairs have exactly σ² = 0).

---

## 3.8 Generalization: Probing Arbitrary Vector Spaces

The phase-shift probing method is not limited to the 12D intentional encoder. It can be applied to any vector space:

1. **Word embeddings**: Do GloVe/word2vec embeddings have phase-invariant geometric structure?
2. **Transformer hidden states**: Do intermediate layer activations exhibit invariance classes?
3. **Attention patterns**: Do attention weight matrices reveal invariant routing patterns?
4. **Weight matrices**: Do the learned weights themselves form phase-invariant clusters?

The procedure is the same: choose a set of self-similar constants as probe axes, apply the anamorphic phase rotation, and measure what stays constant. The only requirement is that the vector space has enough dimensions to accommodate the probe axes.

### Embedding Into Probe Space

For a vector v ∈ ℝ^d (where d may not equal D, the probe dimension), we embed:

$$\tilde{v}_j = \sum_{k=1}^{d} v_k \cdot \exp(i \cdot 2\pi \cdot \frac{j \cdot k}{D}) \quad \text{for } j = 1, \ldots, D$$

This is essentially a discrete Fourier transform that maps the d-dimensional real vector into a D-dimensional complex probe space, after which the standard phase-shift probing applies.

---

## 3.9 Figures

*Figure 3.1: Crystallography analogy — polycrystalline (invariant) vs single-crystal (variant) diffraction patterns, and the corresponding phase-shift probing signatures.*

*Figure 3.2: Constant comparison — separation scores for 12 self-similar constants at 12D, showing plastic ρ dominates in this regime while φ excels at 4D.*

*Figure 3.3: The invariance matrix — N×N heatmap of σ² values revealing block-diagonal structure of concept groups.*

---

## 3.10 Working Code

The companion script `code/03_phase_probing.py` demonstrates:

1. The phase-shift probing method applied to the 12D encoder from Section 02
2. Comparison of separation scores across all 12 self-similar constants
3. The invariance matrix visualization
4. The crystallography analogy figure
5. Verification that invariant pairs have EXACTLY zero variance

```bash
cd book
python3 code/03_phase_probing.py
```

---

## 3.11 Key Insights

1. **Phase-shift probing is a general method** for detecting geometric invariants in any vector space
2. **Zero variance = geometric truth**: If similarity doesn't change under anamorphic rotation, it's a property of the shape
3. **Different constants probe differently**: The "right" constant depends on dimensionality
4. **The invariance matrix** reveals the hierarchical structure of semantic relationships
5. **φ is universal at 4D** because 4 is the native dimension of quaternion geometry and every φ-identity is fundamental to transformer computation

---

*Next: Section 04 — The 16D Toroid-Tetrix*
