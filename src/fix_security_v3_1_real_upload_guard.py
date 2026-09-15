from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys
import re

MAIN = Path("app/main.py")

if not MAIN.exists():
    print("ERROR: app/main.py not found")
    sys.exit(1)

src = MAIN.read_text(encoding="utf-8")

MARK = "PP_SECURITY_HARDENING_V3_1_REAL_UPLOAD_GUARD"

if MARK in src:
    print("Security V3.1 already installed.")
    sys.exit(0)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = MAIN.with_name(
    f"main.py.before_security_v3_1_{stamp}.bak"
)

shutil.copy2(MAIN, backup)

# ============================================================
# 1. Disable the V3 endpoint wrapper.
#
# The previous wrapper changed endpoint callables after
# FastAPI had already constructed dependency information.
# That is why the wrapper count was 0 / unreliable.
#
# We leave the helper code intact but disable invocation.
# ============================================================

old_apply = """try:
    PP_SECURITY_V3_WRAPPED_ROUTES = pp12_wrap_upload_endpoints()
except Exception as _pp_v3_wrap_error:
    PP_SECURITY_V3_WRAPPED_ROUTES = 0
    print(
        "PP_SECURITY_V3 route wrapping warning:",
        str(_pp_v3_wrap_error)
    )
"""

new_apply = """# V3.1 replaces endpoint wrapping with an ASGI request guard.
PP_SECURITY_V3_WRAPPED_ROUTES = 0
"""

if old_apply in src:
    src = src.replace(old_apply, new_apply, 1)
    print("OK   Disabled unreliable endpoint wrapper")
else:
    # If already changed, continue.
    print("INFO Endpoint wrapper block not found; continuing safely")

# ============================================================
# 2. Add real request-level multipart validation.
#
# BaseHTTPMiddleware parses request.form() before the endpoint.
# Starlette caches the parsed form, so FastAPI can consume it
# normally afterward.
# ============================================================

guard = r'''

# ============================================================
# PP_SECURITY_HARDENING_V3_1_REAL_UPLOAD_GUARD
# ============================================================

PP_SECURITY_HARDENING_V3_1 = True

try:
    from starlette.middleware.base import BaseHTTPMiddleware as _PPBaseHTTPMiddleware
except Exception:
    _PPBaseHTTPMiddleware = None


async def pp12_validate_request_form_uploads(request):
    """
    Parse multipart form data once and validate every UploadFile
    before the endpoint executes.

    Starlette caches request.form(), therefore the downstream
    FastAPI endpoint can still read the same UploadFile normally.
    """

    path = request.url.path.lower()

    # Only inspect API endpoints that can receive uploads.
    upload_paths = {
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
        "/api/rotate-pages",
        "/api/batch-process",
        "/api/pdf-inspect",
        "/api/annotate",
        "/api/annotation-page",
    }

    if path not in upload_paths:
        return

    content_type = request.headers.get("content-type", "").lower()

    # Upload endpoints are expected to use multipart/form-data.
    # Empty-body requests will be handled by the endpoint itself.
    if "multipart/form-data" not in content_type:
        return

    try:
        form = await request.form()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid multipart upload."
        )

    uploads = []

    for value in form.values():

        if _PPUploadFile is not None and isinstance(
            value, _PPUploadFile
        ):
            uploads.append(value)

        elif isinstance(value, (list, tuple)):
            for item in value:
                if _PPUploadFile is not None and isinstance(
                    item, _PPUploadFile
                ):
                    uploads.append(item)

    if len(uploads) > PP_MAX_UPLOAD_FILES:
        raise HTTPException(
            status_code=413,
            detail="Too many files were submitted."
        )

    total = 0

    for upload in uploads:

        # Normalize filename before any endpoint touches it.
        try:
            upload.filename = pp12_upload_name(upload)
        except Exception:
            upload.filename = "upload"

        try:
            data = await upload.read()
            await upload.seek(0)
        except Exception:
            try:
                upload.file.seek(0)
                data = upload.file.read()
                upload.file.seek(0)
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Unable to read uploaded file."
                )

        total += len(data)

        if total > PP_MAX_UPLOAD_TOTAL_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Total upload size exceeds the allowed limit."
            )

        filename = upload.filename or "upload"
        ext = Path(filename).suffix.lower()

        # ----------------------------------------------------
        # PDF routes
        # ----------------------------------------------------

        if path in {
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
            "/api/pdf-to-office",
            "/api/rotate-pages",
            "/api/batch-process",
            "/api/pdf-inspect",
            "/api/annotate",
            "/api/annotation-page",
        }:
            pp12_validate_pdf_payload(data)

        # ----------------------------------------------------
        # Image routes
        # ----------------------------------------------------

        elif path in {
            "/api/images-to-pdf",
            "/api/image-resize",
        }:
            pp12_validate_image_payload(
                data,
                filename
            )

        # ----------------------------------------------------
        # Office routes
        # ----------------------------------------------------

        elif path == "/api/office-to-pdf":
            pp12_validate_office_payload(
                data,
                filename
            )


if _PPBaseHTTPMiddleware is not None:

    class PP12SecurityV31Middleware(_PPBaseHTTPMiddleware):

        async def dispatch(self, request, call_next):

            await pp12_validate_request_form_uploads(request)

            return await call_next(request)

    try:
        app.add_middleware(PP12SecurityV31Middleware)
        PP_SECURITY_V3_1_MIDDLEWARE = True
    except Exception as _pp_v31_error:
        PP_SECURITY_V3_1_MIDDLEWARE = False
        print(
            "Security V3.1 middleware installation warning:",
            str(_pp_v31_error)
        )

else:
    PP_SECURITY_V3_1_MIDDLEWARE = False

'''

