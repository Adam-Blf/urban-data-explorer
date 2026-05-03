"""Patche les topics GitHub de chaque repo Adam-Blf via l'API.

Idempotent · `gh api PUT /repos/{owner}/{repo}/topics` remplace l'ensemble
des topics. On lit l'état actuel et on n'écrit que si la liste change.

Topics = mapping manuel curé pour les projets clairs + fallback automatique
basé sur le langage et la description.

Topics GitHub doivent ·
- être en lowercase
- contenir uniquement [a-z0-9-]
- max 50 par repo
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Iterable

OWNER = "Adam-Blf"

# ---------------------------------------------------------------------------
# Curated mapping (precise, hand-picked by domain)
# ---------------------------------------------------------------------------

CURATED: dict[str, list[str]] = {
    # M1 EFREI Data Eng & IA
    "urban-data-explorer": [
        "data-engineering", "medallion-architecture", "fastapi", "duckdb",
        "polars", "maplibre", "open-data", "paris", "python", "efrei",
        "m1", "dashboard", "jwt-authentication",
    ],
    "projet-bdf-m1-olist": [
        "data-engineering", "spark", "hadoop", "hive", "yarn",
        "medallion-architecture", "olist", "fastapi", "streamlit",
        "remotion", "python", "efrei", "m1", "big-data",
    ],
    "projet-dataeng-m1": [
        "data-engineering", "medallion-architecture", "python", "efrei", "m1",
        "data-pipeline", "etl",
    ],
    "Evaluation_Finale_DataScience_Beloucif": [
        "data-science", "machine-learning", "scikit-learn", "fastapi",
        "docker", "churn-prediction", "telco", "python", "efrei",
    ],
    "exam_final_python": [
        "data-science", "machine-learning", "rent-prediction", "jupyter",
        "python", "efrei", "m1",
    ],
    "maintenance-predictive-industrielle": [
        "data-science", "machine-learning", "predictive-maintenance",
        "scikit-learn", "xgboost", "shap", "streamlit", "fastapi",
        "python", "efrei", "rncp",
    ],
    "ProjetML-EFREI": [
        "machine-learning", "wine-quality", "scikit-learn", "kaggle",
        "python", "jupyter", "efrei",
    ],
    "AISCA-Cocktails": [
        "nlp", "semantic-search", "sbert", "rag", "streamlit",
        "recommendation-system", "python", "efrei",
    ],
    "ia-pero": ["nlp", "sentence-transformers", "semantic-search", "streamlit", "python", "efrei"],
    "ia-pero-final": ["nlp", "sentence-transformers", "semantic-search", "streamlit", "python", "efrei"],
    "Projet-IA-Generative-Doctis-AI-mo": [
        "generative-ai", "llm", "healthcare", "doctis", "python", "efrei",
    ],
    "RobotArtist": ["python", "generative-art", "robotics", "ai", "creative-coding"],
    "accidentologie-baac-20": ["open-data", "data-analysis", "baac", "road-safety", "france"],

    # Web / portfolio
    "adam-portfolio": [
        "portfolio", "vercel", "tailwindcss", "typescript", "i18n",
        "dark-mode", "fullstack", "personal-website",
    ],
    "la-nuit-de-l-efrei": [
        "nextjs", "tailwindcss", "framer-motion", "vercel", "event-website",
        "efrei", "gala", "typescript",
    ],

    # PWA / jeux
    "GlouGlou": ["pwa", "react", "vercel", "drinking-game", "javascript"],
    "black-out": ["typescript", "web-game", "interactive", "drinking-game"],
    "Borderland": ["typescript", "web-game", "card-game"],
    "genius": ["pwa", "react", "typescript", "flashcards", "trivia", "education"],
    "skyjo-multiplayer": ["pwa", "react", "typescript", "vite", "peerjs", "multiplayer", "card-game"],
    "ChessAI-SelfLearning-Web": ["chess", "web-game", "ai", "deep-learning", "minimax"],
    "Mendelieve.io": ["javascript", "education", "chemistry", "periodic-table", "interactive"],
    "BeeBle": ["typescript", "collaboration", "web-app"],
    "poke-next": ["nextjs", "typescript", "pokedex", "pokemon", "tailwindcss"],
    "relation_graph": ["typescript", "data-visualization", "force-graph", "interactive"],

    # Mobile / IA perso
    "Echo": ["pwa", "react", "typescript", "dating-app", "matching"],
    "A.B.E.L": [
        "pwa", "personal-assistant", "typescript", "react", "vite",
        "supabase", "biometric-auth", "fullstack",
    ],
    "let-me-cook": [
        "expo", "react-native", "ios", "android", "recipes", "ai",
        "video-extraction",
    ],
    "let-me-cook-v1": [
        "nextjs", "pwa", "supabase", "stripe", "groq", "recipes",
        "video-extraction", "freemium",
    ],
    "let-me-cook-story": ["remotion", "video", "teaser", "typescript"],
    "hadiway": ["pwa", "accessibility", "routing", "pmr", "python"],

    # Hospitalier / pro
    "pgvplaning": [
        "typescript", "react", "healthcare", "scheduling",
        "hospital", "supabase", "firebase",
    ],
    "dimmoulinette": ["python", "automation", "data-processing", "healthcare"],

    # Outils / divers
    "EtudiantOS": ["csharp", "dotnet", "desktop", "student-management"],
    "career-ops": [
        "ai", "claude-code", "job-search", "go", "dashboard",
        "pdf-generation", "automation",
    ],

    # Profil / placeholders
    "Adam-Blf": ["github-profile", "personal", "data-engineer"],
    "op-raton-mission-control": ["typescript", "private", "internal-tool"],
    "festive-leave-manager": ["typescript", "private", "leave-management"],
    "J.A.R.V.I.S": ["placeholder"],
    "Map": ["placeholder"],
}


def _slugify(s: str) -> str:
    """GitHub topics · lowercase, [a-z0-9-]+, max 50 chars."""
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:50]


def _auto_topics(repo: dict) -> list[str]:
    """Fallback · derive topics from language + description keywords."""
    out: list[str] = []
    lang = (repo.get("primaryLanguage") or {}).get("name") or ""
    if lang:
        out.append(_slugify(lang))
    desc = (repo.get("description") or "").lower()

    KEYWORDS = {
        "fastapi": "fastapi",
        "react native": "react-native",
        "react": "react",
        "next.js": "nextjs",
        "nextjs": "nextjs",
        "tailwind": "tailwindcss",
        "supabase": "supabase",
        "firebase": "firebase",
        "stripe": "stripe",
        "vercel": "vercel",
        "expo": "expo",
        "remotion": "remotion",
        "machine learning": "machine-learning",
        "deep learning": "deep-learning",
        "data engineering": "data-engineering",
        "data science": "data-science",
        "nlp": "nlp",
        "open data": "open-data",
        "pwa": "pwa",
        "efrei": "efrei",
        "m1": "m1",
        "rncp": "rncp",
    }
    for kw, topic in KEYWORDS.items():
        if kw in desc:
            out.append(topic)

    # Dedupe + cap
    seen, dedup = set(), []
    for t in out:
        if t and t not in seen:
            seen.add(t); dedup.append(t)
    return dedup[:20]


def _gh_api(args: list[str], input_json: dict | None = None) -> dict | None:
    cmd = ["gh", "api", *args]
    if input_json is not None:
        proc = subprocess.run(cmd, input=json.dumps(input_json), text=True,
                              capture_output=True, check=False)
    else:
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        print(f"  ERROR · {proc.stderr.strip()[:200]}", file=sys.stderr)
        return None
    return json.loads(proc.stdout) if proc.stdout.strip() else {}


def _set_topics(repo: str, names: Iterable[str]) -> bool:
    cleaned = sorted(set(_slugify(n) for n in names if n))[:20]
    if not cleaned:
        print(f"  {repo} · no topics computed · skip")
        return False
    res = _gh_api(
        ["-X", "PUT", f"repos/{OWNER}/{repo}/topics",
         "-H", "Accept: application/vnd.github+json",
         "--input", "-"],
        input_json={"names": cleaned},
    )
    if res is None:
        return False
    print(f"  {repo} <- [{', '.join(cleaned)}]")
    return True


def main():
    repos_raw = subprocess.check_output(
        ["gh", "repo", "list", OWNER, "--limit", "100",
         "--json", "name,description,isArchived,primaryLanguage,repositoryTopics"],
        text=True,
    )
    repos = json.loads(repos_raw)
    active = [r for r in repos if not r["isArchived"]]
    print(f"Active repos: {len(active)} (skipping {len(repos) - len(active)} archived)")

    summary = {"updated": 0, "skipped_already_set": 0, "failed": 0}
    for r in active:
        name = r["name"]
        existing = sorted(t["name"] for t in (r.get("repositoryTopics") or []))

        if name in CURATED:
            new_topics = CURATED[name]
        elif existing:
            print(f"  {name} · already has topics, leaving alone · [{', '.join(existing)}]")
            summary["skipped_already_set"] += 1
            continue
        else:
            new_topics = _auto_topics(r)
            if not new_topics:
                print(f"  {name} · could not auto-derive topics · skip")
                continue

        cleaned = sorted(set(_slugify(t) for t in new_topics))
        if cleaned == existing:
            print(f"  {name} · already up to date · skip")
            summary["skipped_already_set"] += 1
            continue

        ok = _set_topics(name, new_topics)
        if ok:
            summary["updated"] += 1
        else:
            summary["failed"] += 1

    print()
    print("=== Summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
