#!/usr/bin/env bash
# Build and start MCP + extension on Oracle VM (or local smoke test).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f .env ]]; then
  echo "Creating .env from .env.example — set HOST_GOOGLE_API_KEY before production use."
  cp .env.example .env
  if command -v gcloud >/dev/null 2>&1; then
    if KEY="$(gcloud secrets versions access latest \
      --secret=olexi-host-google-api-key \
      --project=olexi-extension 2>/dev/null || true)"; then
      if [[ -n "$KEY" ]]; then
        printf 'HOST_GOOGLE_API_KEY=%s\n' "$KEY" > .env
        echo "Loaded HOST_GOOGLE_API_KEY from GCP Secret Manager."
      fi
    fi
  fi
fi

if ! grep -q '^HOST_GOOGLE_API_KEY=.\+' .env 2>/dev/null; then
  echo "WARNING: HOST_GOOGLE_API_KEY is empty — extension AI features will not work."
fi

export GIT_COMMIT_SHA="${GIT_COMMIT_SHA:-$(git -C ../.. rev-parse --short HEAD 2>/dev/null || echo unknown)}"

echo "Building and starting stack..."
docker compose up -d --build

echo "Waiting for health checks..."
sleep 15

echo "--- MCP (internal) ---"
docker compose exec -T mcp curl -fsS "http://127.0.0.1:3000/" >/dev/null && echo "mcp: ok" || echo "mcp: check logs"

echo "--- Extension (internal) ---"
docker compose exec -T extension curl -fsS "http://127.0.0.1:8080/health" && echo || echo "extension: check logs"

echo "Done. After DNS points here, verify:"
echo "  curl -fsS https://mcp-api.olexi.legal/"
echo "  curl -fsS https://ext.olexi.legal/health"
