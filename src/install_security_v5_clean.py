from pathlib import Path
import shutil
import subprocess
import sys
import re

APP = Path("app/main.py")
BACKUP = Path("app/main.py.before_security_v5_clean")

MARKER = "PP_SECURITY_HARDENING_V5_CLEAN"

print("=" * 62)
print("PRIVATEPDF PRO — SECURITY V5 CLEAN INSTALLER")
print("=" * 62)

if not APP.exists():
    raise RuntimeError("app/main.py not found")

src_original = APP.read_text(encoding="utf-8")

# ------------------------------------------------------------
# SAFETY CHECKS — V3.1 / V4 / V4.1 MUST EXIST
# ------------------------------------------------------------
required_base = [
    "PP_SECURITY_HARDENING_V3_1",
    "PP_SECURITY_HARDENING_V4",
    "PP_SECURITY_HARDENING_V4_1",
]

for marker in required_base:
    if marker not in src_original:
        raise RuntimeError(f"Required security layer missing: {marker}")

print("PASS V3.1 base")
print("PASS V4 base")
print("PASS V4.1 base")

# ------------------------------------------------------------
# BACKUP
# ------------------------------------------------------------
shutil.copy2(APP, BACKUP)
print(f"OK Backup: {BACKUP}")

try:
    src = src_original

    # --------------------------------------------------------
    # FIX V3.1 MIDDLEWARE — UPLOAD VALIDATION ONLY FOR POST
    # --------------------------------------------------------
    old_dispatch = """    async def dispatch(self, request, call_next):

        await pp12_validate_request_form_uploads(request)

        return await call_next(request)
"""

    new_dispatch = """    async def dispatch(self, request, call_next):

        # Upload validation is only required for POST requests.
        # GET/HEAD health/readiness/status endpoints must pass
        # through without attempting request.form().
        if request.method.upper() == "POST":
            await pp12_validate_request_form_uploads(request)

        return await call_next(request)
"""

    if old_dispatch in src:
        src = src.replace(old_dispatch, new_dispatch, 1)
        print("PASS V3.1 POST-only upload guard connected")
    elif 'if request.method.upper() == "POST":' in src:
        print("PASS V3.1 POST-only upload guard already present")
    else:
        raise RuntimeError("Could not verify V3.1 POST-only guard")

    # --------------------------------------------------------
    # HEALTH / READY / SECURITY STATUS
    # --------------------------------------------------------
    if "/api/health" not in src:

        block = r'''

# ============================================================
# PRIVATEPDF PRO — SECURITY V5
# Health / Readiness / Security Status
# ============================================================

PP_SECURITY_HARDENING_V5 = True


@app.get("/api/health")
async def pp_v5_health():
    return {
        "status": "ok",
        "service": "PrivatePDF Pro"
    }


@app.get("/api/ready")
async def pp_v5_ready():
    try:
        jobs_path = Path(JOBS)

        if not jobs_path.exists():
            jobs_path.mkdir(parents=True, exist_ok=True)

        return {
            "status": "ready",
            "service": "PrivatePDF Pro"
        }

    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "PrivatePDF Pro"
            }
        )


@app.get("/api/security-status")
async def pp_v5_security_status():

    checks = {
        "trusted_hosts": bool(
            globals().get("_PP_TRUSTED_HOSTS")
        ),

        "rate_limit": bool(
            globals().get("PP_SECURITY_RATE_LIMITER")
            or globals().get("_PP_RATE_LIMIT")
        ),

        "heavy_rate_limit": bool(
            globals().get("PP_SECURITY_HEAVY_RATE_LIMITER")
            or globals().get("_PP_HEAVY_RATE_LIMIT")
        ),

        "max_request_bytes": bool(
            globals().get("_PP_MAX_REQUEST_BYTES")
            or globals().get("PP_MAX_REQUEST_BYTES")
            or globals().get("PP_MAX_REQUEST_MB")
        ),

        "heavy_semaphore": bool(
            globals().get("_PP_HEAVY_SEMAPHORE")
            or globals().get("PP_HEAVY_SEMAPHORE")
            or globals().get("PP_MAX_CONCURRENT_JOBS")
        ),

        "v3_upload_middleware": bool(
            globals().get("PP_SECURITY_HARDENING_V3_1")
            or globals().get("PP_SECURITY_V3_1_MIDDLEWARE")
        ),

        "v4_output_guard": bool(
            globals().get("PP_SECURITY_HARDENING_V4")
            or globals().get("PP_V4_OUTPUT_GUARD")
        ),

        "v4_1": bool(
            globals().get("PP_SECURITY_HARDENING_V4_1")
        ),

        "security_v3_1": bool(
            globals().get("PP_SECURITY_HARDENING_V3_1")
        ),

        "security_v4": bool(
            globals().get("PP_SECURITY_HARDENING_V4")
        ),

        "v5": True,
    }

    production_mode = bool(
        globals().get("_PP_PRODUCTION", False)
    )

    all_security_controls_ok = all(checks.values())

    return JSONResponse(
        status_code=200 if all_security_controls_ok else 503,
        content={
            "status": (
                "secure"
                if all_security_controls_ok
                else "degraded"
            ),
            "production_mode": production_mode,
            "checks": checks
        }
    )


'''

        # Insert before static mount
        mount_marker = 'app.mount("/static"'

        pos = src.find(mount_marker)

        if pos == -1:
            raise RuntimeError(
                'Could not find app.mount("/static"...'
            )

        src = src[:pos] + block + src[pos:]

        print("PASS V5 health endpoint")
        print("PASS V5 readiness endpoint")
        print("PASS V5 security-status endpoint")

    else:
        print("INFO V5 endpoints already present")

    # --------------------------------------------------------
    # V5.1 CONFIGURATION MARKER
    # --------------------------------------------------------
    if MARKER not in src:
        src += """

# ============================================================
# SECURITY V5 CLEAN CONFIGURATION
# Production mode is NOT required during local development.
# ============================================================
PP_SECURITY_HARDENING_V5_CLEAN = True
"""
    else:
        print("INFO V5 clean marker already present")

    APP.write_text(src, encoding="utf-8")

    # --------------------------------------------------------
    # PYTHON SYNTAX
    # --------------------------------------------------------
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(APP)
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Python syntax failed:\n" +
            (result.stderr or result.stdout)
        )

    print("PASS Python syntax")

    # --------------------------------------------------------
    # IMPORT APPLICATION
    # --------------------------------------------------------
    from fastapi.testclient import TestClient
    import app.main as main
    from app.main import app

    print()
    print("=" * 62)
    print("REAL APPLICATION VERIFICATION")
    print("=" * 62)

    routes = {
        getattr(route, "path", None)
        for route in app.routes
    }

    print(f"Routes: {len(app.routes)}")

    required_routes = [
        "/",
        "/api/health",
        "/api/ready",
        "/api/security-status",
        "/api/annotate",
        "/api/annotation-page",
        "/api/merge",
        "/api/pages",
        "/api/rotate",
        "/api/compress",
        "/api/resize",
        "/api/crop",
        "/api/numbers",
        "/api/watermark",
        "/api/protect",
        "/api/unlock",
        "/api/metadata",
        "/api/grayscale",
        "/api/text",
        "/api/markdown",
        "/api/pdf-to-jpg",
        "/api/images-to-pdf",
        "/api/office-to-pdf",
        "/api/pdf-to-office",
        "/api/image-resize",
        "/api/page-thumbnails",
        "/api/rotate-pages",
        "/api/batch-process",
        "/api/pdf-inspect",
    ]

    for route in required_routes:
        if route not in routes:
            raise RuntimeError(
                f"Required route missing: {route}"
            )

    print("PASS All required routes")

    # --------------------------------------------------------
    # USE LOCALHOST — TRUSTED HOST
    # --------------------------------------------------------
    client = TestClient(
        app,
        base_url="http://localhost"
    )

    # --------------------------------------------------------
    # ROOT
    # --------------------------------------------------------
    r = client.get("/")
    print(f"/: HTTP {r.status_code}")

    if r.status_code != 200:
        raise RuntimeError(
            f"Root endpoint failed: {r.status_code}"
        )

    # --------------------------------------------------------
    # HEALTH
    # --------------------------------------------------------
    r = client.get("/api/health")
    print(f"/api/health: HTTP {r.status_code}")

    if r.status_code != 200:
        raise RuntimeError(
            f"Health failed: {r.status_code}; "
            f"body={r.text!r}"
        )

    payload = r.json()

    if payload.get("status") != "ok":
        raise RuntimeError(
            f"Invalid health payload: {payload!r}"
        )

    print("PASS Health JSON")

    # --------------------------------------------------------
    # READY
    # --------------------------------------------------------
    r = client.get("/api/ready")
    print(f"/api/ready: HTTP {r.status_code}")

    if r.status_code != 200:
        raise RuntimeError(
            f"Readiness failed: {r.status_code}; "
            f"body={r.text!r}"
        )

    payload = r.json()

    if payload.get("status") != "ready":
        raise RuntimeError(
            f"Invalid readiness payload: {payload!r}"
        )

    print("PASS Readiness JSON")

    # --------------------------------------------------------
    # SECURITY STATUS
    # --------------------------------------------------------
    r = client.get("/api/security-status")

    print(
        f"/api/security-status: HTTP {r.status_code}"
    )
    print(
        f"Security status body: {r.text}"
    )

    if r.status_code != 200:
        raise RuntimeError(
            "Security status returned "
            f"{r.status_code}"
        )

    status = r.json()

    if status.get("status") != "secure":
        raise RuntimeError(
            f"Security status not secure: {status!r}"
        )

    # Production mode is INFORMATIONAL.
    # False is correct during local testing.
    if "production_mode" not in status:
        raise RuntimeError(
            "production_mode missing"
        )

    if "production_flag" in status.get("checks", {}):
        raise RuntimeError(
            "Old production_flag check still present"
        )

    for key, value in status.get("checks", {}).items():
        if value is not True:
            raise RuntimeError(
                f"Security control failed: "
                f"{key}={value!r}"
            )

    print("PASS All active security controls")

    # --------------------------------------------------------
    # VERIFY V3.1 POST-ONLY
    # --------------------------------------------------------
    current_src = APP.read_text(
        encoding="utf-8"
    )

    if (
        'if request.method.upper() == "POST":'
        not in current_src
    ):
        raise RuntimeError(
            "V3.1 POST-only upload guard missing"
        )

    print("PASS V3.1 POST-only upload guard")

    # --------------------------------------------------------
    # SECURITY MARKERS
    # --------------------------------------------------------
    final_src = APP.read_text(
        encoding="utf-8"
    )

    marker_checks = {
        "V3.1": "PP_SECURITY_HARDENING_V3_1"
                 in final_src,

        "V4": "PP_SECURITY_HARDENING_V4"
               in final_src,

        "V4.1": "PP_SECURITY_HARDENING_V4_1"
                 in final_src,

        "V5": "PP_SECURITY_HARDENING_V5"
               in final_src,

        "V5 clean": MARKER in final_src,
    }

    for name, ok in marker_checks.items():
        if not ok:
            raise RuntimeError(
                f"Security marker missing: {name}"
            )

        print(f"PASS Security {name}")

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------
    print()
    print("=" * 62)
    print("SECURITY V5 CLEAN: COMPLETE")
    print("=" * 62)
    print()
    print("Production mode:",
          status.get("production_mode"))
    print("Security status:",
          status.get("status"))
    print("Routes:", len(app.routes))

except Exception as exc:

    print()
    print("=" * 62)
    print("SECURITY V5 CLEAN INSTALL FAILED")
    print("=" * 62)
    print(f"{type(exc).__name__}: {exc}")
    print()
    print("ROLLING BACK AUTOMATICALLY...")

    if BACKUP.exists():
        shutil.copy2(BACKUP, APP)
        print("PASS rollback completed")

    print()
    print("DO NOT RUN ANOTHER INSTALLER.")
    print("Current application restored to pre-V5 state.")

    raise

