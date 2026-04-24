import os
import json
import urllib.request

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"


def _call_gemini(prompt, max_tokens=1400, temperature=0.35):
    if not GEMINI_API_KEY:
        return ""
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
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read())
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"  [AI] call failed: {e}")
        return ""


def infer_purpose(meta, commits):
    if not GEMINI_API_KEY:
        return (
            f"{meta['name']} has {meta['total_commits']} commits "
            f"from {meta['first_commit']} to {meta['last_commit']}. "
            "Set GEMINI_API_KEY for AI insights."
        )
    top = [c["message"] for c in commits[:50]]
    prompt = f"""You are a senior engineer writing a brutal, honest re-entry briefing for a teammate.

Repository: {meta['name']}
Total commits: {meta['total_commits']}
Active period: {meta['first_commit']} to {meta['last_commit']}
Recent commit messages:
{chr(10).join(f'  - {m}' for m in top)}

Write exactly 3 sentences:
1. What this project does and the core problem it solves (be specific, not generic).
2. The single most important non-obvious thing to understand before touching the code.
3. What the team actually spends most effort on, inferred from commit patterns.

Be direct and concrete. No fluff. No "This project is a..." opener."""
    return _call_gemini(prompt) or f"{meta['name']} — set GEMINI_API_KEY for AI analysis."


def extract_decisions(commits):
    if not GEMINI_API_KEY:
        return ["Set GEMINI_API_KEY to extract key architectural decisions."]
    messages = [c["message"] for c in commits[:120]]
    prompt = f"""From these git commit messages, extract 5 key architectural decisions that shaped this codebase.
Focus on decisions that would surprise a new developer or explain something non-obvious about the code structure.
Return ONLY a JSON array of 5 strings. Each string is one decision, starting with an action verb.
Example: ["Replaced synchronous DB calls with async to handle 10x traffic spike", ...]

Commits:
{chr(10).join(f'- {m}' for m in messages)}"""
    result = _call_gemini(prompt)
    try:
        cleaned = result.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        return json.loads(cleaned.strip())[:5]
    except Exception:
        return ["Could not parse decisions. Check your GEMINI_API_KEY."]


def generate_shock_insight(meta, churn, cochange, commits):
    """Generate a single 'oh damn' insight that makes developers share this tool."""
    if not GEMINI_API_KEY:
        return None
    top_churn = [f"{c['file']} ({c['changes']}x)" for c in churn[:5]]
    top_pairs = [f"{p['file_a']} <-> {p['file_b']} ({p['co_changes']}x)" for p in cochange[:3]]
    commit_types = {}
    for c in commits:
        commit_types[c.get("type", "other")] = commit_types.get(c.get("type", "other"), 0) + 1
    prompt = f"""You are analyzing git history for {meta['name']} ({meta['total_commits']} commits).

Most changed files: {', '.join(top_churn)}
Implicit coupling pairs: {', '.join(top_pairs) if top_pairs else 'none detected'}
Commit breakdown: {json.dumps(commit_types)}

Generate ONE shocking, specific insight about this codebase that would make a developer say "oh damn, I didn't expect that."
It should be a concrete observation about risk, architecture, or team behavior — NOT generic advice.

Examples of good shock insights:
- "80% of all bugs originate from 2 files that are never tested together"
- "This codebase has been in 'refactor mode' for 8 months — features are 3x slower to ship than year 1"
- "auth.py and db.py change together in 91% of commits — they are secretly one module"

Return ONLY the insight as a single sentence. No preamble. Make it specific to this repo's data."""
    return _call_gemini(prompt, max_tokens=200, temperature=0.5)


def identify_dangers(cochange, churn, commits):
    dangers = []

    if cochange:
        # Find the highest coupling pair
        top = cochange[0]
        total_commits = max(len(commits), 1)
        pct = round((top["co_changes"] / total_commits) * 100)
        dangers.append({
            "zone": "IMPLICIT COUPLING",
            "severity": "high" if pct > 20 else "medium",
            "warning": (
                f"`{top['file_a']}` and `{top['file_b']}` change together "
                f"{top['co_changes']}x ({pct}% of all commits). "
                f"They are architecturally entangled — touching one without the other causes silent failures."
            ),
            "files": [top["file_a"], top["file_b"]],
        })

        # Check for a second dangerous pair
        if len(cochange) > 1:
            second = cochange[1]
            dangers.append({
                "zone": "CO-CHANGE CLUSTER",
                "severity": "medium",
                "warning": (
                    f"`{second['file_a']}` and `{second['file_b']}` are a secondary coupling risk "
                    f"({second['co_changes']}x together). Any refactor of one should include the other."
                ),
                "files": [second["file_a"], second["file_b"]],
            })

    if churn:
        top = churn[0]
        dangers.append({
            "zone": "CHURN HOTSPOT",
            "severity": "high" if top["changes"] > 50 else "medium",
            "warning": (
                f"`{top['file']}` has been modified {top['changes']} times — "
                f"the single most volatile file in this repo. "
                f"Every PR that touches it carries elevated regression risk."
            ),
            "files": [top["file"]],
        })

    # Detect fix-heavy repos (instability signal)
    fix_count = sum(1 for c in commits if c.get("type") == "fix")
    total = len(commits)
    if total > 0 and fix_count / total > 0.35:
        pct = round((fix_count / total) * 100)
        dangers.append({
            "zone": "INSTABILITY SIGNAL",
            "severity": "high",
            "warning": (
                f"{pct}% of commits are bug fixes — well above the healthy threshold of ~20%. "
                f"This codebase is in chronic firefighting mode. Suggest: isolate the top 3 churn files for test coverage."
            ),
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
