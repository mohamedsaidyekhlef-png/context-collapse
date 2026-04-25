from datetime import datetime


def render(data, output_path="cold-start-report.html"):
    meta = data["meta"]
    ai = data.get("ai", {})
    churn = data["churn"][:15]
    cochange = data["cochange"][:12]
    commits = data["commits"][:60]
    reentry = data["reentry_sequence"]
    commit_types = data["commit_types"]
    ghost_zones = data.get("ghost_zones", [])

    type_colors = {
        "feature": "#00d4aa", "fix": "#ff6b6b", "refactor": "#a78bfa",
        "performance": "#fbbf24", "test": "#60a5fa", "docs": "#94a3b8",
        "revert": "#f97316", "devops": "#e879f9", "security": "#f43f5e",
        "other": "#475569",
    }
    total_typed = sum(commit_types.values()) or 1

    try:
        from card_renderer import generate_card_svg, classify_personality, compute_stability_score
        total_churn = sum(c["changes"] for c in churn)
        top_churn_ratio = (churn[0]["changes"] / total_churn * 100) if total_churn and churn else 0
        type_pct = {k: round(v / total_typed * 100, 1) for k, v in commit_types.items()}
        bus_factor_risk = False
        contributors_list = meta.get("contributors", [])
        if contributors_list and meta["total_commits"] > 0:
            if contributors_list[0]["commits"] / meta["total_commits"] > 0.7:
                bus_factor_risk = True
        personality = classify_personality(type_pct, bus_factor_risk)
        bf = len(contributors_list) if not bus_factor_risk else 1
        stability = compute_stability_score(type_pct, bf, type_pct.get("test", 0), top_churn_ratio)
        card_svg = generate_card_svg(data)
    except Exception as e:
        print("  [Card] generation failed: %s" % e)
        card_svg = ""
        personality = {"name": "Unknown", "emoji": "building", "desc": ""}
        stability = 0

    commit_bars = ""
    for t, color in type_colors.items():
        count = commit_types.get(t, 0)
        if not count:
            continue
        pct = round(count / total_typed * 100, 1)
        commit_bars += '<div class="bar-row"><span class="bar-label">%s</span><div class="bar-track"><div class="bar-fill" style="width:%s%%;background:%s"></div></div><span class="bar-count">%d <span class="muted">(%s%%)</span></span></div>' % (t, pct, color, count, pct)

    churn_rows = ""
    max_churn = churn[0]["changes"] if churn else 1
    for i, f in enumerate(churn):
        pct = round(f["changes"] / max_churn * 100)
        rank = ["&#x1F947;", "&#x1F948;", "&#x1F949;"][i] if i < 3 else "%d." % (i+1)
        churn_rows += '<tr><td class="rank">%s</td><td class="filepath">%s</td><td><div class="mini-bar-track"><div class="mini-bar-fill" style="width:%d%%"></div></div></td><td class="change-count">%dx</td></tr>' % (rank, f["file"], pct, f["changes"])

    cochange_html = ""
    for p in cochange:
        fa = p["file_a"].split("/")[-1]
        fb = p["file_b"].split("/")[-1]
        cochange_html += '<div class="pair-card"><div class="pair-files"><span class="pair-file">%s</span><span class="pair-arrow">&#x27F7;</span><span class="pair-file">%s</span></div><div class="pair-meta">changed together <strong>%dx</strong></div></div>' % (fa, fb, p["co_changes"])

    reentry_html = ""
    for i, f in enumerate(reentry, 1):
        fname = f["file"].split("/")[-1]
        reentry_html += '<div class="reentry-step"><div class="step-num">%02d</div><div class="step-content"><div class="step-file">%s</div><div class="step-path">%s</div><div class="step-meta">%d changes / score %s</div></div></div>' % (i, fname, f["file"], f["changes"], f["score"])

    danger_html = ""
    for z in ai.get("danger_zones", []):
        files_html = "".join('<span class="dz-file">%s</span>' % fi for fi in z.get("files", []))
        severity_color = "#ff6b6b" if z.get("severity") == "high" else "#fbbf24"
        danger_html += '<div class="danger-card" style="border-color:%s25;background:%s08"><div class="danger-label" style="color:%s">&#x26A0; %s</div><div class="danger-warning">%s</div><div class="danger-files">%s</div></div>' % (severity_color, severity_color, severity_color, z.get("zone","Risk"), z.get("warning",""), files_html)

    decisions_html = ""
    for i, d in enumerate(ai.get("key_decisions", []), 1):
        decisions_html += '<div class="decision-item"><span class="decision-num">%d</span><span class="decision-text">%s</span></div>' % (i, d)

    commits_html = ""
    for c in commits[:20]:
        color = type_colors.get(c.get("type", "other"), "#475569")
        commits_html += '<div class="commit-row"><span class="commit-dot" style="background:%s"></span><span class="commit-hash">%s</span><span class="commit-date">%s</span><span class="commit-msg">%s</span><span class="commit-author">%s</span></div>' % (color, c["hash"], c["date"], c["message"][:80], c["author"].split()[0])

    contributors_html = ""
    for c in meta.get("contributors", [])[:5]:
        contributors_html += '<div class="contrib-row"><span>%s</span><span class="muted">%d commits</span></div>' % (c["name"], c["commits"])

    ai_badge = "&#x2726; AI-Enhanced" if ai.get("ai_powered") else "&#x25CC; Static Analysis"

    shock_block = ""
    shock = ai.get("shock_insight")
    if shock:
        shock_block = '<div class="shock-block"><div class="shock-label">&#x26A1; INSIGHT YOU DID NOT EXPECT</div><div class="shock-text">%s</div></div>' % shock

    ghost_html = ""
    if ghost_zones:
        for g in ghost_zones:
            if g["status"] == "ghost":
                status_label = "GHOST"
                status_color = "#a78bfa"
            else:
                status_label = "AT RISK"
                status_color = "#fbbf24"
            fname = g["file"].split("/")[-1]
            active_list = ", ".join(g.get("active_authors", [])[:2]) or "none"
            inactive_list = ", ".join(g.get("inactive_authors", [])[:2]) or "none"
            ghost_html += '<div class="ghost-card" style="border-color:%s25;background:%s06"><div class="ghost-header"><span class="ghost-status" style="color:%s">%s</span><span class="ghost-file">%s</span></div><div class="ghost-path">%s</div><div class="ghost-detail"><strong>%s</strong> owns %s%% of this file (%d/%d lines)</div><div class="ghost-detail">Last seen: <strong>%s</strong> (%d days ago)</div><div class="ghost-authors"><span class="ghost-tag active">Active: %s</span><span class="ghost-tag inactive">Inactive: %s</span></div></div>' % (status_color, status_color, status_color, status_label, fname, g["file"], g["ghost_author"], g["ownership_pct"], g["lines_owned"], g["total_lines"], g["last_seen"], g["days_inactive"], active_list, inactive_list)
    else:
        ghost_html = '<div class="muted" style="font-size:11px;padding:8px 0">No ghost zones detected -- all critical file authors are still active.</div>'

    personality_section = ""
    if card_svg:
        personality_section = '<div class="card" style="margin-bottom:20px"><div class="card-title">Repo Personality Card</div><div class="personality-wrap"><div class="personality-badge"><span class="personality-name">%s</span></div><div class="personality-desc">%s</div><div class="personality-stability"><span class="stability-label">Stability Score</span><div class="stability-track"><div class="stability-fill" style="width:%d%%"></div></div><span class="stability-value">%d%%</span></div><div class="personality-svg">%s</div></div></div>' % (personality["name"], personality["desc"], stability, stability, card_svg)

    now_str = datetime.now().strftime("%B %d, %Y")
    repo_name = meta["name"]
    total_c = meta["total_commits"]
    n_contribs = len(meta.get("contributors", []))
    n_churn = len(churn)
    n_cochange = len(cochange)
    n_dangers = len(ai.get("danger_zones", [])) + len(ghost_zones)
    n_ghosts = len(ghost_zones)
    first_c = meta["first_commit"]
    last_c = meta["last_commit"]

    html = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Cold Start Pack -- %s</title>\n' % repo_name
    html += '<style>\n'
    html += "@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Syne:wght@700;800&display=swap');\n"
    html += '*{box-sizing:border-box;margin:0;padding:0}\n'
    html += "body{background:#07090c;color:#c8dce8;font-family:'IBM Plex Mono',monospace;font-size:13px;line-height:1.6}\n"
    html += '.page{max-width:1100px;margin:0 auto;padding:48px 32px}\n'
    html += '.header-tag{font-size:11px;color:#00d4aa;letter-spacing:.2em;text-transform:uppercase;margin-bottom:12px}\n'
    html += ".header-title{font-family:'Syne',sans-serif;font-size:clamp(2rem,5vw,3.5rem);font-weight:800;color:#fff;letter-spacing:-.02em}\n"
    html += '.header-title span{color:#00d4aa}\n'
    html += '.header-sub{margin-top:12px;color:#3a5060;font-size:11px;display:flex;gap:20px;flex-wrap:wrap}\n'
    html += '.header-sub strong{color:#c8dce8}\n'
    html += '.ai-badge{display:inline-flex;align-items:center;gap:6px;background:#00d4aa15;border:1px solid #00d4aa33;color:#00d4aa;padding:4px 12px;border-radius:100px;font-size:11px;margin-top:14px}\n'
    html += '.shock-block{background:linear-gradient(135deg,#1a1200,#0e1318);border:1px solid #fbbf2440;border-radius:12px;padding:20px 24px;margin:0 0 24px}\n'
    html += '.shock-label{font-size:10px;color:#fbbf24;letter-spacing:.2em;text-transform:uppercase;margin-bottom:8px}\n'
    html += ".shock-text{font-family:'Syne',sans-serif;font-size:15px;font-weight:700;color:#fff;line-height:1.5}\n"
    html += '.purpose-block{background:linear-gradient(135deg,#0d1e1a,#0e1318);border:1px solid #00d4aa25;border-radius:12px;padding:24px 28px;margin-bottom:24px}\n'
    html += '.purpose-label{font-size:10px;color:#00d4aa;letter-spacing:.2em;text-transform:uppercase;margin-bottom:10px}\n'
    html += ".purpose-text{font-family:'Syne',sans-serif;font-size:14px;line-height:1.75;color:#c8dce8;max-width:800px}\n"
    html += '.stats-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-bottom:28px}\n'
    html += '.stat-pill{background:#0e1318;border:1px solid #1e2a35;border-radius:8px;padding:14px 18px}\n'
    html += ".stat-value{font-family:'Syne',sans-serif;font-size:24px;font-weight:800;color:#fff;display:block}\n"
    html += '.stat-label{color:#3a5060;font-size:11px}\n'
    html += '.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}\n'
    html += '@media(max-width:700px){.grid-2{grid-template-columns:1fr}}\n'
    html += '.card{background:#0e1318;border:1px solid #1e2a35;border-radius:10px;padding:22px}\n'
    html += ".card-title{font-size:10px;color:#3a5060;letter-spacing:.15em;text-transform:uppercase;margin-bottom:18px;display:flex;align-items:center;gap:8px}\n"
    html += ".card-title::before{content:'';display:inline-block;width:3px;height:12px;background:#00d4aa;border-radius:2px}\n"
    html += '.bar-row{display:grid;grid-template-columns:90px 1fr 80px;gap:8px;align-items:center;margin-bottom:8px}\n'
    html += '.bar-label{color:#3a5060;font-size:11px;text-transform:capitalize}\n'
    html += '.bar-track{background:#141b22;border-radius:100px;height:5px;overflow:hidden}\n'
    html += '.bar-fill{height:100%;border-radius:100px}\n'
    html += '.bar-count{color:#c8dce8;font-size:11px;text-align:right}\n'
    html += 'table{width:100%;border-collapse:collapse}\n'
    html += 'tr{border-bottom:1px solid #141b22}\n'
    html += 'tr:last-child{border-bottom:none}\n'
    html += 'td{padding:7px 4px;vertical-align:middle}\n'
    html += '.rank{color:#3a5060;font-size:12px;width:28px}\n'
    html += '.filepath{color:#c8dce8;font-size:11px;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n'
    html += '.mini-bar-track{background:#141b22;border-radius:100px;height:4px;width:80px;overflow:hidden}\n'
    html += '.mini-bar-fill{height:100%;background:#00d4aa;border-radius:100px}\n'
    html += '.change-count{color:#3a5060;font-size:11px;text-align:right}\n'
    html += '.reentry-step{display:flex;gap:16px;padding:12px 0;border-bottom:1px solid #141b22;align-items:flex-start}\n'
    html += '.reentry-step:last-child{border-bottom:none}\n'
    html += ".step-num{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#00d4aa;min-width:32px;line-height:1;padding-top:2px}\n"
    html += '.step-file{color:#fff;font-size:13px;margin-bottom:2px}\n'
    html += '.step-path{color:#3a5060;font-size:11px;margin-bottom:3px}\n'
    html += '.step-meta{color:#1e3525;font-size:10px}\n'
    html += '.pair-card{background:#141b22;border:1px solid #1e2a35;border-radius:8px;padding:10px 14px;margin-bottom:8px}\n'
    html += '.pair-files{display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap}\n'
    html += '.pair-file{background:#ff6b6b15;border:1px solid #ff6b6b30;color:#ff6b6b;padding:2px 8px;border-radius:4px;font-size:11px}\n'
    html += '.pair-arrow{color:#3a5060}\n'
    html += '.pair-meta{color:#3a5060;font-size:11px}\n'
    html += '.danger-card{border-radius:8px;padding:14px 16px;margin-bottom:8px}\n'
    html += '.danger-label{font-size:12px;font-weight:600;margin-bottom:6px}\n'
    html += '.danger-warning{color:#c8dce8;font-size:12px;line-height:1.6;margin-bottom:8px}\n'
    html += '.danger-files{display:flex;flex-wrap:wrap;gap:6px}\n'
    html += '.dz-file{background:#fbbf2415;border:1px solid #fbbf2430;color:#fbbf24;padding:2px 8px;border-radius:4px;font-size:10px}\n'
    html += '.decision-item{display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #141b22;align-items:flex-start}\n'
    html += '.decision-item:last-child{border-bottom:none}\n'
    html += ".decision-num{color:#60a5fa;min-width:20px;font-family:'Syne',sans-serif;font-size:16px;font-weight:800}\n"
    html += '.decision-text{color:#c8dce8;font-size:12px;line-height:1.6}\n'
    html += '.commit-row{display:grid;grid-template-columns:10px 60px 80px 1fr 80px;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid #0d1318;font-size:11px}\n'
    html += '.commit-row:last-child{border-bottom:none}\n'
    html += '.commit-dot{width:7px;height:7px;border-radius:50%;display:inline-block;flex-shrink:0}\n'
    html += '.commit-hash{color:#00d4aa}\n'
    html += '.commit-date{color:#3a5060}\n'
    html += '.commit-msg{color:#c8dce8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n'
    html += '.commit-author{color:#3a5060;text-align:right;overflow:hidden;text-overflow:ellipsis}\n'
    html += '.contrib-row{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #141b22;font-size:12px}\n'
    html += '.contrib-row:last-child{border-bottom:none}\n'
    html += '.muted{color:#3a5060}\n'
    html += '.footer{margin-top:48px;padding-top:20px;border-top:1px solid #1e2a35;color:#1e3040;font-size:11px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}\n'
    html += '.ghost-card{border:1px solid;border-radius:10px;padding:16px 18px;margin-bottom:10px}\n'
    html += '.ghost-header{display:flex;align-items:center;gap:10px;margin-bottom:6px}\n'
    html += '.ghost-status{font-size:11px;font-weight:700;letter-spacing:.15em;text-transform:uppercase}\n'
    html += '.ghost-file{color:#fff;font-size:13px;font-weight:600}\n'
    html += '.ghost-path{color:#3a5060;font-size:11px;margin-bottom:8px}\n'
    html += '.ghost-detail{color:#c8dce8;font-size:12px;line-height:1.7}\n'
    html += '.ghost-authors{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}\n'
    html += '.ghost-tag{font-size:10px;padding:3px 10px;border-radius:100px}\n'
    html += '.ghost-tag.active{background:#00d4aa15;color:#00d4aa;border:1px solid #00d4aa30}\n'
    html += '.ghost-tag.inactive{background:#ff6b6b15;color:#ff6b6b;border:1px solid #ff6b6b30}\n'
    html += '.personality-wrap{padding:8px 0}\n'
    html += '.personality-badge{display:flex;align-items:center;gap:12px;margin-bottom:12px}\n'
    html += ".personality-name{font-family:'Syne',sans-serif;font-size:24px;font-weight:800;color:#fff}\n"
    html += '.personality-desc{color:#3a5060;font-size:12px;line-height:1.7;margin-bottom:18px}\n'
    html += '.personality-stability{display:flex;align-items:center;gap:12px;margin-bottom:20px}\n'
    html += '.stability-label{color:#3a5060;font-size:11px;min-width:100px}\n'
    html += '.stability-track{flex:1;height:8px;background:#141b22;border-radius:100px;overflow:hidden}\n'
    html += '.stability-fill{height:100%;background:linear-gradient(90deg,#ff6b6b,#fbbf24,#00d4aa);border-radius:100px}\n'
    html += '.stability-value{color:#00d4aa;font-size:14px;font-weight:700;min-width:40px}\n'
    html += '.personality-svg{margin:16px 0;text-align:center;overflow:hidden;border-radius:12px;border:1px solid #1e2a35}\n'
    html += '.personality-svg svg{max-width:100%;height:auto}\n'
    html += '</style>\n</head>\n<body>\n<div class="page">\n'

    html += '<header style="border-bottom:1px solid #1e2a35;padding-bottom:28px;margin-bottom:32px">\n'
    html += '  <div class="header-tag">context-collapse / Cold Start Pack</div>\n'
    html += '  <h1 class="header-title"><span>%s</span> Re-Entry Report</h1>\n' % repo_name
    html += '  <div class="header-sub">\n'
    html += '    <span>Generated <strong>%s</strong></span>\n' % now_str
    html += '    <span>First commit <strong>%s</strong></span>\n' % first_c
    html += '    <span>Last activity <strong>%s</strong></span>\n' % last_c
    html += '  </div>\n'
    html += '  <div class="ai-badge">%s</div>\n' % ai_badge
    html += '</header>\n'

    html += '<div class="stats-row">\n'
    html += '  <div class="stat-pill"><span class="stat-value">%s</span><span class="stat-label">total commits</span></div>\n' % "{:,}".format(total_c)
    html += '  <div class="stat-pill"><span class="stat-value">%d</span><span class="stat-label">contributors</span></div>\n' % n_contribs
    html += '  <div class="stat-pill"><span class="stat-value">%d</span><span class="stat-label">active files</span></div>\n' % n_churn
    html += '  <div class="stat-pill"><span class="stat-value">%d</span><span class="stat-label">implicit couplings</span></div>\n' % n_cochange
    html += '  <div class="stat-pill"><span class="stat-value">%d</span><span class="stat-label">danger zones</span></div>\n' % n_dangers
    html += '  <div class="stat-pill"><span class="stat-value">%d</span><span class="stat-label">ghost zones</span></div>\n' % n_ghosts
    html += '</div>\n'

    html += shock_block + '\n'
    html += personality_section + '\n'

    html += '<div class="purpose-block">\n'
    html += '  <div class="purpose-label">Project Purpose / AI Inference</div>\n'
    html += '  <div class="purpose-text">%s</div>\n' % ai.get("purpose", "Set GEMINI_API_KEY for AI-powered analysis.")
    html += '</div>\n'

    html += '<div class="grid-2">\n'
    html += '  <div class="card"><div class="card-title">Re-Entry Reading Sequence</div>%s</div>\n' % reentry_html
    html += '  <div class="card"><div class="card-title">Key Architectural Decisions</div>%s</div>\n' % decisions_html
    html += '</div>\n'

    html += '<div class="grid-2">\n'
    html += '  <div class="card"><div class="card-title">Ghost Zones -- Abandoned Ownership</div>%s</div>\n' % ghost_html
    danger_content = danger_html or '<div class="muted" style="font-size:11px;padding:8px 0">No danger zones detected.</div>'
    html += '  <div class="card"><div class="card-title">Danger Zones</div>%s</div>\n' % danger_content
    html += '</div>\n'

    html += '<div class="grid-2">\n'
    cochange_content = cochange_html or '<div class="muted" style="font-size:11px;padding:8px 0">No coupling pairs detected.</div>'
    html += '  <div class="card"><div class="card-title">Implicit Coupling Map</div>%s</div>\n' % cochange_content
    html += '  <div class="card"><div class="card-title">File Churn Heatmap</div><table>%s</table></div>\n' % churn_rows
    html += '</div>\n'

    html += '<div class="grid-2">\n'
    html += '  <div class="card"><div class="card-title">Commit DNA</div>%s<div style="margin-top:24px"><div class="card-title">Top Contributors</div>%s</div></div>\n' % (commit_bars, contributors_html)
    html += '  <div class="card"><div class="card-title">Recent Commit Timeline</div>%s</div>\n' % commits_html
    html += '</div>\n'

    html += '<footer class="footer">\n'
    html += '  <span>context-collapse / Cold Start Pack</span>\n'
    html += '  <span>Understand any codebase in 30 minutes -- not 3 days.</span>\n'
    html += '</footer>\n'
    html += '</div>\n</body>\n</html>'

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("  Report saved: %s" % output_path)
    return output_path
