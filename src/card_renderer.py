"""
Repo Personality Card - a Spotify-Wrapped-style SVG identity card for any git repo.
Returns a self-contained SVG string with zero external dependencies.
"""
import json


ARCHETYPES = [
    {
        "id": "perfectionist",
        "name": "The Perfectionist",
        "emoji": "target",
        "desc": "Obsessed with quality. Refactors before adding features.",
        "match": lambda d: d.get("refactor", 0) + d.get("fix", 0) > 50 and d.get("test", 0) > 5,
    },
    {
        "id": "firefighter",
        "name": "The Firefighter",
        "emoji": "fire",
        "desc": "More time fixing than building. The codebase fights back.",
        "match": lambda d: d.get("fix", 0) > 35,
    },
    {
        "id": "speedrunner",
        "name": "Move Fast and Break Things",
        "emoji": "rocket",
        "desc": "Feature velocity is everything. Tests? Maybe later.",
        "match": lambda d: d.get("feature", 0) > 40 and d.get("test", 0) < 3,
    },
    {
        "id": "ghost_ship",
        "name": "The Ghost Ship",
        "emoji": "ghost",
        "desc": "One person drives the entire project. Knowledge is concentrated.",
        "match": lambda d: d.get("_bus_factor_risk", False),
    },
    {
        "id": "documentation_nerd",
        "name": "The Documentation Nerd",
        "emoji": "books",
        "desc": "Commits are well-documented. Docs ratio is unusually high.",
        "match": lambda d: d.get("docs", 0) > 12,
    },
    {
        "id": "test_driven",
        "name": "Test-Driven Machine",
        "emoji": "lab",
        "desc": "Tests come first. High confidence in every change.",
        "match": lambda d: d.get("test", 0) > 15,
    },
    {
        "id": "devops_warrior",
        "name": "The DevOps Warrior",
        "emoji": "gear",
        "desc": "Pipeline tweaking is a lifestyle. CI/CD is always evolving.",
        "match": lambda d: d.get("devops", 0) > 10,
    },
    {
        "id": "steady_builder",
        "name": "The Steady Builder",
        "emoji": "building",
        "desc": "Balanced mix of features, fixes, and maintenance. Sustainable pace.",
        "match": lambda d: True,
    },
]

EMOJI_MAP = {
    "target": "&#x1F3AF;",
    "fire": "&#x1F525;",
    "rocket": "&#x1F680;",
    "ghost": "&#x1F47B;",
    "books": "&#x1F4DA;",
    "lab": "&#x1F9EA;",
    "gear": "&#x2699;",
    "building": "&#x1F3D7;",
}


def classify_personality(commit_types_pct, bus_factor_risk=False):
    data = dict(commit_types_pct)
    data["_bus_factor_risk"] = bus_factor_risk
    for archetype in ARCHETYPES:
        if archetype["match"](data):
            return archetype
    return ARCHETYPES[-1]


