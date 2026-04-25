import subprocess
import os
from collections import defaultdict
from pathlib import Path


def run_git(cmd, cwd):
    result = subprocess.run(
        ["git"] + cmd, cwd=cwd,
        capture_output=True, text=True, errors="replace"
    )
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
    active_days = 0
    if first_commit and last_commit:
        try:
            from datetime import datetime
            fmt = "%Y-%m-%d"
            d1 = datetime.strptime(first_commit[:10], fmt)
            d2 = datetime.strptime(last_commit[:10], fmt)
            active_days = max((d2 - d1).days, 1)
        except Exception:
            active_days = 0
    return {
        "name": name,
        "total_commits": int(total_commits) if total_commits.isdigit() else 0,
        "first_commit": first_commit[:10] if first_commit else "unknown",
        "last_commit": last_commit[:10] if last_commit else "unknown",
        "contributors": contributors[:10],
        "active_days": active_days,
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
        files = list(set(f for f in files if not f.endswith((".lock", ".sum", ".mod"))))
        if len(files) < 2 or len(files) > 20:
            continue
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                pair = tuple(sorted([files[i], files[j]]))
                pair_counts[pair] += 1
    sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
    total_commits = len(commits)
    if total_commits < 100:
        min_cochanges = 1
    elif total_commits < 500:
        min_cochanges = 2
    else:
        min_cochanges = 3
    return [
        {"file_a": p[0], "file_b": p[1], "co_changes": c}
        for p, c in sorted_pairs[:top_n]
        if c >= min_cochanges
    ]


def get_commit_messages(repo_path, limit=500):
    raw = run_git(["log", "--no-merges", "--max-count=%d" % limit, "--format=%H|||%an|||%ci|||%s"], repo_path)
    commits = []
    for line in raw.splitlines():
        parts = line.split("|||", 3)
        if len(parts) == 4:
            commits.append({"hash": parts[0][:8], "author": parts[1], "date": parts[2][:10], "message": parts[3].strip()})
    return commits


def classify_commit(message):
    msg = message.lower()
    if any(w in msg for w in ["fix", "bug", "patch", "hotfix", "resolve", "close #", "closes #"]):
        return "fix"
    if any(w in msg for w in ["feat", "add", "new", "implement", "introduce", "support"]):
        return "feature"
    if any(w in msg for w in ["refactor", "clean", "restructure", "rename", "move", "extract", "simplify"]):
        return "refactor"
    if any(w in msg for w in ["test", "spec", "coverage", "assert"]):
        return "test"
    if any(w in msg for w in ["doc", "readme", "changelog", "comment", "typo"]):
        return "docs"
    if any(w in msg for w in ["perf", "optim", "speed", "cache", "fast", "lazy"]):
        return "performance"
    if any(w in msg for w in ["revert", "rollback", "undo"]):
        return "revert"
    if any(w in msg for w in ["ci", "deploy", "docker", "github action", "workflow", "pipeline"]):
        return "devops"
    if any(w in msg for w in ["security", "vuln", "cve", "auth", "permission", "sanitize"]):
        return "security"
    return "other"


def score_reentry(churn, file_tree):
    import re
    ENTRY = [r"main\.", r"index\.", r"app\.", r"server\.", r"cli\.", r"__init__", r"core\.", r"config\.", r"routes?\.", r"api\.", r"handler\."]
    CODE = {".py", ".ts", ".js", ".jsx", ".tsx", ".go", ".rs", ".java", ".rb", ".cs", ".cpp", ".c", ".swift", ".kt"}
    churn_map = {c["file"]: c["changes"] for c in churn}
    scored = []
    for f in file_tree:
        if Path(f).suffix.lower() not in CODE:
            continue
        changes = churn_map.get(f, 0)
        score = min(changes / 10.0, 5.0)
        if any(re.search(p, os.path.basename(f)) for p in ENTRY):
            score += 2.0
        depth = f.count("/")
        if depth <= 1:
            score += 0.5
        if score > 0:
            scored.append({"file": f, "score": round(score, 2), "changes": changes})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:15]


def mine(repo_path):
    print("  Repo: %s" % os.path.abspath(repo_path))
    meta = get_repo_meta(repo_path)
    print("  %d commits found" % meta["total_commits"])
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
    ghost_zones = []
    try:
        from ghost_detector import detect_ghosts
        print("  Scanning for ghost contributors...")
        ghost_zones = detect_ghosts(repo_path, churn)
        print("  %d ghost zone(s) found" % len(ghost_zones))
    except Exception as e:
        print("  [Ghost] detection failed: %s" % e)
    return {
        "meta": meta,
        "churn": churn,
        "cochange": cochange,
        "commits": commits,
        "commit_types": dict(type_counts),
        "reentry_sequence": reentry,
        "ghost_zones": ghost_zones,
    }
