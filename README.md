# KBTU CampusHub

Our Django midterm project. Below is how to run it and some rules for the team.

If you change something in the project (new app, new setting, new package) - update this README and CHANGELOG pls.

## What we use
- Python 3.12 (3.9 won't work with Django 5)
- uv for venv and packages - https://github.com/astral-sh/uv
- ruff for linting

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## How to run

Clone and go to dev branch:
```bash
git clone <repo-url>
cd Midterm_Django
git checkout dev
```

Make venv and install packages:
```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements/dev.txt
```
On Windows: `.venv\Scripts\activate`

Make sure `python --version` says 3.12. Also pick `.venv` as interpreter in PyCharm.

Create `settings/.env`:
```
CAMPUS_ENV_ID=local
CAMPUS_SECRET_KEY=your-secret-key
CAMPUS_ALLOWED_HOSTS=localhost,127.0.0.1
```
Don't push .env to github!!

Then:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Go to http://127.0.0.1:8000/admin/ and login with your email (there is no username).

Note: don't run `django-admin startproject`, project is already created.

## Structure
```
apps/
  abstracts/   base model (created_at, updated_at, deleted_at)
  users/       custom user, login by email, roles
  events/
  clubs/
  library/
  tutoring/
settings/
  .env
  conf.py      reads .env
  base.py      main settings
  env/
    local.py   sqlite, for us
    prod.py    postgres
requirements/
  base.txt
  dev.txt
  prod.txt
```

## Team

| App | Who |
|---|---|
| users | <name> (team lead) |
| events | <name> |
| clubs | <name> |
| library | <name> |
| tutoring | <name> |

## Notes for everyone

Your models should inherit from AbstractBaseModel:
```python
from apps.abstracts.models import AbstractBaseModel


class Event(AbstractBaseModel):
    ...
```

If you need a link to user use `settings.AUTH_USER_MODEL`, not User directly:
```python
from django.conf import settings

organizer = ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=CASCADE)
```

User roles are `student`, `tutor`, `admin`. Check like `user.role == User.Role.TUTOR`.

`soft_delete()` doesn't really delete, it just sets deleted_at. So add `.filter(deleted_at__isnull=True)` when you show stuff.

## Rules
- don't push to main or dev, make your branch from dev and open PR
- work only in your app
- make migrations only for your app, and do `git pull` before `makemigrations`
- type hints + PEP8
- before PR run:
```bash
ruff check .
python manage.py check
```