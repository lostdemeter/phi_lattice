#!/usr/bin/env python3
"""Build the phi-lattice white paper PDF from sections/ + figures/.

Assembles the 20 section markdown files in order, appends each section's
figures (matched by NN_ prefix), and converts to PDF via pandoc + xelatex.

Usage:
    python3 build_paper.py            # build book/whitepaper.pdf
    python3 build_paper.py --no-pdf   # only emit build/whitepaper.md

Output:
    whitepaper/whitepaper.md   (intermediate assembly)
    whitepaper/whitepaper.pdf  (the finished paper — checked into git)
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SECTIONS_DIR = HERE / "sections"
FIGURES_DIR = HERE / "figures"
PAPER_DIR = HERE / "whitepaper"
PAPER_DIR.mkdir(exist_ok=True)

TITLE = "The φ-Lattice: A Geometric Theory of Language and Computation"
SUBTITLE = "From geometric theory to pure integer transformer inference"
AUTHOR = "lostdemeter"
DATE = r"\today"

# Glyphs missing from DejaVu Serif → safe replacements
# (\ding needs \usepackage{pifont}, injected via header-includes below)
GLYPH_FIXES = {
    "✅": r"\ding{51}",
    "❌": r"\ding{55}",
    "★": r"$\star$",
    "≫": r"$\gg$",
}


def prettify_filename(name: str) -> str:
    """01_phi_lattice_structure.png -> Phi lattice structure."""
    stem = Path(name).stem
    stem = re.sub(r"^\d+_", "", stem)  # strip NN_ prefix
    return stem.replace("_", " ").strip().capitalize()


def collect_figures(section_num: str):
    """Figure files belonging to section NN, sorted."""
    return sorted(FIGURES_DIR.glob(f"{section_num}_*.png"))


def build_markdown() -> str:
    section_files = sorted(SECTIONS_DIR.glob("*.md"))
    assert len(section_files) == 20, f"expected 20 sections, found {len(section_files)}"

    parts = [
        "---",
        f'title: "{TITLE}"',
        f'subtitle: "{SUBTITLE}"',
        f'author: "{AUTHOR}"',
        f"date: '{DATE}'",
        "toc: true",
        "toc-depth: 2",
        "numbersections: false",
        "---",
        "",
    ]

    for idx, sec_file in enumerate(section_files):
        sec_num = sec_file.stem.split("_")[0]  # "01"
        text = sec_file.read_text(encoding="utf-8")

        for old, new in GLYPH_FIXES.items():
            text = text.replace(old, new)

        if idx > 0:
            parts.append("\\newpage")
            parts.append("")
        parts.append(text.rstrip())
        parts.append("")

        figs = collect_figures(sec_num)
        if figs:
            parts.append(f"### Figures — Section {int(sec_num)}")
            parts.append("")
            for j, fig in enumerate(figs, start=1):
                caption = prettify_filename(fig.name)
                parts.append(f"![Figure {int(sec_num)}.{j} — {caption}]"
                             f"(figures/{fig.name}){{width=100%}}")
                parts.append("")

    return "\n".join(parts) + "\n"


def build_pdf(md_path: Path) -> None:
    pdf_path = PAPER_DIR / "whitepaper.pdf"
    cmd = [
        "pandoc", str(md_path),
        "-o", str(pdf_path),
        "--pdf-engine=xelatex",
        "-V", "geometry:margin=1in",
        "-V", "fontsize=11pt",
        "-V", "colorlinks=true",
        "-V", "linkcolor=MidnightBlue",
        "-V", "urlcolor=MidnightBlue",
        "-V", "mainfont=DejaVu Serif",
        "-V", "monofont=DejaVu Sans Mono",
        "-V", r"header-includes=\usepackage{pifont}",
        "--highlight-style=tango",
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the phi-lattice white paper PDF.")
    ap.add_argument("--no-pdf", action="store_true",
                    help="only emit the combined markdown, skip PDF")
    args = ap.parse_args()

    PAPER_DIR.mkdir(exist_ok=True)
    md_path = PAPER_DIR / "whitepaper.md"

    print("Assembling sections + figures...")
    md_path.write_text(build_markdown(), encoding="utf-8")
    print(f"Wrote {md_path} ({md_path.stat().st_size // 1024} KB)")

    if args.no_pdf:
        return 0

    build_pdf(md_path)
    pdf_path = PAPER_DIR / "whitepaper.pdf"
    size_mb = pdf_path.stat().st_size / (1024 * 1024)
    print(f"Wrote {pdf_path} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
