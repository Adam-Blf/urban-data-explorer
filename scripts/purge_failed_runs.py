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


def gh(args: list[str]) -> dict | list | None:
    proc = subprocess.run(["gh", *args], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        if "404" in proc.stderr or "Not Found" in proc.stderr:
            return None
        print(f"  ERROR · {proc.stderr.strip()[:200]}", file=sys.stderr)
        return None
    return json.loads(proc.stdout) if proc.stdout.strip() else None


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
        runs = gh(["api", f"repos/{OWNER}/{name}/actions/workflows/{args.workflow}/runs",
                   "--jq", ".workflow_runs[] | {id, conclusion}"])
        if not runs:
            continue
        # gh --jq returns one JSON object per line · subprocess concat'd them
        ids = []
        for line in str(runs).splitlines() if isinstance(runs, str) else []:
            obj = json.loads(line) if line.strip() else None
            if obj and obj.get("conclusion") == "failure":
                ids.append(obj["id"])

        # Re-fetch the proper way · the gh api with --jq returns a stream
        proc = subprocess.run(
            ["gh", "api",
             f"repos/{OWNER}/{name}/actions/workflows/{args.workflow}/runs",
             "--paginate"],
            text=True, capture_output=True, check=False,
        )
        if proc.returncode != 0:
            continue
        try:
            data = json.loads(proc.stdout)
        except Exception:
            continue
        ids = [
            r["id"] for r in (data.get("workflow_runs") or [])
            if r.get("conclusion") == "failure"
        ]
        if not ids:
            continue
        print(f"  {name}: {len(ids)} failed run(s) → deleting")
        for rid in ids:
            d = subprocess.run(
                ["gh", "api", "-X", "DELETE",
                 f"repos/{OWNER}/{name}/actions/runs/{rid}"],
                capture_output=True, text=True, check=False,
            )
            if d.returncode == 0:
                total += 1

    print(f"\nDeleted {total} failed run(s) total.")


if __name__ == "__main__":
    main()
