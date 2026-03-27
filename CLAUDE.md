# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Linux/macOS | venv\Scripts\activate on Windows
pip install -r requirements.txt

# Development
cp .env.local .env         # Use local SQLite config
python manage.py migrate
python manage.py runserver # http://localhost:8000

# Tests
python manage.py test
python manage.py test apps.properties  # Single app

# Create superuser
python manage.py createsuperuser
```

## Architecture

### Project Layout
- `app_propify/` — Django project config (settings, root URLs)
- `apps/` — Six Django apps: `users`, `locations`, `catalogs`, `properties`, `crm`, `notifications`
- `common/` — Shared base models, auth, middleware, crypto utilities

### Base Models (`common/models/base.py`)
All apps inherit from these:
- `BaseAuditModel` — adds `created_at`, `updated_at`, `created_by`, `updated_by` (auto-populated via `CurrentUserMiddleware`)
- `BaseDefinitionModel` — adds `name` (unique), `is_active` (for catalog/lookup tables)
- `BaseModel` — combines both; used for most catalog entries

### App Responsibilities
- **users** — Custom `AbstractUser` with `Role`/`Area` FKs; JWT auth + local dev mode
- **locations** — Geographic hierarchy: Country → Department → Province → District → Urbanization
- **catalogs** — Reference/lookup data: property types, statuses, currencies, lead statuses, etc.
- **properties** — Core real estate listings; related models `PropertySpecs`, `PropertyMedia`, `PropertyDocument`, `PropertyFinancialInfo` hang off `Property` via FK/1:1
- **crm** — Lead pipeline: `Contact` → `Lead` → `Requirement` → `RequirementMatch` ↔ `Property` → `Match` → `Event`/`Proposal`
- **notifications** — Simple notification store

### Authentication
- **Production:** JWT Bearer tokens (`/api/auth/token/`, `/api/auth/token/refresh/`)
- **Local dev:** Set `LOCAL_MODE=True` in `.env` and pass `X-User-Id` header — no token needed; user is auto-created if missing
- All API endpoints require authentication except `/api/auth/token*`, Swagger, and ReDoc

### Database
- **Local:** SQLite (`USE_SQLITE=True` in `.env.local`)
- **Production/Staging:** Azure SQL Server (MSSQL) via `mssql-django`; connection configured via `DB_HOST/DB_NAME/DB_USER/DB_PASS`

### Environment Files
- `.env.local` — SQLite, debug on, local mode
- `.env.staging` — Azure SQL, staging services
- `.env.prod` — Azure SQL, production services
- Set `ENV_FILE` env var to override which file loads, or copy to `.env`

### API
- DRF ViewSets with `DefaultRouter`; all routes under `/api/{app}/`
- Filtering via `django-filter` (`DjangoFilterBackend`)
- Default pagination: 20 items per page
- Swagger UI at `/swagger/`, ReDoc at `/redoc/`

### Media Storage
- **Production:** Azure Blob Storage (`USE_AZURE_STORAGE=true`); configured via `AZURE_ACCOUNT_NAME`, `AZURE_ACCOUNT_KEY`, `AZURE_CONTAINER`
- **Local:** Local filesystem

### Deployment
- Deployed to Azure App Service; GitHub Actions CI/CD pipelines in `.github/workflows/`
- Push to `main` triggers production deploy; `staging` branch deploys to staging
