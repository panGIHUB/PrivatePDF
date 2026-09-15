from pathlib import Path
import shutil
import sys
import py_compile

MAIN = Path("app/main.py")
BACKUP = Path("app/main.py.before_security_v5")

MARKER = "PP_SECURITY_HARDENING_V5"

print("=" * 62)
print("PRIVATEPDF PRO — SECURITY V5 INSTALLER")
print("=" * 62)

if not MAIN.exists():
    print("FAIL: app/main.py not found")
    sys.exit(1)

src = MAIN.read_text(encoding="utf-8")

if MARKER in src:
    print("INFO: Security V5 marker already exists.")
    print("No duplicate installation performed.")
    sys.exit(0)

# ------------------------------------------------------------
# Backup
# ------------------------------------------------------------

shutil.copy2(MAIN, BACKUP)
print("OK Backup:", BACKUP)

try:

    # ========================================================
    # V5 configuration + health/readiness
    # ========================================================

    block = r'''

# ============================================================
# PP_SECURITY_HARDENING_V5
# Production health, readiness and security observability
#
# V5 is intentionally stateless:
# - no document database
# - no persistent uploaded documents
# - health/readiness expose only operational state
# - no filesystem paths or internal exception details
# ============================================================

PP_SECURITY_HARDENING_V5 = True

# ------------------------------------------------------------
# Health endpoint
# ------------------------------------------------------------

@app.get("/api/health")
async def pp_v5_health():
    """
    Lightweight liveness endpoint.

    This endpoint intentionally does not inspect uploaded files,
    parse multipart forms, or expose internal filesystem details.
    """

    return {
        "status": "ok",
        "service": "PrivatePDF Pro"
    }


# ------------------------------------------------------------
# Readiness endpoint
# ------------------------------------------------------------

@app.get("/api/ready")
async def pp_v5_ready():
    """
    Readiness endpoint.

    Checks only application-level prerequisites that are safe to
    expose. It does not expose internal paths or stack traces.
    """

    checks = {}

    try:
        checks["application"] = True
    except Exception:
        checks["application"] = False

    try:
        checks["temporary_workspace"] = JOBS.exists()
    except Exception:
        checks["temporary_workspace"] = False

    ready = all(checks.values())

    if ready:
        return {
            "status": "ready",
            "service": "PrivatePDF Pro",
            "checks": checks
        }

    return _PPJSONResponse(
        {
            "status": "not_ready",
            "service": "PrivatePDF Pro",
            "checks": checks
        },
        status_code=503
    )


# ------------------------------------------------------------
# V5 security configuration validator
# ------------------------------------------------------------

PP_V5_REQUIRED_SECURITY = {
    "production_flag": "_PP_PRODUCTION",
    "trusted_hosts": "_PP_TRUSTED_HOSTS",
    "rate_limit": "_PP_RATE_LIMIT",
    "heavy_rate_limit": "_PP_HEAVY_RATE_LIMIT",
    "max_request_bytes": "_PP_MAX_REQUEST_BYTES",
    "heavy_semaphore": "_PP_HEAVY_SEMAPHORE",
    "v3_upload_middleware": "PP_SECURITY_V3_1_MIDDLEWARE",
    "v4_output_guard": "PP12_V4_OUTPUT_GUARD",
    "v4_1": "PP_SECURITY_HARDENING_V4_1",
}


def pp_v5_security_config():
    result = {}

    for name, variable in PP_V5_REQUIRED_SECURITY.items():
        result[name] = bool(
            globals().get(variable, False)
        )

    result["security_v3_1"] = bool(
        globals().get(
            "PP_SECURITY_HARDENING_V3_1",
            False
        )
    )

    result["security_v4"] = bool(
        globals().get(
            "PP_SECURITY_HARDENING_V4",
            False
        )
    )

    result["v5"] = True

    return result


@app.get("/api/security-status")
async def pp_v5_security_status():
    """
    Safe security-status endpoint.

    Exposes boolean capability state only.
    No paths, environment secrets, hostnames or exception details.
    """

    checks = pp_v5_security_config()

    if all(checks.values()):
        return {
            "status": "secure",
            "checks": checks
        }

    return _PPJSONResponse(
        {
            "status": "degraded",
            "checks": checks
        },
        status_code=503
    )

# === END PP_SECURITY_HARDENING_V5 ===

'''

    # --------------------------------------------------------
    # Insert before static mount.
    # At this point all existing security helpers/configuration
    # are already defined and routes can safely use JOBS.
    # --------------------------------------------------------

    anchor = 'app.mount("/static", StaticFiles(directory=STATIC), name="static")'

    if anchor not in src:
        raise RuntimeError(
            "Static mount anchor not found."
        )

    src = src.replace(
        anchor,
        block + "\n" + anchor,
        1
    )

    MAIN.write_text(src, encoding="utf-8")

    # --------------------------------------------------------
    # Syntax
    # --------------------------------------------------------

    py_compile.compile(
        str(MAIN),
        doraise=True
    )

    print("PASS Python syntax")

    # --------------------------------------------------------
    # Static checks
    # --------------------------------------------------------

    installed = MAIN.read_text(encoding="utf-8")

    required = [
        "PP_SECURITY_HARDENING_V5",
        "@app.get(\"/api/health\")",
        "@app.get(\"/api/ready\")",
        "@app.get(\"/api/security-status\")",
        "PP_V5_REQUIRED_SECURITY",
        "pp_v5_security_config",
    ]

    for item in required:
        if item not in installed:
            raise RuntimeError(
                "Missing V5 component: " + item
            )

    print("PASS V5 health endpoint")
    print("PASS V5 readiness endpoint")
    print("PASS V5 security-status endpoint")
    print("PASS V5 security validator")

    # ========================================================
    # Real import + TestClient verification
    # ========================================================

    print()
    print("=" * 62)
    print("REAL APPLICATION VERIFICATION")
    print("=" * 62)

    # Import after modification.
    from app.main import app

    from fastapi.testclient import TestClient

    print("Routes:", len(app.routes))

    paths = {
        "/": 200,
        "/api/health": 200,
        "/api/ready": 200,
        "/api/security-status": 200,
    }

    # IMPORTANT:
    # localhost is an explicitly trusted local host.
    client = TestClient(
        app,
        base_url="http://localhost"
    )

    for path, expected in paths.items():

        response = client.get(path)

        print(
            f"{path}: HTTP {response.status_code}"
        )

        if response.status_code != expected:
            raise RuntimeError(
                f"{path} expected HTTP {expected}, "
                f"got HTTP {response.status_code}; "
                f"body={response.text[:300]!r}"
            )

        content_type = (
            response.headers.get(
                "content-type",
                ""
            )
        )

        if path != "/" and "application/json" not in content_type:
            raise RuntimeError(
                f"{path} did not return JSON."
            )

    # --------------------------------------------------------
    # Verify health payload
    # --------------------------------------------------------

    health = client.get(
        "/api/health"
    ).json()

    if health.get("status") != "ok":
        raise RuntimeError(
            "Health payload invalid: "
            + repr(health)
        )

    print("PASS health JSON")

    # --------------------------------------------------------
    # Verify readiness payload
    # --------------------------------------------------------

    ready = client.get(
        "/api/ready"
    ).json()

    if ready.get("status") != "ready":
        raise RuntimeError(
            "Readiness payload invalid: "
            + repr(ready)
        )

    print("PASS readiness JSON")

    # --------------------------------------------------------
    # Verify security status
    # --------------------------------------------------------

    security = client.get(
        "/api/security-status"
    ).json()

    if security.get("status") != "secure":
        raise RuntimeError(
            "Security status is not secure: "
            + repr(security)
        )

    print("PASS security status")

    # --------------------------------------------------------
    # Verify critical routes remain registered
    # --------------------------------------------------------

    route_paths = {
        getattr(route, "path", "")
        for route in app.routes
    }

    critical = [
        "/api/annotate",
        "/api/annotation-page",
        "/api/merge",
        "/api/compress",
        "/api/office-to-pdf",
        "/api/pdf-to-office",
        "/api/batch-process",
        "/api/pdf-inspect",
    ]

    for route in critical:
        if route not in route_paths:
            raise RuntimeError(
                "Critical route missing: " + route
            )

    print("PASS critical routes preserved")

    # --------------------------------------------------------
    # Verify V3.1 middleware is still POST-only
    # --------------------------------------------------------

    current = MAIN.read_text(encoding="utf-8")

    expected_guard = (
        'if request.method.upper() == "POST":'
    )

    if expected_guard not in current:
        raise RuntimeError(
            "V3.1 POST-only guard missing."
        )

    print("PASS V3.1 POST-only upload guard")

    # --------------------------------------------------------
    # Verify previous security layers
    # --------------------------------------------------------

    previous = [
        "PP_SECURITY_HARDENING_V2",
        "PP_SECURITY_HARDENING_V2_1",
        "PP_SECURITY_HARDENING_V3_1",
        "PP_SECURITY_HARDENING_V4",
        "PP_SECURITY_HARDENING_V4_1",
    ]

    for marker in previous:
        if marker not in current:
            raise RuntimeError(
                "Previous security marker missing: "
                + marker
            )

        print(
            "PASS",
            marker
        )

    print()
    print("=" * 62)
    print("SECURITY V5 INSTALLATION COMPLETE")
    print("=" * 62)

except Exception as exc:

    print()
    print("=" * 62)
    print("SECURITY V5 VERIFICATION FAILED")
    print("=" * 62)

    print(
        type(exc).__name__ + ":",
        str(exc)
    )

    print()
    print("ROLLING BACK AUTOMATICALLY...")

    try:
        shutil.copy2(
            BACKUP,
            MAIN
        )
        print("PASS rollback completed")
    except Exception as rollback_exc:
        print(
            "CRITICAL rollback failure:",
            type(rollback_exc).__name__,
            str(rollback_exc)
        )

    sys.exit(1)
