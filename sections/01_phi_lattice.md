# Section 01: The φ-Lattice Foundation

*The golden ratio as the organizing principle of geometric computation.*

---

## 1.1 The Golden Ratio

The golden ratio φ is the mathematical constant:

$$\phi = \frac{1 + \sqrt{5}}{2} \approx 1.618033988749895$$

Its defining property is self-similarity, captured in a single equation:

$$\phi^2 = \phi + 1 \quad \Longleftrightarrow \quad \phi = 1 + \frac{1}{\phi}$$

This means φ can be decomposed into a part that equals 1 and a part that equals 1/φ. The ratio between the whole and the larger part equals the ratio between the larger part and the smaller part — **φ is self-similar at every scale**.

### Why φ Is Special

The golden ratio is the *most irrational* number. Its continued fraction expansion:

$$\phi = 1 + \cfrac{1}{1 + \cfrac{1}{1 + \cfrac{1}{1 + \dots}}} = [1; 1, 1, 1, \dots]$$

has the slowest possible convergence of any irrational number. For the φ-lattice, this means:

1. **Uniform distribution**: Fractional parts of n · log_φ(x) fill [0, 1) with minimal clustering
2. **Injective encoding**: No two distinct values map to the same lattice point
3. **Scale-invariant precision**: Same relative error at all scales
4. **No rational approximation**: φ cannot be well-approximated by simple fractions

### Powers of φ

The powers of φ follow a Fibonacci-like recurrence:

| n | φ^n | Value |
|---|-----|-------|
| -3 | φ^-3 | ≈ 0.236 |
| -2 | φ^-2 | ≈ 0.382 |
| -1 | φ^-1 = φ - 1 | ≈ 0.618 |
| 0 | φ^0 | 1.000 |
| 1 | φ^1 | ≈ 1.618 |
| 2 | φ^2 = φ + 1 | ≈ 2.618 |
| 3 | φ^3 = 2φ + 1 | ≈ 4.236 |
| 4 | φ^4 = 3φ + 2 | ≈ 6.854 |

The coefficients are consecutive Fibonacci numbers: φ^n = F_n · φ + F_{n-1}.

### Three Manifestations of Self-Similarity

1. **Scale invariance**: A transformation that works at φ^2 works identically at φ^-3
2. **Recursive decomposition**: Any φ interval decomposes into smaller φ intervals:
   φ^n = φ^{n-1} + φ^{n-2}
3. **Natural spacing**: φ^n provides logarithmic spacing that avoids collisions — critical for encoding distinct concepts without overlap

---

## 1.2 The φ-Lattice Definition

The **φ-lattice** is a discrete set of values parameterized by an integer resolution `k`:

$$\mathcal{L}_k = \left\{ s \cdot \phi^{n/k} \;\middle|\; s \in \{-1, +1\},\; n \in \mathbb{Z} \right\}$$

### Lattice Spacing

At resolution k = 256:
- Each octave (factor of 2) contains **k · log_2(φ) ≈ 177** lattice points
- Relative spacing between adjacent points: **φ^(1/256) - 1 ≈ 0.1882%**
- This provides approximately **11 bits of effective resolution** per value
- Spacing is constant *proportionally* but grows *absolutely* with magnitude

### Key Properties

| Property | Description |
|----------|-------------|
| **Multiplicative** | Multiplication → exponent addition (exact) |
| **Self-similar** | Same structure at every power of φ |
| **Injective** | Each float maps to a unique lattice point |
| **Uniform** | Minimal clustering — φ is the most irrational number |
| **Unbounded** | Spans 10+ orders of magnitude without overflow |

---

## 1.3 Encoding: Float → (Sign, Exponent)

Any nonzero float x maps to the nearest φ-lattice point:

$$s = \text{sign}(x) = \begin{cases} +1 & \text{if } x \geq 0 \\\\ -1 & \text{if } x < 0 \end{cases}$$

$$e = \text{round}\left( k \cdot \frac{\ln(|x| + \varepsilon)}{\ln(\phi)} \right)$$

The encoding satisfies: **x ≈ s · φ^(e/k)**

### Midpoint Correction

Unlike linear quantization, the arithmetic midpoint between two lattice points is NOT at the half-exponent. The true midpoint ratio is:

$$m_{\text{hi}} = \frac{1 + \phi^{1/k}}{2}, \quad m_{\text{lo}} = \frac{1 + \phi^{-1/k}}{2}$$

