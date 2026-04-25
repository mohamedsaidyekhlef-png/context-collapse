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
                    print(f"  [AI] no candidates in response (attempt {attempt+1})")
                    continue
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    print(f"  [AI] no parts in response (attempt {attempt+1})")
                    continue
                return parts[0].get("text", "").strip()
        except Exception as e:
            print(f"  [AI] attempt {attempt+1} failed: {e}")
    return ""


def infer_purpose(meta, commits):
    if not GEMINI_API_KEY:
        return (
            f"{meta['name']} has {meta['total_commits']} commits "
            f"from {meta['first_commit']} to {meta['last_commit']}. "
            "Set GEMINI_API_KEY for AI insights."
        )
    top = [c["message"] for c in commits[:80]]
    contributors = meta.get("contributors", [])
    top_authors = ", ".join(c["name"] for c in contributors[:3]) if contributors else "unknown"
    prompt = f"""You are a senior engineer writing a brutal, honest re-entry briefing for a teammate.

Repository: {meta['name']}
Total commits: {meta['total_commits']}
Active period: {meta['first_commit']} to {meta['last_commit']}
Top contributors: {top_authors}
Recent commit messages:
{chr(10).join(f'  - {m}' for m in top)}

Write exactly 3 sentences:
1. What this project does and the core problem it solves (be specific, not generic).
2. The single most important non-obvious thing to understand before touching the code.
3. What the team actually spends most effort on, inferred from commit patterns.

Be direct and concrete. No fluff. No "This project is a..." opener."""
    return _call_gemini(prompt) or f"{meta['name']} — AI analysis unavailable."


def extract_decisions(commits):
    if not GEMINI_API_KEY:
        return ["Set GEMINI_API_KEY to extract key architectural decisions."]
    messages = [c["message"] for c in commits[:200]]
    prompt = f"""From these git commit messages, extract 5 key architectural decisions that shaped this codebase.
Focus on decisions that would surprise a new developer or explain something non-obvious about the code structure.
Return ONLY a valid JSON array of exactly 5 strings. No markdown, no code fences, no explanation.
Each string starts with an action verb.
Example format: ["Replaced synchronous DB calls with async to handle 10x traffic spike", "Moved auth logic into middleware to decouple from route handlers", "Adopted monorepo structure to share types between frontend and backend", "Switched from REST to GraphQL for mobile client performance", "Pinned all dependencies after a breaking transitive update"]

Commits:
{chr(10).join(f'- {m}' for m in messages)}"""
    result = _call_gemini(prompt, max_tokens=800)
    if not result:
        return ["AI analysis unavailable — check API key and model access."]
    try:
        cleaned = result.strip()
        # Strip markdown code fences if present
        if "```" in cleaned:
            parts = cleaned.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("["):
                    cleaned = part
                    break
        # Find the JSON array in the response
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        parsed = json.loads(cleaned)
        if isinstance(parsed, list) and len(parsed) > 0:
            return [str(d) for d in parsed[:5]]
        return ["AI returned unexpected format."]
    except Exception as e:
        print(f"  [AI] decision parse error: {e}")
        print(f"  [AI] raw response: {result[:200]}")
        return ["Could not parse AI decisions — raw response logged."]


def generate_shock_insight(meta, churn, cochange, commits):
    """Generate a single 'oh damn' insight that makes developers share this tool."""
    if not GEMINI_API_KEY:
        return None

    top_churn = [f"{c['file']} ({c['changes']}x)" for c in churn[:8]]
    top_pairs = [f"{p['file_a']} <-> {p['file_b']} ({p['co_changes']}x)" for p in cochange[:5]]

    commit_types = {}
    for c in commits:
        t = c.get("type", "other")
        commit_types[t] = commit_types.get(t, 0) + 1

    fix_pct = round(commit_types.get("fix", 0) / max(len(commits), 1) * 100)
    feature_pct = round(commit_types.get("feature", 0) / max(len(commits), 1) * 100)

    prompt = f"""You are analyzing git history for {meta['name']} ({meta['total_commits']} commits, active {meta.get('active_days', '?')} days).

Most changed files: {', '.join(top_churn)}
Implicit coupling pairs: {', '.join(top_pairs) if top_pairs else 'none detected'}
Commit breakdown: {json.dumps(commit_types)}
Fix rate: {fix_pct}% | Feature rate: {feature_pct}%
Contributors: {len(meta.get('contributors', []))}

Generate ONE shocking, specific, data-backed insight about this codebase that would make a developer say "oh damn."
It MUST reference specific filenames or percentages from the data above.
It should be a concrete observation about risk, architecture, or team behavior — NOT generic advice.

Examples of good shock insights:
- "80% of all bugs in this repo originate from agent_loop.py and tools.py — 2 files that are never tested together"
- "This codebase has been in firefighting mode for 3 months: fixes outnumber features 2:1 since January"
- "auth.py and db.py change together in 91% of commits — they are secretly one module wearing two hats"
- "One developer wrote 73% of all commits — this is a single-point-of-failure disguised as a team project"

Return ONLY the insight as a single sentence. No preamble, no quotes, no explanation."""
    return _call_gemini(prompt, max_tokens=250, temperature=0.6)


def identify_dangers(cochange, churn, commits):
    dangers = []

    if cochange:
        top = cochange[0]
        total_commits = max(len(commits), 1)
        pct = round((top["co_changes"] / total_commits) * 100)
        dangers.append({
            "zone": "IMPLICIT COUPLING",
            "severity": "high" if pct > 15 else "medium",
            "warning": (
                f"`{top['file_a']}` and `{top['file_b']}` change together "
                f"{top['co_changes']}x ({pct}% of all commits). "
                f"They are architecturally entangled — touching one without the other causes silent failures."
            ),
            "files": [top["file_a"], top["file_b"]],
        })

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
            "severity": "high" if top["changes"] > 40 else "medium",
            "warning": (
                f"`{top['file']}` has been modified {top['changes']} times — "
                f"the single most volatile file in this repo. "
                f"Every PR that touches it carries elevated regression risk."
            ),
            "files": [top["file"]],
        })

    # Detect fix-heavy repos
    fix_count = sum(1 for c in commits if c.get("type") == "fix")
    total = len(commits)
    if total > 0 and fix_count / total > 0.30:
        pct = round((fix_count / total) * 100)
        dangers.append({
            "zone": "INSTABILITY SIGNAL",
            "severity": "high" if pct > 40 else "medium",
            "warning": (
                f"{pct}% of commits are bug fixes — above the healthy threshold of ~20%. "
                f"This codebase may be in chronic firefighting mode."
            ),
            "files": [],
        })

    # Detect single-contributor risk
    contributors = []
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
                "warning": (
                    f"`{top_author}` authored {top_pct}% of all commits. "
                    f"If this person leaves, institutional knowledge walks out the door."
                ),
                "files": [],
            })

    # Detect low test coverage signal
    test_count = sum(1 for c in commits if c.get("type") == "test")
    if total > 50 and test_count / max(total, 1) < 0.02:
        dangers.append({
            "zone": "TEST DESERT",
            "severity": "medium",
            "warning": (
                f"Only {test_count} of {total} commits mention tests ({round(test_count/max(total,1)*100, 1)}%). "
                f"This codebase likely has minimal automated test coverage."
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
