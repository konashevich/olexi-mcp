# main.py (Final Production Version)

from fastapi import FastAPI
from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from austlii_scraper import search_austlii, check_austlii_health, AustliiUnavailableError
# Defer AI imports so server can start even if AI key is missing
try:
    from mcp_handler import generate_search_plan, summarize_results  # type: ignore
    AI_AVAILABLE = True
except Exception as _ai_err:
    generate_search_plan = None  # type: ignore
    summarize_results = None  # type: ignore
    AI_AVAILABLE = False
from database_map import DATABASE_TOOLS_LIST
import urllib.parse # To help build the final search URL
import os
from typing import List, Dict, Optional
import contextlib
import asyncio
import time
from pydantic import BaseModel
import secrets
import logging
import json
from logging.handlers import RotatingFileHandler
from contextlib import AsyncExitStack
from collections import deque
from typing import Deque

# Optional MCP import for hybrid mode
olexi_mcp = None
try:
    from mcp_server import mcp as _mcp_instance
    olexi_mcp = _mcp_instance
except Exception:
    olexi_mcp = None

# --- App Initialization ---
app = FastAPI(
    title="Olexi AI Server",
    description="Backend server for the Olexi AI browser extension.",
    version="1.0.0",
)
# Load API keys for extension and manual clients
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
# Extension keys (auto-authorized)
EXT_KEYS: set = set()
keys_env = os.getenv("EXTENSION_API_KEYS")
keys_file = os.getenv("EXTENSION_API_KEYS_FILE", "extension_api_keys.txt")
if keys_env:
    EXT_KEYS = {k.strip() for k in keys_env.split(",") if k.strip()}
elif os.path.exists(keys_file):
    with open(keys_file) as f:
        EXT_KEYS = {line.strip() for line in f if line.strip()}
# Manual client keys (must be pre-authorized by admin)
CLIENT_KEYS: set = set()
client_file = os.getenv("CLIENT_API_KEYS_FILE", "client_api_keys.txt")
if os.path.exists(client_file):
    with open(client_file) as f:
        CLIENT_KEYS = {line.strip() for line in f if line.strip()}
# Combined valid keys
VALID_API_KEYS = EXT_KEYS | CLIENT_KEYS
# Map key to type for origin and client checks
KEY_TYPES: Dict[str, str] = {**{k: 'extension' for k in EXT_KEYS}, **{k: 'client' for k in CLIENT_KEYS}}
# Admin API key (optional) for managing client keys
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "")
ADMIN_KEY_NAME = "X-Admin-Key"
admin_key_header = APIKeyHeader(name=ADMIN_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key in VALID_API_KEYS:
        return api_key
    try:
        security_logger.info(json.dumps({
            "event": "invalid_api_key",
            "ts": _to_iso(time.time()),
            "has_header": bool(api_key),
            "header_len": len(api_key or ""),
            "valid_keys_count": len(VALID_API_KEYS),
        }))
    except Exception:
        pass
    raise HTTPException(status_code=403, detail="Invalid or missing API Key")
from fastapi import Request
from datetime import date

def verify_extension_origin(request: Request, api_key: str = Depends(get_api_key)):
    """Ensure extension keys are used only from allowed extension contexts (UA/ID/origin)."""
    if KEY_TYPES.get(api_key) == 'extension':
        ua_prefix = os.getenv("EXTENSION_UA_PREFIX", "").strip()
        ua = request.headers.get("User-Agent", "")
        if ua_prefix and not ua.startswith(ua_prefix):
            raise HTTPException(status_code=403, detail="User-Agent not allowed for this API key")
        ids_cfg = os.getenv("EXTENSION_IDS", "")
        allowed_ids = [i.strip() for i in ids_cfg.split(",") if i.strip()]
        ext_id = request.headers.get("X-Extension-Id", "").strip()
        if allowed_ids and ext_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="Extension ID not allowed for this API key")
        allowed = os.getenv("EXTENSION_ALLOWED_ORIGINS", "")
        origins = [o.strip() for o in allowed.split(",") if o.strip()]
        origin = request.headers.get("Origin") or request.headers.get("Referer") or ""
        if origins and origin not in origins:
            raise HTTPException(status_code=403, detail="Origin not allowed for this API key")
    return api_key

