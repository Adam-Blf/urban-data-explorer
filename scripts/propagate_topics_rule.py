"""Propage `.github/topics.yml` + `.github/workflows/sync-topics.yml` sur
tous les repos actifs d'Adam, en pré-remplissant `topics.yml` avec les topics
actuels du repo.

Idempotent · ne PUT que si les fichiers manquent ou si leur contenu diffère.

Usage::

    python scripts/propagate_topics_rule.py
    python scripts/propagate_topics_rule.py --dry-run
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

OWNER = "Adam-Blf"
ROOT = Path(__file__).resolve().parent.parent
TOPICS_TPL = (ROOT / ".github" / "topics.yml").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github" / "workflows" / "sync-topics.yml").read_text(encoding="utf-8")

AUTHOR = {"name": "Adam Beloucif", "email": "adam.beloucif@efrei.net"}


def gh(args: list[str], input_json: dict | None = None) -> dict | None:
    cmd = ["gh", "api", *args]
    proc = subprocess.run(
        cmd, text=True, capture_output=True, check=False,
        input=json.dumps(input_json) if input_json is not None else None,
    )
    if proc.returncode != 0:
        if "404" in proc.stderr or "Not Found" in proc.stderr:
            return None
        print(f"  ERROR · {proc.stderr.strip()[:200]}", file=sys.stderr)
        return None
    return json.loads(proc.stdout) if proc.stdout.strip() else {}


def make_topics_yml(existing_topics: list[str]) -> str:
    """Personnalise topics.yml avec la liste actuelle du repo."""
    if not existing_topics:
        return TOPICS_TPL
    lines = [
        "# GitHub topics du repo · source de vérité.",
        "#",
        "# Modifier ce fichier puis push → le workflow .github/workflows/sync-topics.yml",
        "# remplace les topics du repo via l'API GitHub.",
        "#",
        "# Règles ·",
        "#   - lowercase, [a-z0-9-]+, max 50 chars par topic",
        "#   - max 20 topics par repo (limite GitHub)",
        "",
        "topics:",
    ]
    for t in sorted(set(existing_topics)):
        lines.append(f"  - {t}")
    return "\n".join(lines) + "\n"


def put_file(repo: str, path: str, content: str, default_branch: str,
             dry_run: bool) -> str:
    info = gh([f"repos/{OWNER}/{repo}/contents/{path}"])
    sha = info["sha"] if info else None
    existing = base64.b64decode(info["content"]).decode("utf-8") if info else None
    if existing == content:
        return f"{path}: up-to-date"
    if dry_run:
        return f"{path}: WOULD {'UPDATE' if sha else 'CREATE'}"
    payload: dict = {
        "message": f"chore(topics): {'update' if sha else 'add'} {path}",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": default_branch,
        "author": AUTHOR,
        "committer": AUTHOR,
    }
    if sha:
        payload["sha"] = sha
    res = gh(["-X", "PUT", f"repos/{OWNER}/{repo}/contents/{path}", "--input", "-"],
             input_json=payload)
    return f"{path}: {'updated' if sha else 'created'}" if res else f"{path}: FAILED"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--exclude", nargs="*", default=["urban-data-explorer"],
                   help="Repos to skip (already has the convention)")
    args = p.parse_args()

    repos_raw = subprocess.check_output(
        ["gh", "repo", "list", OWNER, "--limit", "100",
         "--json", "name,defaultBranchRef,isArchived,repositoryTopics"],
        text=True,
    )
    repos = json.loads(repos_raw)
    active = [r for r in repos if not r["isArchived"] and r["name"] not in args.exclude]
    print(f"Active targets: {len(active)} (excluded: {args.exclude})")

    summary = {"ok": 0, "skipped": 0, "failed": 0}
    for r in active:
        name = r["name"]
        branch = (r.get("defaultBranchRef") or {}).get("name") or "main"
        existing_topics = [t["name"] for t in (r.get("repositoryTopics") or [])]
        print(f"\n>> {name} (branch={branch}, topics={len(existing_topics)})")

        topics_yml = make_topics_yml(existing_topics)
        try:
            res1 = put_file(name, ".github/topics.yml", topics_yml, branch, args.dry_run)
            res2 = put_file(name, ".github/workflows/sync-topics.yml", WORKFLOW, branch, args.dry_run)
            print(f"   {res1}")
            print(f"   {res2}")
            if "FAILED" in res1 or "FAILED" in res2:
                summary["failed"] += 1
            elif "up-to-date" in res1 and "up-to-date" in res2:
                summary["skipped"] += 1
            else:
                summary["ok"] += 1
        except Exception as e:
            print(f"   ERROR · {e}", file=sys.stderr)
            summary["failed"] += 1

    print()
    print("=== Summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
