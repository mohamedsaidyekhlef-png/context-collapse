"""
Repo Personality Card - Spotify-Wrapped-style SVG identity card for any git repo.
Now with animated SVG avatars per personality archetype.
"""
import json


ARCHETYPES = [
    {
        "id": "perfectionist",
        "name": "The Perfectionist",
        "emoji": "target",
        "desc": "Obsessed with quality. Refactors before adding features.",
        "match": lambda d: d.get("refactor", 0) + d.get("fix", 0) > 50 and d.get("test", 0) > 5,
        "avatar_color": "#00d4aa",
        "avatar_bg": "#0d1e1a",
    },
    {
        "id": "firefighter",
        "name": "The Firefighter",
        "emoji": "fire",
        "desc": "More time fixing than building. The codebase fights back.",
        "match": lambda d: d.get("fix", 0) > 35,
        "avatar_color": "#ff6b6b",
        "avatar_bg": "#1e0d0d",
    },
    {
        "id": "speedrunner",
        "name": "Move Fast and Break Things",
        "emoji": "rocket",
        "desc": "Feature velocity is everything. Tests? Maybe later.",
        "match": lambda d: d.get("feature", 0) > 40 and d.get("test", 0) < 3,
        "avatar_color": "#00d4aa",
        "avatar_bg": "#0d1e1a",
    },
    {
        "id": "ghost_ship",
        "name": "The Ghost Ship",
        "emoji": "ghost",
        "desc": "One person drives the entire project. Knowledge is concentrated.",
        "match": lambda d: d.get("_bus_factor_risk", False),
        "avatar_color": "#a78bfa",
        "avatar_bg": "#150d1e",
    },
    {
        "id": "documentation_nerd",
        "name": "The Documentation Nerd",
        "emoji": "books",
        "desc": "Commits are well-documented. Docs ratio is unusually high.",
        "match": lambda d: d.get("docs", 0) > 12,
        "avatar_color": "#60a5fa",
        "avatar_bg": "#0d141e",
    },
    {
        "id": "test_driven",
        "name": "Test-Driven Machine",
        "emoji": "lab",
        "desc": "Tests come first. High confidence in every change.",
        "match": lambda d: d.get("test", 0) > 15,
        "avatar_color": "#60a5fa",
        "avatar_bg": "#0d141e",
    },
    {
        "id": "devops_warrior",
        "name": "The DevOps Warrior",
        "emoji": "gear",
        "desc": "Pipeline tweaking is a lifestyle. CI/CD is always evolving.",
        "match": lambda d: d.get("devops", 0) > 10,
        "avatar_color": "#e879f9",
        "avatar_bg": "#1e0d1e",
    },
    {
        "id": "steady_builder",
        "name": "The Steady Builder",
        "emoji": "building",
        "desc": "Balanced mix of features, fixes, and maintenance. Sustainable pace.",
        "match": lambda d: True,
        "avatar_color": "#fbbf24",
        "avatar_bg": "#1e1a0d",
    },
]