RATE_LIMIT_PER_DAY = int(os.getenv("RATE_LIMIT_PER_DAY", "50"))
MAX_DISTINCT_IPS = int(os.getenv("MAX_DISTINCT_IPS", "10"))
_api_key_usage: Dict[str, Dict] = {}

def rate_limit(request: Request, api_key: str = Depends(get_api_key)):
    """Limit to RATE_LIMIT_PER_DAY per key/day and track IPs to deter sharing."""
    today = date.today()
    record = _api_key_usage.get(api_key)
    if record is None or record.get('date') != today:
        _api_key_usage[api_key] = {'date': today, 'count': 0, 'ips': set()}
        record = _api_key_usage[api_key]
    client = request.client
    ip = client.host if client else 'unknown'
    record['ips'].add(ip)
    if len(record['ips']) > MAX_DISTINCT_IPS:
        try:
            security_logger.info(json.dumps({"event": "too_many_ips", "ts": _to_iso(time.time()), "key_type": KEY_TYPES.get(api_key), "ips": len(record['ips'])}))
        except Exception:
            pass
        raise HTTPException(status_code=429, detail="Too many distinct IPs using this API key")
    if record['count'] >= RATE_LIMIT_PER_DAY:
        try:
            security_logger.info(json.dumps({"event": "rate_limited", "ts": _to_iso(time.time()), "key_type": KEY_TYPES.get(api_key), "count": record['count']}))
        except Exception:
            pass
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded: {RATE_LIMIT_PER_DAY} per day")
    record['count'] += 1
    return api_key

# --- Admin endpoints to manage client API keys ---
def _persist_client_keys() -> None:
    try:
        with open(client_file, "w") as f:
            for k in sorted(CLIENT_KEYS):
                f.write(k + "\n")
    except Exception:
        pass

def _require_admin(admin_key: Optional[str]):
    if not ADMIN_KEY:
        raise HTTPException(status_code=503, detail="Admin API not configured")
    if not admin_key or admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admin key invalid")
    return True

@app.get("/admin/clients", tags=["Admin"])
async def list_clients(admin_key: Optional[str] = Security(admin_key_header)):
    _require_admin(admin_key)
    return {"count": len(CLIENT_KEYS), "keys": sorted(CLIENT_KEYS)}

class NewClientRequest(BaseModel):
    key: Optional[str] = None

@app.post("/admin/clients", tags=["Admin"])
async def add_client(req: NewClientRequest, admin_key: Optional[str] = Security(admin_key_header)):
    _require_admin(admin_key)
    new_key = (req.key or "").strip() or secrets.token_urlsafe(32)
    CLIENT_KEYS.add(new_key)
    VALID_API_KEYS.add(new_key)
    KEY_TYPES[new_key] = 'client'
    _persist_client_keys()
    return {"key": new_key}

@app.delete("/admin/clients/{key}", tags=["Admin"])
async def delete_client(key: str, admin_key: Optional[str] = Security(admin_key_header)):
    _require_admin(admin_key)
    removed = False
    if key in CLIENT_KEYS:
        CLIENT_KEYS.remove(key)
        removed = True
    VALID_API_KEYS.discard(key)
    KEY_TYPES.pop(key, None)
    _persist_client_keys()
    return {"removed": removed}

# --- Static Files Configuration ---
# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount MCP Streamable HTTP transport under /mcp for hybrid mode (if available)
if olexi_mcp:
    # Ensure the MCP app expects POST at '/' within the sub-app, so external '/mcp' works
    try:
        olexi_mcp.settings.streamable_http_path = "/"
    except Exception:
        pass
    mcp_subapp = olexi_mcp.streamable_http_app()
    # Save session manager to integrate its lifespan at the top-level app
    try:
        app.state.mcp_session_mgr = olexi_mcp.session_manager  # created lazily by streamable_http_app()
        app.state.mcp_exit_stack = AsyncExitStack()
    except Exception:
        app.state.mcp_session_mgr = None
    app.mount("/mcp", mcp_subapp)

