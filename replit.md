# Overview

**bubble** is a Django-based sharing platform for Treibhaus donaufeld, a community space in Vienna. The platform allows users to share various items like books, tools, and services within the community. It features a modern web interface with internationalization support (German primary language), user authentication, item management with image upload, AI-powered item processing via Temporal.io workflows, and a comprehensive category system.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Django templates with Bootstrap 5 for responsive UI
- **Asset Management**: Webpack with hot reloading for development
- **Styling**: SCSS compilation with PostCSS processing
- **JavaScript**: jQuery with Select2 for enhanced form controls
- **Internationalization**: Django i18n with German as primary language, all user-facing text must use `{% trans %}` tags
- **Theme System**: Light/dark/auto theme support with session-based persistence
- **Progressive Web App**: PWA support for mobile app-like experience

## Backend Architecture
- **Framework**: Django 5.2+ with Cookiecutter Django boilerplate
- **API**: Django REST Framework with spectacular documentation
- **Authentication**: Django Allauth with social login support and MFA
- **Background Tasks**: Celery with Redis broker for async processing
- **Workflows**: Temporal.io for complex item processing workflows including AI image analysis
- **File Storage**: Django's file handling with image processing capabilities

## Data Storage Solutions
- **Primary Database**: PostgreSQL with pgvector extension for embedding storage
- **Caching**: Redis for session storage and caching
- **File Storage**: Local filesystem for development, configurable for production
- **Vector Storage**: pgvector (1536 dimensions) for semantic search using OpenAI embeddings in books app

## Authentication and Authorization
- **User Management**: Custom User model extending AbstractUser
- **Social Auth**: Django Allauth supporting multiple providers
- **Multi-Factor Auth**: FIDO2/WebAuthn support via django-allauth
- **Permissions**: Django's built-in permission system with custom user profiles
- **API Authentication**: Token-based authentication for API endpoints

## External Dependencies
- **AI Services**: 
  - Anthropic Claude API for image analysis and content generation
  - OpenAI text-embedding-3-small for book embeddings (1536 dimensions)
- **Workflow Engine**: Temporal.io for reliable workflow execution
- **Email**: Configurable email backend (console for dev, SMTP for production)
- **Monitoring**: Sentry for error tracking and performance monitoring
- **Development Tools**: Docker with docker-compose for local development

## Core Applications Structure
- **Core**: Homepage and base functionality
- **Items**: Main sharing platform with categories, images, and AI processing
- **Books**: Specialized book sharing with semantic search via embeddings
- **Users**: User management and profiles
- **Favorites**: User favorites system
- **Messaging**: User-to-user communication about items
- **Bookings**: Item reservation system
- **Rooms**: Physical space management
- **Tags**: Item tagging system
- **Payments**: Internal payment handling

## Key Design Patterns
- **Model Inheritance**: Use of abstract base classes for common functionality
- **Signal-Driven**: Django signals for automated embedding generation and updates
- **Task Queues**: Celery tasks for background processing with retry logic
- **API-First**: RESTful API design for potential mobile app integration
- **Component-Based**: Reusable Django apps with clear separation of concerns