"""Ajoute un badge EFREI Paris en tête de README sur tous les repos
de cours EFREI d'Adam, via l'API GitHub (pas besoin de cloner).

Idempotent · skip si le badge est déjà présent.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys

OWNER = "Adam-Blf"

# Badge unique réutilisé · couleur EFREI #005CA9
BADGE = (
    "[![EFREI Paris](https://img.shields.io/badge/EFREI-Paris-005CA9"
    "?style=flat-square&labelColor=000000)](https://www.efrei.fr/)"
)

# Repos identifiés comme projets de cours EFREI d'Adam (M1 Data Eng & IA + L3 BICT).
COURSE_REPOS = [
    "maintenance-predictive-industrielle",
    "projet-bdf-m1-olist",
    "projet-dataeng-m1",
    "ProjetML-EFREI",
    "AISCA-Cocktails",
    "ia-pero",
    "ia-pero-final",
    "EFREI-NLP-Anime-Recommendation",
    "Projet-IA-Generative-Doctis-AI-mo",
    "accidentologie-baac-20",
    "Langue-des-signes",
    "exam_final_python",
    "Evaluation_Finale_DataScience_Beloucif",
]

AUTHOR = {"name": "Adam Beloucif", "email": "adam.beloucif@efrei.net"}


def gh_api(args: list[str], input_json: dict | None = None) -> dict | None:
    """Wrap `gh api`. Returns parsed JSON or None on 404."""
    cmd = ["gh", "api", *args]
    if input_json is not None:
        proc = subprocess.run(
            cmd, input=json.dumps(input_json), text=True,
            capture_output=True, check=False,
        )
    else:
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        if "404" in proc.stderr or "Not Found" in proc.stderr:
            return None
        print(f"  ERROR · {proc.stderr.strip()}", file=sys.stderr)
        return None
    if not proc.stdout.strip():
        return {}
    return json.loads(proc.stdout)


def insert_badge(content: str) -> str | None:
    """Insère le badge après le premier `# Titre`. Retourne None si déjà présent."""
    if "EFREI-Paris-005CA9" in content or "img.shields.io/badge/EFREI" in content:
        return None

    lines = content.splitlines()
    out: list[str] = []
    inserted = False
    for i, line in enumerate(lines):
        out.append(line)
        if not inserted and line.lstrip().startswith("# "):
            # Empty line + badge + empty line, then continue with original content
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            out.append("")
            out.append(BADGE)
            # Mark · skip the blank lines we already represented
            inserted = True
            # If next non-empty line is a badge-cluster, prepend ours to it
            # (handled naturally by appending here · existing lines follow)
    if not inserted:
        # No top-level # title → prepend badge at the very top
        return BADGE + "\n\n" + content
    return "\n".join(out) + ("\n" if content.endswith("\n") else "")


def patch_repo(repo: str) -> str:
    print(f"\n>> {repo}")
    info = gh_api([f"repos/{OWNER}/{repo}/contents/README.md"])
    if info is None:
        return "no README"
    content_b64 = info["content"]
    sha = info["sha"]
    raw = base64.b64decode(content_b64).decode("utf-8", errors="replace")

    new = insert_badge(raw)
    if new is None:
        return "already badged · skip"

    payload = {
        "message": "docs(readme): add EFREI badge",
        "content": base64.b64encode(new.encode("utf-8")).decode("ascii"),
        "sha": sha,
        "branch": info.get("default_branch", "main") or "main",
        "author":    AUTHOR,
        "committer": AUTHOR,
    }
    # Need to fetch default branch separately for safety
    repo_info = gh_api([f"repos/{OWNER}/{repo}"])
    if repo_info:
        payload["branch"] = repo_info.get("default_branch", "main")

    result = gh_api(
        ["-X", "PUT", f"repos/{OWNER}/{repo}/contents/README.md", "--input", "-"],
        input_json=payload,
    )
    if result and "commit" in result:
        return f"OK · commit {result['commit']['sha'][:8]} on branch {payload['branch']}"
    return "PATCH failed"


def main():
    summary = []
    for repo in COURSE_REPOS:
        status = patch_repo(repo)
        summary.append((repo, status))

    print("\n=== Summary ===")
    for repo, status in summary:
        print(f"  {repo:45s} · {status}")


if __name__ == "__main__":
    main()
