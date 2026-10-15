# KBTU CampusHub

Our Django midterm project: one campus portal with tutoring, a study library, events and student clubs.
Below is how to run it and the rules for the team.

If you change something in the project (new app, new setting, new package) - update this README and CHANGELOG pls.

## What we use
- Python 3.12 (3.9 won't work with Django 5)
- Django 5.2
- uv for venv and packages - https://github.com/astral-sh/uv
- ruff for linting (config is in `ruff.toml`)
- Pillow (needed for club logos, `ImageField`)

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## How to run

Clone:
```bash
git clone <repo-url>
cd Midterm_Django
```

Make venv and install packages:
```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements/dev.txt
```
On Windows: `.venv\Scripts\activate`

No uv? `python -m pip install -r requirements/dev.txt` inside the venv works too.

Make sure `python --version` says 3.12. Also pick `.venv` as interpreter in PyCharm.

Create `settings/.env` from the example:
```bash
cp settings/.env.example settings/.env
```
It must contain:
```
CAMPUS_ENV_ID=local
CAMPUS_SECRET_KEY=your-secret-key
CAMPUS_ALLOWED_HOSTS=localhost,127.0.0.1
```
Generate a real key with:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Don't push `.env` to github!! It's in `.gitignore`.

Then:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Demo data for tutoring (local only):
```bash
python manage.py seed_tutoring
```
It prints demo account emails and their shared password (`--password` to choose another one). You get an admin, three tutors, two students, open / nearly full / cancelled sessions and a finished session with a review.

## Pages

| URL | What |
|---|---|
| `/` | home, cards for every app when logged in |
| `/users/register/` | sign up (student or tutor) |
| `/users/login/` | login with email (there is no username) |
| `/users/profile/` | my profile |
| `/users/profile/edit/` | edit my name |
| `/tutoring/` | tutor directory, search and subject filter |
| `/tutoring/tutors/<id>/` | tutor page, upcoming sessions, reviews, booking |
| `/tutoring/schedule/` | tutor: my sessions (add / edit / cancel) |
| `/tutoring/profile/edit/` | tutor: my tutor profile |
| `/tutoring/bookings/` | student: my bookings, cancel, leave a review |
| `/library/` | study resources list |
| `/events/` | campus events, registration |
| `/clubs/` | clubs list, search and category filter |
| `/clubs/<id>/` | club page, members, join requests |
| `/admin/` | admin |

Open the site with **one** host - `localhost:8000` **or** `127.0.0.1:8000`. Cookies don't go between them, so mixing gives CSRF errors.

## Structure
```
apps/
  __init__.py  (needed, without it `manage.py test` crashes)
  abstracts/   AbstractBaseModel (created_at, updated_at, deleted_at, soft_delete)
  users/       custom user, register / login / logout / profile
  tutoring/    tutor profiles, subjects, sessions, bookings, reviews, seed_tutoring command
  library/     study resources: upload, edit, delete, protected download
  events/      events, registration with capacity check (see apps/events/DEFENSE.md)
  clubs/       clubs, memberships, join requests, president approves / rejects
templates/
  base.html    main layout with navbar and messages, extend it in your pages
  home.html    home page with cards for every app
settings/
  .env         your local secrets (not in git)
  .env.example template for .env (in git)
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
.gitignore
.gitattributes  (keeps line endings LF for everyone)
```

## Team

| App | Who |
|---|---|
| users | <name> (team lead) |
| events | <name> |
| clubs | <name> |
| library | <name> |
| tutoring | <name> |

## Apps in short

**Users.** Roles are `student`, `tutor`, `admin`. Students and tutors can register themselves, admins are created in the admin panel.

**Tutoring.** Tutors fill their tutor profile (headline, subjects, rate, "is available") and add sessions to their schedule. A tutor shows in the directory only when "is available" is on. Students book seats, can cancel before the session starts, and leave a review after it ends. Validation: seat capacity, no overlapping bookings, no overlapping sessions for a tutor, sessions only in the future.

**Library.** Logged in users browse and download resources. Uploader or admin can edit / delete. Files are downloaded through a view, not a public `/media/` link.

**Events.** Any logged in user can create an event and becomes the organizer. Organizer, admin or superuser can edit / delete. Registration and cancel are POST only, capacity is checked inside a transaction. Rejoining restores the same registration. Registration closes when the event starts. Details: `apps/events/DEFENSE.md`.

**Clubs.** Logged in users create clubs (creator becomes president and member). Others send a join request, the president approves or rejects it. Only the president can edit / delete the club. Clubs have an optional logo (needs Pillow).

## Connecting your app to the navbar (important!)

The navbar in `base.html` and the cards on the home page link to every app. A link shows up only when your app has a URL with the right name, so nothing breaks before that.

You need 3 things:

1. `app_name` in your `urls.py` - the same as your app folder name
2. the main (list) page with `name="list"`
3. your urls included in `settings/urls.py`

Example, `apps/events/urls.py`:
```python
from django.urls import path

from apps.events.views import EventListView


app_name = "events"

urlpatterns = [
    path("", EventListView.as_view(), name="list"),
]
```

And in `settings/urls.py`:
```python
path("events/", include("apps.events.urls")),
```

| App | `app_name` | List URL name |
|---|---|---|
| tutoring | `"tutoring"` | `tutoring:list` |
| library | `"library"` | `library:list` |
| events | `"events"` | `events:list` |
| clubs | `"clubs"` | `clubs:list` |

Other pages can have any name, but `list` must be there. **Don't rename `list`** - the navbar, home page and other apps use it.

## Notes for everyone

Your models should inherit from AbstractBaseModel:
```python
from apps.abstracts.models import AbstractBaseModel


class Event(AbstractBaseModel): ...
```

If you need a link to user use `settings.AUTH_USER_MODEL`, not User directly:
```python
from django.conf import settings

organizer = ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=CASCADE)
```

User roles: check like `user.role == User.Role.TUTOR` in python, `user.role == "tutor"` in templates.

`soft_delete()` doesn't really delete, it just sets `deleted_at`. So add `.filter(deleted_at__isnull=True)` when you show stuff. `deleted_at` is not editable in forms and admin - only `soft_delete()` sets it. If something "disappeared", check its `deleted_at` in the shell.

Your templates go to `apps/<your_app>/templates/<your_app>/` (yes, app name twice) and start with:
```html
{% extends "base.html" %}
```
Don't make your own `base.html` inside your app - then your pages lose the navbar and messages.

All urls have a namespace, so always write the app name before the url name in templates, `redirect()` and `reverse()`:
```html
<a href="{% url 'events:list' %}">Events</a>
<a href="{% url 'users:login' %}">Log in</a>
```
`{% url 'login' %}` without `users:` gives `NoReverseMatch`.

Auth urls: `users:register`, `users:login`, `users:logout`, `users:profile`, `users:profile_edit`.

Pages only for logged in users: `LoginRequiredMixin` (or `@login_required` for function views). Put it first: `class MyView(LoginRequiredMixin, ListView)`.

Anything that changes data (book, join, register, delete, approve, logout) must be a POST form with `{% csrf_token %}`, not a link.

Forms with file upload need `enctype="multipart/form-data"`, otherwise the file is not sent.

To show a message after an action use `SuccessMessageMixin` with `success_message = "..."`, or `messages.success(request, "...")`. `base.html` already shows messages.

When a user edits his own stuff, take the object from `request.user` (filter the queryset by owner), not only from the url id, so nobody can edit other people's things.

After logout user goes to home page (`LOGOUT_REDIRECT_URL`), so there is no logout template.

## Git workflow

- `main` is the shared branch. Make your branch from the latest `main`, open a PR into `main`.
- PRs are merged with **Squash and merge** - one clean commit per PR.
- Keep PRs small (one feature or fix), merge often.
- To get the latest `main` into your branch use **merge, not rebase**:
  ```bash
  git fetch origin
  git merge origin/main
  ```
  Rebasing a branch you already pushed creates duplicate commits and the same conflicts again and again.
- Optional, but helps: `git config --global rerere.enabled true` - git remembers how you solved a conflict.
- Don't commit `.env`, `db.sqlite3`, `media/`, `.idea/` - they are in `.gitignore`.

## Before PR
```bash
ruff check . --fix
ruff check .
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## If something breaks
- `TemplateDoesNotExist` - check file name and folder: `apps/<app>/templates/<app>/file.html` (`.html`, not `.htm`)
- `NoReverseMatch` - forgot the namespace (`users:login`, not `login`), app not included in `settings/urls.py`, `app_name` missing, or someone renamed a url (`grep -rn "old_name" templates/ apps/`)
- `CAMPUS_ENV_ID not found` - `settings/.env` is missing (git can delete it when switching branches) - copy it again from `.env.example`
- `Cannot use ImageField because Pillow is not installed` - `uv pip install -r requirements/dev.txt`
- `Model ... was already registered` - the same model class is written twice in `models.py` (usually after a merge conflict)
- `CSRF verification failed` - form has no `{% csrf_token %}`, or you mixed `localhost` and `127.0.0.1`, or the page is old - reload and try again
- `You have N unapplied migration(s)` - run `python manage.py migrate`
- `manage.py test` crashes with `TypeError ... NoneType` - `apps/__init__.py` is missing
- object exists in admin but not on the site - check `deleted_at`, `is_available` / `is_cancelled`, and that its date is in the future
- left over `<<<<<<<` / `>>>>>>>` - `grep -rn "<<<<<<<\|>>>>>>>" apps/ templates/`
- weird old error after you fixed it - stop runserver (Ctrl+C) and start again
- `'tuple' object has no attribute ...` - extra comma at the end of a line like `model = User,`
- `No module named 'django'` - venv is not activated

## Rules
- work only in your app; shared files (`base.html`, `home.html`, `settings/`, `abstracts`) - tell the team lead
- make migrations only for your app, and `git pull` / `git merge origin/main` before `makemigrations`
- type hints + PEP8
- run ruff from the project root, not from inside your app folder