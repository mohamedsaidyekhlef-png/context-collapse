import os
import json
import urllib.request


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"


def _call_gemini(prompt):
    if not GEMINI_API_KEY:
        return ""
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024}}).encode()
    req = urllib.request.Request(GEMINI_URL.format(key=GEMINI_API_KEY), data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"  [AI] call failed: {e}")
        return ""


def infer_purpose(meta, commits):
    if not GEMINI_API_KEY:
        return f"{meta['name']} has {meta['total_commits']} commits from {meta['first_commit']} to {meta['last_commit']}. Set GEMINI_API_KEY for AI insights."
    top = [c["message"] for c in commits[:40]]
    prompt = f"Repository: {meta['name']}\nCommits: {meta['total_commits']}\nRecent messages:\n" + "\n".join(top) + "\n\nIn 3 sentences: what does this project do, what problem does it solve, and what is the most important thing to understand before touching the code? Be direct."
    return _call_gemini(prompt) or f"{meta['name']} — set GEMINI_API_KEY for AI analysis."


def extract_decisions(commits):
    if not GEMINI_API_KEY:
        return ["Set GEMINI_API_KEY to extract key architectural decisions."]
    messages = [c["message"] for c in commits[:100]]
    prompt = "From these git commits, identify 5 key architectural decisions. Return ONLY a JSON array of strings.\n\n" + "\n".join(f"- {m}" for m in messages)
    result = _call_gemini(prompt)
    try:
        return json.loads(result.strip().lstrip("`json").rstrip("`").strip())[:5]
    except:
        return ["Could not parse decisions. Check your GEMINI_API_KEY."]


def identify_dangers(cochange, churn):
    dangers = []
    if cochange:
        top = cochange[0]
        dangers.append({"zone": "High Coupling", "warning": f"These files change together {top['co_changes']} times.", "files": [top["file_a"], top["file_b"]]})
    if churn:
        top = churn[0]
        dangers.append({"zone": "Hotspot", "warning": f"Modified {top['changes']} times — high instability risk.", "files": [top["file"]]})
    return dangers


def enrich(data):
    print("  Running AI layer...")
    data["ai"] = {
        "purpose": infer_purpose(data["meta"], data["commits"]),
        "key_decisions": extract_decisions(data["commits"]),
        "danger_zones": identify_dangers(data["cochange"], data["churn"]),
        "ai_powered": bool(GEMINI_API_KEY),
    }
    return data
