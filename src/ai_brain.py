import os
import json
import urllib.request

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"


def _call_gemini(prompt, max_tokens=1400, temperature=0.35, retries=2):
    if not GEMINI_API_KEY:
        return ""
    for attempt in range(retries):
        try:
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "thinkingConfig": {"thinkingBudget": 0}
                },
            }).encode()
            req = urllib.request.Request(
                GEMINI_URL.format(key=GEMINI_API_KEY),
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                candidates = data.get("candidates", [])
                if not candidates:
                    print("  [AI] no candidates (attempt %d)" % (attempt+1))
                    continue
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    print("  [AI] no parts (attempt %d)" % (attempt+1))
                    continue
                return parts[0].get("text", "").strip()
        except Exception as e:
            print("  [AI] attempt %d failed: %s" % (attempt+1, e))
    return ""


def infer_purpose(meta, commits):
    if not GEMINI_API_KEY:
        return "%s has %d commits. Set GEMINI_API_KEY for AI insights." % (meta["name"], meta["total_commits"])
    top = [c["message"] for c in commits[:60]]
    prompt = """Repository: %s (%d commits, %s to %s)

Commits:
%s

Write 3 sentences about this project:
1. What it does specifically.
2. One non-obvious thing to know before editing the code.
3. What the team spends most effort on based on commits.

Start with the project name. No filler words.""" % (
        meta["name"], meta["total_commits"], meta["first_commit"], meta["last_commit"],
        "\n".join("- %s" % m for m in top)
    )
    return _call_gemini(prompt, max_tokens=400) or ("%s -- AI unavailable." % meta["name"])


def extract_decisions(commits):
    if not GEMINI_API_KEY:
        return ["Set GEMINI_API_KEY to extract decisions."]
    messages = [c["message"] for c in commits[:100]]
    prompt = """From these git commits, list 5 key architectural decisions.

Format: one decision per line, numbered 1 to 5.
Each under 15 words. Start each with a verb.
No JSON. No bullets. No explanation. Just 5 numbered lines.

Example:
1. Switched from REST to GraphQL for mobile performance
2. Added Redis caching layer for session persistence
3. Split auth into dedicated middleware service
4. Migrated database from MongoDB to PostgreSQL
5. Adopted monorepo to share types across packages

Commits:
%s""" % "\n".join("- %s" % m for m in messages)
    result = _call_gemini(prompt, max_tokens=300)
    if not result:
        return ["AI unavailable."]
    lines = []
    for line in result.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        cleaned = line.lstrip("0123456789.-:) ").strip()
        if len(cleaned) > 8:
            lines.append(cleaned[:120])
    if len(lines) >= 3:
        return lines[:5]
    try:
        start = result.find("[")
        end = result.rfind("]")
        if start != -1 and end != -1:
            parsed = json.loads(result[start:end+1])
            if isinstance(parsed, list):
                return [str(d)[:120] for d in parsed[:5]]
    except Exception:
        pass
    return lines[:5] if lines else ["Could not extract decisions from this repo."]


def generate_shock_insight(meta, churn, cochange, commits):
    if not GEMINI_API_KEY:
        return None
    top_churn = ["%s (%dx)" % (c["file"], c["changes"]) for c in churn[:6]]
    commit_types = {}
    for c in commits:
        t = c.get("type", "other")
        commit_types[t] = commit_types.get(t, 0) + 1
    fix_pct = round(commit_types.get("fix", 0) / max(len(commits), 1) * 100)
    feature_pct = round(commit_types.get("feature", 0) / max(len(commits), 1) * 100)
    prompt = """Repo: %s, %d commits, %d contributors.
Hottest files: %s
Fix rate: %d%%, Feature rate: %d%%

One shocking sentence about this codebase (under 25 words).
Must mention a specific filename or percentage. No quotes. Just the sentence.""" % (
        meta["name"], meta["total_commits"], len(meta.get("contributors", [])),
        ", ".join(top_churn), fix_pct, feature_pct
    )
    return _call_gemini(prompt, max_tokens=100, temperature=0.6)


def identify_dangers(cochange, churn, commits):
    dangers = []
    if cochange:
        top = cochange[0]
        total_commits = max(len(commits), 1)
        pct = round((top["co_changes"] / total_commits) * 100)
        dangers.append({
            "zone": "IMPLICIT COUPLING",
            "severity": "high" if pct > 15 else "medium",
            "warning": "%s and %s change together %dx (%d%% of commits)." % (top["file_a"], top["file_b"], top["co_changes"], pct),
            "files": [top["file_a"], top["file_b"]],
        })
    if churn:
        top = churn[0]
        dangers.append({
            "zone": "CHURN HOTSPOT",
            "severity": "high" if top["changes"] > 40 else "medium",
            "warning": "%s has been modified %d times -- the most volatile file. Every PR touching it carries regression risk." % (top["file"], top["changes"]),
            "files": [top["file"]],
        })
    fix_count = sum(1 for c in commits if c.get("type") == "fix")
    total = len(commits)
    if total > 0 and fix_count / total > 0.30:
        pct = round((fix_count / total) * 100)
        dangers.append({
            "zone": "INSTABILITY SIGNAL",
            "severity": "high" if pct > 40 else "medium",
            "warning": "%d%% of commits are bug fixes -- above the ~20%% healthy threshold." % pct,
            "files": [],
        })
    author_counts = {}
    for c in commits:
        a = c.get("author", "unknown")
        author_counts[a] = author_counts.get(a, 0) + 1
    if author_counts:
        top_author = max(author_counts, key=author_counts.get)
        top_pct = round(author_counts[top_author] / max(total, 1) * 100)
        if top_pct > 70:
            dangers.append({
                "zone": "BUS FACTOR RISK",
                "severity": "high",
                "warning": "%s authored %d%% of all commits. If they leave, institutional knowledge walks out." % (top_author, top_pct),
                "files": [],
            })
    test_count = sum(1 for c in commits if c.get("type") == "test")
    if total > 50 and test_count / max(total, 1) < 0.02:
        dangers.append({
            "zone": "TEST DESERT",
            "severity": "medium",
            "warning": "Only %d of %d commits mention tests (%s%%). Minimal test coverage likely." % (test_count, total, round(test_count/max(total,1)*100, 1)),
            "files": [],
        })
    return dangers


def enrich(data):
    print("  Running AI layer...")
    shock = generate_shock_insight(
        data["meta"], data["churn"], data["cochange"], data["commits"]
    )
    data["ai"] = {
        "purpose": infer_purpose(data["meta"], data["commits"]),
        "key_decisions": extract_decisions(data["commits"]),
        "danger_zones": identify_dangers(data["cochange"], data["churn"], data["commits"]),
        "shock_insight": shock,
        "ai_powered": bool(GEMINI_API_KEY),
    }
    return data
