from fastmcp import FastMCP
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

mcp = FastMCP("context-collapse")


@mcp.tool()
def analyze_repo(repo_path: str) -> dict:
    """Analyze a git repository and return a cold-start briefing
    including re-entry sequence, file coupling, danger zones,
    and commit DNA. Use this when you need to understand an
    unfamiliar codebase quickly."""
    from git_miner import mine
    from ai_brain import enrich

    data = mine(repo_path)
    data = enrich(data)
    return {
        "purpose": data["ai"]["purpose"],
        "read_these_first": data["reentry_sequence"][:5],
        "danger_zones": data["ai"]["danger_zones"],
        "shock_insight": data["ai"]["shock_insight"],
        "key_decisions": data["ai"]["key_decisions"],
        "top_coupling": data["cochange"][:5],
        "commit_dna": data["commit_types"],
    }


if __name__ == "__main__":
    mcp.run()
