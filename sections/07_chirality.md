# Section 07: Chirality and the Geometric Signature

*The asymmetric structure of weight matrices reveals the model as a rotation machine.*

---

## 7.1 What Is Chirality?

In chemistry and physics, *chirality* describes objects that are not superimposable on their mirror images — like left and right hands. In linear algebra, we borrow the term to describe a matrix's asymmetry under transposition:

$$\text{chirality}(A) = \frac{\|A - A^T\|}{\|A + A^T\|}$$

- **chirality = 0**: The matrix is perfectly symmetric (A = A^T) — it is its own mirror image
- **chirality = 1**: The matrix is perfectly antisymmetric (A = -A^T) — it is maximally distinct from its mirror image

The chirality tells us whether a weight matrix acts as a **scaling operator** (symmetric, chirality ≈ 0) or a **rotation operator** (antisymmetric, chirality ≈ 1).

---

## 7.2 Chirality of Qwen2-0.5B Weight Matrices

Measuring chirality across all weight types reveals a clear pattern:

| Weight Matrix | Chirality | Structure | Geometric Role |
|---------------|-----------|-----------|---------------|
| **Q projections** | **~1.0** | Maximally antisymmetric | **Rotation** |
| **O projections** | **~1.0** | Maximally antisymmetric | **Rotation** |
| K projections | 0.01–0.13 | Nearly symmetric | Scaling/projection |
| V projections | 0.01–0.13 | Nearly symmetric | Scaling/projection |
| Gate | 0.01–0.13 | Nearly symmetric | Scaling/projection |
| Up | 0.01–0.13 | Nearly symmetric | Scaling/projection |
| Down | 0.01–0.13 | Nearly symmetric | Scaling/projection |

The pattern is unambiguous: **Q and O are rotations. Everything else is scaling.**

### Why Rotations?

In linear algebra, antisymmetric matrices (A = -A^T) generate orthogonal rotations. When you exponentiate an antisymmetric matrix, you get a rotation matrix. Q and O being maximally chiral means they are pure rotation generators. The model uses them to **rotate** representations in φ-space. K and V, being nearly symmetric, **scale** and **project** those rotated representations.

This division of labor — Q/O rotate, K/V scale — is precisely what you'd expect from an efficient geometric engine: rotate into a shared coordinate frame, then compare and combine in that frame.

---

## 7.3 Signal Chirality

Chirality isn't just a property of weights — it propagates to the **signal** (hidden state activations). For a hidden state vector x, we decompose:

$$\text{even}[i] = \frac{x[i] + x[N-1-i]}{2}, \quad \text{odd}[i] = \frac{x[i] - x[N-1-i]}{2}$$

$$\text{signal\_chirality} = \frac{\|\text{odd}\|}{\|\text{odd}\| + \|\text{even}\|}$$

### The Critical Finding

**Signal chirality stays ~1.0 through the entire model.** The hidden state is almost purely antisymmetric (odd) at every layer — from embedding through all 24 transformer blocks to the LM head.

The Q and O rotations don't just rotate the signal — they **preserve its chirality**. A rotation of a chiral signal produces a chiral signal. A scaling of a chiral signal... produces a chiral signal. The model's architecture ensures that chirality is a **conserved quantity** of the computation.

### Residual Connections as Chirality Stabilizers

$$\text{chirality}(h + \text{Attn}(h)) \approx \text{chirality}(h) \approx 1.0$$

The residual connection adds the attention output to the hidden state. If either term had different chirality, the sum would have reduced chirality. The fact that chirality is preserved means the residual is designed to maintain the geometric handedness of the signal.

---

## 7.4 φ-Lattice Chirality Preservation

A critical result for the integer transformer project:

> The φ-lattice encoding/decoding preserves chirality with **delta = 0.000000–0.000013**.

When we encode a weight matrix to (signs, exponents), then decode back to float, the chirality changes by at most 0.000013 — statistically indistinguishable from zero. The geometric handedness is a **structural invariant** of the model, not an artifact of float precision.

