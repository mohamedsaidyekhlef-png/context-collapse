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
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
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
                    print("  [AI] no candidates in response (attempt %d)" % (attempt+1))
                    continue
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    print("  [AI] no parts in response (attempt %d)" % (attempt+1))
                    continue
                return parts[0].get("text", "").strip()
        except Exception as e:
            print("  [AI] attempt %d failed: %s" % (attempt+1, e))
    return ""


def infer_purpose(meta, commits):
    if not GEMINI_API_KEY:
        return (
            "%s has %d commits from %s to %s. "
            "Set GEMINI_API_KEY for AI insights."
        ) % (meta["name"], meta["total_commits"], meta["first_commit"], meta["last_commit"])
    top = [c["message"] for c in commits[:80]]
    contributors = meta.get("contributors", [])
    top_authors = ", ".join(c["name"] for c in contributors[:3]) if contributors else "unknown"
    prompt = """You are a senior engineer writing a re-entry briefing.

Repository: %s
Total commits: %d
Active period: %s to %s
Top contributors: %s
Recent commit messages:
%s

Write exactly 3 sentences:
1. What this project does (be specific).
2. The single most important non-obvious thing to understand before touching the code.
3. What the team spends most effort on based on commit patterns.

Be direct. No fluff. No "Alright listen up" opener. Start with the project name.""" % (
        meta["name"], meta["total_commits"], meta["first_commit"], meta["last_commit"],
        top_authors, "\n".join("  - %s" % m for m in top)
    )
    return _call_gemini(prompt) or ("%s -- AI analysis unavailable." % meta["name"])


def extract_decisions(commits):
    if not GEMINI_API_KEY:
        return ["Set GEMINI_API_KEY to extract key architectural decisions."]
    messages = [c["message"] for c in commits[:120]]
    prompt = """From these commits, extract 5 short architectural decisions.

RULES:
- Return a JSON array of 5 strings
- Each string MUST be under 20 words
- Start each with a verb
- No markdown, no code fences
- Start response with [ end with ]

Example: ["Added Redis caching for session data", "Split monolith into three microservices", "Switched from REST to GraphQL", "Moved auth to middleware layer", "Adopted trunk-based development"]

Commits:
%s""" % "\n".join("- %s" % m for m in messages)
    result = _call_gemini(prompt, max_tokens=500)
    if not result:
        return ["AI analysis unavailable -- check API key."]
    try:
        cleaned = result.strip()
        if "`" in cleaned:
            parts = cleaned.split("`")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("["):
                    cleaned = part
                    break
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and len(parsed) > 0:
                return [str(d)[:120] for d in parsed[:5]]
        lines = [l.strip().lstrip("0123456789.-) ") for l in result.strip().splitlines() if len(l.strip()) > 10 and not l.strip().startswith("`")]
        if len(lines) >= 3:
            return [l[:120] for l in lines[:5]]
        return ["AI returned incomplete response. Try again."]
    except Exception as e:
        print("  [AI] decision parse error: %s" % e)
        lines = [l.strip().lstrip("0123456789.-) ") for l in result.strip().splitlines() if len(l.strip()) > 10 and not l.strip().startswith("`")]
        if len(lines) >= 3:
            return [l[:120] for l in lines[:5]]
        return ["Could not parse AI decisions."]


def generate_shock_insight(meta, churn, cochange, commits):
    if not GEMINI_API_KEY:
        return None
    top_churn = ["%s (%dx)" % (c["file"], c["changes"]) for c in churn[:8]]
    top_pairs = ["%s <-> %s (%dx)" % (p["file_a"], p["file_b"], p["co_changes"]) for p in cochange[:5]]
    commit_types = {}
    for c in commits:
        t = c.get("type", "other")
        commit_types[t] = commit_types.get(t, 0) + 1
    fix_pct = round(commit_types.get("fix", 0) / max(len(commits), 1) * 100)
    feature_pct = round(commit_types.get("feature", 0) / max(len(commits), 1) * 100)
    prompt = """You are analyzing git history for %s (%d commits, active %s days).

Most changed files: %s
Coupling pairs: %s
Fix rate: %d%% | Feature rate: %d%%
Contributors: %d

Generate ONE shocking data-backed insight (one sentence, under 30 words).
Reference specific filenames or percentages.
No preamble. No quotes. Just the sentence.""" % (
        meta["name"], meta["total_commits"], meta.get("active_days", "?"),
        ", ".join(top_churn),
        ", ".join(top_pairs) if top_pairs else "none",
        fix_pct, feature_pct,
        len(meta.get("contributors", []))
    )
    return _call_gemini(prompt, max_tokens=150, temperature=0.6)


def identify_dangers(cochange, churn, commits):
    dangers = []
    if cochange:
        top = cochange[0]
        total_commits = max(len(commits), 1)
        pct = round((top["co_changes"] / total_commits) * 100)
        dangers.append({
            "zone": "IMPLICIT COUPLING",
            "severity": "high" if pct > 15 else "medium",
            "warning": "%s and %s change together %dx (%d%% of all commits). They are architecturally entangled." % (top["file_a"], top["file_b"], top["co_changes"], pct),
            "files": [top["file_a"], top["file_b"]],
        })
        if len(cochange) > 1:
            second = cochange[1]
            dangers.append({
                "zone": "CO-CHANGE CLUSTER",
                "severity": "medium",
                "warning": "%s and %s are a secondary coupling risk (%dx together)." % (second["file_a"], second["file_b"], second["co_changes"]),
                "files": [second["file_a"], second["file_b"]],
            })
    if churn:
        top = churn[0]
        dangers.append({
            "zone": "CHURN HOTSPOT",
            "severity": "high" if top["changes"] > 40 else "medium",
            "warning": "%s has been modified %d times -- the single most volatile file in this repo. Every PR that touches it carries elevated regression risk." % (top["file"], top["changes"]),
            "files": [top["file"]],
        })
    fix_count = sum(1 for c in commits if c.get("type") == "fix")
    total = len(commits)
    if total > 0 and fix_count / total > 0.30:
        pct = round((fix_count / total) * 100)
        dangers.append({
            "zone": "INSTABILITY SIGNAL",
            "severity": "high" if pct > 40 else "medium",
            "warning": "%d%% of commits are bug fixes -- above the healthy threshold of ~20%%." % pct,
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
                "warning": "%s authored %d%% of all commits. If this person leaves, institutional knowledge walks out the door." % (top_author, top_pct),
                "files": [],
            })
    test_count = sum(1 for c in commits if c.get("type") == "test")
    if total > 50 and test_count / max(total, 1) < 0.02:
        dangers.append({
            "zone": "TEST DESERT",
            "severity": "medium",
            "warning": "Only %d of %d commits mention tests (%s%%). This codebase likely has minimal automated test coverage." % (test_count, total, round(test_count/max(total,1)*100, 1)),
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
