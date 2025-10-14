# Build stage
FROM oven/bun:1-alpine AS build

# Create an unprivileged runtime user and ensure nginx serves files from correct owner
RUN addgroup --system appuser && adduser --system --ingroup appuser --no-create-home --shell /usr/sbin/nologin appuser \
	&& chown -R appuser:appuser /usr/share/nginx/html

USER appuser

WORKDIR /app

# Copy package files
COPY bun.lockb package*.json ./

# Install dependencies
RUN bun install

# Copy source code
COPY . .

# Build the app
RUN bun run build

# Production stage
# FROM nginx:alpine
FROM nginxinc/nginx-unprivileged:alpine-slim

# Copy built app to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.default.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 8888
