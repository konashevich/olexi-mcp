#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
OUT_DIR="$ROOT_DIR/dist/ip-submission"
PKG_ZIP="$ROOT_DIR/dist/olexi-mcp-ip-submission.zip"

rm -rf "$OUT_DIR" "$PKG_ZIP"
mkdir -p "$OUT_DIR/icons"

# Copy artifacts
cp "$ROOT_DIR/docs/copilot/connector/mcp-manifest.json" "$OUT_DIR/"
cp "$ROOT_DIR/docs/copilot/connector/README.md" "$OUT_DIR/"
cp "$ROOT_DIR/docs/copilot/connector/TESTING.md" "$OUT_DIR/"
cp "$ROOT_DIR/docs/copilot/connector/SUPPORT.md" "$OUT_DIR/"
cp "$ROOT_DIR/docs/copilot/connector/SECURITY.md" "$OUT_DIR/"
cp "$ROOT_DIR/docs/copilot/connector/CHANGELOG.md" "$OUT_DIR/"
cp "$ROOT_DIR/docs/copilot/connector/RIGHTS.md" "$OUT_DIR/"
cp "$ROOT_DIR/docs/copilot/connector/SUBMISSION_PACKAGE.md" "$OUT_DIR/"
cp "$ROOT_DIR/docs/copilot/connector/SUBMISSION_PR_BODY.md" "$OUT_DIR/"

# Copy icons
cp "$ROOT_DIR/icons/icon32.png" "$OUT_DIR/icons/"
cp "$ROOT_DIR/icons/icon128.png" "$OUT_DIR/icons/"

# Include references to AustLII materials (PDFs)
mkdir -p "$OUT_DIR/austlii"
cp "$ROOT_DIR/docs/austlii/"*.pdf "$OUT_DIR/austlii/" || true

# Zip
mkdir -p "$ROOT_DIR/dist"
( cd "$OUT_DIR/.." && zip -r "$(basename "$PKG_ZIP")" "$(basename "$OUT_DIR")" >/dev/null )

echo "Created package: $PKG_ZIP"
