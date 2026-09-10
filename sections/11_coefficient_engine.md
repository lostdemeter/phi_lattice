# Section 11: The Coefficient Accumulation Engine

*Eliminating 80% of quantization events by deferring re-encoding to the final output.*

---

## 11.1 The Problem: Death by a Thousand Solves

Every operation that produces a (sign, exponent) pair from non-lattice intermediates requires a **solve** — converting a sum of φ-lattice values back to the nearest single lattice point. The standard forward pass performs ~384 solves per token:

```
Per layer:  ~16 solves
× 24 layers: ~384 solves
Per token:  ~384 quantization events
```

Each solve introduces ~0.09% quantization error. Across 384 events, the error compounds to the 0.985 ceiling. The challenge is not that any single operation is inaccurate — it's that there are too many of them.

### The Insight

The sum of φ-lattice values can be represented **exactly** as an integer coefficient vector. The quantization error comes from the final conversion back to a single lattice point — not from the addition itself. If we can keep values in coefficient form through multiple operations and only solve at the very end, we eliminate all intermediate quantization.

---

## 11.2 The 2kD Coefficient Space

Every φ-lattice value decomposes into a **2k-dimensional integer vector** in the basis {1, φ^(1/k), φ^(2/k), ..., φ^((2k-1)/k)}:

$$\phi^{e/k} = F_{q-1} \cdot \phi^{r/k} + F_q \cdot \phi^{(k+r)/k}$$

where q = ⌊e/k⌋, r = e mod k, and F_n are Fibonacci numbers.

### The Representation

A coefficient-mode value is a pair (coeffs, max_exp):
- **coeffs**: int64 array of length 2k (at k=256, this is a 512D space)
- **max_exp**: int32 scalar giving the overall exponent shift

$$\text{actual\_value} = \phi^{\text{max\_exp}/k} \cdot \sum_{i=0}^{2k-1} \text{coeffs}[i] \cdot \phi^{i/k}$$

### Key Operations

| Operation | Coefficient Form | Error |
|-----------|-----------------|-------|
| **Multiply** (lattice × coeffs) | coeffs'[i] = sign · coeffs[i], max' = max_exp + exp_lattice | **0 (exact)** |
| **Add** (coeffs + coeffs) | coeffs'[i] = coeffs₁[i] + coeffs₂[i] (int64) | **0 (exact)** |
| **Solve** (coeffs → lattice) | Multi-limb uint64 integer solver | ~0.09% (once at end) |

The critical operations — multiply and add — are **exact integer operations**. Only the final solve back to a single lattice point introduces quantization error. And that solve happens once, not 384 times.

---

## 11.3 The Architecture: Before and After

### Standard Path (384 solves/token)

```
Layer:
  Q = x @ W_q       → solve 1
  K = x @ W_k       → solve 2
  V = x @ W_v       → solve 3
  ... bias adds     → solves 4-5
  ... softmax       → solve 6
  ... V-weighted    → solve 7
  O = attn @ W_o    → solve 8
  h = h + O         → solve 9  (residual)
  RMSNorm(h)        → solve 10
  gate = h @ W_g    → solve 11
  up = h @ W_u      → solve 12
  gate = SiLU(gate) → solve 13
  mid = gate × up   → solve 14
  mlp = mid @ W_d   → solve 15
  h = h + mlp       → solve 16  (residual)

× 24 layers = 384 solves
```

### Coefficient Path (48 solves/token)

```
Layer:
  Q_coeff = x @ W_q       → defer  (coefficient matmul)
  K_coeff = x @ W_k       → defer
  V_coeff = x @ W_v       → defer
  ... accumulate all coeffs ...
  O = solve(coeff_attn)   → solve 1  (one for attention)
  h = accumulate(O_coeff + h_coeff) → defer
  RMSNorm(h)              → solve 2  (BBP carry)
  gate_coeff = h @ W_g    → defer
  up_coeff = h @ W_u      → defer
  gate_coeff = SiLU_coeff → defer
  mid_coeff = gate × up   → defer
  mlp_coeff = mid @ W_d   → defer
  h = accumulate(mlp_coeff + h_coeff) → defer

× 24 layers = 48 solves  (80% reduction!)
```

**80% reduction in quantization events.** From 384 solves to 48. Only RMSNorm and the attention softmax require solving back to lattice form — all projections, multiplications, and additions stay in coefficient space.

---

## 11.4 The BBP Fractional Carry

RMSNorm is the one operation that must solve back to the lattice (it needs a 1D value for the normalization factor). But this solve introduces its own quantization. The **BBP fractional carry** eliminates this.

### The Problem

RMSNorm computes mean(x²) and then rrms = 1/√(mean). On the φ-lattice, √(mean) requires dividing the exponent by 2. If the exponent is odd, we lose 0.5 exponent units — a systematic downward bias.

### The Solution

Instead of discarding the fractional part, **carry it to the next layer's mean computation**:

