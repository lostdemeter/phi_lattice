# The φ-Lattice: A Geometric Theory of Language and Computation

What if a language model isn't a statistical machine at all — but a navigator moving through a geometric space?

This book traces a research program that started with that question and ended somewhere unexpected: a working transformer that runs on pure integer arithmetic, with no floating-point operations in its hot path. Along the way it touches number theory, crystallography, dynamical systems, and hardware design.

---

## The core idea

Every number in a neural network can be written as a power of the golden ratio:

```
value = sign × φ^(exponent / k)
```

On this **φ-lattice**, multiplication becomes integer addition — an XOR gate plus an adder, in a single cycle. Addition becomes accumulation of Fibonacci coefficients. The transcendental functions that normally require expensive hardware (exp, sqrt, sigmoid) turn out to have exact or near-exact integer forms.

The result: a complete 24-layer transformer doing real inference with nothing but integer ops and a 9 KB lookup table.

## What's inside

The book is organized as 20 self-contained sections:

**Foundations** — the φ-lattice itself, the hypothesis that training captures only the *surface* of semantic structure, and a crystallography-inspired method for telling surface patterns from geometric truth.

**Geometry** — language as a 16-dimensional phase space living on a torus, style (literary, ethical, visual) as positions in a navigable space, and the discovery that inference is better understood as *navigation* than computation.

**Computation** — the integer transformer in full: Fibonacci-based accumulation, a transformation that makes lattice softmax exactly match float softmax, the elimination of the last floating-point operations, and the engine that defers rounding until the final output.

**Connections** — Riemann zeta zeros as deterministic hash functions, a zero-parameter language model built from a single primitive, an intentional LLM with explicit beliefs, and the golden ratio showing up in word frequencies.

**Frontier** — Heegner numbers hiding in the coefficient space, a hardware design 24× more energy-efficient than floating point, and twelve open problems.

## Using this repo

Each section pairs mathematical exposition with runnable code:

```
book/
├── README.md          ← you are here
├── sections/          ← the 20 chapters (start with 01)
├── code/              ← one Python script per section
└── figures/           ← output of running the scripts
```

Read straight through from `sections/01_phi_lattice.md`, or jump to whatever catches your eye. To regenerate any figure, run its script:

```bash
python3 code/01_lattice_demo.py
```

Most scripts need only NumPy and Matplotlib. A few load real models (Qwen2-0.5B, BERT) from HuggingFace — those fall back to built-in demonstrations if the dependencies aren't installed.

## Status and honesty

This is a research record, not a polished textbook. Some sections demonstrate mathematical frameworks with synthetic data; others measure real models. Where the code shows a concept rather than proving a claim, the text says so. The strongest results — the integer transformer running real weights, the exact softmax transformation — are reproducible from the scripts here.

## License

GPLv3 — see [LICENSE](LICENSE).