# --- Proactive AustLII Monitoring ---
AUSTLII_STATUS: Dict[str, Optional[object]] = {
    "ok": None,         # type: ignore[assignment]
    "status": 0,
    "error": "",
    "checked_at": 0.0,
    "latency_ms": 0,
}

from typing import Union, cast

# Monitoring configuration (env-overridable)
AUSTLII_POLL_INTERVAL: int = int(os.getenv("AUSTLII_POLL_INTERVAL", "60"))
AUSTLII_MONITOR_LOG: str = os.getenv("AUSTLII_MONITOR_LOG", "austlii_monitoring.txt")
AUSTLII_LOG_MAX_BYTES: int = int(os.getenv("AUSTLII_LOG_MAX_BYTES", "2097152"))
AUSTLII_LOG_BACKUPS: int = int(os.getenv("AUSTLII_LOG_BACKUPS", "5"))

# Rolling samples for uptime windows (approx 7d worth)
_SEVEN_DAYS = 7 * 24 * 60 * 60
_approx_samples = max(1, int(_SEVEN_DAYS / max(1, AUSTLII_POLL_INTERVAL))) + 500
AUSTLII_SAMPLES: Deque[Dict[str, Union[float, bool, int]]] = deque(maxlen=_approx_samples)
AUSTLII_COUNTERS: Dict[str, Union[int, float]] = {
    "total_checks": 0,
    "ok_checks": 0,
    "fail_checks": 0,
    "first_checked_at": 0.0,
    "last_ok_at": 0.0,
    "last_fail_at": 0.0,
    "current_downtime_start": 0.0,
}

# Dedicated rotating logger for monitoring JSONL
monitor_logger = logging.getLogger("austlii.monitor")
if not monitor_logger.handlers:
    monitor_logger.setLevel(logging.INFO)
    try:
        handler = RotatingFileHandler(AUSTLII_MONITOR_LOG, maxBytes=AUSTLII_LOG_MAX_BYTES, backupCount=AUSTLII_LOG_BACKUPS)
        handler.setFormatter(logging.Formatter("%(message)s"))
        monitor_logger.addHandler(handler)
        monitor_logger.propagate = False
    except Exception:
        # Logging failures are non-fatal
        pass

# Dedicated security logger (JSONL)
SECURITY_LOG = os.getenv("SECURITY_LOG", "security_events.log")
security_logger = logging.getLogger("security")
if not security_logger.handlers:
    security_logger.setLevel(logging.INFO)
    try:
        _sec_handler = RotatingFileHandler(SECURITY_LOG, maxBytes=1048576, backupCount=3)
        _sec_handler.setFormatter(logging.Formatter("%(message)s"))
        security_logger.addHandler(_sec_handler)
        security_logger.propagate = False
    except Exception:
        pass

def _as_int(val: Optional[Union[int, float, str]], default: int = 0) -> int:
    try:
        return int(val) if val is not None else default
    except Exception:
        return default

def _as_float(val: Optional[Union[int, float, str]], default: float = 0.0) -> float:
    try:
        return float(val) if val is not None else default
    except Exception:
        return default

def _to_iso(ts: float) -> str:
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
    except Exception:
        return ""

