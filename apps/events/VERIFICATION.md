# Executed verification and delivery

Verified on 15 October 2026 with Windows, Python 3.14.2, Django 5.2.18 and SQLite.
The team recommends Python 3.12; that interpreter was not available locally and
was not tested. Existing requirements were installed in the ignored `.venv`;
no dependency files changed. Downloaded wheels were checked against PyPI SHA-256
checksums. Temporary download scripts/cache were removed.

## Results

| Executed check | Result |
| --- | --- |
| `python -m compileall -q apps/events` | Passed. |
| `python manage.py check` | Passed; no issues. |
| `python manage.py test apps.events --verbosity 1` | Passed: 32 tests, including concurrent last-place registration, admin editing, permissions, CSRF, forms, CRUD, filters, cancellation/rejoining and constraints. |
| `python manage.py makemigrations --check --dry-run` | Passed; no changes detected across the project. |
| `python manage.py migrate --noinput` | Passed; all migrations, including Events, applied locally. |
| `python manage.py showmigrations events` | `[X] 0001_initial`. |
| `ruff check apps/events settings/urls.py` | Passed. |
| `git diff --check` | Passed. |
| Explicit tests for all five application modules | 54 tests: 40 passed, 14 Library errors. All errors are missing `library` URL namespace. |
| `ruff check .` | Two existing I001 errors: `apps/users/admin.py`, `apps/users/views.py`. Events is clean. |

The initial Events test run exposed a test discovery import issue under this
namespace-package layout and an admin split-date-field/widget mismatch. Both were
fixed before the passing run. Tests use absolute app imports, and EventForm
explicitly declares its date field so admin uses the same valid input widget.

The complete-suite command was:

```powershell
python manage.py test apps.users.tests apps.events.tests apps.clubs.tests apps.library.tests apps.tutoring.tests --verbosity 1
```

## Issues requiring team coordination

- **Library integration:** its routes exist in `apps/library/urls.py` but are not
  included by the existing root URL configuration. The Library developer/team
  lead should include that namespace. All 14 broader-suite errors have that cause.
  The navbar expects `library:list`, while Library currently uses `resource_list`;
  its developer should also provide the compatible name.
- **Users lint:** add the expected blank line after imports in `admin.py` and
  `views.py`. Neither file was changed by Events.
- **Guest home template:** `templates/home.html` still reverses the unnamespaced
  `login` URL. The team lead should change it to `users:login`. Use `/events/`
  directly for the guest Events demonstration.
- **Production settings:** the existing `settings/env/prod.py` does not import
  the base settings and uses literal `DB_HOST`/`DB_PORT` strings. The settings
  owner must repair it before deployment. PostgreSQL and production deployment
  have not been tested; the executed concurrency test used SQLite.
- No shared-user-model dependency is missing. Events uses the existing user model
  and abstract base model without modifying them.

## Branch and manual delivery

No remote `dev` branch existed. The feature is based on `main` and belongs on
`feature/events`. `PULL_REQUEST.md` contains a ready-to-use PR title/description.
Never push this feature directly to `main`, force-push, or merge automatically.

If GitHub push authentication is unavailable, authenticate Git for Windows with
an account that has repository write access, then run from the repository root:

```powershell
git push --set-upstream origin feature/events
```

Open https://github.com/ioiiiomio/Midterm_Django/compare/main...feature/events?expand=1
and create a PR with base `main`, compare `feature/events`, and the text from
`PULL_REQUEST.md`. If the team creates/designates `dev`, use that branch as the
base instead. If your account lacks repository write access, ask the owner to
invite you as a collaborator or push this branch to your fork and open a PR from it.

See the final delivery note below for the actual push/PR outcome.


## Actual delivery outcome

- Implementation committed as `09ea9b8` on `feature/events`.
- Branch pushed successfully to `origin/feature/events` with upstream tracking.
- Draft PR created into `main`: https://github.com/ioiiiomio/Midterm_Django/pull/5
- No force-push or merge was performed. No manual authentication step is needed.
- All 18 changed/created files are listed in `DEFENSE.md`; teammates' application
  files remain unchanged. The working tree was checked after delivery.
