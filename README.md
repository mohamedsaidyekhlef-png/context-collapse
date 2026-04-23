# context-collapse

[![PyPI version](https://badge.fury.io/py/context-collapse.svg)](https://pypi.org/project/context-collapse/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-green.svg)]()

> **Eliminate the 3-day re-entry cost of returning to any codebase.**

You open a repo you haven't touched in 6 months. You spend 3 days just re-understanding it before writing a single line. Multiply that across every developer, every new hire, every open-source contributor.

This is the **cold start problem**. Nobody had a tool for it. Until now.

---

## What it does

Run one command on any git repo. Get a beautiful HTML report — your **Cold Start Pack** — with everything your brain needs to re-enter in 30 minutes instead of 3 days.

``n                    YOUR CODEBASE
                         |
              context-collapse .
                         |
         ________________|________________
        |        |        |        |       |
    Re-entry  Churn  Coupling  Danger  Commit
    Sequence  Map     Map      Zones   DNA
`  

---

## Install

`ash
pip install context-collapse
`  

---

## Usage

`ash
# Analyze current directory
context-collapse .

# Analyze any repo
context-collapse path/to/repo

# Skip AI layer
context-collapse . --no-ai

# Custom output
context-collapse . -o my-report.html
`  

---

## What's inside the report

| Section | What it tells you |
|---|---|
| **Re-entry sequence** | Exactly which 10 files to read first |
| **File churn heatmap** | What changes most — ranked |
| **Implicit coupling** | Files that always change together |
| **Danger zones** | Where to be careful before touching |
| **Key decisions** | Why the code is shaped this way |
| **Commit DNA** | How the team works, by intent |
| **Commit timeline** | Full history at a glance |

---

## AI layer (free, optional)

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com) — 1500 requests/day, no credit card needed.

`ash
# Windows
set GEMINI_API_KEY=your_key_here

# macOS / Linux
export GEMINI_API_KEY=your_key_here

# Then run
context-collapse path/to/repo
`  

With the key set, the report gains:
- AI-inferred project purpose
- Extracted architectural decisions
- Smart danger zone analysis

---

## Zero dependencies

Pure Python standard library. Works on any git repo in any language.

---

## The problem

Every developer knows this pain:

- Open a codebase not touched in 6 months
- Spend 2-3 days re-understanding it
- Finally make the change in 20 minutes

Multiply that by every new hire, every PR review, every open-source contribution. It is an invisible, trillion-dollar productivity drain — and nobody named it, let alone built a tool for it.

**context-collapse names it. And eliminates it.**

---

## Contributing

PRs welcome. Open an issue first for big changes.

---

## License

MIT — use it, fork it, ship it.
