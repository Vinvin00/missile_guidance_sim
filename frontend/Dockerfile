# Guidance sim viewer: static Vite/React build served by nginx.
#
# Vite inlines VITE_* env vars at build time, so the two backend URLs are
# build args here rather than runtime env. They must be reachable from the
# *browser* (the host machine), not from inside the compose network — so
# they point at the published host ports, not container service names.

FROM node:22-slim AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_AERO_RAG_API_URL=http://localhost:8001
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_AERO_RAG_API_URL=$VITE_AERO_RAG_API_URL

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1:80/ || exit 1
