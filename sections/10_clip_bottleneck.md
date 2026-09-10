# Section 10: The ±4096 Clip Bottleneck

*The dominant error source wasn't integer quantization — it was a hardcoded clip range inherited from the float reference.*

---

## 10.1 The Misleading Ceiling

For weeks, the integer transformer appeared to hit a hard ceiling at **corr = 0.985** with the float reference. This was interpreted as an irreducible quantization limit — the cost of discretizing continuous weights onto the φ-lattice. Every effort focused on reducing per-operation error: polynomial SiLU, lattice native RMSNorm, Fibonacci accumulation.

The ceiling was real. But it was measuring the wrong thing.

### The Actual Measurement Chain

The "float reference" was not the true PyTorch model. It was the `PhiEngine` — our own φ-lattice implementation running in float. Here is the actual chain:

```
True float (PyTorch)  ← corr=0.749 →  PhiEngine float reference
                                        ← corr=0.985 →  Integer chain
```

The integer chain closely matched the float reference (0.985). But the float reference was itself **severely degraded** from the true model (0.749). The integer chain's true correlation with the PyTorch model was only **0.704**. Most of the error we had been attributing to "integer quantization" was actually coming from the float reference's own built-in losses.

---

## 10.2 What the ±4096 Clip Does

Both `PhiEngine.matmul` (the float reference) and `phi_matmul_int` (the integer chain) share a common operation: clipping product exponents to the range [-4096, +4096] before decoding:

```python
# In PhiEngine.matmul:
me = np.clip(me, -4096, 4096)
c += phi_decode(ms, me, k=k).sum(axis=-2)

# In phi_matmul_int:
me = np.clip(me, -4096, 4096)
c += phi_decode(ms, me, k=k).sum(axis=-2)
```

### What This Means Mathematically

At k=256, the clip corresponds to a value range of:

$$\phi^{-4096/256} \leq \text{value} \leq \phi^{+4096/256}$$
$$\phi^{-16} \approx 0.000453 \leq \text{value} \approx 2210 \leq \phi^{+16}$$

Any product whose exponent falls outside ±4096 is truncated to the boundary. The information about **how far outside** the range the value was is destroyed. The clipped product contributes only φ^(±16) regardless of whether the true product was φ^(−17) or φ^(−30) — they're indistinguishable after clipping.

---

## 10.3 The Scale of Clipping

### At k=256

For a random 896×896 weight×weight matmul:

| Metric | Value |
|--------|-------|
| Product exponent range | [−13275, −2819] |
| Products clipped to −4096 | **656,423 / 802,816 (81.8%)** |
| Products within range | 146,393 / 802,816 (18.2%) |

**81.8% of all products are already clipped in the float reference.** Only 18.2% carry the actual signal. The clipped products all decode to the same value (φ^(−16) ≈ 0.000453), acting as a uniform soft floor.

The model still works despite this massive clipping because the clipped products are uniformly distributed across the K dimension and contribute roughly equally to the output sum. The surviving 18.2% carry **all the discrimination** between output values.

### At k=4096

When we increased the lattice resolution to k=4096 for higher precision, the situation became catastrophic:

| Quantity | k=256 | k=4096 |
|----------|-------|--------|
| Embedding exponents | [−36749, −869] | [−587977, −13901] |
| Product exponents | [−13275, −2819] | [−212404, −45096] |
| Products clipped to ±4096 | 81.8% | **100.0%** |

At k=4096, **every single product is clipped.** The surviving signal (the 18.2% at k=256) is gone. The integer chain and float reference diverge completely — **corr drops to 0.029**.

This was why the k=4096 experiments failed so spectacularly. The clip range of ±4096 is a design constant, not a tunable parameter. It was chosen to match a 4096-entry LUT in the PhiEngine's decode operation. When we increased k by 16×, the exponents scaled by 16× but the clip range stayed fixed, destroying all signal.

---

## 10.4 The Breakthrough: Removing the Clip

The solution was simple but profound: **remove the clip entirely.** Instead of `np.clip(me, -4096, 4096)`, let exponents flow through unbounded. Compute φ^(e/k) directly via `PHI ** (exps / k)` instead of via a clipped LUT.

| Configuration | vs True Float | Top-5 Overlap |
|--------------|---------------|---------------|
| Float with clip (PhiEngine reference) | 0.749 | 1/5 |
| Integer with clip (old baseline) | 0.704 | 1/5 |
| Float without clip | 0.749 | 1/5 |
| **Integer without clip** | **0.989** | **4/5** |