def compute_stability_score(commit_types_pct, bus_factor, test_pct, top_churn_ratio):
    score = 0.0
    fix_pct = commit_types_pct.get("fix", 0)
    score += max(0, 30 - fix_pct)
    score += min(test_pct * 2.5, 25)
    if bus_factor >= 3:
        score += 25
    elif bus_factor == 2:
        score += 15
    else:
        score += 5
    score += max(0, 20 - top_churn_ratio * 0.4)
    return min(round(score), 100)


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def generate_card_svg(data):
    meta = data.get("meta", {})
    churn = data.get("churn", [])
    commit_types = data.get("commit_types", {})
    cochange = data.get("cochange", [])
    ghosts = data.get("ghost_zones", [])

    name = meta.get("name", "unknown")
    total_commits = meta.get("total_commits", 0)
    contributors = meta.get("contributors", [])
    num_contributors = len(contributors)
    first_commit = meta.get("first_commit", "?")
    last_commit = meta.get("last_commit", "?")
    active_days = meta.get("active_days", 0)

    total_typed = sum(commit_types.values()) or 1
    type_pct = {k: round(v / total_typed * 100, 1) for k, v in commit_types.items()}

    bus_factor_risk = False
    bus_factor = num_contributors
    if contributors and total_commits > 0:
        top_author_commits = contributors[0].get("commits", 0)
        if top_author_commits / total_commits > 0.7:
            bus_factor_risk = True
            bus_factor = 1

    hottest_file = churn[0]["file"].split("/")[-1] if churn else "none"
    hottest_changes = churn[0]["changes"] if churn else 0
    total_churn = sum(c["changes"] for c in churn)
    top_churn_ratio = (hottest_changes / total_churn * 100) if total_churn else 0

    pace = round(total_commits / max(active_days, 1), 1)
    ghost_count = len([g for g in ghosts if g.get("status") == "ghost"])
    test_pct = type_pct.get("test", 0)
    personality = classify_personality(type_pct, bus_factor_risk)
    stability = compute_stability_score(type_pct, bus_factor, test_pct, top_churn_ratio)

    bar_width = round(stability * 2.8)
    if stability >= 60:
        stability_color = "#00d4aa"
    elif stability >= 35:
        stability_color = "#fbbf24"
    else:
        stability_color = "#ff6b6b"

    sorted_types = sorted(type_pct.items(), key=lambda x: -x[1])[:3]
    dna_text = " / ".join("%s %s%%" % (t, p) for t, p in sorted_types)

    if test_pct >= 10:
        test_label = "Strong"
        test_color = "#00d4aa"
    elif test_pct >= 3:
        test_label = "Moderate"
        test_color = "#fbbf24"
    else:
        test_label = "Weak"
        test_color = "#ff6b6b"

    if bus_factor >= 3:
        bf_label = "Healthy"
        bf_color = "#00d4aa"
    elif bus_factor == 2:
        bf_label = "Moderate"
        bf_color = "#fbbf24"
    else:
        bf_label = "Critical"
        bf_color = "#ff6b6b"

    emoji_char = EMOJI_MAP.get(personality["emoji"], "&#x2753;")

    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 520" width="440" height="520">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%%" stop-color="#0a0e14"/>
      <stop offset="100%%" stop-color="#0e1620"/>
    </linearGradient>
  </defs>
  <rect width="440" height="520" rx="16" fill="url(#bg)"/>
  <rect x="0" y="0" width="440" height="4" rx="2" fill="#00d4aa"/>
  <text x="28" y="40" font-family="monospace" font-size="10" fill="#00d4aa" letter-spacing="3">REPO DNA</text>
  <text x="28" y="70" font-family="monospace" font-size="22" fill="#ffffff" font-weight="bold">%s</text>
  <text x="28" y="90" font-family="monospace" font-size="11" fill="#3a5060">%s to %s / %d commits</text>
  <rect x="28" y="110" width="384" height="56" rx="10" fill="#00d4aa08" stroke="#00d4aa25" stroke-width="1"/>
  <text x="44" y="134" font-family="monospace" font-size="11" fill="#3a5060">PERSONALITY</text>
  <text x="44" y="154" font-family="monospace" font-size="16" fill="#ffffff" font-weight="bold">%s %s</text>
  <text x="28" y="196" font-family="monospace" font-size="10" fill="#3a5060" letter-spacing="2">STABILITY SCORE</text>
  <rect x="28" y="206" width="280" height="8" rx="4" fill="#141b22"/>
  <rect x="28" y="206" width="%d" height="8" rx="4" fill="%s"/>
  <text x="316" y="214" font-family="monospace" font-size="13" fill="%s" font-weight="bold">%d%%</text>
  <text x="44" y="250" font-family="monospace" font-size="10" fill="#3a5060">Hottest file</text>
  <text x="44" y="264" font-family="monospace" font-size="12" fill="#ffffff">%s (%dx)</text>
  <text x="250" y="250" font-family="monospace" font-size="10" fill="#3a5060">Test health</text>
  <text x="250" y="264" font-family="monospace" font-size="12" fill="%s">%s (%s%%)</text>
  <text x="44" y="294" font-family="monospace" font-size="10" fill="#3a5060">Ghost zones</text>
  <text x="44" y="308" font-family="monospace" font-size="12" fill="#ffffff">%d critical file%s</text>
  <text x="250" y="294" font-family="monospace" font-size="10" fill="#3a5060">Bus factor</text>
  <text x="250" y="308" font-family="monospace" font-size="12" fill="%s">%d (%s)</text>
  <line x1="28" y1="332" x2="412" y2="332" stroke="#1e2a35" stroke-width="1"/>
  <text x="44" y="356" font-family="monospace" font-size="10" fill="#3a5060">Commit pace</text>
  <text x="44" y="370" font-family="monospace" font-size="12" fill="#ffffff">%s/day / %d contributor%s</text>
  <text x="44" y="396" font-family="monospace" font-size="10" fill="#3a5060">Implicit couplings</text>
  <text x="44" y="410" font-family="monospace" font-size="12" fill="#ffffff">%d hidden pair%s</text>
  <line x1="28" y1="432" x2="412" y2="432" stroke="#1e2a35" stroke-width="1"/>
  <text x="28" y="456" font-family="monospace" font-size="10" fill="#3a5060" letter-spacing="2">COMMIT DNA</text>
  <text x="28" y="474" font-family="monospace" font-size="12" fill="#c8dce8">%s</text>
  <line x1="28" y1="492" x2="412" y2="492" stroke="#1e2a35" stroke-width="1"/>
  <text x="28" y="510" font-family="monospace" font-size="10" fill="#1e3a30">context-collapse.ghostskill.com</text>
</svg>""" % (
        _esc(name),
        first_commit, last_commit, total_commits,
        emoji_char, _esc(personality["name"]),
        bar_width, stability_color,
        stability_color, stability,
        _esc(hottest_file), hottest_changes,
        test_color, test_label, test_pct,
        ghost_count, "s" if ghost_count != 1 else "",
        bf_color, bus_factor, bf_label,
        pace, num_contributors, "s" if num_contributors != 1 else "",
        len(cochange), "s" if len(cochange) != 1 else "",
        _esc(dna_text),
    )
    return svg


def save_card(data, output_path="repo-card.svg"):
    svg = generate_card_svg(data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  Card saved: %s" % output_path)
    return output_path
