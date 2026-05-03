# Security policy

## Versions supportées

| Version | Support |
|---|---|
| 1.0.x | ✅ Active |

## Reporter une vulnérabilité

Si tu découvres une vulnérabilité de sécurité dans Urban Data Explorer,
**ne pas ouvrir d'issue publique**. Contacter directement ·

- Adam Beloucif · `adam.beloucif@efrei.net`
- Emilien Morice · via GitHub `@emilien754`

Réponse sous 5 jours ouvrés. Disclosure coordonnée selon la gravité.

## Audit en place

| Outil | Couverture | Config |
|---|---|---|
| `ruff` | lint + format | `pyproject.toml` |
| `bandit` | analyse statique sécu Python | `.bandit.yaml` |
| `pytest --cov` | tests + couverture | 20 tests, API à 90%+ |
| `pre-commit` | hooks pré-commit | `.pre-commit-config.yaml` |
| GitHub Actions | CI obligatoire | `.github/workflows/ci.yml` |

## Choix de sécurité du projet

### Authentification

- **JWT HS256** via `python-jose`.
- TTL configurable (`JWT_TTL_MINUTES`, défaut 60 min).
- `JWT_SECRET` jamais commité, lu depuis `.env` ou env vars cloud.
- Endpoint `/auth/login` retourne 401 sur mauvais creds (pas d'info leak).

### Validation des inputs

- Toutes les query params API sont validées via Pydantic (`Field`,
  `pattern`, `ge`, `le`).
- Les colonnes `ORDER BY` sont contraintes par regex (whitelist statique)
  pour empêcher l'injection.
- Les valeurs WHERE sont passées en placeholders DuckDB `?` paramétrés.

### Bandit · faux positifs documentés

| Code | Justification |
|---|---|
| **B608** (SQL hardcoded) | Toutes les requêtes "à risque" utilisent des placeholders `?` paramétrés et les options `ORDER BY` sont whitelistées par regex Pydantic. Pas d'injection possible. |
| **B104** (bind 0.0.0.0) | Default attendu en container Docker. En prod, exposition derrière reverse proxy / WAF / Cloudflare. |

### Données

- **Pas de PII** dans le datamart Gold · seules des données ouvertes
  agrégées par arrondissement.
- DVF déjà publié sous Licence Ouverte 2.0 par la DGFiP.
- INSEE Filosofi / OpenData Paris / Airparif → **ODbL / Licence Ouverte**.
- Pas de cookie de tracking, pas d'analytics tiers sur le frontend.

### Secrets & env

- `.env` dans `.gitignore`.
- Patterns de défense en profondeur · `*secret*`, `*.token`, `sbp_*`,
  `ghp_*`, `github_pat_*`, `*.pem`.
- Pre-commit hook `detect-private-key` actif.

### Dépendances

- Toutes les versions épinglées dans `requirements.txt`.
- À auditer périodiquement via `pip-audit` (à intégrer dans la CI à
  l'occasion).

## En production · checklist

Voir [docs/DEPLOYMENT.md § Sécurité production](docs/DEPLOYMENT.md#4-sécurité-production)
pour la checklist complète (régénérer JWT_SECRET, restreindre CORS,
activer rate-limiting, WAF, logs centralisés).
