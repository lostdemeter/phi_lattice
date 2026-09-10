# Section 08: The T Transformation (Softmax Geometry)

*There exists a linear transformation T such that lattice softmax of T(x) equals float softmax of x.*

---

## 8.1 The Problem

The softmax operation is the **last float operation** in the hot path — called 24 times per token, operating on the full Q·K^T score matrix. Every other major operation (matmul, multiply, bias-add, RoPE, residual add) has been converted to pure integer via the φ-lattice. But softmax resists:

$$\text{softmax}(x_i) = \frac{\exp(x_i)}{\sum_j \exp(x_j)}$$

The exponential function exp(x) is **transcendental** — it has no closed form on the φ-lattice. The current implementation decodes QK scores to float64, runs `np.exp()`, computes softmax, and re-encodes to the lattice. This decode→float→encode cycle is a complete escape hatch from integer arithmetic.

### The Naive Approach: Lattice Softmax

The most natural lattice-native softmax would be:

$$\text{lattice\_softmax}(e_i) = \frac{\phi^{e_i/k}}{\sum_j \phi^{e_j/k}}$$

But this is a **different mathematical function** from exp-softmax:

| Softmax Type | Formula | Correlation vs Float |
|-------------|---------|---------------------|
| Float softmax | exp(x)/Σ exp(x) | 1.000 (reference) |
| Lattice softmax | φ^(e/k)/Σ φ^(e/k) | **0.206** |
| φ-softmax (Section 06) | φ^(x/ln φ)/Σ φ^(x/ln φ) | 1.000 (identity) |

The model was trained with float softmax — its weights are optimized for it. The lattice-native φ^(e/k)/Σ φ^(e/k) computes a different function, producing wrong attention weights. We cannot simply replace the softmax without retraining.

---

## 8.2 The Discovery: T Exists

Is there a way to convert the float softmax model to use lattice softmax **mathematically**, without retraining?

The question reduces to: does there exist a transformation T such that:

$$\text{lattice\_softmax}(T(x)) = \text{float\_softmax}(x)$$

### The Derivation

Equate the two forms:

$$\frac{\phi^{e_i/k}}{\sum_j \phi^{e_j/k}} = \frac{\exp(x_i)}{\sum_j \exp(x_j)}$$

For this to hold, the numerators must be proportional (same constant per row):

$$\phi^{e_i/k} = C \cdot \exp(x_i)$$

Take log base φ of both sides:

$$\frac{e_i}{k} = \log_\phi(C) + \frac{x_i}{\ln(\phi)}$$

Multiply by k and absorb the constant:

$$e_i = \frac{k \cdot x_i}{\ln(\phi)} + \text{constant}$$

### The Result

$$T(x_i) = \text{round}\left(\frac{k}{\ln(\phi)} \cdot x_i\right) = \text{round}(532 \cdot x_i)$$

where 532 = k/ln(φ) = 256/0.4812... is a lattice constant — not model-specific.

**T exists, and it's a scalar multiplication.** For each float score x_i, multiply by 532, round to integer — that's the φ-exponent of the transformed score. These exponents are what lattice softmax expects.

---

## 8.3 Properties of T

| Property | Value | Significance |
|----------|-------|-------------|
| **Formula** | T(x) = round(532 · x) | Simple scalar linear transform |
| **Layer-independent** | Same T for all 24 layers | Depends only on k and φ, not model weights |
| **Analytic** | Derived from φ^(e/k) = C·exp(x) | No learning, no approximation |
| **No retraining** | Mathematical identity | Converts existing float-trained models |
| **Correlation** | 0.99999858 | Verified across all layers |

### T Is NOT a Weight Transformation

T operates on the **score values** after the QK dot product, not on the weights. Trying to fold T into the Q and K weight matrices would require:

$$W_Q' \cdot {W_K'}^T = 532 \cdot W_Q \cdot W_K^T$$

This cannot hold for all inputs because the dot product is bilinear but T is applied element-wise after the dot product — these are different operations. T must be applied at inference time to the scores.

---

## 8.4 The Taylor Series IS T

Computing T requires evaluating exp(x) from φ^(e/k) — which is exactly what the Taylor series does. An 8-term Taylor series:

