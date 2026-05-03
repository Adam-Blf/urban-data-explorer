"""Purge les runs `sync-topics.yml` en failure sur tous les repos d'Adam.

Idempotent · ne supprime que les runs failed du workflow indiqué.

Usage::

    python scripts/purge_failed_runs.py
    python scripts/purge_failed_runs.py --workflow sync-topics.yml
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

OWNER = "Adam-Blf"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workflow", default="sync-topics.yml")
    args = p.parse_args()

    repos_raw = subprocess.check_output(
        ["gh", "repo", "list", OWNER, "--limit", "100",
         "--json", "name,isArchived"],
        text=True,
    )
    repos = [r["name"] for r in json.loads(repos_raw) if not r["isArchived"]]
    print(f"Scanning {len(repos)} active repos for failed `{args.workflow}` runs")

    total = 0
    for name in repos:
        proc = subprocess.run(
            ["gh", "api",
             f"repos/{OWNER}/{name}/actions/workflows/{args.workflow}/runs",
             "--paginate"],
            text=True, capture_output=True, check=False,
        )
        if proc.returncode != 0:
            continue

        # `gh api --paginate` concatenates JSON pages with newlines · split & merge
        runs: list[dict] = []
        for chunk in proc.stdout.strip().split("\n{"):
            if not chunk.strip():
                continue
            try:
                obj = json.loads(chunk if chunk.startswith("{") else "{" + chunk)
            except json.JSONDecodeError:
                continue
            runs.extend(obj.get("workflow_runs") or [])

        ids = [r["id"] for r in runs if r.get("conclusion") == "failure"]
        if not ids:
            continue
        print(f"  {name}: {len(ids)} failed run(s) -> deleting")
        for rid in ids:
            d = subprocess.run(
                ["gh", "api", "-X", "DELETE",
                 f"repos/{OWNER}/{name}/actions/runs/{rid}"],
                capture_output=True, text=True, check=False,
            )
            if d.returncode == 0:
                total += 1
            else:
                print(f"    DELETE {rid} failed · {d.stderr.strip()[:120]}", file=sys.stderr)

    print(f"\nDeleted {total} failed run(s) total.")


if __name__ == "__main__":
    main()
