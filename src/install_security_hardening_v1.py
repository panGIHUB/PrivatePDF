from pathlib import Path
import re
import shutil
from datetime import datetime

# ============================================================
# PRIVATEPDF PRO
# PUBLIC DEPLOYMENT SECURITY HARDENING — V1
# ============================================================

HERE = Path.cwd()

if (HERE / "src/app/main.py").exists():
    ROOT = HERE
elif (HERE / "app/main.py").exists():
    ROOT = HERE.parent
else:
    raise SystemExit(
        "Run this from PrivatePDF_Pro_Advanced_V2 or its src folder."
    )

APP = (
    ROOT / "src/app/main.py"
    if (ROOT / "src/app/main.py").exists()
    else ROOT / "app/main.py"
)

if not APP.exists():
    raise SystemExit(f"Backend not found: {APP}")

main = APP.read_text(encoding="utf-8")

MARKER = "# === PP_SECURITY_HARDENING_V1 ==="

if MARKER in main:
    print("Security hardening V1 already installed.")
    raise SystemExit(0)

backup = APP.with_name(
    f"main.py.before_security_hardening_{datetime.now():%Y%m%d_%H%M%S}.bak"
)

shutil.copy2(APP, backup)

print()
print("=" * 70)
print("PRIVATEPDF PRO — SECURITY HARDENING V1")
print("=" * 70)
print("Backup:", backup.name)

# ------------------------------------------------------------
# Locate FastAPI application construction
# ------------------------------------------------------------

m = re.search(
    r"(?m)^app\s*=\s*FastAPI\([^\n]*\)\s*$",
    main
)

if m:
    app_start = m.start()
    app_end = m.end()
else:
    m = re.search(
        r"(?m)^app\s*=\s*FastAPI\(",
        main
    )

    if not m:
        raise SystemExit(
            "ERROR: Could not safely locate app = FastAPI(...). "
            "NO CHANGES MADE."
        )

    close = main.find(")", m.end())

    if close < 0:
        raise SystemExit(
            "ERROR: Could not safely locate FastAPI constructor. "
            "NO CHANGES MADE."
        )

    app_start = m.start()
    app_end = close + 1


# ------------------------------------------------------------
# Security configuration/imports
# ------------------------------------------------------------

