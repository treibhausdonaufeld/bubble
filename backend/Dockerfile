# define an alias for the specific python version used in this file.
FROM docker.io/python:3.13-slim AS python

# Python 'run' stage
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}
ENV UV_PROJECT_ENVIRONMENT=/home/django/.venv

WORKDIR ${APP_HOME}

RUN addgroup --system django \
  && useradd --uid 1000 --gid django --shell /bin/bash --create-home django

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  # psycopg dependencies
  libpq-dev \
  # Translations dependencies
  gettext \
  # entrypoint
  wait-for-it \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

COPY --chown=django:django ./docker/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY --chown=django:django ./docker/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY --chown=django:django ./docker/start_worker /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY --chown=django:django ./docker/start_beat /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY --chown=django:django ./docker/start_flower /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# make django owner of the WORKDIR directory as well.
RUN chown django:django ${APP_HOME}

USER django

# Requirements are installed here to ensure they will be cached.
COPY uv.lock pyproject.toml ./

RUN --mount=type=cache,target=/home/django/.cache/uv,uid=1000 \
  uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="$UV_PROJECT_ENVIRONMENT/bin:$PATH"

COPY --chown=django:django . ${APP_HOME}

RUN DATABASE_URL="" \
  DJANGO_SETTINGS_MODULE="config.settings.test" \
  python manage.py compilemessages -v 0 -i .venv

EXPOSE 5000

ENTRYPOINT ["/entrypoint"]