```python
rrms_e = (-mean_e + carry) // 2
carry = mean_e % 2   # Save for next layer
```

The fractional error at each layer self-corrects at the next layer. The carry oscillates around zero instead of accumulating. This is the same principle as the BBP formula for π and the Chudnovsky algorithm — the "error" IS the computation.

### Effect

```
Without BBP carry:  error accumulates linearly across layers → drift
With BBP carry:     error oscillates around zero → self-correcting
```

Combined with coefficient accumulation, this brings the full chain correlation to **0.998**.

---

## 11.5 Numba JIT Optimization: From Hours to Seconds

The initial Python implementation of coefficient-mode operations was unusably slow — a single token took hours. The mathematical insight that unlocked performance: coefficient-to-coefficient operations are **sparse shift operators**.

### The Geometric Observation

Each coefficient at position `pos` maps to at most **2 output positions** via Fibonacci decomposition (not 512). This reduces the operation from O(2k × 2k) = 262K operations to O(2k × 2) = **1,024 operations per weight**.

### The Bit-Op Trick

Since k = 256 = 2^8:
- `delta // k` = `delta >> 8` (single-cycle arithmetic shift)
- `delta % k` = `delta & 0xFF` (single-cycle bitwise AND)

Replacing integer division/modulo with bit operations saves 20-80 cycles per operation.

### Results

| Operation | Before | After | Speedup |
|-----------|--------|-------|---------|
| coeff_matmul (896×4864) | hours (Python) | **0.231s** (Numba) | ~10,000× |
| matmul_to_coeff | hours | **0.004s** | ~100,000× |
| coeff_add (896 elts) | minutes | **<0.001s** | ~100,000× |
| **Per token (24 layers)** | **hours** | **23 seconds** | ~1,000× |

Numba JIT with prange parallelization over 4864 output dimensions achieves 8× throughput. Coefficient values stay within ±987 — far below int64's limit, eliminating overflow concerns.

---

## 11.6 RMSNorm as Natural Coefficient Binder

A concern with coefficient accumulation: coefficient magnitudes grow with every addition, eventually exceeding int64. But the model architecture naturally prevents this.

**RMSNorm appears 48 times per forward pass** (before every attention and MLP block). Each RMSNorm solves back to a lattice point and re-encodes, **resetting** the coefficient representation to a single 2-element vector.

Measured coefficient range through all 24 layers with normalization:

```
Layer  0: coefficients up to 89-144
Layer 12: coefficients up to 89-144
Layer 23: coefficients up to 89-144
```

The normalization acts as a natural garbage collector — 63 bits of int64 headroom remain unused. No explicit folding or clipping needed.

---

## 11.7 The Full Picture

| Component | Solves (Standard) | Solves (Coefficient) |
|-----------|------------------|---------------------|
| Q/K/V/O/Up/Down matmuls | 6 per layer | **0** |
| Bias adds | 2 per layer | **0** |
| Attention softmax | 1 per layer | 1 per layer |
| Residual adds | 2 per layer | **0** |
| SiLU | 1 per layer | **0** |
| RMSNorm × 2 | 2 per layer | 2 per layer (BBP) |
| **Total per layer** | ~16 | **2** |
| **Total 24 layers** | ~384 | **48** |
| **Chain correlation** | 0.993 | **0.998** |

**An 80% reduction in quantization events.** The 0.993 → 0.998 improvement represents a 3.5× reduction in error (from 0.007 to 0.002 1-corr). The final 0.002 gap comes from the 48 remaining RMSNorm and softmax solves — operations that fundamentally require leaving the lattice.

---

## 11.8 Figures

*Figure 11.1: Coefficient accumulation walkthrough — how a φ-lattice value decomposes to two Fibonacci coefficients and accumulates in 512D space.*

*Figure 11.2: Solves before vs after — bar chart showing 80% reduction from 384 to 48 quantization events per token.*

---

## 11.9 Working Code

The companion script `code/11_coefficient_engine.py` demonstrates:

1. Fibonacci decomposition into coefficient vectors
2. Coefficient addition (exact integer)
3. Coefficient-to-lattice solve
4. BBP fractional carry for self-correcting RMSNorm
5. Solves reduction visualization

```bash
cd book
python3 code/11_coefficient_engine.py
```

---

## 11.10 Key Insights

1. **384→48 solves**: 80% reduction in quantization events
2. **2kD exact integer space**: All intermediate operations are exact
3. **Sparse shift operators**: O(2k×2) not O(2k²) for coefficient ops
4. **Bit ops for speed**: k=256=2^8 enables >>8 and &0xFF single-cycle ops
5. **BBP carry**: Fractional RMSNorm error self-corrects instead of accumulating
6. **RMSNorm as binder**: Natural coefficient magnitude reset every 2 layers
7. **0.998 chain correlation**: 3.5× better than standard integer path
8. **23 sec/token**: From hours to seconds via Numba JIT + prange

---

*Next: Section 12 — The Zeta Connection*