security_pre = r'''
# === PP_SECURITY_HARDENING_V1 ===
# Public deployment security foundation.
# IMPORTANT:
# - No database
# - No persistent document storage
# - Existing PDF processing remains unchanged

import os as _pp_os
import time as _pp_time
import threading as _pp_threading

from collections import defaultdict as _pp_defaultdict
from collections import deque as _pp_deque

from starlette.responses import JSONResponse as _PPJSONResponse
from starlette.middleware.trustedhost import (
    TrustedHostMiddleware as _PPTrustedHostMiddleware
)
from fastapi.middleware.httpsredirect import (
    HTTPSRedirectMiddleware as _PPHTTPSRedirectMiddleware
)


_PP_PRODUCTION = (
    _pp_os.getenv("PP_PRODUCTION", "0")
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)


_PP_TRUSTED_HOSTS = [
    x.strip()
    for x in _pp_os.getenv(
        "PP_TRUSTED_HOSTS",
        "127.0.0.1,localhost"
    ).split(",")
    if x.strip()
]


_PP_CORS_ORIGINS = [
    x.strip()
    for x in _pp_os.getenv(
        "PP_CORS_ORIGINS",
        ""
    ).split(",")
    if x.strip()
]


_PP_RATE_WINDOW = max(
    10,
    int(
        _pp_os.getenv(
            "PP_RATE_WINDOW_SECONDS",
            "60"
        )
    )
)


_PP_RATE_LIMIT = max(
    10,
    int(
        _pp_os.getenv(
            "PP_RATE_LIMIT",
            "120"
        )
    )
)


_PP_HEAVY_RATE_LIMIT = max(
    3,
    int(
        _pp_os.getenv(
            "PP_HEAVY_RATE_LIMIT",
            "30"
        )
    )
)


_PP_MAX_REQUEST_MB = max(
    16,
    int(
        _pp_os.getenv(
            "PP_MAX_REQUEST_MB",
            "300"
        )
    )
)


_PP_MAX_REQUEST_BYTES = (
    _PP_MAX_REQUEST_MB * 1024 * 1024
)


_PP_MAX_CONCURRENT = max(
    1,
    int(
        _pp_os.getenv(
            "PP_MAX_CONCURRENT_JOBS",
            "4"
        )
    )
)


# Heavy endpoints receive stricter rate/concurrency protection.
_PP_HEAVY_PATHS = {
    "/api/merge",
    "/api/compress",
    "/api/resize",
    "/api/crop",
    "/api/numbers",
    "/api/watermark",
    "/api/protect",
    "/api/unlock",
    "/api/grayscale",
    "/api/pdf-to-jpg",
    "/api/images-to-pdf",
    "/api/office-to-pdf",
    "/api/pdf-to-office",
    "/api/image-resize",
    "/api/batch-process",
    "/api/annotate",
    "/api/annotation-page",
}


_PP_RATE_LOCK = _pp_threading.Lock()

_PP_RATE_BUCKETS = _pp_defaultdict(
    _pp_deque
)

_PP_HEAVY_SEMAPHORE = (
    _pp_threading.BoundedSemaphore(
        _PP_MAX_CONCURRENT
    )
)


def _pp_client_key(request):
    """
    Do NOT blindly trust X-Forwarded-For.

    If a reverse proxy is used in production,
    configure Uvicorn forwarded-header trust
    explicitly.
    """
    client = getattr(
        request,
        "client",
        None
    )

    return (
        getattr(
            client,
            "host",
            None
        )
        or "unknown"
    )


def _pp_rate_allowed(
    key,
    limit,
    now
):
    cutoff = (
        now -
        _PP_RATE_WINDOW
    )

    with _PP_RATE_LOCK:

        queue = _PP_RATE_BUCKETS[
            key
        ]

        while (
            queue
            and
            queue[0] <= cutoff
        ):
            queue.popleft()

        if len(queue) >= limit:
            return False

        queue.append(now)

        # Prevent attacker-created IP keys
        # from growing forever.
        if len(_PP_RATE_BUCKETS) > 20000:

            stale = [
                k
                for k, v
                in _PP_RATE_BUCKETS.items()
                if (
                    not v
                    or
                    v[-1] <= cutoff
                )
            ]

            for k in stale[:5000]:
                _PP_RATE_BUCKETS.pop(
                    k,
                    None
                )

        return True
'''


# ------------------------------------------------------------
# Security middleware
# ------------------------------------------------------------

