# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**willgeben** is a Django-based sharing platform for Treibhaus donaufeld, built with Cookiecutter Django. It uses Docker for local development and includes Celery for background tasks, Django REST Framework for API endpoints, and webpack for frontend asset compilation.

## Development Commands

### Docker Environment (Primary)
```bash
# Build containers
just build

# Start development environment  
just up

# Stop containers
just down

# Remove containers and volumes
just prune

# View container logs
just logs [service]

# Run Django management commands
just manage <command>
```

### Frontend Development
```bash
# Development server with hot reload
npm run dev

# Build production assets
npm run build
```

### Python Development (Direct)
```bash
# Run tests
pytest

# Type checking
mypy willgeben

# Code formatting/linting
ruff check willgeben
ruff format willgeben

# Test coverage
coverage run -m pytest
coverage html

# Create superuser
python manage.py createsuperuser

# Run Celery worker
celery -A config.celery_app worker -l info

# Run Celery beat scheduler
celery -A config.celery_app beat
```

## Architecture

### Django Structure
- **config/**: Project configuration and settings
  - `settings/`: Environment-specific settings (base, local, production, test)
  - `api_router.py`: DRF API URL routing
  - `celery_app.py`: Celery configuration
- **willgeben/**: Main application directory
  - `users/`: User management app with custom User model
  - `static/`: Frontend assets (CSS, JS, SASS)
  - `templates/`: Django templates with Bootstrap 5
  - `contrib/sites/`: Custom sites framework migrations

### Key Technologies
- **Backend**: Django 4.x with PostgreSQL database
- **Frontend**: Bootstrap 5 + Webpack + SASS compilation
- **API**: Django REST Framework with drf-spectacular for OpenAPI docs
- **Auth**: django-allauth with email verification
- **Tasks**: Celery with Redis broker and django-celery-beat
- **Deployment**: Docker with production configs

### Settings Configuration
- Uses django-environ for environment variable management
- Multi-environment setup: local, production, test
- Custom User model in `users.User`
- API available at `/api/` with Swagger docs for admin users
- CORS enabled for API endpoints

### Frontend Assets
- Webpack handles JS/CSS bundling with hot reload in development
- Bootstrap 5 customization via SASS variables in `static/sass/`
- Asset compilation outputs to `static/js/vendors.js` and processed CSS

### Development Notes
- Local email testing via Mailpit at http://127.0.0.1:8025
- API documentation available in debug mode
- Custom webpack configuration for development vs production builds
- Celery beat uses database scheduler for periodic tasks

## Architectural Notes
- **items** is the basic unit for any element in the project