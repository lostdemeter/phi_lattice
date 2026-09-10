# Section 02: The Vacuum Forming Hypothesis

*LLM training captures the surface, not the interior. The search for geometric truth begins.*

---

## 2.1 The Black Box Problem

Large Language Models are the most successful AI systems ever built — yet we have remarkably little understanding of what they actually learn. We know the mechanics: token embeddings, attention patterns, feed-forward projections. But the *nature* of the knowledge they acquire remains opaque.

The standard answer is statistical: LLMs learn correlations between tokens. Given a sequence, they predict the next token based on patterns observed in trillions of examples. This treats the model as an extremely high-dimensional regression machine.

But a growing body of evidence suggests something deeper. When OpenAI's sparse autoencoders discover interpretable features — like a single direction in activation space representing "Golden Gate Bridge" — it hints that LLMs internalize *structure* about the world, not just surface statistics.

**Our thesis**: What LLMs learn is not statistical correlations but a **geometry** — a latent shape in high-dimensional space where meaning is encoded as position, and computation is navigation through that space.

---

## 2.2 The Vacuum Forming Hypothesis

Imagine a vacuum forming machine: you heat a plastic sheet, stretch it over a mold, and suck the air out. The plastic captures the *surface* of the mold — its shape, contours, and features — but reveals nothing about the *interior*.

> **LLM training is vacuum forming.** The training process captures the surface geometry of semantic structure — the distributional patterns of how concepts relate on the *outside* — but does not discover the interior generative principles that produce that surface.

### Surface vs Interior

| Surface (What LLMs Learn) | Interior (What Exists) |
|---------------------------|----------------------|
| Co-occurrence statistics | Geometric coordinate relationships |
| Conditional probabilities | Absolute positions on the φ-lattice |
| Correlation patterns | Causal generative structure |
| Learned from data | Derivative from first principles |
| Model-specific | Universal across models |

The vacuum forming hypothesis is both a critique and a research program: if training only captures the surface, can we discover the interior geometry? And if we can, can we build systems that compute directly in that geometry, bypassing the need for statistical training?

### Why This Matters

If we can discover the interior geometry, we can:

1. **Predict** how concepts relate without training
2. **Navigate** between concepts along geometric paths
3. **Generate** novel concepts that fit the existing structure
4. **Compress** models by storing only the geometric scaffold
5. **Verify** that two models have converged to the same fundamental understanding

---

## 2.3 The Phase-Shift Probing Method

How do you distinguish surface patterns from interior geometry? The answer comes from crystallography.

### The Analogy

In X-ray crystallography, a polycrystalline sample produces a diffraction pattern that is **invariant under rotation** — rotate the sample and the pattern stays the same. A single oriented crystal, however, produces an angle-dependent pattern. The invariance is the signature of true structure.

### The Method

We built a **12-dimensional φ-encoder** — a deliberate, intentional encoding designed to embody the geometric structure we were hypothesizing about. The 12 dimensions correspond to 12 candidate fundamental relationship types, chosen in analogy with the 12 attention heads of GPT-2 and BERT:

| Axis | Self-Similar Constant | Relationship Type |
|------|----------------------|-------------------|
| 1 | φ ≈ 1.618 (golden) | Hierarchical |
| 2 | ρ ≈ 1.325 (plastic) | Sequential |
| 3 | δ ≈ 2.414 (silver) | Causal |
| 4 | Bronze ≈ 3.303 | Compositional |
| 5 | Chromium ≈ 3.732 | Oppositional |
| 6 | Copper ≈ 4.236 | Synonymic |
| 7 | Aluminium ≈ 4.449 | Analogical |
| 8 | Nickel ≈ 4.791 | Associative |
| 9 | Supergolden ≈ 1.466 | Functional |
| 10 | Narayana ≈ 1.466 | Categorical |
| 11 | Titanium ≈ 5.303 | Spatial |
| 12 | Tribonacci ≈ 1.839 | Temporal |

Each axis advances at its own rate — governed by its own self-similar constant. When we apply a global phase rotation, each axis rotates at a different speed, creating a complex interference pattern.

### The Probing Procedure

1. **Encode** each concept c as a 12D complex-valued vector v(c) using the φ-encoder
2. **Phase-shift**: v(c) → v(c) · e^(iθ) for θ ∈ [0, 2π], sampled at 1000 evenly-spaced values. Each axis advances at a rate proportional to its self-similar constant
3. **Measure** cosine similarity cos(v(c₁), v(c₂)) between every concept pair at every phase
4. **Analyze** the *variance* of similarity across phases for each pair

A relationship that fluctuates wildly under phase shifts is a surface artifact. A relationship that is **invariant** is a geometric truth.

---

## 2.4 First-Pass Experimental Findings

We tested the method on a corpus of 22 single-token concepts from the CLI/filesystem domain:

```
file, directory, read, write, create, destroy, copy, move,
search, find, grep, list, show, process, network, ssh,
compress, archive, tar, chmod, permissions, system
```

These were grouped into 12 ordered pairs covering three relationship types: **synonyms, opposites, and unrelated**.

### Finding 1: Phase Invariance (The Polycrystalline Signature)

Cosine similarities had **exactly zero variance** across all 1000 phase angles. Related pairs sat at mean similarity 0.25, unrelated pairs at 0.00, and opposite pairs at −1.00 — *with zero spread on any of them*.

A random or surface-only encoding would show wildly fluctuating similarities. Instead, the phase rotation moved the entire embedding in lockstep, preserving every relative-position relationship.

