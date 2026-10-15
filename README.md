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

If runserver says `You have N unapplied migration(s)` - someone pushed a new migration, just run `python manage.py migrate` again.

Pages that work now:
- http://127.0.0.1:8000/ - home (cards for tutoring, library, events, clubs when logged in)
- http://127.0.0.1:8000/users/register/ - sign up
- http://127.0.0.1:8000/users/login/ - login (with email, there is no username)
- http://127.0.0.1:8000/users/profile/ - my profile (only when logged in)
- http://127.0.0.1:8000/users/profile/edit/ - edit my name
- http://127.0.0.1:8000/tutoring/ - tutor directory and subject search
- http://127.0.0.1:8000/tutoring/tutors/<id>/ - tutor profile and available sessions
- http://127.0.0.1:8000/tutoring/schedule/ - tutor schedule management
- http://127.0.0.1:8000/tutoring/bookings/ - student bookings and eligible reviews
- http://127.0.0.1:8000/admin/ - admin

To load repeatable local tutoring demo data, run `python manage.py seed_tutoring`. The command prints demo account emails and their shared password; pass `--password` to choose another one. Demo accounts include an admin, three tutors, two students, available and nearly full sessions, a cancelled session, and a completed session with a review. Use these accounts only in local development.

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
  tutoring/    tutor profiles, subjects, sessions, bookings and reviews
templates/
  base.html    main layout with navbar and messages, extend it in your pages
  home.html    home page with cards for every app
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

Tutoring models use the shared custom user via `settings.AUTH_USER_MODEL`. Tutors manage their profile and future sessions under `/tutoring/`; students can book available sessions, cancel upcoming bookings, and review a confirmed session after it ends. Booking validation enforces seat capacity and prevents overlapping sessions.

## Team

| App | Who |
|---|---|
| users | <name> (team lead) |
| events | <name> |
| clubs | <name> |
| library | <name> |
| tutoring | <name> |

## Connecting your app to the navbar (important!)

The navbar in `base.html` and the cards on the home page already have links to tutoring, library, events and clubs. A link shows up only when your app has a URL with the right name. Until then it's hidden (navbar) or goes to `#` (home cards), so nothing breaks.

To make your link work you need 3 things:

1. `app_name` in your `urls.py` - the same as your app folder name
2. a main page (list page) with `name="list"`
3. your urls included in `settings/urls.py`

Example for events, `apps/events/urls.py`:
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
(path("events/", include("apps.events.urls")),)
```

So the names must be exactly:

| App | `app_name` | URL name used in navbar |
|---|---|---|
| tutoring | `"tutoring"` | `tutoring:list` |
| library | `"library"` | `library:list` |
| events | `"events"` | `events:list` |
| clubs | `"clubs"` | `clubs:list` |

Other pages (detail, create, etc.) you can name however you want, but `list` must be there.

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

User roles are `student`, `tutor`, `admin`. Check like `user.role == User.Role.TUTOR`.

`soft_delete()` doesn't really delete, it just sets deleted_at. So add `.filter(deleted_at__isnull=True)` when you show stuff.

Your templates go to `apps/<your_app>/templates/<your_app>/` (yes, app name twice) and should start with:
```html
{% extends "base.html" %}
```

All urls have a namespace, so always write the app name before the url name in templates and `reverse()`:
```html
<a href="{% url 'events:list' %}">Events</a>
<a href="{% url 'users:login' %}">Log in</a>
```
`{% url 'login' %}` without `users:` will give `NoReverseMatch`.

Auth urls are in the users app: `users:register`, `users:login`, `users:logout`, `users:profile`, `users:profile_edit`.

If a page is only for logged in users, use `LoginRequiredMixin` (or `@login_required` for function views). It will send people to the login page automatically. Put it first: `class MyView(LoginRequiredMixin, ListView)`.

To show a message after an action (like "Registered for event"), use `SuccessMessageMixin` with `success_message = "..."`. `base.html` already shows messages.

When a user edits his own stuff, take the object from `request.user`, not from the url id, so nobody can edit other people's things.

Logout must be a POST form, not a link (Django 5 thing, a link gives 405). There is already a button in `base.html`. After logout user goes to home page (`LOGOUT_REDIRECT_URL`), so there is no logout template.

## If something breaks
- `TemplateDoesNotExist` - check file name and folder (`.html`, not `.htm`, and `templates/<app>/` inside your app)
- `NoReverseMatch` - you forgot the namespace (`users:login`, not `login`), or your app is not included in `settings/urls.py`, or `app_name` is missing
- `You have N unapplied migration(s)` - run `python manage.py migrate`
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

## Events application

Events are available at `/events/`; the existing navbar and home card resolve
`events:list` automatically. See [the Events defense guide](apps/events/DEFENSE.md)
for the file inventory, design explanation, local setup, and demonstration script.

Any logged-in user may create an event and becomes its organizer. Only the
organizer, an account with the shared `admin` role, or a superuser may edit/delete
it. Registration/cancellation always apply to the current user and require POST
with CSRF protection. Events and cancelled registrations use the shared soft-delete
flag. Rejoining restores the same registration row. Past events remain visible,
but new registration closes when the event starts. Filters use campus-local dates.

Run verification after installing `requirements/dev.txt` and configuring the
existing environment variables:

```bash
python manage.py makemigrations --check --dry-run
python manage.py check
python manage.py test apps.events
ruff check apps/events settings/urls.py
```

No remote `dev` branch existed when Events was implemented, so `feature/events`
starts from `main` and its PR targets `main` unless the team creates/designates
another integration branch. No new dependency was introduced.