The encoder compares the measured ratio against these thresholds to select the correct nearest point — this is critical for accuracy at low k.

### Quantization Error Bound

$$|x - s \cdot \phi^{e/k}| \leq \frac{1}{2} \cdot |x| \cdot (\phi^{1/k} - 1) \approx |x| \cdot \frac{\ln(\phi)}{2k}$$

For k = 256: relative error ≤ 0.094% per value.

### Storage

Each value occupies 5 bytes: `int8` sign + `int32` exponent.

---

## 1.4 Decoding: (Sign, Exponent) → Float

$$\text{decode}(s, e) = s \cdot \phi^{e/k}$$

This is exact — no loss of information beyond the initial encoding quantization.

---

## 1.5 Lattice-Native Multiplication

**The fundamental insight of the φ-lattice**: multiplication becomes integer addition.

For two lattice values a = s_a · φ^(e_a/k) and b = s_b · φ^(e_b/k):

$$a \cdot b = (s_a \cdot s_b) \cdot \phi^{(e_a + e_b)/k}$$

| Operation | Integer Equivalent | Hardware | Error |
|-----------|-------------------|----------|-------|
| **Sign** | XOR | Single XOR gate | 0 (exact) |
| **Exponent** | ADD | Integer adder | 0 (exact) |

### Sign Multiplication Truth Table

Using the arithmetic convention (1/-1):

```
s_a   s_b   s_a · s_b
+1    +1      +1
+1    -1      -1
-1    +1      -1
-1    -1      +1
```

This is the XOR function when signs are mapped to {0, 1}. **Critical note**: Using {0, 1} signs directly computes AND (0·0=0, 0·1=0, 1·0=0, 1·1=1), NOT XOR. The 1/-1 convention is required for correct sign arithmetic.

---

## 1.6 Lattice-Native Operations Catalog

### Exact Operations (Zero Error)

| Operation | Formula | Lattice Form | Hardware |
|-----------|---------|-------------|----------|
| **Multiply** | a · b | XOR(signs) + ADD(exps) | XOR gate + adder |
| **Divide** | a / b | XOR(signs) + SUB(exps) | XOR gate + subtractor |
| **Power** | a^n | MULTIPLY exponent by n | Integer multiply |
| **Reciprocal** | 1/a | NEGATE exponent | Negation |
| **Scale** | a · φ^(c/k) | ADD constant c to exp | Adder |
| **Negate** | -a | FLIP sign | NOT gate |

### Approximate Operations (Small Error)

| Operation | Method | Error |
|-----------|--------|-------|
| **Add (two values)** | Decode→float→add→re-encode | ~0.09% |
| **Accumulate (many values)** | Shift-and-sum in float64 | ~0.001% per K-block |
| **sqrt** | Divide exponent by 2 | 0 if even, ~0.09% if odd |
| **mean(x²)** | Accumulate 896 squared values | ~0.1-0.3% |

### Impossible Operations (Require Decode/Encode)

| Operation | Why |
|-----------|-----|
| **exp(x)** | exp(φ^(e/k)) is not a lattice point |
| **softmax** | Requires exp for each element |
| **SiLU = x·σ(x)** | σ requires exp |
| **RMSNorm = x/√(mean(x²))** | sqrt is nonlinear |

**Overcoming the impossible operations is the central challenge of the pure integer transformer project.**

---

## 1.7 The Addition Problem

Unlike multiplication, addition has no closed form on the φ-lattice. Given:

$$a + b = s_a \cdot \phi^{e_a/k} + s_b \cdot \phi^{e_b/k}$$

We need to find (s_c, e_c) such that a + b ≈ s_c · φ^(e_c/k).

### The Shift-and-Sum Algorithm

```
phi_accumulate(signs[], exps[], axis, k):
  1. Find minimum exponent: e_min = min(exps)
  2. Shift to avoid underflow: e_shifted = exps - e_min (all ≥ 0)
  3. Decode each term to float64: val = sign · φ^(e_shifted/k)
  4. Sum in float64: total = Σ val
  5. Re-apply shift: result = total · φ^(e_min/k)
  6. Re-encode: s = sign(result), e = round(k · ln(|result|) / ln(φ))
```

Steps 4 and 6 introduce float operations (decode/encode). The pure integer approach uses **Fibonacci decomposition** (Section 09) to keep the accumulation entirely in integer space until the final decode.

---

