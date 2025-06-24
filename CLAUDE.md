# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**bubble** is a Django-based sharing platform for Treibhaus donaufeld, built with Cookiecutter Django. It uses Docker for local development and includes Celery for background tasks, Django REST Framework for API endpoints, and webpack for frontend asset compilation.

## Development Environment

**IMPORTANT**: This project is developed using Dropbox and Just commands. All Django management commands should be run using `just manage <command>`.

**Language**: The website is in German, so all texts, labels, and user-facing content must be in German only.

## Formatting Guidelines

### User Mentions
When mentioning user anywhere show like this username (Full Name) according to @bubble/users/models.py

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

# Create migrations
just manage makemigrations

# Apply migrations
just manage migrate

# Create superuser
just manage createsuperuser
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
mypy bubble

# Code formatting/linting
ruff check bubble
ruff format bubble

# Run pre-commit hooks (used in CI/CD)
pre-commit run --all-files

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
- **bubble/**: Main application directory
  - `users/`: User management app with custom User model and Profile
  - `items/`: Item management app with CRUD operations and filtering
  - `categories/`: Category and tag management for items and services
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

## Data Models

### Items App (`items.models`)

#### Item Model
Core entity representing physical items users want to share.

**Item Types:**
- **Sell (0)**: Items for sale with optional price
- **Give Away (1)**: Free items to give away
- **Borrow (2)**: Items available for borrowing

**Key Fields:**
- `item_type`: Integer field with choices above
- `name`, `description`: Item details
- `price`: Required for selling items, empty for others
- `status`: Item condition (new/used/old)
- `user`: Item owner (ForeignKey to User)
- `category`: Single ItemCategory assignment
- `intern`: Boolean (only visible to intern users)
- `th_payment`: Boolean (accepts Treibhaus payment)
- `display_contact`: Boolean (show owner contact info)
- `active`: Boolean (item is publicly visible)

#### ItemTagRelation Model
Many-to-many relationship between Items and ItemTags.



#### Image Model
Multiple images per item with ordering support.

### Categories App (`categories.models`)

#### ItemCategory Model
Hierarchical organization system for items.
- `parent_category`: Self-referential for unlimited nesting
- `get_hierarchy()`: Returns full path (e.g., "Electronics > Phones")

#### ServiceCategory Model
Flat organization system for future services (no hierarchy).

#### ItemTag Model
Independent labeling system for items.
- Many-to-many relationship with Items via ItemTagRelation
- Admin-managed only (users can select, not create)

### Users App (`users.models`)

#### Profile Model
Extended user information linked to Django User.
- `intern`: Boolean (enables admin features like intern/th_payment fields)
- `address`, `phone`: Contact information
- `email_reminder`: Notification preferences

### Relationships
- **Item ↔ ItemCategory**: One-to-many (each item has one category)
- **Item ↔ ItemTag**: Many-to-many via ItemTagRelation
- **Item ↔ User**: Many-to-one (user owns multiple items)
- **User ↔ Profile**: One-to-one (automatic creation)

## URL Structure

### Items App URLs (`/items/`)
```
/items/                    # All items
/items/sell/              # Items for sale (shareable)
/items/give_away/         # Free items (shareable)
/items/borrow/            # Items to borrow (shareable)
/items/<id>/              # Item detail
/items/create/            # Create item (login required)
/items/<id>/edit/         # Edit item (owner only)
/items/<id>/delete/       # Delete item (owner only)
/items/my-items/          # User's item management
/items/<id>/toggle-status/ # Activate/deactivate item
```

**Filtering Support:**
- GET parameters: `?search=laptop&category=1&tags=2,3&status=1`
- URL-based type filtering: `/items/sell/?category=1&tags=2`
- Shareable filtered links for easy sharing

## Frontend Features

### Item Management
- **Complete CRUD operations** with proper permissions
- **Tag selection** via checkboxes (admin-managed tags)
- **Category hierarchies** with dropdown selection
- **Image upload support** (multiple images per item)
- **Responsive design** with Bootstrap 5

### Filtering & Search
- **Text search** across name and description
- **Category filtering** with hierarchical support
- **Tag filtering** with checkbox selection
- **Item type filtering** via URL or form
- **Status/condition filtering**
- **Pagination** with customizable page size

### User Experience
- **Navigation pills** for quick type switching
- **Shareable URLs** for specific item types and filters
- **Owner-only actions** (edit/delete/toggle status)
- **Intern-only features** (intern/th_payment fields for intern users)
- **Contact display toggle** per item

### Security & Permissions
- **Login required** for create/edit/delete operations
- **Owner verification** for item modifications
- **Intern field visibility** based on user.profile.intern
- **Form validation** for price requirements by item type

## Code Quality & CI/CD

### Pre-commit Hooks
This project uses pre-commit hooks that run automatically on GitHub Actions. Key checks include:
- **Trailing whitespace removal**
- **End-of-file fixing**
- **Ruff linting** (max line length: 88 characters)
- **Ruff formatting**
- **djLint template formatting** (requires explicit block names like `{% endblock content %}`)

**IMPORTANT**: Always run `pre-commit run --all-files` before committing to catch formatting issues early.

### Linter Actions
- **Save findings for passing linter actions next time**
  - Understand common linter issues specific to this project
  - Review specific ruff and pre-commit hook error patterns
  - Create a checklist of frequent formatting and linting corrections

## Git Workflow

**CRITICAL**: Never push directly to main branch. Always create pull requests for code changes:

1. Create feature branch: `git checkout -b feature/description`
2. Make changes and commit
3. Push branch: `git push -u origin feature/description`
4. Create PR: `gh pr create --title "Title" --body "Description"`
5. Wait for CI/CD checks to pass before merging

## Future Services App Structure

### Planned Architecture
When implementing the services app, follow this structure:

```
bubble/services/
├── models.py           # Service model with ServiceCategory
├── forms.py           # ServiceForm with ServiceTag support
├── views.py           # ServiceListView, ServiceDetailView, etc.
├── urls.py            # URL patterns following items app pattern
├── admin.py           # Admin interface for services
└── templates/services/
    ├── service_list.html
    ├── service_detail.html
    ├── service_form.html
    └── my_services.html
```

### Service Model Structure
```python
class Service(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.DurationField()  # Service duration
    location = models.CharField(max_length=255)  # Service location
    availability = models.TextField()  # When service is available
    active = models.BooleanField(default=True)
    # ... other service-specific fields
```

### Services URLs (`/services/`)
```
/services/                 # All services
/services/<category>/      # Services by category (flat structure)
/services/<id>/           # Service detail
/services/create/         # Create service (login required)
/services/<id>/edit/      # Edit service (owner only)
/services/my-services/    # User's service management
```

### Key Differences from Items
- **Flat categories**: ServiceCategory has no hierarchy
- **Duration-based**: Services have time components
- **Location-aware**: Services tied to physical locations
- **Availability scheduling**: When services can be provided
- **Different pricing model**: Services typically always have prices
```
