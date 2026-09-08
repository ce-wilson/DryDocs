# =============================================================================
# deploy/console.Dockerfile — the console AND its reverse proxy, one image
# =============================================================================
# THIS IS THE FIFTH SERVICE, and the one ADR 0020 made necessary. The browser
# calls /api and /agent on the PAGE'S OWN ORIGIN; something has to serve the page
# and forward those two prefixes. In dev that something is Vite (server.proxy in
# web/vite.config.ts). Here it is nginx, serving the PRODUCTION BUILD — dist/,
# not the dev server — because this stack is where the production delivery shape
# is first exercised, and a Vite dev container would exercise the dev one twice.
#
# The per-process path in the runbook keeps `npm run dev` for HMR; the two are
# alternatives on purpose, not a stack missing a feature.
#
# Build context is the REPO ROOT: the build stage needs web/, and the render step
# needs deploy/.

# ---- stage 1: build the bundle and render the proxy config ------------------
FROM node:22-alpine AS build
WORKDIR /app/web

# package.json + lock alone first, so `npm ci` is cached across source edits.
COPY web/package.json web/package-lock.json ./
# `npm ci` and not `npm install`: ci installs the LOCKFILE exactly and fails if
# package.json disagrees with it, which is the property an image build wants.
RUN npm ci

COPY web/ ./

# `tsc -b && vite build` — the same command CI runs, so a type error is a failed
# image build rather than a bundle that ships anyway.
RUN npm run build

# THE COORDINATE GUARD, RUN INSIDE THE BUILD (WEB10 / ADR 0020). It fails if any
# host:port reached the bundle, which is what makes "one build promotes through
# every environment" a checked claim instead of an intention. Note this passes
# here even on a machine where it fails on the host: .dockerignore excludes
# web/.env.local, whose VITE_* values Vite would otherwise inline.
RUN npm run dist:check

# The proxy config is RENDERED from web/delivery.json — the same file the bundle
# and vite.config.ts read — so the path map exists once. See the script header.
COPY deploy/render_proxy_config.mjs /app/deploy/
# The upstreams default to the Compose service names inside the script. These
# ARGs are what make the script's "overridable" claim true from a plain
# `docker build --build-arg`, for an image fronting upstreams that are not this
# stack's; unset, they expand to the empty string, which the script treats as
# unset for exactly that reason.
ARG DRYDOCS_API_UPSTREAM
ARG DRYDOCS_AGENT_UPSTREAM
RUN node /app/deploy/render_proxy_config.mjs ./delivery.json /app/default.conf

# ---- stage 2: serve ---------------------------------------------------------
# nginx:alpine ships busybox wget, which the compose health check uses; the plain
# nginx image has neither wget nor curl and the check would fail on a healthy
# server — an instrument reporting on itself.
FROM nginx:alpine
COPY --from=build /app/web/dist /usr/share/nginx/html
COPY --from=build /app/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
