# Implement Campus Events with capacity-safe registration

CampusHub's Events app was empty. This change adds `/events/` with event browsing,
local-date/category filters, details, organizer-owned CRUD, participant lists,
remaining spots, registration and cancellation. The existing `events:list`
navbar/home link now resolves.

Models reuse the shared custom user and base timestamps. Database constraints
prevent duplicate registrations and invalid capacities/categories. Registration,
cancellation and capacity edits serialize through a transaction on the parent
event. Cancelled registrations can be restored without duplicate rows. Event
admin uses the same validation/lock, and registration admin cannot bypass capacity
by manually adding/editing entries. All mutation forms use CSRF protection.

Only Events files, the Events include in `settings/urls.py`, README and CHANGELOG
are changed. Users, clubs, library and tutoring files are untouched. No new
packages. `apps/events/DEFENSE.md` explains the implementation and demonstration.

Validation on Python 3.14.2 / Django 5.2.18 / SQLite:

- 32 Events tests passed, including last-place concurrency and admin validation.
- Django system checks, migration drift check and local migration application passed.
- Ruff passed for Events and the root URL file; `git diff --check` passed.
- Broader suite: 54 tests, 40 passed, 14 pre-existing Library namespace errors.
- Repository-wide Ruff: two existing Users I001 import-format errors.

See `apps/events/VERIFICATION.md` for details and existing team-owned integration
issues. PostgreSQL and Python 3.12 were not tested. Base is `main` because remote
`dev` did not exist; change the PR base if the team designates another branch.
