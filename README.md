# context-collapse

[![PyPI version](https://badge.fury.io/py/context-collapse.svg)](https://pypi.org/project/context-collapse/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()
[![PyPI Downloads](https://img.shields.io/pypi/dm/context-collapse.svg)](https://pypi.org/project/context-collapse/)

<div align="center">
<h3>Eliminate the 3-day re-entry cost of returning to any codebase.</h3>
<p>One command. Any repo. Any language. Zero dependencies.</p>
<a href="https://pypi.org/project/context-collapse/"><img src="https://img.shields.io/badge/Install-pip install context--collapse-00d4aa?style=for-the-badge&logo=python&logoColor=black"/></a>
</div>

---

## The Problem

``nYou open a codebase you haven't touched in 6 months.
You spend 3 days re-understanding it.
You make the change in 20 minutes.

Multiply that by every developer. Every new hire.
Every open-source contributor. Every code review.

This is the cold start problem. Nobody had a tool for it.
`  

---

## Install

`ash
pip install context-collapse
`  

## Usage

`ash
# Analyze any git repo
context-collapse path/to/repo

# Current directory
context-collapse .

# Skip AI layer
context-collapse . --no-ai

# Custom output
context-collapse . -o report.html
`  

---

## What You Get

| Section | What it answers |
|---|---|
| **Re-entry sequence** | Which 10 files to read first |
| **File churn heatmap** | What changes most and why it matters |
| **Implicit coupling** | Files that always change together |
| **Danger zones** | Where to be careful before touching |
| **Key decisions** | Why the code is shaped this way |
| **Commit DNA** | How the team works, by intent |
| **Commit timeline** | Full classified history at a glance |

---

## Real Example — Flask (pallets/flask)

``ncontext-collapse flask/

→ 1,247 commits mined in 0.3s
→ Top file: src/flask/app.py (89 changes)
→ Hidden coupling: app.py ↔ ctx.py (changed together 34x)
→ Danger zone: sessions.py — modified during every auth change
→ Re-entry: read ctx.py first, then app.py, then helpers.py
`  

---

## AI Layer (Free)

Get a free key at [aistudio.google.com](https://aistudio.google.com) — 1500 req/day, no credit card.

`ash
# Windows
set GEMINI_API_KEY=your_key_here

# macOS / Linux
export GEMINI_API_KEY=your_key_here

context-collapse .
`  

With AI enabled you also get:
- Project purpose inference
- Architectural decision extraction
- Smart danger zone analysis
- Re-entry tips specific to your codebase

---

## Why Zero Dependencies

Most developer tools pull in 50 packages and break on Python version upgrades. context-collapse uses only the Python standard library. If you have Python 3.9+ and git, it works. No virtual environments, no conflicts, no setup.

---

## Contributing

PRs welcome. Open an issue first for big changes.

`ash
git clone https://github.com/mohamedsaidyekhlef-png/context-collapse
cd context-collapse
python cc.py . --no-ai
`  

---

## License

MIT

---

<div align="center">
<strong>context-collapse</strong> · Built with zero budget · Powered by Python stdlib
<br>
<a href="https://pypi.org/project/context-collapse/">PyPI</a> · <a href="https://github.com/mohamedsaidyekhlef-png/context-collapse/issues">Issues</a>
</div>
