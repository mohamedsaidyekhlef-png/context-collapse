#!/usr/bin/env python3
import sys
import os
import argparse
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from git_miner import mine
from ai_brain import enrich
from report_renderer import render

def main():
    parser = argparse.ArgumentParser(description="context-collapse: Cold Start Pack for any git repo")
    parser.add_argument("repo", nargs="?", default=".", help="Path to git repository")
    parser.add_argument("-o", "--output", default="cold-start-report.html", help="Output HTML file")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI layer")
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo)

    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"Error: '{repo_path}' is not a git repository.")
        sys.exit(1)

    print(f"context-collapse starting...")
    print(f"Repo: {repo_path}")
    start = time.time()

    print("[1/3] Mining git history...")
    data = mine(repo_path)

    if not args.no_ai:
        print("[2/3] Running AI analysis...")
        data = enrich(data)
    else:
        data["ai"] = {"purpose": "Run without --no-ai for AI insights.", "key_decisions": [], "danger_zones": [], "ai_powered": False}

    print("[3/3] Rendering report...")
    render(data, args.output)

    elapsed = round(time.time() - start, 1)
    print(f"Done in {elapsed}s -> {os.path.abspath(args.output)}")

if __name__ == "__main__":
    main()
