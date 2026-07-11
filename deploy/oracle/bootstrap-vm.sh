#!/usr/bin/env bash
# One-shot bootstrap for a fresh Ubuntu 22.04/24.04 ARM VM (Oracle Cloud).
# Run as root or with sudo on the VM.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends ca-certificates curl git

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi

REPO_URL="${REPO_URL:-https://github.com/konashevich/olexi-mcp.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/olexi-mcp}"

if [[ ! -d "$INSTALL_DIR/.git" ]]; then
  git clone --recurse-submodules "$REPO_URL" "$INSTALL_DIR"
else
  git -C "$INSTALL_DIR" pull --ff-only
  git -C "$INSTALL_DIR" submodule update --init --recursive
fi

cd "$INSTALL_DIR/deploy/oracle"

if [[ -n "${HOST_GOOGLE_API_KEY:-}" ]]; then
  printf 'HOST_GOOGLE_API_KEY=%s\n' "$HOST_GOOGLE_API_KEY" > .env
elif [[ ! -f .env ]]; then
  cp .env.example .env
  echo "WARNING: HOST_GOOGLE_API_KEY not set — set it in .env before using extension AI."
fi

export GIT_COMMIT_SHA="$(git -C "$INSTALL_DIR" rev-parse --short HEAD)"
docker compose up -d --build

echo "Bootstrap complete. Open ports 80/443 in OCI security list, then point DNS:"
echo "  mcp-api.olexi.legal -> this VM public IP"
echo "  ext.olexi.legal     -> this VM public IP"
