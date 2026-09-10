# The φ-Lattice: A Geometric Theory of Language and Computation

## A Comprehensive Reference

---

## Sections

| # | Title | Status |
|---|-------|--------|
| 01 | [The φ-Lattice: Foundation](sections/01_phi_lattice.md) | ✅ Complete |
| 02 | The Vacuum Forming Hypothesis | ✅ Complete |
| 03 | Phase-Shift Probing and Geometric Invariants | ✅ Complete |
| 04 | The 16D Toroid-Tetrix | ✅ Complete |
| 05 | Style Is Geometry | ✅ Complete |
| 06 | Navigation Replaces Inference | ✅ Complete |
| 07 | Chirality and the Geometric Signature | ✅ Complete |
| 08 | The T Transformation (Softmax Geometry) | ✅ Complete |
| 09 | φ-Integer Arithmetic and the Pure Integer Transformer | ✅ Complete |
| 10 | The ±4096 Clip Bottleneck | ✅ Complete |
| 11 | The Coefficient Accumulation Engine | ✅ Complete |
| 12 | The Zeta Connection | ✅ Complete |
| 13 | The Resonant Language Model | ✅ Complete |
| 14 | Echion: The Intentional LLM | ✅ Complete |
| 15 | Templates Are Geometry | ✅ Complete |
| 16 | The Wall-Breaking Protocol | ✅ Complete |
| 17 | φ-Zipf and the Zipf Connection | ✅ Complete |
| 18 | The Heegner Subspace | ✅ Complete |
| 19 | Hardware Implications: The φ-FPU | ✅ Complete |
| 20 | Open Problems and Future Directions | ✅ Complete |

## Appendices

| # | Title | Status |
|---|-------|--------|
| A | Sign Convention Reference | - |
| B | Layer-by-Layer Chirality Data | - |
| C | The φ-Geist Library Reference | - |
| D | Configuration Guide: When to Use Each Dimensionality | - |

---

## Repository Layout

```
book/
├── README.md                    ← You are here
├── sections/                    ← One markdown file per section
│   ├── 01_phi_lattice.md
│   ├── 02_vacuum_forming.md
│   └── ...
├── code/                        ← Self-contained Python scripts
│   ├── 01_lattice_demo.py
│   ├── 02_phase_probing.py
│   └── ...
└── figures/                     ← Generated figures (PNG)
    ├── 01_phi_lattice_spacing.png
    ├── 01_phi_self_similarity.png
    └── ...
```

## Usage

Each section is self-contained. The matching code script in `code/` generates the figures in `figures/` and demonstrates the mathematics with working examples. To rebuild all figures:

```bash
cd book
for script in code/??_*.py; do python3 "$script"; done
```