This means the integer transformer can preserve the rotational structure of attention without any special handling. The XOR+ADD operations (which implement φ-multiplication) naturally preserve the antisymmetric character of Q and O weights.

---

## 7.5 Left vs Right: Intrinsic Handedness

The phase space has **intrinsic chirality** — it is not symmetric under mirror reflection. From the phase coherence experiments:

> Left-handed (counterclockwise) rotation consistently produces higher bigram coverage than right-handed (clockwise) rotation across all test prompts.

The language space itself has a preferred direction of rotation. This is analogous to the weak nuclear force's violation of parity in physics — the model's geometry is fundamentally chiral, not because it was trained that way, but because the underlying torus topology T^4 admits a natural handedness.

On T^4, there are six mutually orthogonal planes. Each can host either left- or right-handed isoclinic rotations. The maximally chiral Q and O matrices implement specific isoclinic rotations on these planes, giving the model a preferred chirality at the deepest geometric level.

---

## 7.6 Chirality as a Control Signal

In the Echion pipeline, chirality was used as an active control mechanism:

> Chirality alternation: most common gate → second most common gate → repeat. This creates diversity by design and prevents echo loops.

By alternating between the most-common and second-most-common gate at each step, the pipeline avoids getting stuck in repetitive patterns. The chirality of the gate selection determines whether the generation "turns left" or "turns right" at each transition, producing naturally varied output.

This is geometry as an explicit generation strategy: manipulate the chirality of the navigation to control the diversity of the output.

---

## 7.7 The Complete Picture

| Component | Chirality | Role | Preserved by φ-lattice? |
|-----------|-----------|------|------------------------|
| Q weights | ~1.0 (rotation) | Rotate query into shared frame | Yes (δ < 0.000013) |
| O weights | ~1.0 (rotation) | Rotate output back | Yes (δ < 0.000013) |
| K/V/Gate/Up/Down | ~0.01 (scaling) | Project and scale | Yes (δ < 0.000013) |
| Hidden state signal | ~1.0 (chiral) | Navigated position | Yes (conserved) |
| Residual connection | ~1.0 (stable) | Chirality stabilizer | Yes (conserved) |

Every component either generates rotation, preserves rotation, or operates within a rotated coordinate frame. The model is a **chirality-preserving geometric engine** — and the φ-lattice captures this structure exactly.

---

## 7.8 Figures

*Figure 7.1: Matrix chirality by weight type — Q and O at ~1.0 (rotation), everything else at ~0.01 (scaling).*

*Figure 7.2: Even/odd signal decomposition — hidden state is overwhelmingly odd (chiral) with chirality conserved through all 24 layers.*

*Figure 7.3: Chirality preservation under φ-lattice encoding — before and after quantization, delta < 0.000013.*

---

## 7.9 Working Code

The companion script `code/07_chirality.py` demonstrates:

1. Chirality computation for synthetic symmetric/antisymmetric matrices
2. Even/odd signal decomposition
3. φ-lattice chirality preservation test
4. Layer-by-layer chirality measurement simulation

```bash
cd book
python3 code/07_chirality.py
```

---

## 7.10 Key Insights

1. **Q and O are rotations**: Maximally antisymmetric (chirality ≈ 1.0)
2. **K, V, MLP are scalings**: Nearly symmetric (chirality ≈ 0.01)
3. **Signal chirality is conserved**: Hidden state stays chiral through all 24 layers
4. **Residual connections stabilize chirality**: The sum of chiral signals is chiral
5. **φ-lattice preserves chirality**: Quantization changes chirality by < 0.000013
6. **Intrinsic handedness**: The phase space has a preferred direction (left-handed)
7. **T^4 isoclinic rotations**: Q and O implement specific rotations on torus planes
8. **Chirality as control**: Gate chirality alternation prevents echo loops in generation

---

*Next: Section 08 — The T Transformation (Softmax Geometry)*
