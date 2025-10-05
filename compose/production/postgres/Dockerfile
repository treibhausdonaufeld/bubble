FROM docker.io/pgvector/pgvector:pg17

COPY ./compose/production/postgres/maintenance /usr/local/bin/maintenance

COPY ./compose/production/postgres/init.sql /docker-entrypoint-initdb.d/init.sql

RUN chmod +x /usr/local/bin/maintenance/*
RUN mv /usr/local/bin/maintenance/* /usr/local/bin \
    && rmdir /usr/local/bin/maintenance