def _record_probe(now: float, ok: bool, code: int, err: str, latency_ms: int, source: str, interval_s: int) -> None:
    # Update cache
    AUSTLII_STATUS.update({
        "ok": ok,
        "status": code,
        "error": err,
        "checked_at": now,
        "latency_ms": latency_ms,
    })
    # Samples and counters
    AUSTLII_SAMPLES.append({"t": now, "ok": ok, "latency_ms": latency_ms})
    if AUSTLII_COUNTERS["total_checks"] == 0:
        AUSTLII_COUNTERS["first_checked_at"] = now
    AUSTLII_COUNTERS["total_checks"] = int(AUSTLII_COUNTERS["total_checks"]) + 1
    if ok:
        AUSTLII_COUNTERS["ok_checks"] = int(AUSTLII_COUNTERS["ok_checks"]) + 1
        AUSTLII_COUNTERS["last_ok_at"] = now
        if float(AUSTLII_COUNTERS["current_downtime_start"]) > 0:
            AUSTLII_COUNTERS["current_downtime_start"] = 0.0
    else:
        AUSTLII_COUNTERS["fail_checks"] = int(AUSTLII_COUNTERS["fail_checks"]) + 1
        AUSTLII_COUNTERS["last_fail_at"] = now
        if float(AUSTLII_COUNTERS["current_downtime_start"]) == 0.0:
            AUSTLII_COUNTERS["current_downtime_start"] = now
    # Log JSON line
    line = {
        "ts": _to_iso(now),
        "ok": ok,
        "status": code,
        "error": err,
        "latency_ms": latency_ms,
        "source": source,
        "interval_s": interval_s,
    }
    try:
        monitor_logger.info(json.dumps(line, ensure_ascii=False))
    except Exception:
        pass

def _compute_uptime(window_secs: int) -> Optional[float]:
    if window_secs <= 0:
        return None
    now = time.time()
    start = now - window_secs
    total = 0
    ok_count = 0
    for s in list(AUSTLII_SAMPLES):
        t = float(s.get("t", 0.0))
        if t >= start:
            total += 1
            if bool(s.get("ok", False)):
                ok_count += 1
    if total == 0:
        return None
    return ok_count / total

def _current_downtime() -> Optional[Dict[str, float]]:
    cds = float(AUSTLII_COUNTERS.get("current_downtime_start", 0.0))
    if cds > 0:
        return {"start_at": cds, "seconds": max(0.0, time.time() - cds)}
    return None

def _snapshot(cached: bool) -> Dict[str, object]:
    uptimes: Dict[str, Optional[float]] = {
        "last_5m": _compute_uptime(5 * 60),
        "last_1h": _compute_uptime(60 * 60),
        "last_24h": _compute_uptime(24 * 60 * 60),
        "last_7d": _compute_uptime(7 * 24 * 60 * 60),
        "since_start": None,
    }
    tot = int(AUSTLII_COUNTERS.get("total_checks", 0))
    okc = int(AUSTLII_COUNTERS.get("ok_checks", 0))
    uptimes["since_start"] = (okc / tot) if tot > 0 else None
    return {
        "ok": bool(AUSTLII_STATUS.get("ok")),
        "status": _as_int(cast(Union[int, float, str, None], AUSTLII_STATUS.get("status"))),
        "error": str(AUSTLII_STATUS.get("error") or ""),
        "checked_at": _as_float(cast(Union[int, float, str, None], AUSTLII_STATUS.get("checked_at"))),
        "latency_ms": int(cast(Union[int, float, str, None], AUSTLII_STATUS.get("latency_ms")) or 0),
        "cached": cached,
        "uptime": uptimes,
        "counters": {
            "total_checks": tot,
            "ok_checks": okc,
            "fail_checks": int(AUSTLII_COUNTERS.get("fail_checks", 0)),
            "first_checked_at": float(AUSTLII_COUNTERS.get("first_checked_at", 0.0)),
            "last_ok_at": float(AUSTLII_COUNTERS.get("last_ok_at", 0.0)),
            "last_fail_at": float(AUSTLII_COUNTERS.get("last_fail_at", 0.0)),
        },
        "current_downtime": _current_downtime(),
    }

def do_probe(source: str = "probe", timeout: int = 3, interval_s: int = 0) -> Dict[str, object]:
    start = time.perf_counter()
    ok, code, err = check_austlii_health(timeout=timeout)
    latency_ms = int((time.perf_counter() - start) * 1000)
    now = time.time()
    _record_probe(now, ok, code, err, latency_ms, source, interval_s)
    return _snapshot(cached=False)

async def _poll_austlii_health(interval: int = 60) -> None:
    while True:
        try:
            do_probe(source="poll", timeout=3, interval_s=interval)
        except Exception:
            pass
        await asyncio.sleep(interval)

