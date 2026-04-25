"""
Ghost Contributors - detect abandoned ownership of critical files.
Finds files where the last meaningful author is inactive or gone.
Zero dependencies, pure stdlib.
"""
import subprocess
import os
from collections import defaultdict
from datetime import datetime


def run_git(cmd, cwd):
    result = subprocess.run(
        ["git"] + cmd, cwd=cwd,
        capture_output=True, text=True, errors="replace", timeout=60
    )
    return result.stdout.strip()


def get_last_active_date(author, repo_path):
    raw = run_git(
        ["log", "--author=" + author, "--format=%ci", "--max-count=1"],
        repo_path
    )
    if raw:
        try:
            return datetime.strptime(raw[:10], "%Y-%m-%d")
        except ValueError:
            pass
    return None


def get_blame_authors(filepath, repo_path, sample_lines=200):
    authors = defaultdict(int)
    author_times = {}
    try:
        raw = run_git(
            ["blame", "--line-porcelain", "-L", "1,%d" % sample_lines, "--", filepath],
            repo_path
        )
    except Exception:
        return authors, author_times
    current_author = None
    current_time = None
    for line in raw.splitlines():
        if line.startswith("author "):
            current_author = line[7:].strip()
        elif line.startswith("author-time "):
            try:
                ts = int(line[12:].strip())
                current_time = datetime.fromtimestamp(ts)
            except (ValueError, OSError):
                current_time = None
        elif line.startswith("\t"):
            if current_author and current_author != "Not Committed Yet":
                authors[current_author] += 1
                if current_time:
                    if current_author not in author_times or current_time > author_times[current_author]:
                        author_times[current_author] = current_time
            current_author = None
            current_time = None
    return dict(authors), author_times


def detect_ghosts(repo_path, churn_files, inactive_days=60):
    now = datetime.now()
    ghosts = []
    contributors_raw = run_git(
        ["shortlog", "-sn", "--no-merges", "--all"], repo_path
    )
    all_authors = {}
    for line in contributors_raw.splitlines():
        parts = line.strip().split("\t", 1)
        if len(parts) == 2:
            name = parts[1].strip()
            last_date = get_last_active_date(name, repo_path)
            if last_date:
                all_authors[name] = last_date
    files_to_check = [f["file"] for f in churn_files[:10]]
    for filepath in files_to_check:
        exists = run_git(["ls-files", "--", filepath], repo_path)
        if not exists:
            continue
        blame_authors, blame_times = get_blame_authors(filepath, repo_path)
        if not blame_authors:
            continue
        total_lines = sum(blame_authors.values())
        if total_lines < 5:
            continue
        dominant = max(blame_authors, key=blame_authors.get)
        dominant_lines = blame_authors[dominant]
        ownership_pct = round(dominant_lines / total_lines * 100, 1)
        last_seen = blame_times.get(dominant) or all_authors.get(dominant)
        if not last_seen:
            for name, date in all_authors.items():
                if dominant.lower() in name.lower() or name.lower() in dominant.lower():
                    last_seen = date
                    break
        if not last_seen:
            continue
        days_inactive = (now - last_seen).days
        if days_inactive >= inactive_days:
            status = "ghost"
        elif days_inactive >= inactive_days // 2:
            status = "at_risk"
        else:
            status = "active"
        active_authors = []
        inactive_authors = []
        for author in blame_authors:
            a_date = blame_times.get(author) or all_authors.get(author)
            if a_date and (now - a_date).days >= inactive_days:
                inactive_authors.append(author)
            elif a_date:
                active_authors.append(author)
        if status in ("ghost", "at_risk"):
            ghosts.append({
                "file": filepath,
                "ghost_author": dominant,
                "lines_owned": dominant_lines,
                "total_lines": total_lines,
                "ownership_pct": ownership_pct,
                "last_seen": last_seen.strftime("%Y-%m-%d"),
                "days_inactive": days_inactive,
                "status": status,
                "active_authors": active_authors[:3],
                "inactive_authors": inactive_authors[:3],
            })
    ghosts.sort(key=lambda g: (-1 if g["status"] == "ghost" else 0, -g["ownership_pct"]))
    return ghosts
