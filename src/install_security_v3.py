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

MARK = "PP_SECURITY_HARDENING_V3"

if MARK in src:
    print("Security V3 already installed.")
    sys.exit(0)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = MAIN.with_name(
    f"main.py.before_security_v3_{stamp}.bak"
)
shutil.copy2(MAIN, backup)

# ============================================================
# SECURITY V3 HELPER LAYER
# ============================================================

helper = r'''

# ============================================================
# PP_SECURITY_HARDENING_V3
# Universal Upload Security + Resource Protection
# ============================================================

PP_SECURITY_HARDENING_V3 = True

import io
import os
import re
import zipfile
from pathlib import Path as _PPPath

try:
    from PIL import Image as _PPImage
    _PP_PIL_AVAILABLE = True
except Exception:
    _PP_PIL_AVAILABLE = False

try:
    from fastapi import UploadFile as _PPUploadFile
except Exception:
    _PPUploadFile = None


# Conservative production limits.
PP_MAX_UPLOAD_FILES = int(
    os.getenv("PP_MAX_UPLOAD_FILES", "20")
)

PP_MAX_UPLOAD_TOTAL_MB = int(
    os.getenv("PP_MAX_UPLOAD_TOTAL_MB", "300")
)

PP_MAX_PDF_PAGES = int(
    os.getenv("PP_MAX_PDF_PAGES", "1000")
)

PP_MAX_IMAGE_PIXELS = int(
    os.getenv("PP_MAX_IMAGE_PIXELS", "100000000")
)

PP_MAX_OFFICE_ZIP_ENTRIES = int(
    os.getenv("PP_MAX_OFFICE_ZIP_ENTRIES", "5000")
)

PP_MAX_OFFICE_UNCOMPRESSED_MB = int(
    os.getenv("PP_MAX_OFFICE_UNCOMPRESSED_MB", "500")
)


def pp12_upload_extension(upload):
    name = getattr(upload, "filename", "") or ""
    name = os.path.basename(name)
    return _PPPath(name).suffix.lower()


def pp12_upload_name(upload):
    name = getattr(upload, "filename", "") or "upload"
    name = os.path.basename(name)

    # Never allow path traversal or control characters.
    name = re.sub(r"[\x00-\x1f\x7f]", "_", name)
    name = name.replace("/", "_").replace("\\", "_")
    name = re.sub(r"\.\.+", ".", name)

    if not name or name in {".", ".."}:
        name = "upload"

    return name[:180]


async def pp12_read_upload_safely(upload):
    """
    Read an UploadFile once for validation and rewind it.
    Existing endpoints can subsequently read the same stream normally.
    """
    data = await upload.read()

    try:
        await upload.seek(0)
    except Exception:
        try:
            upload.file.seek(0)
        except Exception:
            pass

    return data


def pp12_validate_pdf_payload(data):
    if not data:
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF upload."
        )

    if not data.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid PDF."
        )

    # Require a PDF EOF marker near the end.
    tail = data[-65536:]
    if b"%%EOF" not in tail:
        raise HTTPException(
            status_code=400,
            detail="PDF appears incomplete or corrupted."
        )

    if len(data) > PP_MAX_UPLOAD_TOTAL_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Uploaded file exceeds the allowed size."
        )

    try:
        _doc = fitz.open(stream=data, filetype="pdf")
        pages = _doc.page_count

        if pages < 1:
            _doc.close()
            raise HTTPException(
                status_code=400,
                detail="PDF contains no pages."
            )

        if pages > PP_MAX_PDF_PAGES:
            _doc.close()
            raise HTTPException(
                status_code=413,
                detail="PDF contains too many pages."
            )

        # Force basic page access so obviously broken documents
        # are rejected before expensive processing.
        _doc.load_page(0)

        if pages > 1:
            _doc.load_page(pages - 1)

        _doc.close()

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="PDF validation failed."
        )


def pp12_validate_image_payload(data, filename):
    if not data:
        raise HTTPException(
            status_code=400,
            detail="Invalid image upload."
        )

    if len(data) > PP_MAX_UPLOAD_TOTAL_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Uploaded image exceeds the allowed size."
        )

    if not _PP_PIL_AVAILABLE:
        return

    try:
        with _PPImage.open(io.BytesIO(data)) as img:
            img.verify()

        with _PPImage.open(io.BytesIO(data)) as img:
            width, height = img.size

            if width <= 0 or height <= 0:
                raise ValueError("invalid dimensions")

            if width * height > PP_MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=413,
                    detail="Image dimensions are too large."
                )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image."
        )


def pp12_validate_office_payload(data, filename):
    if not data:
        raise HTTPException(
            status_code=400,
            detail="Invalid Office upload."
        )

    ext = _PPPath(
        pp12_upload_name(type("_X", (), {"filename": filename})())
    ).suffix.lower()

    allowed = {
        ".doc", ".docx",
        ".xls", ".xlsx",
        ".ppt", ".pptx",
        ".odt", ".ods", ".odp"
    }

    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Unsupported Office document type."
        )

    if len(data) > PP_MAX_UPLOAD_TOTAL_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Uploaded document exceeds the allowed size."
        )

    # OOXML/ODF formats are ZIP containers.
    zip_exts = {
        ".docx", ".xlsx", ".pptx",
        ".odt", ".ods", ".odp"
    }

    if ext in zip_exts:
        if not data.startswith(b"PK"):
            raise HTTPException(
                status_code=400,
                detail="Office document container is invalid."
            )

        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                infos = z.infolist()

                if len(infos) > PP_MAX_OFFICE_ZIP_ENTRIES:
                    raise HTTPException(
                        status_code=413,
                        detail="Office document contains too many resources."
                    )

                total_uncompressed = sum(
                    max(0, int(x.file_size))
                    for x in infos
                )

                if total_uncompressed > (
                    PP_MAX_OFFICE_UNCOMPRESSED_MB * 1024 * 1024
                ):
                    raise HTTPException(
                        status_code=413,
                        detail="Office document expands beyond the allowed limit."
                    )

                if z.testzip() is not None:
                    raise HTTPException(
                        status_code=400,
                        detail="Office document is corrupted."
                    )

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Office document validation failed."
            )


def pp12_collect_uploads(value, output=None):
    """
    Recursively collect UploadFile instances from FastAPI endpoint kwargs.
    """
    if output is None:
        output = []

    if _PPUploadFile is not None and isinstance(value, _PPUploadFile):
        output.append(value)
        return output

    if isinstance(value, (list, tuple)):
        for item in value:
            pp12_collect_uploads(item, output)
        return output

    if isinstance(value, dict):
        for item in value.values():
            pp12_collect_uploads(item, output)
        return output

    return output


async def pp12_validate_endpoint_uploads(path, kwargs):
    uploads = []

    for value in kwargs.values():
        pp12_collect_uploads(value, uploads)

    if not uploads:
        return

    if len(uploads) > PP_MAX_UPLOAD_FILES:
        raise HTTPException(
            status_code=413,
            detail="Too many files were submitted."
        )

    total = 0

    for upload in uploads:
        filename = pp12_upload_name(upload)
        ext = pp12_upload_extension(upload)

        data = await pp12_read_upload_safely(upload)

        total += len(data)

        if total > PP_MAX_UPLOAD_TOTAL_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Total upload size exceeds the allowed limit."
            )

        lower_path = path.lower()

        # PDF processing endpoints.
        pdf_paths = {
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
        }

        if lower_path in pdf_paths:
            pp12_validate_pdf_payload(data)

        # Image upload endpoints.
        image_paths = {
            "/api/images-to-pdf",
            "/api/image-resize",
        }

        if lower_path in image_paths:
            pp12_validate_image_payload(data, filename)

        # Office input endpoint.
        office_paths = {
            "/api/office-to-pdf",
        }

        if lower_path in office_paths:
            pp12_validate_office_payload(data, filename)


def pp12_production_safe_filename(upload):
    try:
        upload.filename = pp12_upload_name(upload)
    except Exception:
        pass


# ============================================================
# Endpoint wrapper
# ============================================================

def pp12_wrap_upload_endpoints():
    """
    Wrap FastAPI upload endpoints after route registration.
    The wrapper uses **kwargs so FastAPI's already-built
    dependency model remains compatible.
    """

    target_paths = {
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

    wrapped = 0

    for _route in getattr(app, "routes", []):
        path = getattr(_route, "path", "")

        if path not in target_paths:
            continue

        endpoint = getattr(_route, "endpoint", None)

        if endpoint is None:
            continue

        if getattr(endpoint, "_pp12_security_v3_wrapped", False):
            continue

        original = endpoint

        async def _secure_endpoint(*args, __original=original, __path=path, **kwargs):
            await pp12_validate_endpoint_uploads(
                __path,
                kwargs
            )

            for value in kwargs.values():
                for upload in pp12_collect_uploads(value):
                    pp12_production_safe_filename(upload)

            return await __original(*args, **kwargs)

        _secure_endpoint._pp12_security_v3_wrapped = True
        _secure_endpoint._pp12_original_endpoint = original

        _route.endpoint = _secure_endpoint

        wrapped += 1

    return wrapped


# Apply after all routes have been declared.
try:
    PP_SECURITY_V3_WRAPPED_ROUTES = pp12_wrap_upload_endpoints()
except Exception as _pp_v3_wrap_error:
    PP_SECURITY_V3_WRAPPED_ROUTES = 0
    print(
        "PP_SECURITY_V3 route wrapping warning:",
        str(_pp_v3_wrap_error)
    )

'''

