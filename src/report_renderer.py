from datetime import datetime


def render(data, output_path="cold-start-report.html"):
    meta = data["meta"]
    ai = data.get("ai", {})
    churn = data["churn"][:15]
    cochange = data["cochange"][:12]
    commits = data["commits"][:60]
    reentry = data["reentry_sequence"]
    commit_types = data["commit_types"]

    type_colors = {"feature":"#00d4aa","fix":"#ff6b6b","refactor":"#a78bfa","performance":"#fbbf24","test":"#60a5fa","docs":"#94a3b8","revert":"#f97316","other":"#475569"}
    total_typed = sum(commit_types.values()) or 1

    commit_bars = ""
    for t, color in type_colors.items():
        count = commit_types.get(t, 0)
        if not count: continue
        pct = round(count / total_typed * 100, 1)
        commit_bars += f'<div class="bar-row"><span class="bar-label">{t}</span><div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color}"></div></div><span class="bar-count">{count}</span></div>'

    churn_rows = ""
    max_churn = churn[0]["changes"] if churn else 1
    medals = ["gold","silver","#cd7f32"]
    for i, f in enumerate(churn):
        pct = round(f["changes"] / max_churn * 100)
        rank = ["🥇","🥈","🥉"][i] if i < 3 else f"{i+1}."
        churn_rows += f'<tr><td class="rank">{rank}</td><td class="filepath">{f["file"]}</td><td><div class="mini-bar-track"><div class="mini-bar-fill" style="width:{pct}%"></div></div></td><td class="change-count">{f["changes"]}x</td></tr>'

    cochange_html = ""
    for p in cochange:
        fa = p["file_a"].split("/")[-1]
        fb = p["file_b"].split("/")[-1]
        cochange_html += f'<div class="pair-card"><div class="pair-files"><span class="pair-file">{fa}</span><span class="pair-arrow">⟷</span><span class="pair-file">{fb}</span></div><div class="pair-meta">changed together <strong>{p["co_changes"]}x</strong></div></div>'

    reentry_html = ""
    for i, f in enumerate(reentry, 1):
        fname = f["file"].split("/")[-1]
        reentry_html += f'<div class="reentry-step"><div class="step-num">{i:02d}</div><div class="step-content"><div class="step-file">{fname}</div><div class="step-path">{f["file"]}</div><div class="step-meta">{f["changes"]} changes · score {f["score"]}</div></div></div>'

    danger_html = ""
    for z in ai.get("danger_zones", []):
        files_html = "".join(f'<span class="dz-file">{fi}</span>' for fi in z.get("files", []))
        danger_html += f'<div class="danger-card"><div class="danger-label">⚠ {z.get("zone","Risk")}</div><div class="danger-warning">{z.get("warning","")}</div><div class="danger-files">{files_html}</div></div>'

    decisions_html = ""
    for i, d in enumerate(ai.get("key_decisions", []), 1):
        decisions_html += f'<div class="decision-item"><span class="decision-num">{i}</span><span class="decision-text">{d}</span></div>'

    commits_html = ""
    for c in commits[:20]:
        color = type_colors.get(c.get("type","other"), "#475569")
        commits_html += f'<div class="commit-row"><span class="commit-dot" style="background:{color}"></span><span class="commit-hash">{c["hash"]}</span><span class="commit-date">{c["date"]}</span><span class="commit-msg">{c["message"][:80]}</span><span class="commit-author">{c["author"].split()[0]}</span></div>'

    contributors_html = ""
    for c in meta.get("contributors", [])[:5]:
        contributors_html += f'<div class="contrib-row"><span>{c["name"]}</span><span class="muted">{c["commits"]} commits</span></div>'

    ai_badge = "✦ AI-Enhanced" if ai.get("ai_powered") else "◌ Static Analysis"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Cold Start Pack — {meta["name"]}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Syne:wght@700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#07090c;color:#c8dce8;font-family:'IBM Plex Mono',monospace;font-size:13px;line-height:1.6}}
