from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import subprocess, tempfile, os, sys, shutil, re

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST", "GET"], allow_headers=["*"])


class AnalyzeRequest(BaseModel):
    repo_url: str


def is_valid(url):
    return bool(re.match(r"^https://github\.com/[\w\-\.]+/[\w\-\.]+$", url.strip().rstrip("/")))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    url = req.repo_url.strip().rstrip("/")
    if not is_valid(url):
        raise HTTPException(400, "Invalid GitHub URL")
    tmpdir = tempfile.mkdtemp()
    repo_dir = os.path.join(tmpdir, "repo")
    try:
        r = subprocess.run(
            ["git", "clone", "--depth=1000", url, repo_dir],
            capture_output=True, timeout=120
        )
        if r.returncode != 0:
            raise HTTPException(422, "Could not clone repo. Must be public.")
        src_path = os.path.join(os.path.dirname(__file__), "..", "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        from git_miner import mine
        from report_renderer import render
        raw = mine(repo_dir)
        churn_list = raw.get("churn", [])
        churn = {item["file"]: item["changes"] for item in churn_list}
        cochange = raw.get("cochange", [])
        pairs = []
        for p in cochange:
            if isinstance(p, dict):
                pairs.append({
                    "a": p.get("file_a", p.get("a", "")),
                    "b": p.get("file_b", p.get("b", "")),
                    "count": p.get("co_changes", p.get("count", p.get("n", 1)))
                })
        commit_types = raw.get("commit_types", {})
        total_typed = sum(commit_types.values()) or 1
        dna = {k: round(v / total_typed * 100) for k, v in commit_types.items()}
        reentry = [
            {"file": item["file"], "score": item["score"], "changes": item["changes"]}
            for item in raw.get("reentry_sequence", [])
        ]
        ghost_zones = raw.get("ghost_zones", [])
        meta = raw.get("meta", {})
        total_commits_count = meta.get("total_commits", sum(commit_types.values()))
        ai_data = {
            "purpose": url.split("github.com/")[-1],
            "key_decisions": [],
            "danger_zones": [],
            "shock_insight": None,
            "ai_powered": False
        }
        if os.environ.get("GEMINI_API_KEY"):
            try:
                from ai_brain import enrich
                enriched = enrich(raw)
                ai_data = enriched.get("ai", ai_data)
            except Exception as e:
                print("[AI] enrichment failed: %s" % e)
        out = os.path.join(tmpdir, "report.html")
        render(raw, out)
        with open(out, "r", encoding="utf-8") as f:
            report_html = f.read()
        return JSONResponse({
            "status": "ok",
            "repo": url,
            "report_html": report_html,
            "churn": churn,
            "pairs": pairs,
            "reentry": reentry,
            "dna": dna,
            "ai": ai_data,
            "ghost_zones": ghost_zones,
            "stats": {
                "commits": total_commits_count,
                "files": len(churn),
                "pairs": len(pairs),
                "ghosts": len(ghost_zones)
            }
        })
    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Clone timed out. Try a smaller repo.")
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.get("/api/card/{owner}/{repo}")
def get_card(owner: str, repo: str):
    url = "https://github.com/%s/%s" % (owner, repo)
    if not is_valid(url):
        raise HTTPException(400, "Invalid repo")
    tmpdir = tempfile.mkdtemp()
    repo_dir = os.path.join(tmpdir, "repo")
    try:
        r = subprocess.run(
            ["git", "clone", "--depth=500", url, repo_dir],
            capture_output=True, timeout=90
        )
        if r.returncode != 0:
            raise HTTPException(422, "Could not clone repo.")
        src_path = os.path.join(os.path.dirname(__file__), "..", "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        from git_miner import mine
        from card_renderer import generate_card_svg
        raw = mine(repo_dir)
        svg = generate_card_svg(raw)
        return Response(content=svg, media_type="image/svg+xml", headers={
            "Cache-Control": "public, max-age=3600",
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