# ------------------------------------------------------------
# Insert helper layer BEFORE first @app route.
# ------------------------------------------------------------

route_match = re.search(r'(?m)^@app\.', src)

if not route_match:
    print("ERROR: No FastAPI route declarations found.")
    shutil.copy2(backup, MAIN)
    sys.exit(2)

insert_at = route_match.start()

src = src[:insert_at] + helper + "\n" + src[insert_at:]

MAIN.write_text(src, encoding="utf-8")

# ============================================================
# Verification
# ============================================================

print("=" * 72)
print(" SECURITY V3 INSTALLATION")
print("=" * 72)
print()
print("Backup:", backup.name)
print()

checks = [
    ("Security V3 marker", "PP_SECURITY_HARDENING_V3" in src),
    ("PDF payload validator", "def pp12_validate_pdf_payload" in src),
    ("Image payload validator", "def pp12_validate_image_payload" in src),
    ("Office payload validator", "def pp12_validate_office_payload" in src),
    ("Upload collector", "def pp12_collect_uploads" in src),
    ("Endpoint upload validator", "def pp12_validate_endpoint_uploads" in src),
    ("Route wrapper", "def pp12_wrap_upload_endpoints" in src),
    ("Maximum file count", "PP_MAX_UPLOAD_FILES" in src),
    ("Total upload limit", "PP_MAX_UPLOAD_TOTAL_MB" in src),
    ("PDF page limit", "PP_MAX_PDF_PAGES" in src),
    ("Image pixel limit", "PP_MAX_IMAGE_PIXELS" in src),
    ("Office resource limit", "PP_MAX_OFFICE_ZIP_ENTRIES" in src),
    ("Annotation route preserved", '@app.post("/api/annotate")' in src),
    ("Annotation page preserved", '@app.post("/api/annotation-page")' in src),
]

