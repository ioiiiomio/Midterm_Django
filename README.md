# KBTU CampusHub

Midterm Django project 2026. Here is how to set up the project and how we work as a team.

If you change something in the project structure (new app, new setting, new package), please update this README.

## Tools
- Python 3.12 (3.9 doesn't work with Django 5)
- [uv](https://github.com/astral-sh/uv) for venv and packages
- [ruff](https://docs.astral.sh/ruff/) for linting

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
On Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## How to run the project

1. Clone the repo and switch to `dev`:
```bash
git clone <repo-url>
cd Midterm_Django
git checkout dev
```

2. Create venv and install packages:
```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements/dev.txt
```
(on Windows activate with `.venv\Scripts\activate`)

3. Create `settings/.env` file:
```
CAMPUS_ENV_ID=local
CAMPUS_SECRET_KEY=your-secret-key
CAMPUS_ALLOWED_HOSTS=localhost,127.0.0.1
```
Don't push `.env` to GitHub!

4. Run migrations and start the server:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Don't run `django-admin startproject`, the project is already created.

## Project structure
```
apps/
  abstracts/   base model with created_at and updated_at
  users/       custom user
  events/
  clubs/
  library/
  tutoring/
settings/
  .env         secrets
  conf.py      reads .env
  base.py      main settings
  env/
    local.py   for development (SQLite)
    prod.py    for production (PostgreSQL)
requirements/
  base.txt
  dev.txt
  prod.txt
```

## Team
! Write your names in front of the project 

| App | Who |
|---|---|
| users | <name> (team lead) |
| events | <name> |
| clubs | <name> |
| library | <name> |
| tutoring | <name> |

## Rules
- Don't push to `main` or `dev` directly. Make your own branch from `dev` and open a Pull Request.
- Work only in your own app.
- Only make migrations for your own app. Do `git pull` before `makemigrations`.
- Inherit your models from `AbstractBaseModel`.
- Use type hints and follow PEP8.
- Before PR run:
```bash
ruff check .
python manage.py check
```