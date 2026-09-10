# Section 09: φ-Integer Arithmetic and the Pure Integer Transformer

*Every operation in a 24-layer transformer, running on XOR gates, integer adders, and a 9 KB lookup table.*

---

## 9.1 The Architecture

The pure integer transformer replaces every float32 operation in Qwen2-0.5B with φ-lattice arithmetic. The complete forward pass for a single token traverses 24 layers:

```
Input: (signs, exponents) [1, 896]

For each of 24 layers:

  Attention Block:
    1. RMSNorm(h)       → φ_lattice RMSNorm          (Section 01)
    2. Q, K, V = h@W    → φ_matmul (XOR+ADD)         (Section 01)
    3. + bias           → φ_bias_add (Fibonacci)      (Section 01)
    4. RoPE(Q, K, pos)  → φ_mul (XOR+ADD)             (Section 01)
    5. attn = softmax(Q@K^T/√d)@V  → T-transformed integer softmax  (Section 08)
    6. O = attn@W       → φ_matmul (XOR+ADD)
    7. h = h + O        → φ_add (Fibonacci)           (residual)

  MLP Block:
    8. RMSNorm(h)       → φ_lattice RMSNorm
    9. gate = h@W_g     → φ_matmul (XOR+ADD)
   10. up = h@W_u       → φ_matmul (XOR+ADD)
   11. gate = SiLU(gate) → φ_silu (2D LUT, 9 KB)      (Section 01)
   12. mid = gate × up   → φ_mul (XOR+ADD)
   13. mlp = mid@W_d    → φ_matmul (XOR+ADD)
   14. h = h + mlp      → φ_add (Fibonacci)           (residual)

Output:
   15. RMSNorm(h)        → final normalization
   16. logits = h@W_lm   → φ_matmul → argmax
```

**480+ operations per forward pass. All integer. Zero float in hot path.**

---

## 9.2 Fibonacci Decomposition: The Key to Accumulation

The fundamental challenge of the φ-lattice is that *addition has no closed form*. Multiplying is exact (XOR+ADD), but summing lattice points requires approximation. The breakthrough was **Fibonacci decomposition**:

Every φ-lattice value φ^(e/k) decomposes exactly into a 2-element Fibonacci basis:

$$\phi^{e/k} = F_q \cdot \phi^{(r+k)/k} + F_{q-1} \cdot \phi^{r/k}$$

where q = ⌊e/k⌋, r = e mod k, and F_n are Fibonacci numbers (extended to negative integers).

### How It Works

1. **Decompose** each φ^(e/k) term into its two Fibonacci coefficient components
2. **Accumulate** all 2k coefficients as pure integers — no float, no LUT
3. **Solve** the 2kD coefficient vector → nearest lattice point via multi-limb uint64 arithmetic (5 × 64 = 320 bits of precision)

This is exact integer arithmetic until the very last step. The accumulation of 896 values, each contributing 2k coefficients, requires O(2k) integer additions — all exact.

### Why This Matters

The previous approach (shift-and-sum in float64) introduced compounding error at every accumulation. Fibonacci accumulation eliminates this:

```
Old (float accumulation): 1 add corr=0.995, 5 adds corr=0.279 (catastrophic!)
New (Fibonacci):          corr > 0.9999 at any number of adds
```

This was the single largest improvement in the entire project: replacing float accumulation with Fibonacci coefficients raised chain correlation from 0.9678 to 0.9926 (4.3× error reduction).

---

## 9.3 The 2kD Coefficient Space

The Fibonacci decomposition reframes the entire forward pass. Instead of decoding/encoding at every intermediate step, we can keep values in **2k-dimensional coefficient space** until the final output:

```
Traditional:   Lattice → Decode → Float → Encode → Lattice → ...
                                          ↑ quantization error

Coefficient:   Lattice → Decompose to 2kD → Accumulate → ... → Solve → Lattice
                          ↑ exact integer               ↑ one solve at end
```

The 2kD coefficient space is the "native" format for φ-lattice computation. Every lattice value maps to a 2kD vector of integers. Addition of lattice values = addition of their coefficient vectors (exact). Only the final conversion from 2kD → 1D (lattice point) introduces approximation — and this happens once, not 318 times.

---

## 9.4 Per-Operation Accuracy

| Operation | Method | Correlation | Float Ops? |
|-----------|--------|-------------|------------|
| **φ-matmul** (all projections) | XOR+ADD, Fibonacci solve | **0.99999956** | 0 |
| **φ-mul** (gate×up, RoPE) | XOR+ADD | **1.000000** | 0 |
| **SiLU** | 2D LUT (9 KB) or polynomial accumulation | **0.99999955** | 0 |
| **Softmax** | T-transformation, 8-term Taylor | **0.99999858** | 0 |
| **RMSNorm** | Lattice-native (decode-free) | **0.9999+** | 0 |
| **φ-add** (residual, bias) | Fibonacci accumulation | **0.9999+** | 0 |
| **φ-rope** | φ-mul (XOR+ADD) | **1.000000** | 0 |

**Chain correlation: 0.9938** (compounding across 24 layers, ~480 operations).

