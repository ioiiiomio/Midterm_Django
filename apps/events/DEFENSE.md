# Events: implementation and midterm defense guide

## What each file does

| File | Purpose |
| --- | --- |
| `apps/events/models.py` | Event and EventRegistration database structure, constraints and validation. |
| `apps/events/forms.py` | Event input form and date/category filter validation. |
| `apps/events/services.py` | Transactional registration/cancellation and the event locking helper. |
| `apps/events/views.py` | Read requests, check ownership, process forms, render pages and messages. |
| `apps/events/urls.py` | Namespaced URL routes for the seven features. |
| `apps/events/admin.py` | Admin lists, search, filters, safe event editing and registration inspection. |
| `apps/events/migrations/0001_initial.py` | Creates the Events tables and constraints. |
| `apps/events/tests.py` | Automated behavior, database, security and concurrency tests. |
| `apps/events/templates/events/event_list.html` | Browse events and apply filters. |
| `apps/events/templates/events/event_detail.html` | Description, participants, remaining spots and action buttons. |
| `apps/events/templates/events/event_form.html` | Shared create/edit form. |
| `apps/events/templates/events/event_confirm_delete.html` | Confirmation before deletion. |
| `settings/urls.py` | Includes Events under `/events/`; existing routes are preserved. |
| `README.md`, `CHANGELOG.md` | Team integration and feature documentation. |
| `apps/events/DEFENSE.md` | This explanation and demonstration script. |
| `apps/events/VERIFICATION.md` | Executed checks, upstream issues and delivery steps. |
| `apps/events/PULL_REQUEST.md` | Prepared PR title and description. |

No files in users, clubs, library or tutoring were changed. The existing shared
base template is reused. No new package is required. An ignored local `.venv`
and SQLite database are development artifacts, not committed files.

## Models and relationships

An **Event** stores its title, description, date/time, location, category,
organizer and positive capacity. Its organizer is a ForeignKey: each event points
to one user, while a user may organize many events. The database stores the user
ID as `organizer_id`, not a separate copy of the user. The reverse relationship is
`user.organized_events.all()`.

An **EventRegistration** links one event to one student and records when the
student registered. One event has many registrations and one student can register
for many events. These two ForeignKeys implement that many-to-many relationship
through a model with extra information. Use `event.registrations.all()` and
`user.event_registrations.all()` for the reverse relationships.

Both user fields use `settings.AUTH_USER_MODEL`, so Events works with the team's
email-based `users.User`; there is no new user model. Both models inherit
`AbstractBaseModel` for created/updated/deleted timestamps. Physical deletion of
a user/event cascades to its related rows. Normal website deletion is soft deletion:
it sets `deleted_at` and active website queries exclude the record.

## Registration and capacity

1. The browser submits a POST form with a CSRF token.
2. Django requires login and takes the student from `request.user`; a submitted
   student ID cannot register/cancel somebody else.
3. Inside `transaction.atomic()`, the service locks the event before reading
   registrations. Edits/deletion/cancellation follow the same lock order.
4. The service rejects duplicates, started/deleted events and full capacity.
5. It creates a registration or restores a previously cancelled row, then commits.
6. The browser returns to details with a success or error message.

The database unique constraint on `(event, student)` prevents duplicate rows even
if a caller bypasses the web form. Capacity is at least one by both form validation
and a database constraint. Category is restricted by both choices and a constraint.
Remaining spots = capacity minus registrations whose `deleted_at` is empty.
Capacity cannot be edited below the current active participant count. New events
and changed dates must be in the future. An unchanged past date is accepted at
model validation so historical records can be corrected.

Cancellation soft-deletes only the current user's registration. It immediately
frees a place. Rejoining restores that row with a new registration timestamp;
the unique constraint remains intact.

The lock helper first performs a no-op UPDATE of the parent event, then selects
it for update. PostgreSQL holds an event-row lock through the transaction. SQLite
holds a database write lock before the count is read. Under SQLite contention a
registration/cancellation may ask the user to retry; it does not overbook. The
concurrency test uses two separate connections competing for one remaining spot.
PostgreSQL behavior requires running the suite against a working PostgreSQL setup;
a SQLite test run does not prove PostgreSQL was tested.

