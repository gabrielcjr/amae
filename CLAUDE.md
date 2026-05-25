# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AMAE (Agencia Missionaria de Apoio Estrategico) - a Django platform connecting investors with missionaries in Brazil. Server-side rendered with Django Templates, Tailwind CSS 4, and HTMX. All UI text is in Brazilian Portuguese.

## Tech Stack

- Python 3.14 (pyenv) + Django 6.0.5 + PostgreSQL 18
- Tailwind CSS 4 (`@tailwindcss/cli`) + HTMX 2
- pytest + pytest-django + pytest-xdist for testing
- Linting: flake8, black (line-length 88), isort (black profile)
- PDF generation: reportlab

## Common Commands

```bash
# Environment setup (required in each shell session)
eval "$(pyenv init -)"
source .venv/bin/activate

# Database
docker compose up -d                        # Start PostgreSQL 18
python manage.py migrate
python manage.py seed                       # Load all fixtures (interactive)
python manage.py seed --refresh             # Clear tables + reload fixtures

# Dev server
python manage.py runserver 0.0.0.0:8000     # or: make runserver
npm run dev:css                             # Tailwind watch mode (separate terminal)
npm run build:css                           # Tailwind one-time build

# Tests
pytest                                      # All tests (parallel via -n auto)
pytest missions/tests.py                    # Single app
pytest missions/tests.py::TestClassName     # Single class
pytest missions/tests.py::TestClassName::test_method  # Single test
pytest -x                                   # Stop on first failure

# Linting
make run-check-linters                      # Check all (flake8 + black + isort)
make run-fix-linters                        # Auto-fix all (black + isort + autoflake)
black . --config pyproject.toml             # Format
isort . --settings-file pyproject.toml      # Sort imports

# Migrations
python manage.py makemigrations
python manage.py migrate
```

## Architecture

### Django Apps

- **missions** - Core domain: `MissionField`, `Location`, `Missionary`, `Investor`, `Adoption`. Public views for listing missionaries, mission field map (Google Maps), investor/missionary detail pages.
- **finance** - `FinancialCategory`, `Transaction`. Admin-only with custom views for receipts (PDF), financial reports (HTML + PDF). All finance management happens through Django Admin.
- **pages** - CMS-like content: `Page`, `FAQ`, `Testimonial`, `SiteImage`, `ContactMessage`. Provides a `site_images` context processor for global template access.
- **accounts** - Registration (investor/missionary) and auth (login/logout via Django's built-in views).

### Key Domain Relationships

- `MissionField` has many `Location`s (villages with lat/lng)
- `Missionary` has M2M with `MissionField`
- `Adoption` links `Investor` to `Missionary` with a `mission_field` FK (always financial, monthly_value in BRL)
- `Transaction` optionally links to `Adoption` (for tracking income/expenses per adoption)
- `MissionField.status` is auto-calculated on save based on active adoptions vs `missionaries_needed`

### Template Structure

- `templates/base.html` - Site-wide layout with nav/footer
- `templates/home.html`, `templates/missions/`, `templates/pages/`, `templates/accounts/` - Page templates
- `templates/admin/finance/` - Custom admin templates for financial reports

### Static Assets

- `static/css/input.css` - Tailwind input (uses `@import "tailwindcss"` for v4)
- `static/css/output.css` - Built by Tailwind CLI (gitignored)
- `static/js/mission_field_country.js` - Admin JS for country-dependent field toggling

### Test Setup

- pytest with `DJANGO_SETTINGS_MODULE = amae.settings` (see `pytest.ini`)
- Parallel execution enabled by default (`-n auto`)
- Shared fixtures in root `conftest.py` (mission_field, missionary, investor, adoption, category_income, etc.)
- Tests use `@pytest.mark.django_db` and pytest fixtures (not Django TestCase)

### Fixtures (seed data)

Located in `fixtures/` directory. Loaded in dependency order by `python manage.py seed`. Covers all main models with realistic Brazilian data.

## Environment Notes

- PostgreSQL 18 volume mount must be `/var/lib/postgresql` (not `/var/lib/postgresql/data`)
- Docker container name: `amae_db`
- `.env` file holds DB credentials, SECRET_KEY, GOOGLE_MAPS_API_KEY
- WhiteNoise middleware serves static files
- Locale: `pt-br`, timezone: `America/Sao_Paulo`

## Code Style

- Follow Clean Code principles (see `.claude/skills/clean-code/SKILL.md`)
- Use Black formatting (88 char line length)
- isort with black profile
- Migrations, `apps.py`, `.venv`, and `static` are excluded from linting
- Model verbose names and help text are in Portuguese
- URL paths use Portuguese slugs (e.g., `/campos-missionarios/`, `/missionarios/`, `/investidores/`)