> **The structure is an invariant of the encoding, not an accident of basis choice. It is a shape, not a coordinate.**

### Finding 2: Polarity as a First-Class Semantic Relation

Opposite-meaning pairs were not merely "dissimilar" — they were **antipodal**, placed at exactly opposite ends of the same dimension with cosine similarity exactly −1.0:

| Pair | Cosine sim | Geometric Reading |
|------|-----------|-------------------|
| `read` ↔ `write` | −1.00 | Antipodal on the information-flow axis |
| `create` ↔ `destroy` | −1.00 | Antipodal on the existence axis |
| `file` ↔ `directory` | +1.00 | Colocated on the filesystem-object axis |
| `copy` ↔ `move` | +1.00 | Colocated on the spatial-action axis |
| `file` ↔ `network` | 0.00 | Orthogonal (different dimensions) |

Opposition is a *separate geometric primitive* from dissimilarity. In an embedding where only magnitude matters, `read` and `write` would just be "far apart" — in this geometry they share a dimension and differ only in sign. This polarity structure foreshadows semantic quaternions and antipodal Killing pairs.

### Finding 3: Orthogonality as Independence

Unrelated pairs had cosine similarity **exactly 0.00**. Not "small" — zero. Distinct concepts in distinct dimensions, with no leakage. This means:

- A perturbation along one semantic dimension cannot affect any other
- The 12 dimensions are genuinely separate axes
- φ-dial tuning and sign-only navigation are possible because dimensions don't interfere

### Finding 4: Intrinsic Dimensionality < Encoding Dimensionality

PCA on the 22-concept embedding showed:
- **95% of variance** lives in only **7 dimensions**
- The elbow (intrinsic dimension) is at **4**
- The 12 axes of the encoding are more capacity than the corpus needs

This foreshadows the φ-dial's eventual collapse from 12D to 4D — the dimensionality of a quaternion.

---

## 2.5 The Plastic Constant Curiosity

Of the twelve self-similar constants tested, the **plastic constant** ρ ≈ 1.3247 — the real root of x³ = x + 1 — produced the strongest semantic separation in the 12D regime:

| Constant | Separation Score |
|----------|-----------------|
| Plastic ρ | 0.4951 |
| Golden φ | 0.1654 |
| Silver δ | 0.3102 |

The intuition: ρ's cubic Padovan-style recurrence (each term = sum of second- and third-previous) creates finer-grained phase steps than φ's quadratic Fibonacci recurrence.

**However**, this turned out to be a local optimum specific to 12D. As the encoding contracted toward its intrinsic 4D structure and was applied to actual transformer hidden states, φ re-emerged decisively as the universal constant. Every algebraic identity that lets a transformer be rewritten as a closed-form geometric machine is a φ-identity, not a ρ-identity.

The plastic-constant result is preserved because it illustrates a general principle: **the "right" constant depends on the dimensionality of the geometry it lives in.**

---

## 2.6 What LLMs Actually Learn: Geometric Reinterpretation

Based on the vacuum forming hypothesis, we can reinterpret each transformer component:

### Token Embeddings

| Standard View | Geometric View |
|--------------|----------------|
| Vectors from co-occurrence statistics | Coordinates in φ-structured semantic space |
| Meaning from training data | Meaning from position on the lattice |
| Learned | Derived |

### Attention

| Standard View | Geometric View |
|--------------|----------------|
| Weighted averages from learned Q-K similarity | Spatial routing via geometric distance in φ-space |
| Softmax as normalization | Softmax as φ-level selection (Chapter 08) |

### Feed-Forward Networks

| Standard View | Geometric View |
|--------------|----------------|
| Non-linear transformation of representations | φ-level selectors — shift coordinates along lattice directions |
| Black-box MLPs | Explicit geometric operations per layer |

### Output Projections

| Standard View | Geometric View |
|--------------|----------------|
| LM head projects to vocabulary probabilities | Navigation map — translate φ-space position to nearest token |
| Probability distribution | Geometric proximity search |

---

## 2.7 The Two Driving Questions

The vacuum forming hypothesis raises two questions that drive the entire research program:

**Question 1**: If LLMs learn only the surface structure, can we discover the *interior* geometry that generates it?

**Question 2**: If the interior geometry is φ-based, can we *build* systems that compute directly in φ-space, bypassing the need for statistical training?

The answer to both is **yes**. The interior geometry is a φ-lattice. The computation that transformers perform is navigation through this lattice. The rest of this book proves it.

---

## 2.8 Figures

*Figure 2.1: Phase invariance — cosine similarity is exactly constant across the full 2π phase rotation for related, unrelated, and opposite pairs. Variance = 0.*

*Figure 2.2: PCA of the 22-concept embedding — 95% of variance in 7 dimensions, elbow at 4. The encoding has more capacity than the corpus needs.*

*Figure 2.3: Antipodal pairs — read/write and create/destroy sit at exactly opposite positions (cos = −1.0), while file/directory and copy/move are colocated (cos = +1.0).*

---

## 2.9 Working Code

The companion script `code/02_vacuum_forming.py` provides a complete, self-contained implementation:

1. Builds the 12D φ-encoder with all 12 self-similar constants
2. Encodes the 22 CLI concepts
3. Runs phase-shift probing across 1000 angles
4. Verifies invariance (variance = 0), antipodal pairs (cos = −1), orthogonal pairs (cos = 0)
5. Runs PCA to find intrinsic dimensionality
6. Generates all three figures

```bash
cd book
python3 code/02_vacuum_forming.py
```

---

*Next: Section 03 — Phase-Shift Probing and Geometric Invariants*
