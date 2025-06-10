# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**willgeben** is a Django-based sharing platform built with Cookiecutter Django template. It's a production-ready application for "Treibhaus donaufeld" community space.

## Key Technologies

- **Django 5.2.1** with Python 3.12
- **PostgreSQL** database with **Redis** cache/broker
- **Celery** for background tasks
- **Django REST Framework** for APIs
- **Bootstrap 5** + **Webpack** for frontend
- **Docker Compose** for development environment

## Development Commands

### Primary Workflow (using Just)
```bash
just                    # List all available commands
just up                 # Start development environment
just down               # Stop containers
just manage [command]   # Run Django management commands
just logs [service]     # View container logs
```

### Frontend Development
```bash
npm run dev             # Start webpack dev server (localhost:3000)
npm run build           # Build production assets
```

### Testing and Quality
```bash
pytest                  # Run test suite
coverage run -m pytest && coverage html  # Generate coverage report
mypy willgeben          # Type checking
ruff check              # Linting
ruff format             # Code formatting
```

## Architecture

### Configuration Pattern
- **Split settings**: `config/settings/base.py`, `local.py`, `production.py`, `test.py`
- Environment-based configuration with `.env` files
- Centralized routing in `config/urls.py` and `config/api_router.py`

### Application Structure
- **willgeben/users/**: Custom user model and authentication
- **willgeben/contrib/**: Extended Django contrib apps
- **willgeben/static/**: Frontend assets (CSS, JS, Sass)
- **willgeben/templates/**: Django templates with Bootstrap integration

### Development Environment
Docker services running on:
- **Django**: localhost:8000
- **Frontend dev server**: localhost:3000
- **Mailpit** (email testing): localhost:8025
- **Flower** (Celery monitoring): localhost:5555

### Testing Framework
- **pytest** with Django integration
- **Factory Boy** for test data generation
- Test files follow pattern: `test_*.py` in each app's `tests/` directory
- Global fixtures in `willgeben/conftest.py`

### API Design
- REST API with DRF at `/api/v1/`
- OpenAPI documentation at `/api/docs/`
- Token-based authentication
- CORS enabled for frontend integration

## Key Development Patterns

### User Model
- Custom user model with simplified name field (no first_name/last_name split)
- Authentication via django-allauth with MFA support

### Task Processing
- Celery workers for background tasks
- Redis as message broker
- Example task pattern in `willgeben/users/tasks.py`

### Frontend Integration
- Webpack handles asset bundling
- Sass preprocessing for styles
- Static files served via WhiteNoise in production

### Database Migrations
Always run migrations in Docker:
```bash
just manage migrate
```

## Important Files

- **justfile**: Primary command definitions
- **pyproject.toml**: Python dependencies and tool configuration
- **package.json**: Frontend dependencies and build scripts
- **docker-compose.local.yml**: Development environment definition
- **config/settings/**: Django configuration split by environment

## Internationalization

Multi-language support configured for:
- English (en_US)
- French (fr_FR) 
- Portuguese (pt_BR)

Translation files in `locale/` directory.