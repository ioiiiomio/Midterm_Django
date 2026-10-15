# CHANGELOG

## 1.5.0 - 15.10.2026
### Added
- tutoring profiles, subjects, schedule sessions, student bookings and reviews
- tutor directory with subject and text search
- role-checked tutor schedule and student booking workflows
- capacity, duplicate booking, schedule conflict and review eligibility validation
- tutoring admin configuration, templates, tests and initial migration
- repeatable `seed_tutoring` command with local demo accounts and scenario data

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