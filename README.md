# context-collapse

> **Eliminate the 3-day re-entry cost of returning to any codebase.**

[![PyPI](https://img.shields.io/pypi/v/context-collapse?color=00d4aa&style=flat-square)](https://pypi.org/project/context-collapse/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)](LICENSE)
[![Zero Deps](https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square)](pyproject.toml)

**[🌐 Website](https://context-collapse.ghostskill.com)** · **[📦 PyPI](https://pypi.org/project/context-collapse/)** · **[🐛 Issues](https://github.com/mohamedsaidyekhlef-png/context-collapse/issues)**

![context-collapse mockup](docs/mockup.svg)

---

## The Problem Nobody Named

```
Day 1–3  →  Re-understanding the codebase
Day 4    →  Making the actual change (20 min)
Day 5    →  Wondering why something else broke
```

Multiply by every developer, every new hire, every open-source contributor, every code review.

This is the **cold start problem**. Nobody had a tool for it. Until now.

---

## Install

```bash
pip install context-collapse
```

## Usage

```bash
context-collapse path/to/repo     # any repo
context-collapse .                # current directory
context-collapse . --no-ai        # instant, no API key needed
context-collapse . -o report.html # custom output file
```

## AI Layer — Free

Get a free Gemini key at [aistudio.google.com](https://aistudio.google.com) — 1500 req/day, no credit card.

```bash
# Windows
set GEMINI_API_KEY=your_key_here

# macOS / Linux
export GEMINI_API_KEY=your_key

context-collapse .
```

---

## What You Get

Every run produces a self-contained `cold-start-report.html` with:

| Section | What it tells you |
|---|---|
| **01 Re-Entry Sequence** | Exactly which files to read first, ranked by importance score |
| **02 File Churn Heatmap** | What changes most — high churn = high importance OR high instability |
| **03 Implicit Coupling** | Files that always change together — the hidden architecture |
| **04 Danger Zones** | AI-identified areas where changes cascade silently |
| **05 Commit DNA** | Every commit classified: feature / fix / refactor / perf / docs |
| **06 Key Decisions** | Why the code is shaped the way it is, extracted from history |

### Example output on `pallets/flask`

```
01  src/flask/ctx.py        58 changes  score 5.8
02  src/flask/app.py        89 changes  score 5.0
03  src/flask/helpers.py    39 changes  score 4.9
04  src/flask/sessions.py   48 changes  score 4.2
05  src/flask/globals.py    21 changes  score 3.8

Implicit coupling:
app.py      <->  ctx.py       changed together 34x  ← danger
sessions.py <->  app.py       changed together 28x

Commit DNA:
feature     ████████████░░  42%
fix         ████████░░░░░░  31%
refactor    ████░░░░░░░░░░  14%
```

---

## Architecture

```
context-collapse/
├── cc.py                   ← CLI entrypoint
└── src/
    ├── git_miner.py        ← Git history extraction engine
    ├── ai_brain.py         ← Gemini AI inference layer
    └── report_renderer.py  ← Self-contained HTML report generator
```

Zero external dependencies. Pure Python stdlib. Any OS. Any git repo. Any language.

---

## Why This Exists

Tools like Sourcegraph, CodeSee, and Swimm solve documentation. Nobody solved **re-entry**.

The problem is not missing docs. It is cognitive re-entry cost — the mental overhead of rebuilding your model of a system you once understood. Invisible in sprint planning. Multiplied across every team member. Completely unsolved by existing tooling.

**context-collapse names it. And eliminates it.**

---

## Contributing

```bash
git clone https://github.com/mohamedsaidyekhlef-png/context-collapse
cd context-collapse
python cc.py . --no-ai   # run it on itself
```

PRs welcome. Open an issue first for large changes.

---

## License

MIT © 2026 Mohamed Said Yekhlef