security_post = r'''
@app.middleware("http")
async def _pp_security_middleware(
    request,
    call_next
):

    path = request.url.path
    method = request.method.upper()


    # --------------------------------------------------------
    # Hide developer/API documentation in production
    # --------------------------------------------------------

    if (
        _PP_PRODUCTION
        and
        path in {
            "/docs",
            "/docs/",
            "/redoc",
            "/redoc/",
            "/openapi.json"
        }
    ):

        return _PPJSONResponse(
            {
                "detail":
                    "Not found"
            },
            status_code=404
        )


    # --------------------------------------------------------
    # HTTP method allowlist
    # --------------------------------------------------------

    if method not in {
        "GET",
        "HEAD",
        "POST",
        "OPTIONS"
    }:

        return _PPJSONResponse(
            {
                "detail":
                    "Method not allowed"
            },
            status_code=405,
            headers={
                "Allow":
                    "GET, HEAD, POST, OPTIONS"
            }
        )


    # --------------------------------------------------------
    # Request body size guard
    # --------------------------------------------------------

    content_length = request.headers.get(
        "content-length"
    )

    if content_length:

        try:
            length = int(
                content_length
            )

        except (
            TypeError,
            ValueError
        ):

            return _PPJSONResponse(
                {
                    "detail":
                        "Invalid Content-Length header."
                },
                status_code=400
            )

        if (
            length >
            _PP_MAX_REQUEST_BYTES
        ):

            return _PPJSONResponse(
                {
                    "detail":
                        "Request body exceeds the configured limit."
                },
                status_code=413
            )


    # --------------------------------------------------------
    # API rate limiting
    # --------------------------------------------------------

    if path.startswith("/api/"):

        client_key = (
            _pp_client_key(
                request
            )
        )

        limit = (
            _PP_HEAVY_RATE_LIMIT
            if path in _PP_HEAVY_PATHS
            else _PP_RATE_LIMIT
        )

        now = _pp_time.monotonic()

        if not _pp_rate_allowed(
            client_key,
            limit,
            now
        ):

            return _PPJSONResponse(
                {
                    "detail":
                        "Too many requests. Please try again later."
                },
                status_code=429,
                headers={
                    "Retry-After":
                        str(
                            _PP_RATE_WINDOW
                        )
                }
            )


    # --------------------------------------------------------
    # Concurrent processing protection
    # --------------------------------------------------------

    heavy_request = (
        method == "POST"
        and
        path in _PP_HEAVY_PATHS
    )

    acquired = False

    if heavy_request:

        acquired = (
            _PP_HEAVY_SEMAPHORE.acquire(
                blocking=False
            )
        )

        if not acquired:

            return _PPJSONResponse(
                {
                    "detail":
                        "Server is busy processing other documents. Please retry shortly."
                },
                status_code=503,
                headers={
                    "Retry-After":
                        "10"
                }
            )


    try:

        response = await call_next(
            request
        )

    except Exception:

        # Never expose traceback,
        # parser internals or filesystem
        # details to public users.

        response = _PPJSONResponse(
            {
                "detail":
                    "Internal server error."
            },
            status_code=500
        )

    finally:

        if acquired:

            _PP_HEAVY_SEMAPHORE.release()


    # --------------------------------------------------------
    # Security response headers
    # --------------------------------------------------------

    response.headers.setdefault(
        "X-Content-Type-Options",
        "nosniff"
    )

    response.headers.setdefault(
        "X-Frame-Options",
        "DENY"
    )

    response.headers.setdefault(
        "Referrer-Policy",
        "no-referrer"
    )

    response.headers.setdefault(
        "Permissions-Policy",
        (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "usb=(), "
            "payment=()"
        )
    )


    # Current frontend contains inline JS/CSS,
    # so this CSP is intentionally compatible
    # with the existing UI. We can tighten it
    # further after moving inline code to files.

    response.headers.setdefault(
        "Content-Security-Policy",
        (
            "default-src 'self'; "
            "base-uri 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'"
        )
    )


    # PDF/document API responses should never
    # be cached by browsers/proxies.

    if path.startswith("/api/"):

        response.headers.setdefault(
            "Cache-Control",
            "no-store"
        )


    # HSTS only when explicitly running
    # production mode behind HTTPS.

    if _PP_PRODUCTION:

        response.headers.setdefault(
            "Strict-Transport-Security",
            (
                "max-age=31536000; "
                "includeSubDomains"
            )
        )


    return response


# ------------------------------------------------------------
# Host-header protection
# ------------------------------------------------------------

if _PP_TRUSTED_HOSTS:

    app.add_middleware(
        _PPTrustedHostMiddleware,
        allowed_hosts=
            _PP_TRUSTED_HOSTS
    )


# ------------------------------------------------------------
# HTTPS redirect
# ------------------------------------------------------------

if _PP_PRODUCTION:

    app.add_middleware(
        _PPHTTPSRedirectMiddleware
    )


# ------------------------------------------------------------
# CORS — opt-in only
# ------------------------------------------------------------

if _PP_CORS_ORIGINS:

    from fastapi.middleware.cors import (
        CORSMiddleware as _PPCORSMiddleware
    )

    app.add_middleware(
        _PPCORSMiddleware,
        allow_origins=
            _PP_CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=[
            "GET",
            "HEAD",
            "POST",
            "OPTIONS"
        ],
        allow_headers=[
            "Content-Type",
            "Authorization"
        ],
        max_age=600
    )


# === END PP_SECURITY_HARDENING_V1 ===
'''