@app.on_event("startup")
async def _start_monitors() -> None:
    # Start background health poller
    app.state.austlii_task = asyncio.create_task(_poll_austlii_health(AUSTLII_POLL_INTERVAL))
    # Start MCP session manager if available
    mgr = getattr(app.state, "mcp_session_mgr", None)
    stack = getattr(app.state, "mcp_exit_stack", None)
    if mgr and stack:
        await stack.enter_async_context(mgr.run())

@app.on_event("shutdown")
async def _stop_monitors() -> None:
    # Stop MCP session manager if running
    stack = getattr(app.state, "mcp_exit_stack", None)
    try:
        if stack:
            await stack.aclose()
    except Exception:
        pass

# --- CORS Configuration ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Favicon Endpoints ---
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve the main favicon.ico file."""
    favicon_path = "static/favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return {"message": "Favicon not found"}

@app.get("/favicon-16x16.png", include_in_schema=False)
async def favicon_16():
    """Serve the 16x16 PNG favicon."""
    favicon_path = "static/favicon-16x16.png"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return {"message": "Favicon not found"}

@app.get("/favicon-32x32.png", include_in_schema=False)
async def favicon_32():
    """Serve the 32x32 PNG favicon."""
    favicon_path = "static/favicon-32x32.png"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return {"message": "Favicon not found"}

@app.get("/apple-touch-icon.png", include_in_schema=False)
async def apple_touch_icon():
    """Serve the Apple touch icon."""
    icon_path = "static/apple-touch-icon.png"
    if os.path.exists(icon_path):
        return FileResponse(icon_path)
    return {"message": "Apple touch icon not found"}

@app.get("/site.webmanifest", include_in_schema=False)
async def web_manifest():
    """Serve the web app manifest."""
    manifest_path = "static/site.webmanifest"
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path, media_type="application/manifest+json")
    return {"message": "Web manifest not found"}

# --- API Endpoints ---
@app.get("/", tags=["Health Check"], include_in_schema=False)
async def read_root():
    """Serve the main landing page with Olexi branding."""
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"status": "Olexi AI server is running", "port": 3000, "databases": len(DATABASE_TOOLS_LIST), "mcp": bool(olexi_mcp)}

@app.get("/status", tags=["Health Check"])
async def get_status():
    """JSON status endpoint for programmatic access."""
    # Prefer cached status; if never checked, do a one-off probe
    if not AUSTLII_STATUS.get("checked_at"):
        ok, code, err = check_austlii_health()
        status_obj = {"ok": ok, "status": code, "error": err, "cached": False}
    else:
        status_obj = {
            "ok": bool(AUSTLII_STATUS.get("ok")),
            "status": _as_int(cast(Union[int, float, str, None], AUSTLII_STATUS.get("status"))),
            "error": str(AUSTLII_STATUS.get("error") or ""),
            "checked_at": _as_float(cast(Union[int, float, str, None], AUSTLII_STATUS.get("checked_at"))),
            "cached": True,
        }
    return {
        "status": "Olexi AI server is running",
        "port": 3000,
        "databases": len(DATABASE_TOOLS_LIST),
    "mcp": bool(olexi_mcp),
    "ai": { "available": bool(AI_AVAILABLE) },
        "austlii": status_obj,
    }

## Legacy chat endpoint removed (non-MCP). Use /api/tools/* instead.

# ==============================
# MCP Tools Bridge (REST Facade)
# ==============================

class PlanRequest(BaseModel):
    prompt: str

class PlanResponse(BaseModel):
    query: str
    databases: List[str]

class SearchRequest(BaseModel):
    query: str
    databases: List[str]

class SummaryRequest(BaseModel):
    prompt: str
    results: List[Dict]

class SummaryResponse(BaseModel):
    markdown: str

class BuildUrlRequest(BaseModel):
    query: str
    databases: List[str]

class BuildUrlResponse(BaseModel):
    url: str

@app.get("/api/tools/databases", tags=["MCP Tools Bridge"], dependencies=[Depends(verify_extension_origin), Depends(rate_limit)])
async def tools_databases(api_key: str = Depends(get_api_key)) -> List[Dict]:
    """Return all available AustLII databases (mirrors list_databases tool)."""
    return DATABASE_TOOLS_LIST

@app.post("/api/tools/plan_search", response_model=PlanResponse, tags=["MCP Tools Bridge"], dependencies=[Depends(verify_extension_origin), Depends(rate_limit)])
async def tools_plan_search(req: PlanRequest, api_key: str = Depends(get_api_key)) -> PlanResponse:
    # Upfront AustLII gate: planning is pointless if the source is down
    cached = AUSTLII_STATUS
    stale = (time.time() - _as_float(cast(Union[int, float, str, None], cached.get("checked_at")))) > 120
    if cached.get("ok") is False or stale:
        ok, code, err = check_austlii_health(timeout=3)
        if not ok:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=f"AustLII is not accessible (status {code}). {err}")
    if not AI_AVAILABLE or generate_search_plan is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="AI is not accessible. Configure API keys and try again.")
    sp = generate_search_plan(req.prompt, DATABASE_TOOLS_LIST)
    return PlanResponse(query=sp.get("query", req.prompt), databases=sp.get("databases", []))

@app.post("/api/tools/search_austlii", tags=["MCP Tools Bridge"], dependencies=[Depends(verify_extension_origin), Depends(rate_limit)])
async def tools_search_austlii(req: SearchRequest, api_key: str = Depends(get_api_key)) -> List[Dict]:
    # Upfront AustLII gate
    cached = AUSTLII_STATUS
    stale = (time.time() - _as_float(cast(Union[int, float, str, None], cached.get("checked_at")))) > 120
    if cached.get("ok") is False or stale:
        ok, code, err = check_austlii_health(timeout=3)
        if not ok:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=f"AustLII is not accessible (status {code}). {err}")
    try:
        results = search_austlii(req.query, req.databases)
    except AustliiUnavailableError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"AustLII is not accessible: {e}")
    # Convert to primitive dicts
    out: List[Dict] = []
    for item in results:
        out.append({"title": item.title, "url": str(item.url), "metadata": item.metadata})
    return out

# Dedicated health and uptime endpoints for AustLII
@app.get("/austlii/health", tags=["Health Check"])
async def austlii_health(live: bool = False):
    """Return AustLII health; use cached value unless live=true to probe now. Includes uptime and counters."""
    if live or not AUSTLII_STATUS.get("checked_at"):
        return do_probe(source="probe", timeout=3)
    return _snapshot(cached=True)

@app.post("/austlii/health/probe", tags=["Health Check"])
async def austlii_probe(timeout: int = 3):
    """Trigger an immediate live probe; updates cache/log/metrics and returns fresh snapshot."""
    return do_probe(source="probe", timeout=timeout)

@app.get("/austlii/uptime", tags=["Health Check"])
async def austlii_uptime():
    """Return uptime summary and counters only (no status/error)."""
    snap = _snapshot(cached=True)
    return {
        "uptime": snap.get("uptime"),
        "counters": snap.get("counters"),
        "current_downtime": snap.get("current_downtime"),
    }

@app.post("/api/tools/summarize_results", response_model=SummaryResponse, tags=["MCP Tools Bridge"], dependencies=[Depends(verify_extension_origin), Depends(rate_limit)])
async def tools_summarize_results(req: SummaryRequest, api_key: str = Depends(get_api_key)) -> SummaryResponse:
    if not AI_AVAILABLE or summarize_results is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="AI is not accessible. Configure API keys and try again.")
    md = summarize_results(req.prompt, req.results)
    return SummaryResponse(markdown=md)

@app.post("/api/tools/build_search_url", response_model=BuildUrlResponse, tags=["MCP Tools Bridge"], dependencies=[Depends(verify_extension_origin), Depends(rate_limit)])
async def tools_build_search_url(req: BuildUrlRequest, api_key: str = Depends(get_api_key)) -> BuildUrlResponse:
    params = [("query", req.query), ("method", "boolean"), ("meta", "/au")]
    for db_code in req.databases:
        params.append(("mask_path", db_code))
    url = f"https://www.austlii.edu.au/cgi-bin/sinosrch.cgi?{urllib.parse.urlencode(params)}"
    return BuildUrlResponse(url=url)