AVATAR_SVG = {
    "target": '<circle cx="60" cy="60" r="28" fill="none" stroke="{c}" stroke-width="2" opacity="0.3"><animate attributeName="r" values="28;32;28" dur="3s" repeatCount="indefinite"/></circle><circle cx="60" cy="60" r="18" fill="none" stroke="{c}" stroke-width="2" opacity="0.5"/><circle cx="60" cy="60" r="8" fill="{c}" opacity="0.8"><animate attributeName="r" values="8;10;8" dur="2s" repeatCount="indefinite"/></circle><line x1="60" y1="30" x2="60" y2="90" stroke="{c}" stroke-width="1" opacity="0.2"/><line x1="30" y1="60" x2="90" y2="60" stroke="{c}" stroke-width="1" opacity="0.2"/>',

    "fire": '<path d="M60 85 C45 85 35 70 35 58 C35 42 48 35 52 28 C53 38 58 42 60 42 C62 42 67 38 68 28 C72 35 85 42 85 58 C85 70 75 85 60 85Z" fill="{c}" opacity="0.15"><animate attributeName="opacity" values="0.15;0.25;0.15" dur="1.5s" repeatCount="indefinite"/></path><path d="M60 85 C50 85 42 74 42 65 C42 52 52 46 55 40 C56 48 59 50 60 50 C61 50 64 48 65 40 C68 46 78 52 78 65 C78 74 70 85 60 85Z" fill="{c}" opacity="0.3"/><path d="M60 85 C54 85 49 78 49 72 C49 64 55 60 57 55 C58 60 60 62 60 62 C60 62 62 60 63 55 C65 60 71 64 71 72 C71 78 66 85 60 85Z" fill="{c}" opacity="0.5"><animate attributeName="d" values="M60 85 C54 85 49 78 49 72 C49 64 55 60 57 55 C58 60 60 62 60 62 C60 62 62 60 63 55 C65 60 71 64 71 72 C71 78 66 85 60 85Z;M60 82 C54 82 49 76 49 70 C49 62 55 58 57 52 C58 58 60 60 60 60 C60 60 62 58 63 52 C65 58 71 62 71 70 C71 76 66 82 60 82Z;M60 85 C54 85 49 78 49 72 C49 64 55 60 57 55 C58 60 60 62 60 62 C60 62 62 60 63 55 C65 60 71 64 71 72 C71 78 66 85 60 85Z" dur="2s" repeatCount="indefinite"/></path>',

    "rocket": '<path d="M60 30 C60 30 45 45 45 65 C45 75 52 82 60 85 C68 82 75 75 75 65 C75 45 60 30 60 30Z" fill="{c}" opacity="0.2"><animate attributeName="opacity" values="0.2;0.3;0.2" dur="2s" repeatCount="indefinite"/></path><path d="M60 35 C60 35 50 48 50 63 C50 71 54 77 60 80 C66 77 70 71 70 63 C70 48 60 35 60 35Z" fill="{c}" opacity="0.4"/><circle cx="60" cy="58" r="5" fill="{bg}"/><path d="M48 72 L40 82 L50 78Z" fill="{c}" opacity="0.3"/><path d="M72 72 L80 82 L70 78Z" fill="{c}" opacity="0.3"/><line x1="60" y1="82" x2="60" y2="95" stroke="{c}" stroke-width="2" opacity="0.3"><animate attributeName="y2" values="95;100;95" dur="0.8s" repeatCount="indefinite"/></line><line x1="55" y1="84" x2="53" y2="95" stroke="{c}" stroke-width="1.5" opacity="0.2"><animate attributeName="y2" values="95;98;95" dur="1s" repeatCount="indefinite"/></line><line x1="65" y1="84" x2="67" y2="95" stroke="{c}" stroke-width="1.5" opacity="0.2"><animate attributeName="y2" values="95;98;95" dur="1.2s" repeatCount="indefinite"/></line>',

    "ghost": '<ellipse cx="60" cy="58" rx="22" ry="26" fill="{c}" opacity="0.15"><animate attributeName="ry" values="26;28;26" dur="3s" repeatCount="indefinite"/></ellipse><ellipse cx="60" cy="58" rx="18" ry="22" fill="{c}" opacity="0.25"/><path d="M42 65 C42 65 42 88 42 88 L48 82 L54 88 L60 82 L66 88 L72 82 L78 88 C78 88 78 65 78 65" fill="{c}" opacity="0.25"><animate attributeName="d" values="M42 65 C42 65 42 88 42 88 L48 82 L54 88 L60 82 L66 88 L72 82 L78 88 C78 88 78 65 78 65;M42 65 C42 65 42 90 42 90 L48 84 L54 90 L60 84 L66 90 L72 84 L78 90 C78 90 78 65 78 65;M42 65 C42 65 42 88 42 88 L48 82 L54 88 L60 82 L66 88 L72 82 L78 88 C78 88 78 65 78 65" dur="4s" repeatCount="indefinite"/></path><circle cx="52" cy="52" r="4" fill="{bg}"/><circle cx="68" cy="52" r="4" fill="{bg}"/><circle cx="52" cy="53" r="2" fill="{c}" opacity="0.6"><animate attributeName="cx" values="52;54;52" dur="5s" repeatCount="indefinite"/></circle><circle cx="68" cy="53" r="2" fill="{c}" opacity="0.6"><animate attributeName="cx" values="68;66;68" dur="5s" repeatCount="indefinite"/></circle>',

    "books": '<rect x="38" y="35" width="14" height="50" rx="2" fill="{c}" opacity="0.4" transform="rotate(-5 45 60)"/><rect x="50" y="33" width="12" height="52" rx="2" fill="{c}" opacity="0.3"/><rect x="60" y="36" width="14" height="48" rx="2" fill="{c}" opacity="0.5" transform="rotate(3 67 60)"/><rect x="72" y="38" width="10" height="46" rx="2" fill="{c}" opacity="0.2" transform="rotate(8 77 60)"/><line x1="44" y1="42" x2="44" y2="48" stroke="{bg}" stroke-width="1.5" opacity="0.5"/><line x1="56" y1="40" x2="56" y2="46" stroke="{bg}" stroke-width="1.5" opacity="0.5"/><line x1="66" y1="43" x2="66" y2="49" stroke="{bg}" stroke-width="1.5" opacity="0.5"/><circle cx="56" cy="28" r="3" fill="{c}" opacity="0.3"><animate attributeName="opacity" values="0.3;0.6;0.3" dur="2s" repeatCount="indefinite"/></circle><circle cx="48" cy="25" r="2" fill="{c}" opacity="0.2"><animate attributeName="opacity" values="0.2;0.5;0.2" dur="3s" repeatCount="indefinite"/></circle><circle cx="64" cy="26" r="2.5" fill="{c}" opacity="0.25"><animate attributeName="opacity" values="0.25;0.55;0.25" dur="2.5s" repeatCount="indefinite"/></circle>',

    "lab": '<path d="M52 35 L52 55 L38 80 C36 84 39 88 43 88 L77 88 C81 88 84 84 82 80 L68 55 L68 35Z" fill="{c}" opacity="0.15"/><rect x="50" y="30" width="20" height="8" rx="2" fill="{c}" opacity="0.3"/><path d="M52 55 L68 55" stroke="{c}" stroke-width="1" opacity="0.3"/><circle cx="55" cy="72" r="4" fill="{c}" opacity="0.4"><animate attributeName="r" values="4;5;4" dur="2s" repeatCount="indefinite"/></circle><circle cx="65" cy="68" r="3" fill="{c}" opacity="0.3"><animate attributeName="r" values="3;4;3" dur="1.5s" repeatCount="indefinite"/></circle><circle cx="58" cy="78" r="2.5" fill="{c}" opacity="0.35"><animate attributeName="cy" values="78;76;78" dur="2.5s" repeatCount="indefinite"/></circle>',

    "gear": '<circle cx="60" cy="60" r="20" fill="none" stroke="{c}" stroke-width="3" opacity="0.3"><animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="10s" repeatCount="indefinite"/></circle><circle cx="60" cy="60" r="8" fill="{c}" opacity="0.3"/><line x1="60" y1="38" x2="60" y2="32" stroke="{c}" stroke-width="4" stroke-linecap="round" opacity="0.4"/><line x1="60" y1="82" x2="60" y2="88" stroke="{c}" stroke-width="4" stroke-linecap="round" opacity="0.4"/><line x1="38" y1="60" x2="32" y2="60" stroke="{c}" stroke-width="4" stroke-linecap="round" opacity="0.4"/><line x1="82" y1="60" x2="88" y2="60" stroke="{c}" stroke-width="4" stroke-linecap="round" opacity="0.4"/><line x1="44" y1="44" x2="40" y2="40" stroke="{c}" stroke-width="4" stroke-linecap="round" opacity="0.4"/><line x1="76" y1="76" x2="80" y2="80" stroke="{c}" stroke-width="4" stroke-linecap="round" opacity="0.4"/><line x1="76" y1="44" x2="80" y2="40" stroke="{c}" stroke-width="4" stroke-linecap="round" opacity="0.4"/><line x1="44" y1="76" x2="40" y2="80" stroke="{c}" stroke-width="4" stroke-linecap="round" opacity="0.4"/>',

    "building": '<rect x="40" y="45" width="40" height="42" rx="2" fill="{c}" opacity="0.2"/><rect x="35" y="42" width="50" height="6" rx="1" fill="{c}" opacity="0.3"/><rect x="46" y="52" width="6" height="6" rx="1" fill="{c}" opacity="0.4"/><rect x="56" y="52" width="6" height="6" rx="1" fill="{c}" opacity="0.4"/><rect x="68" y="52" width="6" height="6" rx="1" fill="{c}" opacity="0.4"/><rect x="46" y="62" width="6" height="6" rx="1" fill="{c}" opacity="0.4"/><rect x="56" y="62" width="6" height="6" rx="1" fill="{c}" opacity="0.4"/><rect x="68" y="62" width="6" height="6" rx="1" fill="{c}" opacity="0.4"/><rect x="54" y="74" width="12" height="13" rx="1" fill="{c}" opacity="0.35"/><path d="M60 30 L40 42 L80 42 Z" fill="{c}" opacity="0.25"/><circle cx="60" cy="36" r="2" fill="{c}" opacity="0.5"><animate attributeName="opacity" values="0.5;0.8;0.5" dur="2s" repeatCount="indefinite"/></circle>',
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

    avatar_key = personality.get("emoji", "building")
    avatar_c = personality.get("avatar_color", "#00d4aa")
    avatar_bg = personality.get("avatar_bg", "#0e1318")
    avatar_svg = AVATAR_SVG.get(avatar_key, AVATAR_SVG["building"])
    avatar_svg = avatar_svg.replace("{c}", avatar_c).replace("{bg}", avatar_bg)

    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 560" width="440" height="560">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%%" stop-color="#0a0e14"/>
      <stop offset="100%%" stop-color="#0e1620"/>
    </linearGradient>
    <radialGradient id="avatarGlow" cx="50%%" cy="50%%" r="50%%">
      <stop offset="0%%" stop-color="%s" stop-opacity="0.15"/>
      <stop offset="100%%" stop-color="%s" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="440" height="560" rx="16" fill="url(#bg)"/>
  <rect x="0" y="0" width="440" height="4" rx="2" fill="%s"/>

  <!-- Avatar -->
  <circle cx="60" cy="60" r="40" fill="url(#avatarGlow)"/>
  <g transform="translate(0,0)">%s</g>

  <!-- Header -->
  <text x="110" y="44" font-family="monospace" font-size="10" fill="%s" letter-spacing="3">REPO DNA</text>
  <text x="110" y="68" font-family="monospace" font-size="20" fill="#ffffff" font-weight="bold">%s</text>
  <text x="110" y="86" font-family="monospace" font-size="10" fill="#3a5060">%s to %s / %d commits</text>

  <!-- Personality Badge -->
  <rect x="28" y="110" width="384" height="48" rx="10" fill="%s" stroke="%s25" stroke-width="1"/>
  <text x="44" y="130" font-family="monospace" font-size="10" fill="#3a5060" letter-spacing="1">PERSONALITY</text>
  <text x="44" y="148" font-family="monospace" font-size="15" fill="#ffffff" font-weight="bold">%s</text>

  <!-- Stability Score -->
  <text x="28" y="186" font-family="monospace" font-size="10" fill="#3a5060" letter-spacing="2">STABILITY SCORE</text>
  <rect x="28" y="196" width="280" height="8" rx="4" fill="#141b22"/>
  <rect x="28" y="196" width="%d" height="8" rx="4" fill="%s">
    <animate attributeName="width" from="0" to="%d" dur="1s" fill="freeze"/>
  </rect>
  <text x="316" y="204" font-family="monospace" font-size="13" fill="%s" font-weight="bold">%d%%%%</text>

  <!-- Stats -->
  <text x="44" y="238" font-family="monospace" font-size="10" fill="#3a5060">Hottest file</text>
  <text x="44" y="252" font-family="monospace" font-size="12" fill="#ffffff">%s (%dx)</text>
  <text x="250" y="238" font-family="monospace" font-size="10" fill="#3a5060">Test health</text>
  <text x="250" y="252" font-family="monospace" font-size="12" fill="%s">%s (%s%%%%)</text>

  <text x="44" y="282" font-family="monospace" font-size="10" fill="#3a5060">Ghost zones</text>
  <text x="44" y="296" font-family="monospace" font-size="12" fill="#ffffff">%d critical file%s</text>
  <text x="250" y="282" font-family="monospace" font-size="10" fill="#3a5060">Bus factor</text>
  <text x="250" y="296" font-family="monospace" font-size="12" fill="%s">%d (%s)</text>

  <line x1="28" y1="318" x2="412" y2="318" stroke="#1e2a35" stroke-width="1"/>

  <text x="44" y="342" font-family="monospace" font-size="10" fill="#3a5060">Commit pace</text>
  <text x="44" y="356" font-family="monospace" font-size="12" fill="#ffffff">%s/day / %d contributor%s</text>
  <text x="44" y="382" font-family="monospace" font-size="10" fill="#3a5060">Implicit couplings</text>
  <text x="44" y="396" font-family="monospace" font-size="12" fill="#ffffff">%d hidden pair%s</text>

  <line x1="28" y1="418" x2="412" y2="418" stroke="#1e2a35" stroke-width="1"/>

  <!-- DNA -->
  <text x="28" y="442" font-family="monospace" font-size="10" fill="#3a5060" letter-spacing="2">COMMIT DNA</text>
  <text x="28" y="460" font-family="monospace" font-size="12" fill="#c8dce8">%s</text>

  <!-- DNA mini bar -->
  <rect x="28" y="474" width="384" height="6" rx="3" fill="#141b22"/>""" % (
        avatar_c, avatar_c, avatar_c,
        avatar_svg,
        avatar_c,
        _esc(name),
        first_commit, last_commit, total_commits,
        avatar_bg, avatar_c,
        _esc(personality["name"]),
        bar_width, stability_color, bar_width,
        stability_color, stability,
        _esc(hottest_file), hottest_changes,
        test_color, test_label, test_pct,
        ghost_count, "s" if ghost_count != 1 else "",
        bf_color, bus_factor, bf_label,
        pace, num_contributors, "s" if num_contributors != 1 else "",
        len(cochange), "s" if len(cochange) != 1 else "",
        _esc(dna_text),
    )

    # Add DNA mini color bar segments
    x_offset = 28
    total_w = 384
    for t, p in sorted_types:
        seg_w = round(p / 100.0 * total_w)
        color = {"feature": "#00d4aa", "fix": "#ff6b6b", "refactor": "#a78bfa", "docs": "#94a3b8", "test": "#60a5fa", "other": "#475569"}.get(t, "#475569")
        svg += '\n  <rect x="%d" y="474" width="%d" height="6" rx="0" fill="%s" opacity="0.7"/>' % (x_offset, seg_w, color)
        x_offset += seg_w

    svg += """

  <!-- Footer -->
  <line x1="28" y1="500" x2="412" y2="500" stroke="#1e2a35" stroke-width="1"/>
  <text x="28" y="520" font-family="monospace" font-size="10" fill="#1e3a30">context-collapse.ghostskill.com</text>
  <text x="412" y="520" font-family="monospace" font-size="10" fill="#1e3a30" text-anchor="end">Analyze any repo free</text>

  <!-- Scan lines overlay -->
  <rect width="440" height="560" rx="16" fill="url(#bg)" opacity="0.02"/>
</svg>"""

    return svg


def save_card(data, output_path="repo-card.svg"):
    svg = generate_card_svg(data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  Card saved: %s" % output_path)
    return output_path