# ------------------------------------------------------------
# Assemble safely
# ------------------------------------------------------------

new_main = (
    main[:app_start]
    +
    security_pre
    +
    "\n\n"
    +
    main[app_start:app_end]
    +
    "\n\n"
    +
    security_post
    +
    "\n\n"
    +
    main[app_end:]
)


# ------------------------------------------------------------
# Validate BEFORE committing
# ------------------------------------------------------------

try:
    compile(
        new_main,
        str(APP),
        "exec"
    )

except Exception as exc:

    print()
    print(
        "ERROR: Python syntax validation failed."
    )
    print(exc)
    print(
        "Restoring original file..."
    )

    shutil.copy2(
        backup,
        APP
    )

    raise SystemExit(
        "NO BROKEN FILE LEFT BEHIND."
    )


APP.write_text(
    new_main,
    encoding="utf-8"
)


# ------------------------------------------------------------
# Verification
# ------------------------------------------------------------

checks = {
    "Security marker":
        MARKER in new_main,

    "Rate limiter":
        "_pp_rate_allowed"
        in new_main,

    "Concurrency guard":
        "_PP_HEAVY_SEMAPHORE"
        in new_main,

    "Trusted Host":
        "_PPTrustedHostMiddleware"
        in new_main,

    "HTTPS redirect":
        "_PPHTTPSRedirectMiddleware"
        in new_main,

    "Security headers":
        "Content-Security-Policy"
        in new_main,

    "No-store API":
        '"Cache-Control"'
        in new_main,

    "Request size guard":
        "_PP_MAX_REQUEST_BYTES"
        in new_main,

    "Production docs protection":
        '"/openapi.json"'
        in new_main,

    "Opt-in CORS":
        "_PP_CORS_ORIGINS"
        in new_main,

    "#12 annotate preserved":
        '@app.post("/api/annotate")'
        in new_main,

    "Annotation page preserved":
        '@app.post("/api/annotation-page")'
        in new_main,
}


print()
print("=" * 70)
print(" SECURITY HARDENING V1 INSTALLATION COMPLETE")
print("=" * 70)

for name, ok in checks.items():
    print(
        ("OK   " if ok else "FAIL ")
        + name
    )

print()
print("Python syntax: PASS")
print("Backup:", backup.name)

print()
print("Existing architecture preserved:")
print("  No database")
print("  No persistent PDF storage")
print("  No #12 removal")
print("  No frontend replacement")

print("=" * 70)

if not all(checks.values()):

    print(
        "WARNING: verification failed."
    )
    print(
        "Restoring backup..."
    )

    shutil.copy2(
        backup,
        APP
    )

    raise SystemExit(
        "Security installation rolled back."
    )

print()
print("Production environment variables:")
print()
print("  PP_PRODUCTION=1")
print("  PP_TRUSTED_HOSTS=yourdomain.com,www.yourdomain.com")
print("  PP_CORS_ORIGINS=https://yourdomain.com")
print("  PP_MAX_REQUEST_MB=300")
print("  PP_RATE_LIMIT=120")
print("  PP_HEAVY_RATE_LIMIT=30")
print("  PP_MAX_CONCURRENT_JOBS=4")

print()
print("IMPORTANT:")
print("Keep PP_PRODUCTION=0 during local testing.")
print("Do not expose Uvicorn directly to the public Internet.")
print("Use HTTPS + reverse proxy in production.")
print("=" * 70)
