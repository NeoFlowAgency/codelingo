# CodeLingo V1

Application web **mobile-first** pour apprendre Python débutant (style Duolingo du code).

## Stack
- Frontend: HTML + TailwindCSS + JavaScript
- Backend: FastAPI (Python)
- Auth + Base de données: Supabase (PostgreSQL)
- Sandbox code: exécution Python côté serveur avec timeout

## Structure du projet
- `app/main.py` : routes pages + API
- `app/services/` : contenu leçons, gamification, sandbox
- `app/supabase_client.py` : accès Supabase + mode démo
- `templates/` : pages HTML responsive
- `static/js/app.js` : logique frontend
- `sql/schema.sql` : tables et policies Supabase

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration
1. Copier `.env.example` vers `.env`
2. Renseigner:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
3. Exécuter `sql/schema.sql` dans l’éditeur SQL Supabase

## Lancer
```bash
uvicorn app.main:app --reload
```
Puis ouvrir `http://127.0.0.1:8000/login`.

## Mode démo
Sans configuration Supabase, l’app fonctionne en mode démo local (stockage mémoire + token local).

## Git (commit + push)
Commit utilisé:
```bash
git commit -m "Ajout de l'app CodeLingo V1 générée par Codex"
```
Commande de push à exécuter:
```bash
git push origin main
```
