# main.py (Final Production Version)

from fastapi import FastAPI
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
import asyncio
import time
from pydantic import BaseModel
import logging
import json
from logging.handlers import RotatingFileHandler
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

# --- Static Files Configuration ---
# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount MCP Streamable HTTP transport under /mcp for hybrid mode (if available)
if olexi_mcp:
    app.mount("/mcp", olexi_mcp.streamable_http_app())

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

@app.get("/api/tools/databases", tags=["MCP Tools Bridge"])
async def tools_databases() -> List[Dict]:
    """Return all available AustLII databases (mirrors list_databases tool)."""
    return DATABASE_TOOLS_LIST

@app.post("/api/tools/plan_search", response_model=PlanResponse, tags=["MCP Tools Bridge"])
async def tools_plan_search(req: PlanRequest) -> PlanResponse:
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

@app.post("/api/tools/search_austlii", tags=["MCP Tools Bridge"])
async def tools_search_austlii(req: SearchRequest) -> List[Dict]:
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

@app.post("/api/tools/summarize_results", response_model=SummaryResponse, tags=["MCP Tools Bridge"])
async def tools_summarize_results(req: SummaryRequest) -> SummaryResponse:
    if not AI_AVAILABLE or summarize_results is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="AI is not accessible. Configure API keys and try again.")
    md = summarize_results(req.prompt, req.results)
    return SummaryResponse(markdown=md)

@app.post("/api/tools/build_search_url", response_model=BuildUrlResponse, tags=["MCP Tools Bridge"])
async def tools_build_search_url(req: BuildUrlRequest) -> BuildUrlResponse:
    params = [("query", req.query), ("method", "boolean"), ("meta", "/au")]
    for db_code in req.databases:
        params.append(("mask_path", db_code))
    url = f"https://www.austlii.edu.au/cgi-bin/sinosrch.cgi?{urllib.parse.urlencode(params)}"
    return BuildUrlResponse(url=url)