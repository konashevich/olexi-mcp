# Deploy to Google Cloud Run (MCP-only)

A minimal guide to build, push, and deploy the MCP-only ASGI app to Cloud Run using Artifact Registry.

## Prerequisites
- GCP project with billing enabled
- gcloud CLI authenticated ("gcloud init")
- Artifact Registry API, Cloud Run API, and Secret Manager API enabled
- Domain (optional) for custom URL mapping

## Build and push

1. Create Artifact Registry repo (once):
   - Region: australia-southeast1 (or your preference)
   - Format: Docker

2. Build and push image:
   - gcloud builds submit --tag australia-southeast1-docker.pkg.dev/PROJECT_ID/REPO/olexi-mcp:latest

3. (Optional) Pin a version tag for rollbacks.

## Deploy to Cloud Run

- gcloud run deploy olexi-mcp-root-au \
   --image=australia-southeast1-docker.pkg.dev/PROJECT_ID/REPO/olexi-mcp:latest \
   --platform=managed \
   --region=australia-southeast1 \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=3 \
  --cpu=1 \
  --memory=512Mi \
  --timeout=600 \
   --port=3000

## Environment variables

Set these in Cloud Run console or via --set-env-vars:

- AUSTLII_POLL_INTERVAL, AUSTLII_HEALTH_TIMEOUT: health tuning
- AUSTLII_TIMEOUT, AUSTLII_RETRIES, AUSTLII_BACKOFF: scraper resilience (AUSTLII_TIMEOUT applies to both connect/read if split values not provided)
- AUSTLII_CONNECT_TIMEOUT, AUSTLII_READ_TIMEOUT: optional split timeouts (seconds) for connect and read phases
- AUSTLII_JITTER: optional jitter proportion for retry backoff (e.g., 0.3 => ±30%)

MCP transport is served at the root path `/` in production.

## CI/CD hint
- Add a GitHub Actions workflow to build and deploy on pushes to main. Store GCP creds as GitHub secrets.

## Troubleshooting
- If timeouts occur, inspect logs and adjust AUSTLII_* envs.