.page{{max-width:1100px;margin:0 auto;padding:48px 32px}}
.header-tag{{font-size:11px;color:#00d4aa;letter-spacing:.2em;text-transform:uppercase;margin-bottom:12px}}
.header-title{{font-family:'Syne',sans-serif;font-size:clamp(2rem,5vw,3.5rem);font-weight:800;color:#fff;letter-spacing:-.02em}}
.header-title span{{color:#00d4aa}}
.header-sub{{margin-top:12px;color:#3a5060;font-size:11px;display:flex;gap:20px;flex-wrap:wrap}}
.header-sub strong{{color:#c8dce8}}
.ai-badge{{display:inline-flex;align-items:center;gap:6px;background:#00d4aa15;border:1px solid #00d4aa33;color:#00d4aa;padding:4px 12px;border-radius:100px;font-size:11px;margin-top:14px}}
.purpose-block{{background:linear-gradient(135deg,#0d1e1a,#0e1318);border:1px solid #00d4aa25;border-radius:12px;padding:24px 28px;margin:32px 0}}
.purpose-label{{font-size:10px;color:#00d4aa;letter-spacing:.2em;text-transform:uppercase;margin-bottom:10px}}
.purpose-text{{font-family:'Syne',sans-serif;font-size:14px;line-height:1.75;color:#c8dce8;max-width:800px}}
.stats-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-bottom:28px}}
.stat-pill{{background:#0e1318;border:1px solid #1e2a35;border-radius:8px;padding:14px 18px}}
.stat-value{{font-family:'Syne',sans-serif;font-size:24px;font-weight:800;color:#fff;display:block}}
.stat-label{{color:#3a5060;font-size:11px}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}}
.card{{background:#0e1318;border:1px solid #1e2a35;border-radius:10px;padding:22px}}
.card-title{{font-size:10px;color:#3a5060;letter-spacing:.15em;text-transform:uppercase;margin-bottom:18px;display:flex;align-items:center;gap:8px}}
.card-title::before{{content:'';display:inline-block;width:3px;height:12px;background:#00d4aa;border-radius:2px}}
.bar-row{{display:grid;grid-template-columns:90px 1fr 40px;gap:8px;align-items:center;margin-bottom:8px}}
.bar-label{{color:#3a5060;font-size:11px;text-transform:capitalize}}
.bar-track{{background:#141b22;border-radius:100px;height:5px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:100px}}
.bar-count{{color:#c8dce8;font-size:11px;text-align:right}}
table{{width:100%;border-collapse:collapse}}
tr{{border-bottom:1px solid #141b22}}
tr:last-child{{border-bottom:none}}
td{{padding:7px 4px;vertical-align:middle}}
.rank{{color:#3a5060;font-size:12px;width:28px}}
.filepath{{color:#c8dce8;font-size:11px;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.mini-bar-track{{background:#141b22;border-radius:100px;height:4px;width:80px;overflow:hidden}}
.mini-bar-fill{{height:100%;background:#00d4aa;border-radius:100px}}
.change-count{{color:#3a5060;font-size:11px;text-align:right}}
.reentry-step{{display:flex;gap:16px;padding:12px 0;border-bottom:1px solid #141b22;align-items:flex-start}}
.reentry-step:last-child{{border-bottom:none}}
.step-num{{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#00d4aa;min-width:32px;line-height:1;padding-top:2px}}
.step-file{{color:#fff;font-size:13px;margin-bottom:2px}}
.step-path{{color:#3a5060;font-size:11px;margin-bottom:3px}}
.step-meta{{color:#1e3525;font-size:10px}}
.pair-card{{background:#141b22;border:1px solid #1e2a35;border-radius:8px;padding:10px 14px;margin-bottom:8px}}
.pair-files{{display:flex;align-items:center;gap:8px;margin-bottom:4px}}
.pair-file{{background:#ff6b6b15;border:1px solid #ff6b6b30;color:#ff6b6b;padding:2px 8px;border-radius:4px;font-size:11px}}
.pair-arrow{{color:#3a5060}}
.pair-meta{{color:#3a5060;font-size:11px}}
.danger-card{{background:#ff6b6b08;border:1px solid #ff6b6b25;border-radius:8px;padding:14px 16px;margin-bottom:8px}}
.danger-label{{color:#ff6b6b;font-size:12px;font-weight:600;margin-bottom:6px}}
.danger-warning{{color:#c8dce8;font-size:12px;line-height:1.5;margin-bottom:8px}}
.danger-files{{display:flex;flex-wrap:wrap;gap:6px}}
.dz-file{{background:#fbbf2415;border:1px solid #fbbf2430;color:#fbbf24;padding:2px 8px;border-radius:4px;font-size:10px}}
.decision-item{{display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #141b22;align-items:flex-start}}
.decision-item:last-child{{border-bottom:none}}
.decision-num{{color:#60a5fa;min-width:20px;font-family:'Syne',sans-serif;font-size:16px;font-weight:800}}
.decision-text{{color:#c8dce8;font-size:12px;line-height:1.6}}
.commit-row{{display:grid;grid-template-columns:10px 60px 80px 1fr 80px;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid #0d1318;font-size:11px}}
.commit-row:last-child{{border-bottom:none}}
.commit-dot{{width:7px;height:7px;border-radius:50%;display:inline-block}}
.commit-hash{{color:#00d4aa}}
.commit-date{{color:#3a5060}}
.commit-msg{{color:#c8dce8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.commit-author{{color:#3a5060;text-align:right;overflow:hidden;text-overflow:ellipsis}}
.contrib-row{{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #141b22;font-size:12px}}
.contrib-row:last-child{{border-bottom:none}}
.muted{{color:#3a5060}}
.footer{{margin-top:48px;padding-top:20px;border-top:1px solid #1e2a35;color:#1e3040;font-size:11px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}
::-webkit-scrollbar{{width:5px;background:#07090c}}
::-webkit-scrollbar-thumb{{background:#1e2a35;border-radius:3px}}
</style>
</head>
<body>
<div class="page">
<header style="border-bottom:1px solid #1e2a35;padding-bottom:28px;margin-bottom:36px">
  <div class="header-tag">context-collapse · Cold Start Pack</div>
  <h1 class="header-title"><span>{meta["name"]}</span> Re-Entry Report</h1>
  <div class="header-sub">
    <span>Generated <strong>{datetime.now().strftime("%B %d, %Y")}</strong></span>
    <span>First commit <strong>{meta["first_commit"]}</strong></span>
    <span>Last activity <strong>{meta["last_commit"]}</strong></span>
  </div>
  <div class="ai-badge">{ai_badge}</div>
</header>

<div class="stats-row">
  <div class="stat-pill"><span class="stat-value">{meta["total_commits"]:,}</span><span class="stat-label">total commits</span></div>
  <div class="stat-pill"><span class="stat-value">{len(meta.get("contributors",[]))}</span><span class="stat-label">contributors</span></div>
  <div class="stat-pill"><span class="stat-value">{len(churn)}</span><span class="stat-label">active files</span></div>
  <div class="stat-pill"><span class="stat-value">{len(cochange)}</span><span class="stat-label">implicit couplings</span></div>
  <div class="stat-pill"><span class="stat-value">{len(reentry)}</span><span class="stat-label">re-entry files</span></div>
</div>

<div class="purpose-block">
  <div class="purpose-label">Project Purpose · AI Inference</div>
  <div class="purpose-text">{ai.get("purpose","Set GEMINI_API_KEY for AI-powered analysis.")}</div>
</div>

<div class="grid-2">
  <div class="card"><div class="card-title">Re-Entry Reading Sequence</div>{reentry_html}</div>
  <div class="card"><div class="card-title">Key Architectural Decisions</div>{decisions_html}</div>
</div>

<div class="grid-2">
  <div class="card"><div class="card-title">Danger Zones</div>{danger_html}</div>
  <div class="card"><div class="card-title">Implicit Coupling</div>{cochange_html}</div>
</div>

<div class="grid-2">
  <div class="card"><div class="card-title">File Churn Heatmap</div><table>{churn_rows}</table></div>
  <div class="card">
    <div class="card-title">Commit DNA</div>{commit_bars}
    <div style="margin-top:20px"><div class="card-title">Top Contributors</div>{contributors_html}</div>
  </div>
</div>

<div class="card" style="margin-bottom:20px"><div class="card-title">Recent Commit Timeline</div>{commits_html}</div>

<footer class="footer">
  <span>context-collapse · Cold Start Pack Generator</span>
  <span>Eliminate re-entry cost. Ship faster.</span>
</footer>
</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Report saved: {output_path}")
    return output_path