The integer chain without the clip achieves **0.989 correlation** with the true PyTorch model and gets **4/5 top-5 overlap** — a massive improvement from 0.704/1/5.

---

## 10.5 Why the Integer Chain Beats the Float Reference

This is a surprising and counterintuitive result: **the integer chain is more precise than the float reference.**

The reason is architectural:

**Float reference path:**
```
Float input → encode to (signs, exps) → matmul (clip!) → decode to float → ...
     ↑ quantization                                   ↑ quantization
```
The encode→decode cycle at every matmul introduces quantization error that compounds.

**Integer chain path:**
```
Float input → encode to (signs, exps) → matmul (no clip!) → stay in (signs, exps) → ...
     ↑ one-time                                    ↑ no decode
```
The integer chain keeps values in (signs, exponents) format throughout the entire forward pass. Values only decode once — at the very end, for the argmax token selection. No intermediate decode/encode cycles. No cumulative quantization error from repeated float conversion.

The clip was hiding the integer chain's true quality. By forcing both paths to agree on a lossy representation, it made them appear equally limited. Without the clip, the integer chain's superior precision shines through.

---

## 10.6 No Need to Increase k

At k=256 with no clip, the integer chain achieves 0.989 correlation. The remaining 0.011 gap comes from the intrinsic quantization step size (φ^(1/256) − 1 ≈ 0.00188), which is inherent to the lattice representation.

Increasing k would reduce this gap, but at the cost of:
- Larger exponent values (more bits per exponent)
- Wider LUTs (if any remain)
- More coefficient storage (2kD per value in coefficient mode)

The 0.989 at k=256 is already good enough for most purposes. The path to 1.0 is clear — just increase k — but the diminishing returns suggest k=256 is near the Pareto-optimal point.

---

## 10.7 What Actually Needs to Change

To fix this across the entire codebase:

1. **`phi_matmul_int`**: Remove `np.clip(me, -4096, 4096)`. The `phi_decode` function already handles arbitrary exponents via `PHI ** (exps / k)`.

2. **`PhiEngine.decode`**: Change from LUT-based decode to direct computation: `PHI ** (exps / k)`. The LUT is the source of the clip — it has only 4096 entries per direction.

3. **`PhiEngine.matmul`**: Already calls `self.decode`, so fixing decode fixes matmul too.

These two changes take the integer chain from 0.704 to 0.989 vs true float — **without changing anything else**. No new algorithms. No higher k. No polynomial approximations. Just removing a single line of code.

---

## 10.8 The Deeper Lesson

> **The integer chain is not the bottleneck. The float reference is.**

We had been optimizing the wrong thing. Every effort to improve integer quantization precision (higher k, polynomial SiLU, coefficient accumulation) was attacking a problem that was already solved. The real bottleneck was a legacy design choice — the ±4096 clip — inherited from the PhiEngine's LUT-based decode.

The lesson is methodological: **always measure against the true reference, not your own approximation of it.** The 0.985 ceiling was an artifact of measuring integer-vs-our-float-reference, not integer-vs-truth. The appearance of a precision ceiling was an illusion created by a shared lossy step.

---

## 10.9 Figures

*Figure 10.1: The measurement chain — true float → float reference (corr=0.749) → integer chain (corr=0.985), revealing the misplaced ceiling.*

*Figure 10.2: Clip impact at k=256 and k=4096 — exponent distributions showing 81.8% and 100% clipping respectively.*

*Figure 10.3: Before/after clip removal — integer-vs-true-float correlation jumping from 0.704 to 0.989.*

---

## 10.10 Working Code

The companion script `code/10_clip_bottleneck.py` demonstrates:

1. The measurement chain problem
2. Product exponent distribution and clip boundaries
3. The effect of clip removal on correlation
4. k-scaling analysis

```bash
cd book
python3 code/10_clip_bottleneck.py
```

---

## 10.11 Key Insights

1. **0.985 ceiling was an artifact**: Measuring against the wrong reference
2. **81.8% clipping at k=256**: Most products contribute zero information
3. **100% clipping at k=4096**: Explains why higher-k experiments failed
4. **Removing clip → 0.989**: Near-perfect correlation with true model
5. **Integer chain beats float reference**: Better precision from fewer decode/encode cycles
6. **k=256 is sufficient**: 0.989 without clip, diminishing returns beyond
7. **Methodological lesson**: Always benchmark against the ground truth, not your own approximation

---

*Next: Section 11 — The Coefficient Accumulation Engine*
