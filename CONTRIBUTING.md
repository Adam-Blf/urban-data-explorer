# Contribuer à Urban Data Explorer

Merci pour ton intérêt. Le projet est un livrable d'examen M1 EFREI 2026 mais
reste ouvert aux contributions externes (issues, PR, suggestions).

## Setup local

```bash
git clone https://github.com/Adam-Blf/urban-data-explorer.git
cd urban-data-explorer
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -r requirements.txt
pip install pre-commit ruff bandit pytest-cov
pre-commit install                                  # active les hooks
cp .env.example .env
```

## Workflow

1. **Ouvre une issue** d'abord pour discuter du changement (sauf typo / petit
   fix doc).
2. Branche depuis `main` · `git checkout -b feat/ma-feature` ou `fix/...`.
3. Code + tests · au moins 1 test pytest pour toute nouvelle logique.
4. Vérifie en local ·
   ```bash
   ruff check . && ruff format .
   bandit -c .bandit.yaml -r api pipeline scripts
   pytest -q
   ```
5. Commit · message en anglais court, format conventionnel
   (`feat(scope): ...`, `fix(scope): ...`, `docs: ...`, `chore: ...`).
6. Push + ouvre une **pull request** sur `main`.
7. La CI GitHub Actions doit être verte avant merge.

## Style code

- Python 3.12+ · type hints obligatoires sur les signatures publiques.
- Docstrings en français pour les modules et fonctions principales.
- Pas de chemin codé en dur · tout passe par `pipeline.config.Settings`.
- Pas de log secret (`JWT_SECRET`, mots de passe, tokens) en clair.

## Ajouter une source de données

1. Crée `pipeline/sources/<ma_source>.py` avec une fonction `fetch(...)`.
2. Si c'est un POI Paris OpenData géolocalisé, ajoute juste une entrée à
   `paris_poi.POI_REGISTRY`.
3. Si c'est un POI data.gouv, ajoute à `datagouv_poi.DATAGOUV_REGISTRY`.
4. Documente la source dans `docs/DATA_CATALOG.md`.
5. Ajoute un test `tests/test_<source>.py`.

## Reporter une vulnérabilité

Voir [SECURITY.md](SECURITY.md). Ne jamais publier une vulnérabilité dans une
issue publique.

## Licence

Toute contribution est sous [licence MIT](LICENSE) (même licence que le projet).
