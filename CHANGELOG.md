# CHANGELOG

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