# context-collapse

Eliminate the 3-day re-entry cost of returning to any codebase.

[![PyPI](https://img.shields.io/pypi/v/context-collapse?color=00d4aa&style=flat-square)](https://pypi.org/project/context-collapse/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)](LICENSE)
[![Zero Deps](https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square)]()

---

## The Problem Nobody Named

Day 1-3  ->  Re-understanding the codebase
Day 4    ->  Making the actual change (20 min)
Day 5    ->  Wondering why something else broke

Multiply by every developer, every new hire,
every open-source contributor, every code review.

This is the cold start problem. Nobody had a tool for it.

---

## Demo

    $ context-collapse flask/

      [1/3] Mining git history...
            1247 commits found
            30 files tracked
            18 co-change pairs

      [2/3] Running AI analysis...
            Purpose inference done
            Key decisions extracted
            3 danger zones found

      [3/3] Rendering report...

      Done in 1.4s -> cold-start-report.html

---

## What Is Inside

### 01 - Re-Entry Reading Sequence

    01  src/flask/ctx.py        58 changes  score 5.8
    02  src/flask/app.py        89 changes  score 5.0
    03  src/flask/helpers.py    39 changes  score 4.9
    04  src/flask/sessions.py   48 changes  score 4.2
    05  src/flask/globals.py    21 changes  score 3.8

### 02 - File Churn Heatmap

    #1  src/flask/app.py         ████████████████████  89x
    #2  CHANGES.rst              ██████████████████░░  82x
    #3  src/flask/sansio/app.py  ███████████████░░░░░  69x
    #4  src/flask/ctx.py         █████████████░░░░░░░  58x
    #5  src/flask/sessions.py    ██████████░░░░░░░░░░  48x

### 03 - Implicit Coupling

    app.py       <->  ctx.py       changed together 34x
    sessions.py  <->  app.py       changed together 28x
    sansio/app   <->  helpers.py   changed together 21x

### 04 - Danger Zones

    [!] CONTEXT COUPLING
        app.py and ctx.py share state implicitly.
        Changing one without the other = silent failures.

    [!] SESSION FRAGILITY
        sessions.py modified in every auth-related change.
        No isolated test suite. High breakage risk.

### 05 - Commit DNA

    feature      ████████████░░░░  42%
    fix          ████████░░░░░░░░  31%
    refactor     ████░░░░░░░░░░░░  14%
    docs         ██░░░░░░░░░░░░░░   7%
    performance  █░░░░░░░░░░░░░░░   4%
    test         █░░░░░░░░░░░░░░░   2%

### 06 - Key Architectural Decisions

    1. Merged app and request context to reduce complexity
    2. Introduced sansio layer to separate protocol from framework
    3. Added secret key rotation for zero-downtime key changes
    4. Dropped Python 3.8 to use modern type hints
    5. Switched to uv for faster dependency management

---

## Install

    pip install context-collapse

## Usage

    context-collapse path/to/repo     # any repo
    context-collapse .                # current directory
    context-collapse . --no-ai        # instant, no key needed
    context-collapse . -o report.html # custom output

## AI Layer - Free

Get a free key at aistudio.google.com — 1500 req/day, no credit card.

    set GEMINI_API_KEY=your_key_here   # Windows
    export GEMINI_API_KEY=your_key     # macOS/Linux
    context-collapse .

---

## Architecture

    context-collapse/
    cc.py                  <- CLI entrypoint
    src/
        git_miner.py       <- Git history extraction engine
        ai_brain.py        <- Gemini AI inference layer
        report_renderer.py <- Self-contained HTML generator

    Zero external dependencies. Pure Python stdlib.
    Any OS. Any git repo. Any language.

---

## Why This Exists

Tools like Sourcegraph, CodeSee, and Swimm solve documentation.
Nobody solved re-entry.

The problem is not missing docs. It is cognitive re-entry cost.
The mental overhead of rebuilding your model of a system you once
understood. Invisible in sprint planning. Multiplied across every
team member. Completely unsolved by existing tooling.

context-collapse names it. And eliminates it.

---

## Contributing

    git clone https://github.com/mohamedsaidyekhlef-png/context-collapse
    cd context-collapse
    python cc.py . --no-ai

PRs welcome. Open an issue first for large changes.

---

## License

MIT
