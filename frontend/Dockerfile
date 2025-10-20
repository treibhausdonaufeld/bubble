# Build stage
FROM oven/bun:1-alpine AS build

USER bun

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
FROM nginxinc/nginx-unprivileged:alpine-slim

# Copy built app to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.default.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 8888