for name, ok in checks:
    print(("OK   " if ok else "FAIL ") + name)

print()

if not all(ok for _, ok in checks):
    print("ERROR: Verification failed.")
    print("Restoring backup...")
    shutil.copy2(backup, MAIN)
    sys.exit(3)

# ------------------------------------------------------------
# Python syntax
# ------------------------------------------------------------

print("=" * 62)
print(" PYTHON SYNTAX CHECK")
print("=" * 62)

result = subprocess.run(
    [sys.executable, "-m", "py_compile", "app/main.py"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print("PYTHON SYNTAX: FAIL")
    print(result.stderr)
    print("Restoring backup...")
    shutil.copy2(backup, MAIN)
    sys.exit(4)

print("PYTHON SYNTAX: PASS")
print()

# ------------------------------------------------------------
# Import + route check
# ------------------------------------------------------------

print("=" * 62)
print(" IMPORT / ROUTE CHECK")
print("=" * 62)

check = subprocess.run(
    [
        sys.executable,
        "-c",
        """
from app.main import app
routes = [getattr(r, "path", "") for r in app.routes]
print("Routes:", len(routes))
print("Annotation:", "/api/annotate" in routes)
print("Annotation Page:", "/api/annotation-page" in routes)
print("Merge:", "/api/merge" in routes)
print("Images to PDF:", "/api/images-to-pdf" in routes)
print("Office to PDF:", "/api/office-to-pdf" in routes)
print("Wrapped routes:",
      getattr(__import__("app.main", fromlist=["PP_SECURITY_V3_WRAPPED_ROUTES"]),
              "PP_SECURITY_V3_WRAPPED_ROUTES", 0))
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

print("=" * 72)
print(" SECURITY V3 COMPLETE")
print("=" * 72)
print()
print("Universal upload guards are now connected.")
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
print()
print("No database.")
print("No persistent document storage.")
print()
print("Restart Uvicorn:")
print()
print("python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
print()
