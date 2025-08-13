# Deploy to Google Cloud Run

A minimal guide to build, push, and deploy this FastAPI server to Cloud Run using Artifact Registry and Secret Manager.

## Prerequisites
- GCP project with billing enabled
- gcloud CLI authenticated ("gcloud init")
- Artifact Registry API, Cloud Run API, and Secret Manager API enabled
- Domain (optional) for custom URL mapping

## Build and push

1. Create Artifact Registry repo (once):
   - Region: us-central1 (or your preference)
   - Format: Docker

2. Build and push image:
   - gcloud builds submit --tag us-central1-docker.pkg.dev/PROJECT_ID/REPO/olexi-mcp:latest

3. (Optional) Pin a version tag for rollbacks.

## Deploy to Cloud Run

- gcloud run deploy olexi-mcp \
  --image=us-central1-docker.pkg.dev/PROJECT_ID/REPO/olexi-mcp:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=3 \
  --cpu=1 \
  --memory=512Mi \
  --timeout=600 \
  --port=3000

## Environment variables

Set these in Cloud Run console or via --set-env-vars:

- EXTENSION_API_KEYS: comma-separated extension keys
- CLIENT_API_KEYS_FILE: if mounting a file (else use admin API)
- ADMIN_API_KEY: for /admin endpoints
- EXTENSION_ALLOWED_ORIGINS, EXTENSION_IDS, EXTENSION_UA_PREFIX: tighten extension access
- RATE_LIMIT_PER_DAY, MAX_DISTINCT_IPS: request throttles
- AUSTLII_POLL_INTERVAL, AUSTLII_HEALTH_TIMEOUT: health tuning
- AUSTLII_TIMEOUT, AUSTLII_RETRIES, AUSTLII_BACKOFF: scraper resilience
- PREVIEW_STOPLIST: optional preview noise filters

MCP_URL defaults to http://127.0.0.1:$PORT/mcp, suitable because the MCP server is mounted in-process at /mcp.

## Secrets
- Prefer using Secret Manager for keys. Bind them as env vars or mounted files.

## Custom domain
- Map the service to olexi-mcp.konashevych.com via Cloud Run custom domains.
- Create the DNS A/AAAA records that Google provides.

## CI/CD hint
- Add a GitHub Actions workflow to build and deploy on pushes to main. Store GCP creds as GitHub secrets.

## Troubleshooting
- If health probe warnings appear, requests still proceed; check /austlii/health and logs. Adjust AUSTLII_* envs.
- If SSE stalls, ensure your proxy/CDN supports streaming responses.
- For 403s, verify API keys and extension origin/ID/UA headers.