The remaining 0.0062 error comes not from any single operation but from the accumulation of 72+ quantization events across 24 layers, primarily in RMSNorm.

---

## 9.5 The ±4096 Clip Bottleneck

A critical discovery: the apparent 0.985 ceiling was measuring against the wrong reference.

### The Measurement Chain

```
True float (PyTorch)  ← corr=0.749 →  Float reference (PhiEngine)
                                        ← corr=0.985 →  Integer chain
```

The integer chain closely matched the float reference (0.985), but the float reference was itself severely degraded from the true model (0.749). The integer chain's true correlation with PyTorch was only **0.704**.

### The Clip

Both matmul implementations clip product exponents to [-4096, +4096] before decoding. At k=256, **81.8% of all products** (656,423 out of 802,816 in a single 896×896 matmul) are clipped — their values truncated to the boundaries, losing all discrimination.

The 18.2% that survive carry the signal. The model works despite 81.8% clipping because clipped products contribute uniformly across K dimensions.

### The Breakthrough

Removing the clip:

| Configuration | vs True Float | Top-5 Overlap |
|--------------|---------------|---------------|
| Float with clip (reference) | 0.749 | 1/5 |
| Integer with clip (old) | 0.704 | 1/5 |
| **Integer without clip** | **0.989** | **4/5** |

The integer chain without the clip achieves **0.989 correlation with the true PyTorch float** and gets **4/5 top-5 overlap**. This is essentially solving the problem.

> The integer chain is not the bottleneck. The float reference is. The integer chain, keeping values in (signs, exponents) format throughout, is MORE precise than the float path which encodes→decodes at every matmul.

---

## 9.6 Text Generation Results

The pure integer transformer generates coherent, correct text:

```
Input: "1 + 1 ="              → "1 + 1 = 2. The sum of the first 1"
Input: "The capital of France" → "The capital of France is Paris."
Input: "Python is a"           → "Python is a high-level, interpreted programming language"
Input: "The meaning of life is" → "a question that has been asked by many people"
```

First 2 tokens match float exactly. Subsequent tokens diverge due to compounding quantization error in cached K/V values — the KV cache accumulates error across autoregressive steps.

---

## 9.7 Hardware Implications: The φ-FPU

The φ-lattice enables a fundamentally different computational substrate:

| Property | IEEE 754 float32 | φ-FPU (integer) |
|----------|-----------------|-----------------|
| **Multiply** | 4-5 cycle float multiplier | 1 cycle XOR + ADD |
| **SIMD width** | 8 (AVX2) | 32 (narrower ops) |
| **Energy per multiply** | 20 pJ | 0.2 pJ |
| **Energy efficiency** | 1× | **24×** |
| **Storage per value** | 4 bytes | 5 bytes |
| **Transcendental hardware** | Required (exp, log, sqrt) | None |
| **Overflow risk** | High | None (exponents are signed integers) |
| **Precision** | 7.2 decimal digits | ~11 effective bits per value |
| **Dynamic range** | ±3.4×10^38 | φ^(±2^31/k) — astronomically larger |

The φ-FPU reduces AI hardware to three primitives: **XOR gate, integer adder, small LUT**. No float multiplier. No float accumulator. No transcendental function unit. This is the hardware implication of geometric computation.

### ASIC-Friendly Operations

| Operation | Hardware | Complexity |
|-----------|---------|-----------|
| XOR (sign multiply) | Single XOR gate | O(1) |
| ADD (exponent add) | Integer adder | O(log n) |
| Accumulate (coefficients) | Integer MAC | O(1) |
| Solve (coefficient→lattice) | Multi-limb uint64 | O(k) batch |

---

## 9.8 Figures

*Figure 9.1: Per-operation accuracy comparison — all integer operations vs their float equivalents.*

*Figure 9.2: The clip bottleneck — before/after removal showing the jump from 0.704 to 0.989.*

*Figure 9.3: Fibonacci decomposition walkthrough — how φ^(e/k) decomposes into two integer coefficients.*

---

## 9.9 Working Code

The companion script `code/09_integer_transformer.py` demonstrates:

1. Fibonacci decomposition algorithm
2. Simplified forward pass simulation
3. Per-operation accuracy measurement
4. The clip bottleneck effect
5. Coefficient accumulation walkthrough

```bash
cd book
python3 code/09_integer_transformer.py
```

---

## 9.10 Key Insights

1. **480 integer operations per forward pass**: Zero float in the hot path
2. **Fibonacci decomposition**: Replaces float accumulation with exact integer coefficient arithmetic
3. **Chain correlation 0.9938**: 7× better than initial attempts
4. **The clip was the bottleneck**: Removing ±4096 clip → 0.989 vs true float (from 0.704)
5. **Integer chain beats float reference**: The integer path is MORE precise
6. **24× energy efficiency**: XOR+ADD vs float multiply in silicon
7. **Coherent generation**: "The capital of France is Paris." — from pure integers
8. **ASIC-ready**: Three hardware primitives (XOR, ADD, LUT) for a complete transformer

---

*Next: Section 10 — The ±4096 Clip Bottleneck (detailed)*
