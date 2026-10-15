# CHANGELOG

## 1.8.0 - 16.10.2026
Integration of all apps after merging events, clubs, library and tutoring.

### Added
- clubs templates: list (search + category filter), detail (members, join request, pending requests for the president), create / edit form with logo upload, delete confirm
- tutoring templates wired to the views: tutor list, tutor detail with booking, tutor profile, my schedule, session form, my bookings, review form
- `apps/__init__.py` so `manage.py test` can discover tests
- `.gitignore` (venv, `.env`, sqlite, media, caches, IDE, OS files) and `.gitattributes` (LF line endings)
- `settings/.env.example`
- Pillow in requirements (club logos)
- README: pages table, apps overview, git workflow, more troubleshooting

### Changed
- list urls follow the navbar rule: `tutoring:tutor_list` -> `tutoring:list`, `library:resource_list` -> `library:list`
- clubs urls are namespaced (`clubs:list`, `clubs:detail`, `clubs:create`, `clubs:edit`, `clubs:delete`, `clubs:join`, `clubs:manage_request`), join and approve / reject are POST only
- library pages extend the main `base.html` (navbar and messages on every library page)
- `AbstractBaseModel.deleted_at` is `editable=False` - only `soft_delete()` can set it
- `soft_delete()` also saves `updated_at`
- git flow: branch from `main`, merge (not rebase) to update, squash merge PRs

### Fixed
- duplicate `Membership` model in clubs after merge conflict (broke admin and `unique_together`)
- duplicated half of clubs `views.py` left after rebase
- `NoReverseMatch` for `tutor_list` on home, tutoring and library pages
- tutoring session hidden because `deleted_at` was filled in the admin form
- `{% url 'login' %}` on home page -> `users:login`
- ruff: import order, trailing newlines, `__str__` return types in clubs

## 1.7.0 - 15.10.2026 - Events
### Added
- Event and EventRegistration models using the shared user and abstract base model
- database constraints, initial events migration, admin list / search / filters
- event list / detail / create / edit / delete pages at `/events/`, `events:list` for the navbar
- local-date and category filters, organizer / admin permissions, CSRF-protected registration
- capacity check with transactional locking, soft cancel and rejoin
- events tests and `apps/events/DEFENSE.md` demo guide

## 1.6.0 - 15.10.2026 - Tutoring, Library, Clubs
### Added
- tutoring: tutor profiles, subjects, schedule sessions, student bookings and reviews
- tutoring: tutor directory with subject filter and text search
- tutoring: role-checked tutor schedule and student booking flows
- tutoring: capacity, duplicate booking, schedule conflict and review eligibility validation
- tutoring: admin, templates, tests, initial migration
- tutoring: repeatable `seed_tutoring` command with local demo accounts
- library: resources with subject and type, upload / detail / edit / delete
- library: role-based access, owner or admin edit / delete, protected downloads
- clubs: Club and Membership models, admin
- clubs: create, edit, delete (president only), join requests, approve / reject

## 1.5.0 - 15.10.2026
### Added
- navbar links to tutoring, library, events and clubs (shown only when the app has a `<app>:list` url)
- home page cards for tutoring, library, events and clubs for logged in users
- login / sign up links in navbar and on home page for guests
- README section "Connecting your app to the navbar" with url naming rules

### Changed
- login and logout urls are namespaced: `users:login`, `users:logout`
- logout redirects to home page, no logout template

### Fixed
- `NoReverseMatch` for `logout` and `login` in base.html and home.html
- missing `auth_views` import in users urls (now uses `LogoutView` directly)

## 1.4.0 - 15.10.2026
### Added
- profile page (`/users/profile/`) - shows name, email, role and join date
- profile edit page (`/users/profile/edit/`) - user can change first and last name only
- ProfileForm
- messages block in base.html
- link to profile in navbar

### Fixed
- base.html had wrong extension (.htm)
- imports and blank lines in users views and forms (ruff)

## 1.3.0 - 15.10.2026
### Added
- register, login and logout pages in users app
- RegisterForm (student or tutor only, admin can't register by himself)
- base.html with navbar and home page
- LOGIN_URL, LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL in settings
- MEDIA_URL and MEDIA_ROOT
- ruff.toml with our lint rules

### Changed
- TIME_ZONE is now Asia/Almaty
- DATABASES moved from base.py to env files only

### Fixed
- trailing comma bugs in settings and forms
- removed sys.path hack from settings

## 1.2.0 - 15.10.2026
### Added
- abstracts app with AbstractBaseModel (created_at, updated_at, deleted_at, soft_delete)
- custom User in users app - email login and roles
- AUTH_USER_MODEL in settings
- empty apps: events, clubs, library, tutoring
- split settings into conf / base / env (local, prod)

### Changed
- moved to python 3.12
- updated README

### Fixed
- removed extra git repo inside settings/env
- fixed BASE_DIR and db path

### Removed
- education and auths apps (same as tutoring and users)

## 1.1.0 - 15.10.2026
### Added
- README and CHANGELOG
- project structure from HW1
- ruff linting