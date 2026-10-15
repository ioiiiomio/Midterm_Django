# CHANGELOG

## Events feature - 15.10.2026
### Added
- Event and EventRegistration models using the shared user and abstract base model.
- Database constraints, initial Events migration, and admin listings/search/filtering.
- Event list/detail/create/edit/delete pages at `/events/`, with `events:list` integration.
- Local-date/category filters, ownership/admin permissions, CSRF-protected registrations.
- Capacity checks with transactional parent locking and soft cancellation/rejoining.
- Events tests and a beginner-friendly defense/demo guide.


## 1.5.0 - 15.10.2026
### Added
- navbar links to tutoring, library, events and clubs (shown only when the app has a `<app>:list` url)
- home page cards for tutoring, library, events and clubs for logged in users
- login / sign up links in navbar and on home page for guests
- README section "Connecting your app to the navbar" with url naming rules

### Changed
- login and logout urls are namespaced now: `users:login`, `users:logout`
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
- MEDIA_URL and MEDIA_ROOT (for library uploads later)
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