# CodeLingo (Rebuild)

Application SaaS mobile-first d'apprentissage Python débutant, style "Duolingo du code", avec Supabase Auth + Supabase PostgreSQL.

## Stack
- **Frontend**: Jinja templates + Vanilla JS + CSS custom (mobile-first)
- **Backend API**: FastAPI (architecture en couches)
- **Auth**: Supabase Auth (email/password)
- **DB**: Supabase PostgreSQL
- **Correction auto**: Sandbox Python backend avec blocage d'instructions dangereuses + timeout

## Architecture
```
app/
  api/          # Routes API + dépendances auth
  core/         # Configuration
  db/           # Intégration Supabase + mode démo
  domain/       # Données métier (modules/leçons)
  services/     # Moteur d'exercice + progression
  main.py       # Entrée FastAPI
static/
  css/app.css
  js/app.js
templates/
  *.html
sql/schema.sql  # SQL complet Supabase
```

## Fonctionnalités implémentées
- Signup / login Supabase + session token côté client
- Onboarding post-inscription
- Parcours Python avec 5 modules obligatoires
- Leçon = explication + exemple + quiz + exercice auto-corrigé
- Progression: XP, niveau, streak, badges, historique XP
- Dashboard: progression globale, streak, XP, leçons terminées
- Profil: stats perso + historique

## Installation locale
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Configuration Supabase
1. Créer un projet Supabase.
2. Exécuter `sql/schema.sql` dans SQL Editor.
3. Remplir `.env` avec `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.

## Lancer l'application
```bash
uvicorn app.main:app --reload
```
Puis ouvrir `http://127.0.0.1:8000/app/login`.

## Déploiement
- API FastAPI: Railway / Fly / Render.
- Variables d'environnement identiques à `.env.example`.
- Supabase reste le backend managé pour Auth + DB.