## 1.8 Fibonacci Decomposition (Preview)

Every φ-lattice value φ^(e/k) can be decomposed exactly into a 2-element Fibonacci basis:

$$\phi^{e/k} = F_q \cdot \phi^{(r+k)/k} + F_{q-1} \cdot \phi^{r/k}$$

where q = ⌊e / k⌋ and r = e mod k, and F_n are Fibonacci numbers (extended to negative integers via F_{-n} = (-1)^{n+1} · F_n).

This means any sum of φ-lattice values can be represented as a vector of 2k integer coefficients in the basis {1, φ^(1/k), φ^(2/k), ..., φ^((2k-1)/k)}. Accumulation becomes integer addition of these coefficient vectors — no floating point, no lookup tables.

The final step converts the coefficient vector back to a single (sign, exponent) pair via a multi-limb integer solver — this is exact arithmetic until the very last step.

---

## 1.9 Figure: φ-Lattice Structure

*Figure 1.1 shows the φ-lattice at k=256, demonstrating:*
- *Left: The exponential spacing of φ^(n/k) showing self-similar scaling*
- *Center: The relative error distribution shows uniform quantization*
- *Right: Lattice point density per octave confirms ~177 points per factor of 2*

---

## 1.10 Working Code

The companion script `code/01_lattice_demo.py` provides a complete, self-contained implementation that:
1. Defines φ and the lattice resolution k
2. Implements encode() and decode() with midpoint correction
3. Demonstrates multiplication via XOR+ADD
4. Shows the shift-and-sum accumulation algorithm
5. Generates Figure 1.1
6. Verifies all operations with correlation and error metrics

Run it with:

```bash
cd book
python3 code/01_lattice_demo.py
```

### Core Implementation

```python
import math
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
LN_PHI = math.log(PHI)  # ≈ 0.48121182505960347

def phi_encode(x: np.ndarray, k: int = 256):
    """Encode float array → (signs, exponents) on the φ-lattice."""
    x = np.asarray(x, dtype=np.float64)
    signs = np.where(x >= 0, 1, -1).astype(np.int8)
    mag = np.abs(x) + 1e-300  # avoid log(0)
    exps = np.round(k * np.log(mag) / LN_PHI).astype(np.int64)

    # Midpoint correction: the arithmetic midpoint is NOT at half-exponent
    mag_clip = np.maximum(mag, 1e-300)
    ratio = mag_clip * PHI ** (-exps.astype(np.float64) / k)
    phi_1overk = PHI ** (1.0 / k)
    hi_thresh = (1.0 + phi_1overk) / 2.0
    lo_thresh = (1.0 + 1.0 / phi_1overk) / 2.0
    exps = np.where(ratio > hi_thresh, exps + 1,
                    np.where(ratio < lo_thresh, exps - 1, exps)).astype(np.int32)
    return signs, exps

def phi_decode(signs: np.ndarray, exps: np.ndarray, k: int = 256):
    """Decode (signs, exponents) → float64."""
    return signs.astype(np.float64) * PHI ** (exps.astype(np.float64) / k)

def phi_mul(signs_a, exps_a, signs_b, exps_b, k=256):
    """Multiply two φ-lattice values: XOR signs, ADD exponents."""
    s = (signs_a * signs_b).astype(np.int8)  # 1*-1 works correctly
    e = (exps_a.astype(np.int32) + exps_b.astype(np.int32)).astype(np.int32)
    return s, e
```

### Key Constants

```
PHI      = (1 + √5) / 2     ≈ 1.618033988749895
LN_PHI   = ln(PHI)          ≈ 0.48121182505960347
k        = 256              (default lattice resolution)
```

These three numbers are the only constants needed for the entire φ-lattice framework.

---

## 1.11 Summary

The φ-lattice provides a coordinate system where:

| Property | Benefit |
|----------|---------|
| Multiplication = XOR + ADD | 0 error, 1-cycle hardware |
| Self-similar at every scale | Same precision for 10^-20 and 10^20 |
| Uniform distribution | Minimal quantization bias |
| Exact until decode | All structure preserved until final step |
| 11 bits/5 bytes | Efficient storage representation |

The lattice defines what operations are exact (multiplication, division, powers, scaling) and what requires approximation (addition, activation functions). The rest of this book is about pushing the boundary of what's possible entirely on the lattice.

---

*Next: Section 02 — The Vacuum Forming Hypothesis*
