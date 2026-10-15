# KBTU CampusHub

Our Django midterm project. Below is how to run it and some rules for the team.

If you change something in the project (new app, new setting, new package) - update this README and CHANGELOG pls.

## What we use
- Python 3.12 (3.9 won't work with Django 5)
- uv for venv and packages - https://github.com/astral-sh/uv
- ruff for linting (config is in `ruff.toml`)

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

Pages that work now:
- http://127.0.0.1:8000/ - home
- http://127.0.0.1:8000/users/register/ - sign up
- http://127.0.0.1:8000/users/login/ - login (with email, there is no username)
- http://127.0.0.1:8000/users/profile/ - my profile (only when logged in)
- http://127.0.0.1:8000/users/profile/edit/ - edit my name
- http://127.0.0.1:8000/admin/ - admin

Note: don't run `django-admin startproject`, project is already created.

## Structure
```
apps/
  abstracts/   base model (created_at, updated_at, deleted_at)
  users/       custom user, register / login / logout / profile
    forms.py   RegisterForm, ProfileForm
    templates/users/   login.html, register.html, profile.html, profile_edit.html
  events/
  clubs/
  library/
  tutoring/
templates/
  base.html    main layout with navbar and messages, extend it in your pages
  home.html
settings/
  .env
  conf.py      reads .env
  base.py      main settings
  urls.py
  env/
    local.py   sqlite, for us
    prod.py    postgres
requirements/
  base.txt
  dev.txt
  prod.txt
ruff.toml
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

Your templates go to `apps/<your_app>/templates/<your_app>/` (yes, app name twice) and should start with:
```html
{% extends "base.html" %}
```

If a page is only for logged in users, use `LoginRequiredMixin` (or `@login_required` for function views). It will send people to the login page automatically. Put it first: `class MyView(LoginRequiredMixin, ListView)`.

To show a message after an action (like "Registered for event"), use `SuccessMessageMixin` with `success_message = "..."`. `base.html` already shows messages.

When a user edits his own stuff, take the object from `request.user`, not from the url id, so nobody can edit other people's things.

Add your app urls in `settings/urls.py`:
```python
path("events/", include("apps.events.urls")),
```
and put `app_name = "events"` in your `urls.py`.

Logout must be a POST form, not a link (Django 5 thing). There is already a button in `base.html`.

## If something breaks
- `TemplateDoesNotExist` - check file name and folder (`.html`, not `.htm`, and `templates/<app>/` inside your app)
- weird old error after you fixed it - stop runserver (Ctrl+C) and start again
- `'tuple' object has no attribute ...` - you have an extra comma at the end of a line like `model = User,`
- `No module named 'django'` - venv is not activated

## Rules
- don't push to main or dev, make your branch from dev and open PR
- work only in your app
- make migrations only for your app, and do `git pull` before `makemigrations`
- type hints + PEP8
- run ruff from the project root, not from inside your app folder
- before PR run:
```bash
ruff check .
python manage.py check
```