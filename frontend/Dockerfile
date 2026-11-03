# ---- Build stage -------------------------------------------------------------
FROM node:22-alpine AS build
WORKDIR /app

# Install from the lockfile only (reproducible; includes dev deps needed by Vite).
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite inlines VITE_* values at build time. Railway passes service variables
# to a Dockerfile build as build args, but only those declared here.
ARG VITE_API_URL
ARG VITE_FIREBASE_API_KEY
ARG VITE_FIREBASE_AUTH_DOMAIN
ARG VITE_FIREBASE_PROJECT_ID
ARG VITE_FIREBASE_STORAGE_BUCKET
ARG VITE_FIREBASE_MESSAGING_SENDER_ID
ARG VITE_FIREBASE_APP_ID

RUN npm run build

# ---- Runtime stage -----------------------------------------------------------
FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY Caddyfile /etc/caddy/Caddyfile

# Railway injects PORT; the Caddyfile listens on it.
EXPOSE 8080