Capacity is an aggregate across rows: a simple database CHECK cannot count another
table. Application writes must use these services and locked event forms. Raw SQL,
manual ORM `.create()` or external tools can bypass that aggregate business rule.
Registration admin therefore allows inspection and deletion but disables manual
add/edit; create registrations on event pages. Admin event edits take the parent
lock too. Superusers/staff with the appropriate Django model permissions can use
admin; the custom `admin` role alone does not grant Django admin-site access.

## Views, URLs and permissions

A URL pattern maps a path to a view function. A view reads the request, queries
models and either renders a template or redirects after a successful POST.
`app_name = "events"` makes URL names unambiguous. `events:list` connects to the
team navbar without changing it.

| Route | Name | Access |
| --- | --- | --- |
| `/events/` | `events:list` | Public; optional `?date=YYYY-MM-DD&category=academic`. |
| `/events/<id>/` | `events:detail` | Public event information and participant names. |
| `/events/create/` | `events:create` | Login required; organizer set by server. |
| `/events/<id>/edit/` | `events:update` | Organizer, custom admin role, or superuser. |
| `/events/<id>/delete/` | `events:delete` | Same permission; GET confirms, POST deletes. |
| `/events/<id>/register/` | `events:register` | Login and POST required. |
| `/events/<id>/cancel/` | `events:cancel` | Login and POST; current user only. |

Logged-in non-owners receive HTTP 403 for management actions. Deleted/missing
events return 404. GET registration/cancellation returns 405. Anonymous protected
requests redirect to the existing `users:login`, preserving the return URL.
Any active authenticated role may participate; the field is named `student`
because that is the team's domain terminology, rather than restricting tutors.

Templates extend `base.html`, display Django form errors and messages, and escape
user-entered text. Dates are timezone-aware; input and exact-day filters use the
project's `Asia/Almaty` campus timezone. Invalid filters display form errors.

## Run locally on Windows

The team recommends Python 3.12. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/dev.txt
```

Set environment variables for this PowerShell session (or create an ignored
`settings/.env` as described in the root README):

```powershell
$env:CAMPUS_ENV_ID = "local"
$env:CAMPUS_SECRET_KEY = "replace-with-your-own-local-secret"
$env:CAMPUS_ALLOWED_HOSTS = "localhost,127.0.0.1"
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/events/`. Sign up using `/users/register/` or log in
using `/users/login/`. Users log in with email, not username. Do not commit local
secrets, the virtual environment or the SQLite database.

Verify with:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations events
python manage.py test apps.events
ruff check apps/events settings/urls.py
```

See `VERIFICATION.md` beside this guide for actual executed results and known
upstream failures. A failure outside Events is not a reason to modify a teammate's
application without coordinating with them.

## Midterm demonstration (two users, about five minutes)

1. Open `/events/` as a guest. Show the public list and filters.
2. Log in as user A. Create a future Academic Event with capacity 1. Explain that
   the server automatically makes A the organizer.
3. Open details. Show date, category, location, description and one remaining spot.
4. Open another browser/private window and log in as user B. Register. Show the
   participant name and zero remaining spots. Submit registration again to show
   the duplicate error; user A also cannot register because the event is full.
5. As B, try A's edit URL. Show the 403 permission denial.
6. As B, cancel the registration. Show the place becoming available; register again.
7. As A, increase capacity to 2 and edit the location. Demonstrate errors for zero
   capacity, an invalid date, or reducing capacity below the participant count.
8. Show date/category filters finding the event. Clear filters to see all events.
9. Open `/admin/` as a superuser. Show event/registration search and filters.
10. As A, delete the event through the confirmation form. Show that it disappears.
11. Run Events tests and explain one test for ownership and one for overbooking.

A useful defense explanation: "The form validates input, the view checks who may
act, the service locks the event while changing registrations, and database
constraints protect uniqueness and valid capacities. Templates display the result."

## Delivery

Work belongs on `feature/events`. No `dev` branch existed at implementation time;
use `main` as the PR base unless the team tells you otherwise. Never force-push
or merge automatically. If push/PR authentication is unavailable, follow the
manual delivery steps in `VERIFICATION.md`.
