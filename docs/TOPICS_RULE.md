# Règle · gestion des topics GitHub par fichier

Convention reproductible sur **tous les repos** d'Adam pour gérer les topics
GitHub depuis le code, sans passer par la GUI.

## TL;DR

1. Créer un fichier **`.github/topics.yml`** à la racine du repo.
2. Y lister les topics sous la clé `topics:`.
3. Push.
4. Le workflow **`.github/workflows/sync-topics.yml`** s'exécute et remplace
   les topics du repo via l'API GitHub. Idempotent.

## Format `.github/topics.yml`

```yaml
topics:
  - data-engineering
  - medallion-architecture
  - fastapi
  - python
  - efrei
  - m1
```

## Contraintes GitHub

- chaque topic est en **lowercase**, alphanumérique + `-` uniquement
- max **50 caractères** par topic
- max **20 topics** par repo
- les topics inconnus de GitHub sont créés à la volée

## Workflow

```yaml
name: Sync repo topics

on:
  push:
    branches: [main, master]
    paths:
      - ".github/topics.yml"
  workflow_dispatch:
```

→ se déclenche **uniquement** si `.github/topics.yml` change. Aucun coût en
minutes CI sur les commits qui ne touchent pas la liste.

### Setup PAT (une seule fois)

Le `GITHUB_TOKEN` natif **ne peut pas** modifier les topics (limite GitHub
Actions documentée). Il faut un Personal Access Token avec scope
`public_repo` (ou `repo` pour les privés) stocké dans le secret repo
`TOPICS_PAT`.

```bash
# 1. créer le PAT classique sur github.com/settings/tokens
#    → expiration 1 an · scope public_repo (+ repo si tu as des privés)

# 2. l'enregistrer en bulk sur tous tes repos
gh secret set TOPICS_PAT \
  --body "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXX" \
  --repos "$(gh repo list Adam-Blf --limit 100 --json name,isArchived --jq '[.[] | select(.isArchived==false) | "Adam-Blf/" + .name] | join(",")')"
```

Sans `TOPICS_PAT` configuré, le workflow se termine en **succès** avec un
warning "skip" plutôt que de polluer l'onglet Actions de runs rouges.

## Bootstrap d'un nouveau repo

Pour appliquer la convention sur un repo existant ·

```bash
# 1. copier les deux fichiers
cp .github/topics.yml         <autre-repo>/.github/topics.yml
cp .github/workflows/sync-topics.yml <autre-repo>/.github/workflows/sync-topics.yml

# 2. éditer la liste des topics
# 3. commit + push
git add .github && git commit -m "chore(repo): topics + sync workflow" && git push
```

Ou en bulk via le script `scripts/set_repo_topics.py` qui appelle l'API
`PUT /repos/{owner}/{repo}/topics` directement (sans workflow), pratique
pour la première passe sur 40+ repos d'un coup.

## Déclenchement manuel

Sans modifier le fichier ·

```bash
gh workflow run sync-topics.yml -R Adam-Blf/<repo>
```

ou via l'onglet *Actions* dans l'UI GitHub.

## Pourquoi pas un commit-hook local ?

Un commit-hook côté client ·
- ne déclenche rien si on push depuis un autre poste
- nécessite que chaque contributeur installe les hooks
- ne peut pas valider que le PUT API a réussi

Un workflow GitHub Actions ·
- s'exécute à chaque push, peu importe la machine
- utilise le `GITHUB_TOKEN` automatique (pas de PAT à gérer)
- visible dans l'onglet Actions, traçable

C'est l'équivalent serveur d'un post-commit hook · plus robuste.
