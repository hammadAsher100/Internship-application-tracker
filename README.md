# InternTrack

InternTrack is a university internship application tracker for students, employers, and placement officers. Students maintain a profile and CV, discover approved internships, apply, and follow application progress. Employers manage company postings and review applicants. Placement officers approve employers and postings and monitor activity.

The project is being built in phases for SEN-311 Software Construction, Bahria University Karachi (Fall 2026). This README will be kept aligned with the implementation as each phase lands.

Current progress: Phase 0 is committed. Phase 1 provides email-based accounts, student and employer registration, company approval status, officer account creation, role checks, and login lockout. Student profiles, postings, and the remaining workflow are being added in later phases.

## Features in scope

- Role-based accounts for students, employers, and placement officers.
- Student profile, skills, contact details, and versioned CV uploads.
- Employer company registration and officer approval.
- Internship posting creation, approval, search, and filtering.
- Applications with an immutable profile/CV snapshot and a validated status workflow.
- Interview scheduling, persisted notifications, and live WebSocket updates.
- Role-specific dashboards, placement summaries, and audit activity.

Automated candidate ranking, external job-platform integrations, built-in video interviews, and multi-university support are out of scope.

## Technology

- Python 3.12 and Django 5.2 LTS
- PostgreSQL 16 for persistent data and concurrency-safe selection capacity
- Django Channels, Daphne, and Redis for WebSocket notifications
- Django templates, Bootstrap 5.3, and custom CSS
- pytest, pytest-django, pytest-cov, factory-boy, freezegun, and Ruff
- Docker Compose for local development and GitHub Actions for CI

## Architecture

The application follows a layered Django structure:

- `apps/accounts` owns authentication, the custom user, and role permissions.
- `apps/students` and `apps/employers` own profiles and company records.
- `apps/postings` owns internship listings and approval/search behavior.
- `apps/applications` owns applications, immutable snapshots, status history, interviews, and workflow rules.
- `apps/notifications` owns persisted notifications and Channels consumers.
- `apps/dashboards` and `apps/audit` provide role-based summaries and activity records.
- `apps/core` contains shared domain primitives, validation, and helpers.
- `config` contains environment-specific settings and the ASGI/WSGI entry points.
- `templates`, `static`, `tests`, `scripts`, and `docs` hold the UI, assets, verification, utilities, and project documentation.

Views handle HTTP input and presentation. Business rules belong in service modules and are enforced server-side. Protected data is scoped to the acting user, and high-impact actions are recorded in the audit log.

## Requirements

For the recommended container workflow, install Docker Desktop with Docker Compose v2. For local Python development, use Python 3.12, PostgreSQL 16, and Redis 7. PostgreSQL is required for concurrency tests; SQLite is not a substitute for those tests because it does not provide the needed row-lock behavior.

## Quick start (Docker)

From the cloned project directory:

```sh
git clone <repository-url>
cd internship-application-tracker
cp .env.example .env
```

Set a unique `DJANGO_SECRET_KEY` and a local-only `POSTGRES_PASSWORD` in `.env`, then start the services:

```sh
make up
make migrate
```

Open <http://localhost:8000>. Demo data seeding is planned but not implemented yet. Stop the stack with `make down`; add `-v` to `docker compose down` only when you intentionally want to remove local database and media volumes.

The Makefile also provides `make down`, `make test`, `make lint`, and `make logs`. Officer accounts can be created with `python manage.py create_officer --email officer@example.edu --full-name "Placement Officer"`; the command prompts for a password. Demo seeding and performance checks will be added in later phases.

## Local development

Create and activate a virtual environment, install development dependencies, and set environment variables using `.env.example` as a reference:

```sh
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py runserver
```

Run the application against PostgreSQL and Redis as configured in the environment. Never commit `.env`, secrets, uploaded files, or a local database.

## Tests and code quality

Run the suite against PostgreSQL and Redis:

```sh
pytest --cov=apps --cov-fail-under=80
ruff check .
ruff format --check .
```

The test suite is organized by unit, integration, permission, concurrency, boundary, regression, and performance concerns. Business rules should have automated coverage, including access control, deadline boundaries, duplicate application prevention, snapshot immutability, and selection capacity under concurrent requests.

## WebSocket demonstration

The browser client connects to the authenticated notification socket and displays persisted/live updates. The raw client will be available at `scripts/ws_client.py`; when implemented, run it with:

```sh
python scripts/ws_client.py
```

It uses the demo account/session settings documented with the script and prints notifications received for that user. Notifications are persisted, so users can still see messages after reconnecting.

## Configuration and security

Copy `.env.example` to `.env` for local configuration. Secrets are supplied through environment variables. Production settings must disable debug mode, restrict allowed hosts, use secure cookies, and serve uploaded documents only through permission-checked views. Django templates escape user content by default. Do not place credentials or user uploads in source control.

## Project phases

Implementation follows the build plan's sequence: scaffold; accounts and permissions; student profiles and CVs; employer approval; postings; applications; review workflow; notifications; dashboards and audit; hardening; refactoring; DevOps; and final documentation/evidence. Each phase is intended to finish with its acceptance criteria and a focused commit.

## Repository notes

`INTERNSHIP_TRACKER_BUILD_PLAN.md` is a local planning document and must not be committed or pushed to GitHub. The repository uses Conventional Commit messages, for example `feat(applications): enforce selection capacity with row lock` and `docs: update setup instructions`.

## Troubleshooting

- **Port 8000 is busy:** change the published port in the Compose configuration and use that port in the browser.
- **Database is not ready:** check `docker compose ps` and `docker compose logs db`; wait for the database health check before running migrations.
- **WebSocket connection fails:** confirm Redis is healthy and the application is served through its ASGI/Daphne entry point. Persisted notifications should remain available after reconnecting.
- **Environment changes are not reflected:** recreate the web service with `docker compose up --build -d web`.
- **Need a clean database:** `docker compose down -v` removes named data volumes and is destructive to local demo data.

## Course context

Course: SEN-311 Software Construction  
Institution: Bahria University Karachi  
Term: Fall 2026 (CEP)
