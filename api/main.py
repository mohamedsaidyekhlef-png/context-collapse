from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import subprocess, tempfile, os, sys, shutil, re

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST","GET"], allow_headers=["*"])

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
        r = subprocess.run(["git", "clone", "--depth=500", url, repo_dir], capture_output=True, timeout=60)
        if r.returncode != 0:
            raise HTTPException(422, "Could not clone repo. Must be public.")

        sys.path.insert(0, os.path.join(repo_dir, "..", "..", "src"))
        src_path = os.path.join(os.path.dirname(__file__), "..", "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        from git_miner import mine
        from report_renderer import render

        raw = mine(repo_dir)

        # -- Normalize churn --
        churn = raw.get("churn", {})
        if isinstance(churn, list):
            churn = {item[0]: item[1] for item in churn if len(item) >= 2}

        # -- Normalize pairs --
        raw_pairs = raw.get("pairs", [])
        pairs = []
        for p in raw_pairs:
            if isinstance(p, dict):
                pairs.append({"a": p.get("a",""), "b": p.get("b",""), "count": p.get("count", p.get("n", 0))})
            elif isinstance(p, (list, tuple)) and len(p) >= 2:
                pairs.append({"a": str(p[0]), "b": str(p[1]), "count": int(p[2]) if len(p) > 2 else 1})

        # -- Normalize reentry --
        raw_reentry = raw.get("reentry", [])
        reentry = []
        for item in raw_reentry:
            if isinstance(item, dict):
                reentry.append({"file": item.get("file", item.get("f", "")), "changes": item.get("changes", item.get("churn", 0)), "score": float(item.get("score", 0))})
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                reentry.append({"file": str(item[0]), "changes": int(item[1]), "score": float(item[2]) if len(item) > 2 else 0.0})

        # -- Normalize DNA --
        dna = raw.get("dna", {})
        if isinstance(dna, list):
            dna = {item[0]: item[1] for item in dna if len(item) >= 2}

        data = {
            "churn": churn,
            "pairs": pairs,
            "reentry": reentry,
            "dna": dna,
            "ai": {"purpose": url.split("github.com/")[-1], "key_decisions": [], "danger_zones": [], "ai_powered": False}
        }

        if os.environ.get("GEMINI_API_KEY"):
            try:
                from ai_brain import enrich
                data = enrich(data)
            except:
                pass

        out = os.path.join(tmpdir, "report.html")
        render(raw, out)
        with open(out, "r", encoding="utf-8") as f:
            html = f.read()

        return JSONResponse({
            "status": "ok",
            "repo": url,
            "report_html": html,
            "churn": churn,
            "pairs": pairs,
            "reentry": reentry,
            "dna": dna,
            "ai": data["ai"],
            "stats": {
                "commits": sum(churn.values()),
                "files": len(churn),
                "pairs": len(pairs)
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