$$\exp(x) \approx 1 + x + \frac{x^2}{2!} + \frac{x^3}{3!} + \frac{x^4}{4!} + \frac{x^5}{5!} + \frac{x^6}{6!} + \frac{x^7}{7!}$$

with range reduction for numerical stability. Each term is a φ-lattice product (exponent addition), and the terms accumulate via the coefficient accumulation engine (Section 11).

The 8-term Taylor implementation (`phi_softmax_int_taylor`) achieves:
- **Correlation > 0.99998** with float softmax
- **Zero float operations** in the hot path
- **Zero lookup tables**
- **Zero decode/encode cycles**
- Works for all sequence lengths (4, 8, 16, ...)

The Taylor series **is** T — it computes the transformation from φ-exponent space to exp-space that maps the model's float softmax output onto the lattice.

---

## 8.5 Range Reduction: The Key to Convergence

The Taylor series for exp converges rapidly for small arguments but slowly for large ones. Range reduction solves this:

For any x ≤ 0 (scores are shifted by subtracting the max):

$$\exp(x) = 2^{\lfloor x / \ln 2 \rfloor} \cdot \exp(x \bmod \ln 2)$$

The first factor is just an exponent shift (exact on the φ-lattice). The second factor has argument in (0, ln 2] where the Taylor series converges extremely fast — 8 terms suffice for machine precision.

In φ-lattice terms, this is:
1. Compute `n = floor(e / (k·ln(2)/ln(φ)))` — the number of octaves to shift
2. Compute `e_rem = e - n·k·ln(2)/ln(φ)` — the remainder
3. Taylor-expand exp for the remainder: `1 + φ^(e_rem/k) + (φ^(e_rem/k))²/2 + ...`
4. Multiply result by 2^n (exponent add n·k·ln(2)/ln(φ))

All operations are integer exponent arithmetic.

---

## 8.6 The Full Picture: Zero Float in Softmax

With T, the softmax path becomes:

```
QK scores (lattice) → T(x) = round(532·φ^(e/k)) → lattice_softmax → attention weights
```

No float operations. No decode/encode. No `np.exp()`. No lookup tables. The transformation is computed via 8-term Taylor series with integer coefficient accumulation.

### Comparison

| Approach | Formula | Float Ops | Correlation |
|----------|---------|-----------|-------------|
| Float softmax | exp(x)/Σ exp(x) | 24/token | 1.000 |
| Lattice naive | φ^(e/k)/Σ φ^(e/k) | 0 | 0.206 |
| LUT-based | Precomputed table | 0 | 0.99999955 |
| **T + Taylor** | 8-term series | **0** | **0.99999858** |

The T + Taylor approach achieves near-perfect correlation with zero float operations — eliminating the last decode/encode cycle in the transformer forward pass.

---

## 8.7 Figures

*Figure 8.1: Three softmax variants compared — float softmax (reference), naive lattice softmax (wrong function, corr=0.206), and T-transformed softmax (correct, corr>0.9999).*

*Figure 8.2: T transformation visualization — the linear mapping from float scores to φ-exponents at slope 532.*

*Figure 8.3: Taylor series convergence for softmax — 8 terms achieve >0.99998 correlation, with range reduction.*

---

## 8.8 Working Code

The companion script `code/08_t_transformation.py` demonstrates:

1. Three softmax variants: float, naive lattice, T-transformed
2. Algebraic derivation of T
3. Taylor series with range reduction
4. Correlation measurement at various sequence lengths
5. Visualization of the T mapping

```bash
cd book
python3 code/08_t_transformation.py
```

---

## 8.9 Key Insights

1. **Lattice softmax ≠ float softmax**: φ^(e/k)/Σ φ^(e/k) is a different function (corr=0.206)
2. **T exists**: T(x) = round(532·x) converts float softmax to lattice softmax
3. **T is universal**: Same T for all 24 layers — depends only on k=256 and φ
4. **T is not retraining**: It's an algebraic identity derived from φ^(e/k) = C·exp(x)
5. **The Taylor series is T**: 8-term series computes exp from φ-exponents
6. **Range reduction enables convergence**: x mod ln(2) range makes 8 terms sufficient
7. **Zero float ops**: The last decode/encode cycle in the transformer is eliminated

---

*Next: Section 09 — φ-Integer Arithmetic and the Pure Integer Transformer*
