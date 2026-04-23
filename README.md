# context-collapse

> Eliminate the 3-day re-entry cost of returning to any codebase.

Run one command on any git repo. Get a **Cold Start Pack** — a beautiful HTML report with everything your brain needs to re-enter a codebase in 30 minutes instead of 3 days.

## Install

`ash
pip install context-collapse
` 

## Usage

`ash
# Analyze any git repo
context-collapse path/to/repo

# Without AI layer
context-collapse path/to/repo --no-ai

# Custom output file
context-collapse path/to/repo -o report.html
`  

## What it generates

- **Re-entry reading sequence** — exactly which files to read first to rebuild your mental model
- **File churn heatmap** — what changes most, ranked
- **Implicit coupling map** — files that always change together (the hidden architecture)
- **Key architectural decisions** — why the code is shaped the way it is
- **Danger zones** — where to be careful before touching anything
- **Commit DNA** — how the team works, classified by intent
- **Full commit timeline** — the complete history at a glance

## AI layer (free)

Get Gemini API key free at [aistudio.google.com](https://aistudio.google.com) — 1500 requests/day, no credit card.

`ash
# Windows
set GEMINI_API_KEY=your_key_here
context-collapse path/to/repo

# macOS/Linux
export GEMINI_API_KEY=your_key_here
context-collapse path/to/repo
`  

## Zero dependencies

Pure Python standard library. No pip installs required beyond the package itself.

## The problem it solves

Every developer knows the pain: you open a codebase you haven't touched in 6 months and spend 2-3 days just re-understanding it before you can make a single change. Multiply that by every new hire, every open-source contributor, every 'quick fix' request. This is a trillion-dollar productivity sink with no dedicated tool.

context-collapse names the problem — **cold start cost** — and eliminates it.

## License

MIT
