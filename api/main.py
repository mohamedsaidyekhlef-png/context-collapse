from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import subprocess, tempfile, os, sys, shutil, re

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST","GET"], allow_headers=["*"])
SRC_PATH = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, SRC_PATH)

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
        from git_miner import mine
        from report_renderer import render
        data = mine(repo_dir)
        data["ai"] = {"purpose": url.split("github.com/")[-1], "key_decisions": [], "danger_zones": [], "ai_powered": False}
        if os.environ.get("GEMINI_API_KEY"):
            try:
                from ai_brain import enrich
                data = enrich(data)
            except: pass
        out = os.path.join(tmpdir, "report.html")
        render(data, out)
        with open(out, "r", encoding="utf-8") as f:
            html = f.read()
        return JSONResponse({"status":"ok","repo":url,"report_html":html,"stats":{"commits":sum(data["churn"].values()),"files":len(data["churn"]),"pairs":len(data.get("pairs",[]))}})
    except HTTPException: raise
    except Exception as e: raise HTTPException(500, str(e))
    finally: shutil.rmtree(tmpdir, ignore_errors=True)
