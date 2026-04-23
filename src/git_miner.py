import subprocess
import os
from collections import defaultdict
from pathlib import Path


def run_git(cmd, cwd):
    result = subprocess.run(["git"] + cmd, cwd=cwd, capture_output=True, text=True, errors="replace")
    return result.stdout.strip()


def get_repo_meta(repo_path):
    name = os.path.basename(os.path.abspath(repo_path))
    total_commits = run_git(["rev-list", "--count", "HEAD"], repo_path)
    first_commit = run_git(["log", "--reverse", "--format=%ci", "--max-count=1"], repo_path)
    last_commit = run_git(["log", "--format=%ci", "--max-count=1"], repo_path)
    contributors_raw = run_git(["shortlog", "-sn", "--no-merges", "HEAD"], repo_path)
    contributors = []
    for line in contributors_raw.splitlines():
        parts = line.strip().split("\t", 1)
        if len(parts) == 2:
            contributors.append({"commits": int(parts[0].strip()), "name": parts[1].strip()})
    return {
        "name": name,
        "total_commits": int(total_commits) if total_commits.isdigit() else 0,
        "first_commit": first_commit[:10] if first_commit else "unknown",
        "last_commit": last_commit[:10] if last_commit else "unknown",
        "contributors": contributors[:10],
    }


def get_file_churn(repo_path, top_n=30):
    raw = run_git(["log", "--no-merges", "--name-only", "--format="], repo_path)
    churn = defaultdict(int)
    for line in raw.splitlines():
        line = line.strip()
        if line:
            churn[line] += 1
    sorted_churn = sorted(churn.items(), key=lambda x: x[1], reverse=True)
    return [{"file": f, "changes": c} for f, c in sorted_churn[:top_n]]


def get_cochange_pairs(repo_path, top_n=20):
    raw = run_git(["log", "--no-merges", "--name-only", "--format=COMMIT"], repo_path)
    commits = []
    current = []
    for line in raw.splitlines():
        line = line.strip()
        if line == "COMMIT":
            if current:
                commits.append(current)
            current = []
        elif line:
            current.append(line)
    if current:
        commits.append(current)
    pair_counts = defaultdict(int)
    for files in commits:
        files = list(set(files))
        if len(files) < 2:
            continue
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                pair = tuple(sorted([files[i], files[j]]))
                pair_counts[pair] += 1
    sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"file_a": p[0], "file_b": p[1], "co_changes": c} for p, c in sorted_pairs[:top_n] if c >= 2]


def get_commit_messages(repo_path, limit=200):
    raw = run_git(["log", "--no-merges", f"--max-count={limit}", "--format=%H|||%an|||%ci|||%s"], repo_path)
    commits = []
    for line in raw.splitlines():
        parts = line.split("|||", 3)
        if len(parts) == 4:
            commits.append({"hash": parts[0][:8], "author": parts[1], "date": parts[2][:10], "message": parts[3].strip()})
    return commits


def classify_commit(message):
    msg = message.lower()
    if any(w in msg for w in ["fix", "bug", "patch", "hotfix"]):
        return "fix"
    if any(w in msg for w in ["feat", "add", "new", "implement"]):
        return "feature"
    if any(w in msg for w in ["refactor", "clean", "restructure"]):
        return "refactor"
    if any(w in msg for w in ["test", "spec"]):
        return "test"
    if any(w in msg for w in ["doc", "readme"]):
        return "docs"
    if any(w in msg for w in ["perf", "optim", "speed"]):
        return "performance"
    if any(w in msg for w in ["revert", "rollback"]):
        return "revert"
    return "other"


def score_reentry(churn, file_tree):
    import re
    ENTRY = [r"main\.", r"index\.", r"app\.", r"server\.", r"cli\.", r"__init__", r"core\.", r"config\."]
    CODE = {".py", ".ts", ".js", ".go", ".rs", ".java", ".rb", ".cs"}
    churn_map = {c["file"]: c["changes"] for c in churn}
    scored = []
    for f in file_tree:
        if Path(f).suffix.lower() not in CODE:
            continue
        score = min(churn_map.get(f, 0) / 10.0, 3.0)
        if any(re.search(p, os.path.basename(f)) for p in ENTRY):
            score += 2.0
        if score > 0:
            scored.append({"file": f, "score": round(score, 2), "changes": churn_map.get(f, 0)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:12]


def mine(repo_path):
    print(f"  Repo: {os.path.abspath(repo_path)}")
    meta = get_repo_meta(repo_path)
    print(f"  {meta['total_commits']} commits found")
    churn = get_file_churn(repo_path)
    cochange = get_cochange_pairs(repo_path)
    commits = get_commit_messages(repo_path)
    for c in commits:
        c["type"] = classify_commit(c["message"])
    file_tree = run_git(["ls-files"], repo_path).splitlines()
    reentry = score_reentry(churn, file_tree)
    type_counts = defaultdict(int)
    for c in commits:
        type_counts[c["type"]] += 1
    return {
        "meta": meta,
        "churn": churn,
        "cochange": cochange,
        "commits": commits,
        "commit_types": dict(type_counts),
        "reentry_sequence": reentry,
    }