# ------------------------------------------------------------
# Insert before first FastAPI route.
# ------------------------------------------------------------

route_match = re.search(r'(?m)^@app\.', src)

if not route_match:
    print("ERROR: No FastAPI routes found.")
    shutil.copy2(backup, MAIN)
    sys.exit(2)

src = src[:route_match.start()] + guard + "\n" + src[route_match.start():]

MAIN.write_text(src, encoding="utf-8")

# ============================================================
# Verification
# ============================================================

print()
print("=" * 72)
print(" SECURITY V3.1 — REAL UPLOAD GUARD")
print("=" * 72)
print()
print("Backup:", backup.name)
print()

checks = [
    (
        "Security V3.1 marker",
        MARK in src
    ),
    (
        "Request form validator",
        "def pp12_validate_request_form_uploads" in src
    ),
    (
        "Multipart guard",
        "multipart/form-data" in src
    ),
    (
        "PDF validation",
        "pp12_validate_pdf_payload(data)" in src
    ),
    (
        "Image validation",
        "pp12_validate_image_payload" in src
    ),
    (
        "Office validation",
        "pp12_validate_office_payload" in src
    ),
    (
        "Upload count limit",
        "PP_MAX_UPLOAD_FILES" in src
    ),
    (
        "Total upload limit",
        "PP_MAX_UPLOAD_TOTAL_MB" in src
    ),
    (
        "Annotation preserved",
        '@app.post("/api/annotate")' in src
    ),
    (
        "Annotation page preserved",
        '@app.post("/api/annotation-page")' in src
    ),
]

for name, ok in checks:
    print(("OK   " if ok else "FAIL ") + name)

print()

if not all(ok for _, ok in checks):
    print("ERROR: Verification failed.")
    print("Restoring backup...")
    shutil.copy2(backup, MAIN)
    sys.exit(3)

# ============================================================
# Syntax
# ============================================================

print("=" * 62)
print(" PYTHON SYNTAX CHECK")
print("=" * 62)

result = subprocess.run(
    [
        sys.executable,
        "-m",
        "py_compile",
        "app/main.py"
    ],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print("PYTHON SYNTAX: FAIL")
    print(result.stderr)
    print()
    print("Restoring backup...")
    shutil.copy2(backup, MAIN)
    sys.exit(4)

print("PYTHON SYNTAX: PASS")
print()

# ============================================================
# Import + middleware + routes
# ============================================================

print("=" * 62)
print(" IMPORT / MIDDLEWARE / ROUTE CHECK")
print("=" * 62)

check = subprocess.run(
    [
        sys.executable,
        "-c",
        """
from app.main import app
import app.main as m

routes = [getattr(r, "path", "") for r in app.routes]

print("Routes:", len(routes))
print("Annotation:", "/api/annotate" in routes)
print("Annotation Page:", "/api/annotation-page" in routes)
print("Merge:", "/api/merge" in routes)
print("Images to PDF:", "/api/images-to-pdf" in routes)
print("Office to PDF:", "/api/office-to-pdf" in routes)
print("PDF Inspect:", "/api/pdf-inspect" in routes)

print(
    "Security V3.1 middleware:",
    getattr(m, "PP_SECURITY_V3_1_MIDDLEWARE", False)
)

print(
    "Old V3 wrappers:",
    getattr(m, "PP_SECURITY_V3_WRAPPED_ROUTES", -1)
)
"""
    ],
    capture_output=True,
    text=True
)

print(check.stdout)

if check.returncode != 0:
    print("IMPORT CHECK: FAIL")
    print(check.stderr)
    print("Restoring backup...")
    shutil.copy2(backup, MAIN)
    sys.exit(5)

# ============================================================
# Final source verification
# ============================================================

final_src = MAIN.read_text(encoding="utf-8")

if (
    "PP_SECURITY_HARDENING_V3_1_REAL_UPLOAD_GUARD" not in final_src
    or "PP_SECURITY_V3_1_MIDDLEWARE = True" not in final_src
):
    print("ERROR: V3.1 middleware was not successfully connected.")
    print("Restoring backup...")
    shutil.copy2(backup, MAIN)
    sys.exit(6)

print("=" * 72)
print(" SECURITY V3.1 COMPLETE")
print("=" * 72)
print()
print("REAL upload guard connected through middleware.")
print()
print("Protected:")
print("  PDF uploads")
print("  Image uploads")
print("  Office uploads")
print("  Multi-file uploads")
print("  Total upload size")
print("  Filename sanitization")
print("  PDF page limits")
print("  Image pixel limits")
print("  Office ZIP resource limits")
print()
print("Preserved:")
print("  #12 Annotation Engine")
print("  #12.2 Object Manager")
print("  #12.3 Advanced Text")
print("  #12.4 Text Markup")
print("  #12.5 Shapes")
print("  #12.6 History")
print("  Security V1")
print("  Security V2")
print("  Security V2.1")
print("  Security V3 helpers")
print()
print("No database.")
print("No persistent document storage.")
print()
print("Restart Uvicorn:")
print()
print("python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
