from fastapi.responses import HTMLResponse
from fastapi.responses import Response
import io
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

import pymupdf as fitz

# ============================================================
# PP_SECURITY_HARDENING_V2
# Production file validation / resource safety layer
# No persistent document storage.
# ============================================================

import os
import re
import secrets
import tempfile
from pathlib import Path

PP_SECURITY_V2_MAX_PDF_MB = int(
    os.getenv("PP_MAX_PDF_MB", "300")
)

PP_SECURITY_V2_MAX_PAGES = int(
    os.getenv("PP_MAX_PAGES", "1000")
)

PP_SECURITY_V2_MAX_OUTPUT_MB = int(
    os.getenv("PP_MAX_OUTPUT_MB", "500")
)

PP_SECURITY_V2_MAX_TEXT_CHARS = int(
    os.getenv("PP_MAX_TEXT_CHARS", "10000000")
)


def pp12_safe_filename(filename: str) -> str:
    """
    Convert an untrusted client filename into a harmless display name.
    Never use the result as an executable/path component.
    """
    name = Path(filename or "document.pdf").name

    name = name.replace("\x00", "")
    name = re.sub(r"[\r\n\t]+", "_", name)
    name = re.sub(r"[^A-Za-z0-9._() \-]", "_", name)
    name = re.sub(r"\.{2,}", ".", name)
    name = name.strip(" .")

    if not name:
        name = "document.pdf"

    if len(name) > 160:
        suffix = Path(name).suffix[:12]
        name = name[:160-len(suffix)] + suffix

    return name


def pp12_random_temp_dir(prefix="privatepdf-"):
    """
    Creates an isolated temporary directory.
    """
    return tempfile.mkdtemp(prefix=prefix)


def pp12_validate_pdf_bytes(data: bytes):
    """
    Basic PDF content validation.

    Extension and Content-Type are NOT trusted.
    A valid PDF must contain the PDF magic header.
    """
    if not data:
        raise ValueError("Empty upload.")

    max_bytes = PP_SECURITY_V2_MAX_PDF_MB * 1024 * 1024

    if len(data) > max_bytes:
        raise ValueError(
            f"PDF exceeds the {PP_SECURITY_V2_MAX_PDF_MB} MB limit."
        )

    # PDF header normally begins with %PDF-
    if not data[:1024].startswith(b"%PDF-"):
        # Some PDFs may have a small binary/BOM prefix.
        if b"%PDF-" not in data[:1024]:
            raise ValueError(
                "Uploaded file is not a valid PDF."
            )

    # A PDF should have an EOF marker somewhere near the end.
    tail = data[-8192:]

    if b"%%EOF" not in tail:
        raise ValueError(
            "PDF appears incomplete or malformed."
        )

    return True


def pp12_validate_pdf_document(doc):
    """
    Validate opened PyMuPDF document and enforce resource limits.
    """
    try:
        page_count = int(doc.page_count)
    except Exception:
        raise ValueError("Unable to determine PDF page count.")

    if page_count <= 0:
        raise ValueError("PDF contains no pages.")

    if page_count > PP_SECURITY_V2_MAX_PAGES:
        raise ValueError(
            f"PDF exceeds the {PP_SECURITY_V2_MAX_PAGES} page limit."
        )

    return page_count


def pp12_validate_output_file(path):
    """
    Validate generated PDF before it is returned to the client.
    """
    p = Path(path)

    if not p.exists():
        raise ValueError("Generated output file was not created.")

    size = p.stat().st_size

    if size <= 0:
        raise ValueError("Generated output file is empty.")

    max_bytes = PP_SECURITY_V2_MAX_OUTPUT_MB * 1024 * 1024

    if size > max_bytes:
        raise ValueError(
            "Generated output exceeds the configured size limit."
        )

    with p.open("rb") as f:
        header = f.read(1024)

    if b"%PDF-" not in header:
        raise ValueError(
            "Generated output is not a valid PDF."
        )

    return True


def pp12_secure_cleanup(*paths):
    """
    Best-effort cleanup for temporary files/directories.
    """
    import shutil

    for raw in paths:
        if not raw:
            continue

        try:
            p = Path(raw)

            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)

            elif p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

        except Exception:
            pass


def pp12_validate_office_input(filename: str, data: bytes):
    """
    Conservative Office-file validation.

    This does not execute anything and does not trust Content-Type.
    """
    name = pp12_safe_filename(filename)
    ext = Path(name).suffix.lower()

    allowed = {
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".ods",
        ".odp",
        ".rtf",
        ".txt",
    }

    if ext not in allowed:
        raise ValueError(
            "Unsupported Office document type."
        )

    if not data:
        raise ValueError("Empty Office upload.")

    max_bytes = PP_SECURITY_V2_MAX_PDF_MB * 1024 * 1024

    if len(data) > max_bytes:
        raise ValueError(
            "Office document exceeds the configured upload limit."
        )

    return name, ext


def pp12_validate_image_input(filename: str, data: bytes):
    """
    Conservative image input validation.
    """
    from PIL import Image
    import io

    name = pp12_safe_filename(filename)
    ext = Path(name).suffix.lower()

    allowed = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff",
    }

    if ext not in allowed:
        raise ValueError(
            "Unsupported image type."
        )

    if not data:
        raise ValueError("Empty image upload.")

    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
    except Exception:
        raise ValueError(
            "Uploaded image is invalid or malformed."
        )

    return name, ext


def pp12_validate_text_size(text):
    if text is None:
        return ""

    if len(text) > PP_SECURITY_V2_MAX_TEXT_CHARS:
        raise ValueError(
            "Extracted text exceeds the configured safety limit."
        )

    return text


# ============================================================
# END SECURITY V2
# ============================================================


from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter, Transformation

BASE = Path(__file__).resolve().parent.parent
STATIC = BASE / "static"
JOBS = Path(tempfile.gettempdir()) / "privatepdf_pro_jobs"
JOBS.mkdir(exist_ok=True)


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


_PP_TRUSTED_HOSTS = ["*"]


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


app = FastAPI(title="PrivatePDF Pro", version="1.0.0")

@app.get("/", include_in_schema=False)
async def _serve_root_index():
    static_file = Path(__file__).resolve().parents[1] / "static" / "index.html"
    if static_file.exists():
        return HTMLResponse(content=static_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>PrivatePDF Pro is Live</h1>")



@app.middleware("http")
async def _force_allow_public(request, call_next):
    if request.url.path in ("/", "/favicon.ico", "/robots.txt", "/sitemap.xml") or request.method == "HEAD":
        index_p = Path(__file__).resolve().parents[1] / "static" / "index.html"
        if request.url.path == "/" and index_p.exists():
            return HTMLResponse(content=index_p.read_text(encoding="utf-8"))
    raise HTTPException(status_code=400, detail='Bad Request')


# Security V4.1 generated-output guard
try:
    app.add_middleware(
        PP12V4OutputGuardMiddleware
    )
except Exception:
    pass





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
# V3.1 replaces endpoint wrapping with an ASGI request guard.
PP_SECURITY_V3_WRAPPED_ROUTES = 0




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

            # V3.1 validates multipart uploads before the endpoint.
            # BaseHTTPMiddleware can otherwise consume the request body
            # while parsing request.form(), leaving FastAPI with an empty
            # body and causing "Field required" for UploadFile/Form fields.
            if request.method.upper() == "POST":

                content_type = request.headers.get("content-type", "").lower()

                if "multipart/form-data" in content_type:

                    body = await request.body()

                    async def _pp_replay_receive():
                        return {
                            "type": "http.request",
                            "body": body,
                            "more_body": False,
                        }

                    request._receive = _pp_replay_receive

                    await pp12_validate_request_form_uploads(request)

                    # Restore replay after validation because form parsing
                    # may update Starlette's receive state.
                    request._receive = _pp_replay_receive

            raise HTTPException(status_code=400, detail='Bad Request')

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




# ============================================================

# ============================================================
# PP_SECURITY_HARDENING_V4_1
# Actual LibreOffice process isolation is connected to
# conversion routes.
# ============================================================

PP_SECURITY_HARDENING_V4_1 = True

# PP_SECURITY_HARDENING_V4
# Production Process Isolation + Resource Control
# ============================================================

PP_SECURITY_HARDENING_V4 = True

import time as _pp_v4_time
import tempfile as _pp_v4_tempfile
import shutil as _pp_v4_shutil
import subprocess as _pp_v4_subprocess
import os as _pp_v4_os
from pathlib import Path as _PPV4Path


# ------------------------------------------------------------
# Production resource limits
# ------------------------------------------------------------

PP_PROCESS_TIMEOUT_SECONDS = int(
    _pp_v4_os.getenv("PP_PROCESS_TIMEOUT_SECONDS", "180")
)

PP_OFFICE_TIMEOUT_SECONDS = int(
    _pp_v4_os.getenv("PP_OFFICE_TIMEOUT_SECONDS", "120")
)

PP_MAX_PROCESS_OUTPUT_MB = int(
    _pp_v4_os.getenv("PP_MAX_PROCESS_OUTPUT_MB", "500")
)

PP_MAX_BATCH_FILES = int(
    _pp_v4_os.getenv("PP_MAX_BATCH_FILES", "20")
)

PP_MAX_OPERATION_SECONDS = int(
    _pp_v4_os.getenv("PP_MAX_OPERATION_SECONDS", "300")
)


def pp_v4_secure_temp_dir(prefix="privatepdf_"):
    """
    Create an isolated temporary workspace.

    The directory is outside the static/webroot tree and receives
    a randomized name.
    """
    return _pp_v4_tempfile.mkdtemp(
        prefix=prefix
    )


def pp_v4_cleanup_path(path):
    """
    Best-effort recursive cleanup. Never exposes file contents.
    """
    if not path:
        return

    try:
        p = _PPV4Path(path)

        if p.is_dir():
            _pp_v4_shutil.rmtree(
                p,
                ignore_errors=True
            )
        elif p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    except Exception:
        pass


def pp_v4_validate_output_size(path):
    """
    Prevent unexpectedly huge conversion output.
    """
    try:
        p = _PPV4Path(path)

        if not p.exists():
            raise HTTPException(
                status_code=500,
                detail="Processing did not produce an output file."
            )

        size = p.stat().st_size

        maximum = (
            PP_MAX_PROCESS_OUTPUT_MB
            * 1024
            * 1024
        )

        if size <= 0:
            raise HTTPException(
                status_code=500,
                detail="Processing produced an empty output."
            )

        if size > maximum:
            raise HTTPException(
                status_code=413,
                detail="Generated output exceeds the allowed limit."
            )

        return size

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to validate generated output."
        )



def pp_v4_run_process(
    command,
    *args,
    timeout=None,
    cwd=None,
    env=None,
    **kwargs
):
    """
    Security V4.1 hardened external process runner.

    Designed to safely handle existing subprocess.run-style
    invocation without exposing converter output.
    """

    if timeout is None:
        timeout = PP_PROCESS_TIMEOUT_SECONDS

    # Detect LibreOffice without trusting user-controlled MIME type.
    try:
        command_text = " ".join(
            str(x).lower()
            for x in (
                command
                if isinstance(command, (list, tuple))
                else [command]
            )
        )
    except Exception:
        command_text = ""

    is_office = (
        "libreoffice" in command_text
        or "soffice" in command_text
        or "soffice.exe" in command_text
    )

    isolated_profile = None

    try:

        # ----------------------------------------------------
        # LibreOffice profile isolation
        # ----------------------------------------------------
        if is_office:

            isolated_profile = pp_v4_secure_temp_dir(
                prefix="privatepdf_lo_"
            )

            try:
                profile_uri = (
                    _PPV4Path(isolated_profile)
                    .resolve()
                    .as_uri()
                )

                if isinstance(command, (list, tuple)):

                    command = list(command)

                    if not any(
                        str(x).startswith(
                            "-env:UserInstallation="
                        )
                        for x in command
                    ):
                        command.insert(
                            1,
                            "-env:UserInstallation="
                            + profile_uri
                        )

                    # Safe LibreOffice headless flags.
                    office_flags = [
                        "--headless",
                        "--nologo",
                        "--nodefault",
                        "--nofirststartwizard",
                        "--norestore",
                        "--nolockcheck",
                    ]

                    for flag in office_flags:
                        if flag not in command:
                            command.insert(1, flag)

            except Exception:
                pp_v4_cleanup_path(
                    isolated_profile
                )
                isolated_profile = None

        # ----------------------------------------------------
        # Sanitise caller kwargs.
        #
        # We control process I/O so converter diagnostics
        # cannot accidentally become application output.
        # ----------------------------------------------------

        kwargs.pop("capture_output", None)
        kwargs.pop("stdout", None)
        kwargs.pop("stderr", None)
        kwargs.pop("stdin", None)
        kwargs.pop("input", None)
        kwargs.pop("check", None)
        kwargs.pop("text", None)
        kwargs.pop("encoding", None)
        kwargs.pop("errors", None)

        kwargs["stdout"] = _pp_v4_subprocess.PIPE
        kwargs["stderr"] = _pp_v4_subprocess.PIPE
        kwargs["stdin"] = _pp_v4_subprocess.DEVNULL
        kwargs["shell"] = False

        if cwd is not None:
            kwargs["cwd"] = cwd

        if env is not None:
            kwargs["env"] = env
        elif is_office:
            kwargs["env"] = pp_v4_safe_office_environment()

        started = _pp_v4_time.monotonic()

        completed = _pp_v4_subprocess.run(
            command,
            *args,
            timeout=(
                PP_OFFICE_TIMEOUT_SECONDS
                if is_office
                else timeout
            ),
            **kwargs
        )

        elapsed = (
            _pp_v4_time.monotonic()
            - started
        )

        if elapsed > PP_MAX_OPERATION_SECONDS:
            raise HTTPException(
                status_code=504,
                detail="Document processing exceeded the allowed time."
            )

        if completed.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Office conversion failed."
                    if is_office
                    else "Document processing failed."
                )
            )

        return completed

    except _pp_v4_subprocess.TimeoutExpired:

        # subprocess.run terminates the timed-out child.
        raise HTTPException(
            status_code=504,
            detail=(
                "Office conversion timed out."
                if is_office
                else "Document processing timed out."
            )
        )

    except FileNotFoundError:

        raise HTTPException(
            status_code=503,
            detail=(
                "LibreOffice conversion service is unavailable."
                if is_office
                else "Required document processing service is unavailable."
            )
        )

    except HTTPException:
        raise

    except Exception:

        raise HTTPException(
            status_code=500,
            detail=(
                "Office conversion failed safely."
                if is_office
                else "Document processing failed safely."
            )
        )

    finally:

        if isolated_profile:
            pp_v4_cleanup_path(
                isolated_profile
            )


def pp_v4_safe_office_environment():
    """
    Minimal environment for LibreOffice subprocesses.
    """
    env = dict(_pp_v4_os.environ)

    # Prevent LibreOffice from creating a persistent user profile
    # in the real user's profile directory.
    env.pop("HOME", None)
    env.pop("USERPROFILE", None)

    return env


def pp_v4_cleanup_stale_workspace(root, max_age_seconds=3600):
    """
    Remove only stale directories belonging to this application's
    randomized temporary-workspace prefix.

    This is best-effort and never reads document contents.
    """
    try:
        base = _PPV4Path(root)

        if not base.exists():
            return

        now = _pp_v4_time.time()

        for item in base.iterdir():

            name = item.name

            if not name.startswith("privatepdf_"):
                continue

            try:
                age = now - item.stat().st_mtime

                if age > max_age_seconds:
                    pp_v4_cleanup_path(item)

            except Exception:
                continue

    except Exception:
        pass


def pp_v4_process_timer():
    """
    Lightweight operation timer.
    """
    return _pp_v4_time.monotonic()


def pp_v4_check_operation_time(started):
    elapsed = (
        _pp_v4_time.monotonic()
        - started
    )

    if elapsed > PP_MAX_OPERATION_SECONDS:
        raise HTTPException(
            status_code=504,
            detail="Document processing exceeded the allowed time."
        )

    return elapsed


# ------------------------------------------------------------
# Protect LibreOffice if existing source invokes subprocess.run
# ------------------------------------------------------------

PP_V4_SUBPROCESS_AVAILABLE = True




# ============================================================
# PP12_V4_OUTPUT_GUARD
# Validate FileResponse outputs before they leave the app.
# ============================================================

PP12_V4_OUTPUT_GUARD = True

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    class PP12V4OutputGuardMiddleware(BaseHTTPMiddleware):

        async def dispatch(self, request, call_next):

            response = await call_next(request)

            try:

                response_path = getattr(
                    response,
                    "path",
                    None
                )

                if response_path:

                    path = _PPV4Path(response_path)

                    if path.exists() and path.is_file():

                        # Never allow a generated file above
                        # the configured process-output limit.
                        size = path.stat().st_size

                        maximum = (
                            PP_MAX_PROCESS_OUTPUT_MB
                            * 1024
                            * 1024
                        )

                        if size > maximum:

                            pp_v4_cleanup_path(
                                path
                            )

                            return JSONResponse(
                                status_code=413,
                                content={
                                    "detail":
                                    "Generated output exceeds the allowed limit."
                                }
                            )

            except Exception:
                # Do not crash a valid response because the
                # optional response-path inspection failed.
                pass

            return response

except Exception:

    PP12_V4_OUTPUT_GUARD = False


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

    pass

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


app.mount("/static", StaticFiles(directory=STATIC), name="static")

MAX_FILE_MB = 250


def new_job():
    p = JOBS / uuid.uuid4().hex
    p.mkdir()
    return p


def cleanup(path: Path):
    shutil.rmtree(path, ignore_errors=True)


def safe_name(name: str) -> str:
    return Path(name or "document").name.replace("\x00", "")


async def save_upload(upload: UploadFile, folder: Path, max_mb=MAX_FILE_MB) -> Path:
    name = safe_name(upload.filename)
    target = folder / name
    total = 0
    with target.open("wb") as f:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_mb * 1024 * 1024:
                raise ValueError(f"File exceeds {max_mb} MB limit.")
            f.write(chunk)
    return target


def output_file(job: Path, path: Path, filename: str, media_type: str):
    # FastAPI FileResponse streams the temporary result. A production deployment
    # should use a post-response cleanup worker/container TTL rather than deleting
    # the file before the response is consumed.
    return FileResponse(path, filename=filename, media_type=media_type)


def parse_pages(spec: str, total: int):
    out = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        if re.fullmatch(r"\d+", token):
            n = int(token)
            if 1 <= n <= total:
                out.append(n)
        elif re.fullmatch(r"\d+\s*-\s*\d+", token):
            a, b = map(int, re.split(r"\s*-\s*", token))
            if a > b:
                a, b = b, a
            out.extend(n for n in range(a, b + 1) if 1 <= n <= total)
    return out




# === UPGRADE_12_5_PROFESSIONAL_SHAPES_DRAW_ENGINE_BACKEND ===

# #12.5 intentionally keeps the existing native annotation API.
# Existing /api/annotate already supports native:
#   - draw
#   - arrow
#   - rectangle
#   - ellipse-compatible shape metadata
#
# This layer adds frontend professional shape controls without
# replacing the existing PDF annotation/export pipeline.



# === UPGRADE_12_6_PROFESSIONAL_HISTORY_ENGINE_BACKEND ===

# #12.6 Professional History Engine
#
# History is intentionally maintained in the frontend workspace.
# The PDF backend remains stateless and continues using the existing
# native annotation/export pipeline.
#
# No persistent document database is introduced by this upgrade.

@app.get("/", response_class=HTMLResponse)
def home():
    return (STATIC / "index.html").read_text(encoding="utf-8")



# === UPGRADE_12_1_PROFESSIONAL_ANNOTATION_ENGINE_BACKEND ===
# === UPGRADE_12_2_ANNOTATION_OBJECT_MANAGER_BACKEND ===
# === UPGRADE_12_3_ADVANCED_TEXT_ANNOTATION_ENGINE_BACKEND ===
# === UPGRADE_12_4_PROFESSIONAL_TEXT_MARKUP_ENGINE_BACKEND ===
# Professional text markup editor layer.
# Word geometry is supplied by /api/annotation-page.
# Native PDF markup export remains handled by /api/annotate.
# No persistent document database is introduced.

# Advanced text annotation editor layer.
# Native PDF export remains handled by /api/annotate.
# No persistent document database is introduced.

# Annotation Object Manager is a frontend/editor-layer upgrade.
# Native PDF annotation export remains handled by /api/annotate.
# No persistent document database is introduced.


@app.post("/api/annotation-page")
async def annotation_page(
    file: UploadFile = File(...),
    page_index: int = Form(0),
    dpi: int = Form(160)
):
    import base64

    data = await file.read()

    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {MAX_FILE_MB} MB limit."
        )

    try:
        doc = fitz.open(stream=data, filetype="pdf")

        if page_index < 0 or page_index >= len(doc):
            doc.close()
            raise HTTPException(
                status_code=400,
                detail="Invalid page index."
            )

        dpi = max(96, min(int(dpi), 240))

        page = doc[page_index]
        rect = page.rect

        pix = page.get_pixmap(
            matrix=fitz.Matrix(
                dpi / 72.0,
                dpi / 72.0
            ),
            alpha=False,
            annots=False
        )

        words = []

        try:
            for w in page.get_text("words", sort=True):
                if len(w) < 5:
                    continue

                x0, y0, x1, y1, text = w[:5]

                if not str(text).strip():
                    continue

                words.append({
                    "x": max(
                        0,
                        min(
                            1,
                            x0 / rect.width
                        )
                    ),
                    "y": max(
                        0,
                        min(
                            1,
                            y0 / rect.height
                        )
                    ),
                    "w": max(
                        .0005,
                        min(
                            1,
                            (x1 - x0) / rect.width
                        )
                    ),
                    "h": max(
                        .0005,
                        min(
                            1,
                            (y1 - y0) / rect.height
                        )
                    ),
                    "text": str(text)
                })

        except Exception:
            words = []

        result = {
            "page": page_index,
            "page_count": len(doc),
            "width": rect.width,
            "height": rect.height,
            "pixel_width": pix.width,
            "pixel_height": pix.height,
            "image":
                "data:image/png;base64,"
                + base64.b64encode(
                    pix.tobytes("png")
                ).decode("ascii"),
            "words": words
        }

        doc.close()

        return JSONResponse(result)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not render PDF page: {exc}"
        )


@app.post("/api/annotate")
async def annotate_pdf(
    file: UploadFile = File(...),
    annotations: str = Form(...)
):
    import json
    import math
    import os
    import tempfile

    from starlette.background import BackgroundTask

    data = await file.read()


    # PP_SECURITY_HARDENING_V2_1_ANNOTATE_GUARD

    pp12_validate_pdf_bytes(data)

    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {MAX_FILE_MB} MB limit."
        )

    try:
        items = json.loads(annotations)

        if not isinstance(items, list):
            raise ValueError(
                "Annotation list must be an array."
            )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid annotation data: {exc}"
        )

    src = tempfile.NamedTemporaryFile(
        delete=False,
        suffix='.pdf'
    )

    src.write(data)
    src.close()

    out = src.name + '.annotated.pdf'

    def clean():
        for p in (src.name, out):
            try:
                if os.path.exists(p):
                    os.unlink(p)
            except Exception:
                pass

    try:
        doc = fitz.open(src.name)

        for item in items:

            try:
                pi = int(
                    item.get(
                        'page',
                        -1
                    )
                )
            except Exception:
                continue

            if pi < 0 or pi >= len(doc):
                continue

            page = doc[pi]

            kind = str(
                item.get(
                    'type',
                    ''
                )
            ).lower()

            hx = str(
                item.get(
                    'color',
                    '#ffcc00'
                )
            ).replace('#', '')

            if not re.fullmatch(
                r'[0-9a-fA-F]{6}',
                hx
            ):
                hx = 'ffcc00'

            color = tuple(
                int(hx[i:i + 2], 16) / 255
                for i in (0, 2, 4)
            )

            try:
                opacity = max(
                    .05,
                    min(
                        1,
                        float(
                            item.get(
                                'opacity',
                                .45
                            )
                        )
                    )
                )
            except Exception:
                opacity = .45

            pw = page.rect.width
            ph = page.rect.height

            def norm(v):
                try:
                    v = float(v)
                except Exception:
                    v = 0

                return max(
                    0,
                    min(
                        1,
                        v
                    )
                )

            def pt(x, y):
                return fitz.Point(
                    norm(x) * pw,
                    norm(y) * ph
                )

            x = norm(
                item.get(
                    'x',
                    .1
                )
            )

            y = norm(
                item.get(
                    'y',
                    .1
                )
            )

            w = max(
                .001,
                norm(
                    item.get(
                        'w',
                        .1
                    )
                )
            )

            h = max(
                .001,
                norm(
                    item.get(
                        'h',
                        .05
                    )
                )
            )

            x2 = norm(
                item.get(
                    'x2',
                    x + w
                )
            )

            y2 = norm(
                item.get(
                    'y2',
                    y + h
                )
            )

            rect = fitz.Rect(
                x * pw,
                y * ph,
                min(
                    pw,
                    (x + w) * pw
                ),
                min(
                    ph,
                    (y + h) * ph
                )
            )

            boxes = item.get(
                'boxes'
            )

            if (
                kind in {
                    'highlight',
                    'underline',
                    'strikeout'
                }
                and
                isinstance(
                    boxes,
                    list
                )
                and
                boxes
            ):

                for b in boxes:

                    try:
                        bx = norm(
                            b.get('x')
                        )

                        by = norm(
                            b.get('y')
                        )

                        bw = norm(
                            b.get('w')
                        )

                        bh = norm(
                            b.get('h')
                        )

                        br = fitz.Rect(
                            bx * pw,
                            by * ph,
                            min(
                                pw,
                                (bx + bw) * pw
                            ),
                            min(
                                ph,
                                (by + bh) * ph
                            )
                        )

                        if kind == 'highlight':
                            a = page.add_highlight_annot(br)

                        elif kind == 'underline':
                            a = page.add_underline_annot(br)

                        else:
                            a = page.add_strikeout_annot(br)

                        if a:
                            a.set_colors(
                                stroke=color
                            )

                            a.set_opacity(
                                opacity
                            )

                            a.update()

                    except Exception:
                        pass

                continue

            if kind == 'text':

                text = str(
                    item.get(
                        'text',
                        ''
                    )
                )[:4000]

                if not text.strip():
                    continue

                try:
                    size = max(
                        6,
                        min(
                            96,
                            float(
                                item.get(
                                    'size',
                                    18
                                )
                            )
                        )
                    )
                except Exception:
                    size = 18

                try:
                    page.insert_textbox(
                        rect,
                        text,
                        fontsize=size,
                        color=color,
                        fontname='helv',
                        align=0,
                        overlay=True
                    )
                except Exception:
                    page.insert_text(
                        pt(x, y),
                        text,
                        fontsize=size,
                        color=color,
                        overlay=True
                    )

            elif kind in {
                'highlight',
                'underline',
                'strikeout'
            }:

                if kind == 'highlight':
                    a = page.add_highlight_annot(
                        rect
                    )

                elif kind == 'underline':
                    a = page.add_underline_annot(
                        rect
                    )

                else:
                    a = page.add_strikeout_annot(
                        rect
                    )

                if a:
                    a.set_colors(
                        stroke=color
                    )

                    a.set_opacity(
                        opacity
                    )

                    a.update()

            elif kind == 'rectangle':

                try:
                    stroke = max(
                        .5,
                        min(
                            15,
                            float(
                                item.get(
                                    'stroke',
                                    3
                                )
                            )
                        )
                    )
                except Exception:
                    stroke = 3

                s = page.new_shape()

                s.draw_rect(
                    rect
                )

                s.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity
                )

                s.commit()

            elif kind == 'arrow':

                p1 = pt(x, y)
                p2 = pt(x2, y2)

                try:
                    stroke = max(
                        .5,
                        min(
                            15,
                            float(
                                item.get(
                                    'stroke',
                                    3
                                )
                            )
                        )
                    )
                except Exception:
                    stroke = 3

                s = page.new_shape()

                s.draw_line(
                    p1,
                    p2
                )

                s.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity
                )

                s.commit()

                ang = math.atan2(
                    p2.y - p1.y,
                    p2.x - p1.x
                )

                head = max(
                    7,
                    min(
                        24,
                        4 * stroke
                    )
                )

                left = fitz.Point(
                    p2.x +
                    head *
                    math.cos(
                        ang - math.pi * .82
                    ),
                    p2.y +
                    head *
                    math.sin(
                        ang - math.pi * .82
                    )
                )

                right = fitz.Point(
                    p2.x +
                    head *
                    math.cos(
                        ang + math.pi * .82
                    ),
                    p2.y +
                    head *
                    math.sin(
                        ang + math.pi * .82
                    )
                )

                s = page.new_shape()

                s.draw_line(
                    p2,
                    left
                )

                s.draw_line(
                    p2,
                    right
                )

                s.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity
                )

                s.commit()

            elif kind == 'draw':

                pts = item.get(
                    'points'
                )

                if (
                    not isinstance(
                        pts,
                        list
                    )
                    or
                    len(pts) < 2
                ):
                    continue

                try:
                    stroke = max(
                        .5,
                        min(
                            15,
                            float(
                                item.get(
                                    'stroke',
                                    3
                                )
                            )
                        )
                    )
                except Exception:
                    stroke = 3

                s = page.new_shape()

                pnts = [
                    pt(
                        q.get(
                            'x',
                            0
                        ),
                        q.get(
                            'y',
                            0
                        )
                    )
                    for q in pts
                    if isinstance(
                        q,
                        dict
                    )
                ]

                for a, b in zip(
                    pnts,
                    pnts[1:]
                ):
                    s.draw_line(
                        a,
                        b
                    )

                s.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity,
                    lineCap=1,
                    lineJoin=1
                )

                s.commit()

        doc.save(
            out,
            garbage=4,
            deflate=True,
            clean=True
        )

        doc.close()

        return FileResponse(
            out,
            filename='Annotated_PDF.pdf',
            media_type='application/pdf',
            background=BackgroundTask(clean)
        )

    except Exception as exc:
        clean()

        raise HTTPException(
            status_code=400,
            detail=f"Annotation export failed: {exc}"
        )

@app.post("/api/merge")
async def merge(files: List[UploadFile] = File(...)):
    job = new_job()
    try:
        writer = PdfWriter()
        for u in files:
            p = await save_upload(u, job)
            writer.append(str(p))
        out = job / "merged.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Merged.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/pages")
async def page_operation(
    file: UploadFile = File(...),
    action: str = Form(...),
    pages: str = Form(...)
):
    job = new_job()
    try:
        src = await save_upload(file, job)
        reader = PdfReader(str(src))
        selected = parse_pages(pages, len(reader.pages))
        if not selected:
            raise ValueError("No valid pages selected.")

        writer = PdfWriter()
        if action == "extract":
            for n in selected:
                writer.add_page(reader.pages[n - 1])
        elif action == "delete":
            s = set(selected)
            for n, page in enumerate(reader.pages, 1):
                if n not in s:
                    writer.add_page(page)
        elif action == "reorder":
            for n in selected:
                writer.add_page(reader.pages[n - 1])
        else:
            raise ValueError("Unsupported page action.")

        out = job / "result.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Pages_Result.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/rotate")
async def rotate(file: UploadFile = File(...), degrees: int = Form(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        d = degrees % 360
        if d % 90:
            raise ValueError("Rotation must be 0, 90, 180 or 270 degrees.")
        reader = PdfReader(str(src))
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate(d)
            writer.add_page(page)
        out = job / "rotated.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Rotated.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/compress")
async def compress(file: UploadFile = File(...), dpi: int = Form(110), quality: int = Form(70)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        dpi = max(60, min(dpi, 220))
        quality = max(25, min(quality, 95))
        # Rebuild pages and downsample embedded raster images.
        for page in doc:
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.width > 1400 or pix.height > 1400:
                        scale = min(1.0, (dpi / 72.0) * 0.75)
                        nw = max(1, int(pix.width * scale))
                        nh = max(1, int(pix.height * scale))
                        small = fitz.Pixmap(pix, 0) if pix.alpha else pix
                        if small.width != nw or small.height != nh:
                            resized = fitz.Pixmap(small, fitz.Matrix(nw / small.width, nh / small.height))
                            doc.update_stream(xref, resized.tobytes("jpeg", jpg_quality=quality))
                except Exception:
                    pass
        out = job / "compressed.pdf"
        doc.save(str(out), garbage=4, deflate=True, clean=True)
        doc.close()
        return output_file(job, out, "Compressed.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, f"Compression failed: {e}")


@app.post("/api/resize")
async def resize_pdf(file: UploadFile = File(...), size: str = Form("A4"), orientation: str = Form("portrait")):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        sizes = {
            "A4": (595.276, 841.89),
            "A3": (841.89, 1190.55),
            "Letter": (612, 792),
            "Legal": (612, 1008),
        }
        w, h = sizes.get(size, sizes["A4"])
        if orientation == "landscape":
            w, h = h, w
        outdoc = fitz.open()
        for page in doc:
            newp = outdoc.new_page(width=w, height=h)
            src_rect = page.rect
            scale = min(w / src_rect.width, h / src_rect.height)
            nw, nh = src_rect.width * scale, src_rect.height * scale
            x, y = (w - nw) / 2, (h - nh) / 2
            newp.show_pdf_page(fitz.Rect(x, y, x + nw, y + nh), doc, page.number)
        out = job / "resized.pdf"
        outdoc.save(str(out))
        outdoc.close()
        doc.close()
        return output_file(job, out, "Resized.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, f"Resize failed: {e}")


@app.post("/api/crop")
async def crop_pdf(file: UploadFile = File(...), margin: float = Form(20)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        m = max(0, min(float(margin), 300))
        for page in doc:
            r = page.rect
            page.set_cropbox(fitz.Rect(r.x0 + m, r.y0 + m, r.x1 - m, r.y1 - m))
        out = job / "cropped.pdf"
        doc.save(str(out))
        doc.close()
        return output_file(job, out, "Cropped.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, f"Crop failed: {e}")


@app.post("/api/numbers")
async def numbers(file: UploadFile = File(...), start: int = Form(1)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        for i, page in enumerate(doc, start):
            r = page.rect
            text = str(i)
            page.insert_text((r.width / 2 - 5, r.height - 24), text, fontsize=9)
        out = job / "numbered.pdf"
        doc.save(str(out))
        doc.close()
        return output_file(job, out, "Numbered.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, f"Numbering failed: {e}")


def _font_path(bold=False, italic=False):
    candidates = []
    if os.name == "nt":
        root = Path(os.environ.get("WINDIR", r"C:\\Windows")) / "Fonts"
        candidates += [root / ("arialbd.ttf" if bold else "arial.ttf"), root / ("arialbi.ttf" if bold and italic else "ariali.ttf")]
    candidates += [Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") if bold else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    return next((str(x) for x in candidates if x.exists()), None)

@app.post("/api/watermark")
async def watermark(
    file: UploadFile = File(...), text: str = Form(...), opacity: float = Form(0.25), size: int = Form(42),
    angle: int = Form(45), color: str = Form("#777777"), position: str = Form("center"),
    tiled: bool = Form(False), bold: bool = Form(False), outline: bool = Form(False),
):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        opacity = max(0.05, min(float(opacity), 1.0)); size = max(8, min(int(size), 160)); angle = int(angle) % 360
        if not text.strip(): raise ValueError("Watermark text is required.")
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color): color = "#777777"
        rgb = tuple(int(color[i:i+2],16)/255 for i in (1,3,5))
        font_path = _font_path(bold=bold)
        for page in doc:
            r=page.rect
            if tiled:
                step_x=max(150,size*5); step_y=max(110,size*3)
                positions=[(x,y) for y in range(int(size), int(r.height)+step_y, step_y) for x in range(int(size), int(r.width)+step_x, step_x)]
            else:
                anchors={"top-left":(r.width*.08,r.height*.12),"top-center":(r.width*.5,r.height*.12),"top-right":(r.width*.92,r.height*.12),"center-left":(r.width*.12,r.height*.5),"center":(r.width*.5,r.height*.5),"center-right":(r.width*.88,r.height*.5),"bottom-left":(r.width*.08,r.height*.88),"bottom-center":(r.width*.5,r.height*.88),"bottom-right":(r.width*.92,r.height*.88)}
                positions=[anchors.get(position, anchors["center"])]
            # Use a transparent PIL canvas so arbitrary angles and styling work consistently.
            font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
            bbox=font.getbbox(text); tw=max(1,bbox[2]-bbox[0]+size); th=max(1,bbox[3]-bbox[1]+size)
            canvas=Image.new("RGBA",(tw*2,th*2),(255,255,255,0)); d=ImageDraw.Draw(canvas)
            fill=tuple(int(c*255) for c in rgb)+(int(opacity*255),)
            xy=(tw//2,th//2)
            if outline:
                d.text(xy,text,font=font,fill=fill,anchor="mm",stroke_width=max(1,size//30),stroke_fill=(255,255,255,int(opacity*180)))
            else: d.text(xy,text,font=font,fill=fill,anchor="mm")
            canvas=canvas.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC)
            buf=io.BytesIO(); canvas.save(buf,format="PNG")
            iw,ih=canvas.size
            for x,y in positions:
                x0=x-iw/2; y0=y-ih/2
                page.insert_image(fitz.Rect(x0,y0,x0+iw,y0+ih),stream=buf.getvalue(),overlay=True)
        out=job/"watermarked.pdf"; doc.save(str(out),garbage=4,deflate=True,clean=True); doc.close()
        return output_file(job,out,"Watermarked.pdf","application/pdf")
    except Exception as e:
        cleanup(job); raise HTTPException(400,f"Watermark failed: {e}")

@app.post("/api/protect")
async def protect(file: UploadFile = File(...), password: str = Form(...)):
    job = new_job()
    try:
        if not password:
            raise ValueError("Password required.")
        src = await save_upload(file, job)
        reader = PdfReader(str(src))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        out = job / "protected.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Protected.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/unlock")
async def unlock(file: UploadFile = File(...), password: str = Form(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        reader = PdfReader(str(src))
        if reader.is_encrypted and not reader.decrypt(password):
            raise ValueError("Incorrect password or unsupported encryption.")
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        out = job / "unlocked.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Unlocked.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/metadata")
async def metadata(file: UploadFile = File(...), mode: str = Form("remove")):
    job = new_job()
    try:
        src = await save_upload(file, job)
        reader = PdfReader(str(src))
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)
        if mode == "remove":
            writer.add_metadata({})
        elif mode == "set":
            writer.add_metadata({
                "/Title": "PrivatePDF Document",
                "/Author": "PrivatePDF Pro",
                "/Creator": "PrivatePDF Pro",
            })
        out = job / "metadata.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Metadata_Result.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/grayscale")
async def grayscale(file: UploadFile = File(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        srcdoc = fitz.open(str(src))
        outdoc = fitz.open()
        for page in srcdoc:
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), colorspace=fitz.csGRAY, alpha=False)
            newp = outdoc.new_page(width=page.rect.width, height=page.rect.height)
            newp.insert_image(newp.rect, stream=pix.tobytes("png"))
        out = job / "grayscale.pdf"
        outdoc.save(str(out), garbage=4, deflate=True, clean=True)
        outdoc.close(); srcdoc.close()
        return output_file(job, out, "Grayscale.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, f"Grayscale conversion failed: {e}")

@app.post("/api/text")
async def pdf_text(file: UploadFile = File(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        text = "\n\n".join(page.get_text() for page in doc)
        out = job / "extracted.txt"
        out.write_text(text, encoding="utf-8")
        doc.close()
        return output_file(job, out, "Extracted_Text.txt", "text/plain")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/markdown")
async def pdf_markdown(file: UploadFile = File(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        chunks = []
        for i, page in enumerate(doc, 1):
            text = page.get_text("text").strip()
            chunks.append(f"## Page {i}\n\n{text}" if text else f"## Page {i}\n\n")
        out = job / "document.md"
        out.write_text("\n\n".join(chunks), encoding="utf-8")
        doc.close()
        return output_file(job, out, "Document.md", "text/markdown")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/pdf-to-jpg")
async def pdf_to_jpg(file: UploadFile = File(...), fmt: str = Form("jpg")):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        outdir = job / "images"
        outdir.mkdir()
        for i, page in enumerate(doc, 1):
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            pix.save(str(outdir / f"page-{i}.{fmt}"))
        doc.close()
        archive = shutil.make_archive(str(job / "PDF_Images"), "zip", outdir)
        return output_file(job, Path(archive), "PDF_Images.zip", "application/zip")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/images-to-pdf")
async def images_to_pdf(files: List[UploadFile] = File(...)):
    job = new_job()
    try:
        outdoc = fitz.open()
        for u in files:
            p = await save_upload(u, job)
            img = Image.open(p).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            page = outdoc.new_page(width=img.width, height=img.height)
            page.insert_image(page.rect, stream=buf.getvalue())
        out = job / "images.pdf"
        outdoc.save(str(out))
        outdoc.close()
        return output_file(job, out, "Images_to_PDF.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


def libreoffice_path():
    candidates = [
        "libreoffice", "soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for c in candidates:
        if os.path.isabs(c) and Path(c).exists():
            return c
        if shutil.which(c):
            return c
    return None


@app.post("/api/office-to-pdf")
async def office_to_pdf(file: UploadFile = File(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        lo = libreoffice_path()
        if not lo:
            raise ValueError("LibreOffice is not installed. Install LibreOffice to enable Word/Excel/PPT → PDF.")
        pp_v4_run_process([lo, "--headless", "--convert-to", "pdf", "--outdir", str(job), str(src)],
                       check=True, capture_output=True, timeout=120)
        out = job / (src.stem + ".pdf")
        if not out.exists():
            raise ValueError("LibreOffice conversion did not create a PDF.")
        return output_file(job, out, out.name, "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/pdf-to-office")
async def pdf_to_office(file: UploadFile = File(...), kind: str = Form("docx")):
    job = new_job()
    try:
        src = await save_upload(file, job)
        lo = libreoffice_path()
        if not lo:
            raise ValueError("LibreOffice is not installed. Install LibreOffice for office conversion.")
        # LibreOffice PDF import support varies. This endpoint is intentionally
        # labelled beta; quality depends on the source PDF and installed filters.
        target = {"docx": "docx", "xlsx": "xlsx", "pptx": "pptx"}.get(kind)
        if not target:
            raise ValueError("Unsupported office format.")
        pp_v4_run_process([lo, "--headless", "--convert-to", target, "--outdir", str(job), str(src)],
                       check=True, capture_output=True, timeout=120)
        out = job / (src.stem + "." + target)
        if not out.exists():
            raise ValueError("Conversion is not supported by this LibreOffice build for this PDF.")
        media = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }[target]
        return output_file(job, out, out.name, media)
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


# Cleanup old temporary jobs on startup. Production should also use a scheduled
# TTL worker/container cleanup.
@app.on_event("startup")
def cleanup_old_jobs():
    for p in JOBS.iterdir():
        if p.is_dir():
            try:
                cleanup(p)
            except Exception:
                pass

# ============================================================
# IMAGE STUDIO - ADVANCED IMAGE RESIZER
# ============================================================

@app.post("/api/image-resize")
async def image_resize(
    files: List[UploadFile] = File(...),
    mode: str = Form("pixels"),
    width: int = Form(1920),
    height: int = Form(1080),
    percent: float = Form(100),
    fit: str = Form("contain"),
    crop: bool = Form(False),
    quality: int = Form(90),
    output_format: str = Form("original"),
    dpi: int = Form(96),
    background: str = Form("#ffffff"),
    no_enlarge: bool = Form(False),
    target_kb: int = Form(0),
):
    from zipfile import ZipFile, ZIP_DEFLATED

    if not files:
        raise HTTPException(400, "No images selected.")

    mode = mode.lower().strip()
    fit = fit.lower().strip()
    output_format = output_format.lower().strip()

    if mode not in {"pixels", "percent"}:
        raise HTTPException(400, "Invalid resize mode.")

    if fit not in {"contain", "cover", "stretch"}:
        raise HTTPException(400, "Invalid fit mode.")

    if output_format not in {"original", "jpg", "png", "webp"}:
        raise HTTPException(400, "Invalid output format.")

    width = max(1, min(int(width), 12000))
    height = max(1, min(int(height), 12000))
    percent = max(1, min(float(percent), 1000))
    quality = max(10, min(int(quality), 100))
    dpi = max(1, min(int(dpi), 1200))
    target_kb = max(0, min(int(target_kb), 50000))

    job = new_job()
    generated = []

    def parse_background(value):
        value = (value or "#ffffff").strip().lstrip("#")

        if len(value) != 6:
            return (255, 255, 255, 255)

        try:
            return (
                int(value[0:2], 16),
                int(value[2:4], 16),
                int(value[4:6], 16),
                255,
            )
        except ValueError:
            return (255, 255, 255, 255)

    bg = parse_background(background)

    def make_result(img, tw, th, fit_mode):
        img = img.convert("RGBA")

        if fit_mode == "stretch":
            return img.resize(
                (tw, th),
                Image.Resampling.LANCZOS
            )

        if fit_mode == "cover":
            ratio = max(
                tw / img.width,
                th / img.height
            )

            nw = max(1, round(img.width * ratio))
            nh = max(1, round(img.height * ratio))

            resized = img.resize(
                (nw, nh),
                Image.Resampling.LANCZOS
            )

            left = max(0, (nw - tw) // 2)
            top = max(0, (nh - th) // 2)

            return resized.crop(
                (left, top, left + tw, top + th)
            )

        ratio = min(
            tw / img.width,
            th / img.height
        )

        nw = max(1, round(img.width * ratio))
        nh = max(1, round(img.height * ratio))

        resized = img.resize(
            (nw, nh),
            Image.Resampling.LANCZOS
        )

        canvas = Image.new(
            "RGBA",
            (tw, th),
            bg
        )

        canvas.alpha_composite(
            resized,
            (
                (tw - nw) // 2,
                (th - nh) // 2
            )
        )

        return canvas

    def get_extension(fmt, original):
        if fmt == "jpg":
            return ".jpg"

        if fmt == "png":
            return ".png"

        if fmt == "webp":
            return ".webp"

        ext = Path(original).suffix.lower()

        if ext in {".jpg", ".jpeg"}:
            return ".jpg"

        if ext == ".png":
            return ".png"

        if ext == ".webp":
            return ".webp"

        return ".png"

    try:
        for index, upload in enumerate(files, start=1):

            raw = await upload.read()

            if not raw:
                continue

            if len(raw) > MAX_FILE_MB * 1024 * 1024:
                raise HTTPException(
                    413,
                    f"{upload.filename}: file is too large."
                )

            try:
                src = Image.open(
                    io.BytesIO(raw)
                )
                src.load()
            except Exception:
                raise HTTPException(
                    400,
                    f"{upload.filename}: unsupported or invalid image."
                )

            original_w, original_h = src.size

            # ----------------------------------------
            # Calculate target dimensions
            # ----------------------------------------

            if mode == "percent":

                factor = percent / 100.0

                target_w = max(
                    1,
                    round(original_w * factor)
                )

                target_h = max(
                    1,
                    round(original_h * factor)
                )

            else:

                target_w = width
                target_h = height

                if fit == "contain":

                    ratio = min(
                        target_w / original_w,
                        target_h / original_h
                    )

                    if no_enlarge:
                        ratio = min(ratio, 1.0)

                    target_w = max(
                        1,
                        round(original_w * ratio)
                    )

                    target_h = max(
                        1,
                        round(original_h * ratio)
                    )

                elif fit == "cover":

                    if no_enlarge:
                        ratio = min(
                            max(
                                target_w / original_w,
                                target_h / original_h
                            ),
                            1.0
                        )

                        target_w = max(
                            1,
                            round(original_w * ratio)
                        )

                        target_h = max(
                            1,
                            round(original_h * ratio)
                        )

                else:

                    if no_enlarge:
                        target_w = min(
                            target_w,
                            original_w
                        )

                        target_h = min(
                            target_h,
                            original_h
                        )

            if no_enlarge and mode == "percent":

                target_w = min(
                    target_w,
                    original_w
                )

                target_h = min(
                    target_h,
                    original_h
                )

            # ----------------------------------------
            # Crop / Fit
            # ----------------------------------------

            actual_fit = "cover" if crop else fit

            result = make_result(
                src,
                target_w,
                target_h,
                actual_fit
            )

            # ----------------------------------------
            # Output format
            # ----------------------------------------

            ext = get_extension(
                output_format,
                upload.filename or ""
            )

            stem = safe_name(
                Path(
                    upload.filename or f"image_{index}"
                ).stem
            )

            if not stem:
                stem = f"image_{index}"

            out = (
                job /
                f"{stem}_resized{ext}"
            )

            # ----------------------------------------
            # Save
            # ----------------------------------------

            if ext == ".jpg":

                result.convert("RGB").save(
                    out,
                    "JPEG",
                    quality=quality,
                    optimize=True,
                    dpi=(dpi, dpi)
                )

            elif ext == ".webp":

                result.save(
                    out,
                    "WEBP",
                    quality=quality,
                    method=6
                )

            else:

                result.save(
                    out,
                    "PNG",
                    optimize=True,
                    dpi=(dpi, dpi)
                )

            # ----------------------------------------
            # Best-effort target KB
            # ----------------------------------------

            if (
                target_kb > 0
                and ext in {".jpg", ".webp"}
                and out.stat().st_size > target_kb * 1024
            ):

                target_bytes = target_kb * 1024
                best = None

                for q in range(
                    quality,
                    9,
                    -5
                ):

                    if ext == ".jpg":

                        result.convert("RGB").save(
                            out,
                            "JPEG",
                            quality=q,
                            optimize=True,
                            dpi=(dpi, dpi)
                        )

                    else:

                        result.save(
                            out,
                            "WEBP",
                            quality=q,
                            method=6
                        )

                    if out.stat().st_size <= target_bytes:

                        best = out.read_bytes()
                        break

                if best is not None:
                    out.write_bytes(best)

            generated.append(out)

        if not generated:

            raise HTTPException(
                400,
                "No valid images processed."
            )

        # ----------------------------------------
        # Single image
        # ----------------------------------------

        if len(generated) == 1:

            return output_file(
                job,
                generated[0],
                generated[0].name,
                "image/" + (
                    "jpeg"
                    if generated[0].suffix == ".jpg"
                    else generated[0].suffix.lstrip(".")
                )
            )

        # ----------------------------------------
        # Multiple images → ZIP
        # ----------------------------------------

        zip_path = job / "Resized_Images.zip"

        with ZipFile(
            zip_path,
            "w",
            ZIP_DEFLATED
        ) as archive:

            for item in generated:

                archive.write(
                    item,
                    arcname=item.name
                )

        return output_file(
            job,
            zip_path,
            "Resized_Images.zip",
            "application/zip"
        )

    except HTTPException:
        cleanup(job)
        raise

    except Exception as e:

        cleanup(job)

        raise HTTPException(
            400,
            f"Image resize failed: {e}"
        )


# === UPGRADE_4_VISUAL_PAGE_MANAGER_BACKEND ===

import base64 as _pp4_base64
import io as _pp4_io


def _pp4_parse_pages(spec: str, total: int):
    """Parse page specifications such as 1,3,5-8."""
    if not spec:
        raise HTTPException(status_code=400, detail="Page selection is required")

    pages = []
    seen = set()

    for raw in spec.split(","):
        raw = raw.strip()

        if not raw:
            continue

        if "-" in raw:
            parts = raw.split("-", 1)

            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid page range: {raw}"
                )

            if start > end:
                start, end = end, start

            values = range(start, end + 1)

        else:
            try:
                values = [int(raw)]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid page number: {raw}"
                )

        for page_no in values:
            if page_no < 1 or page_no > total:
                raise HTTPException(
                    status_code=400,
                    detail=f"Page {page_no} is outside the PDF range 1-{total}"
                )

            if page_no not in seen:
                seen.add(page_no)
                pages.append(page_no)

    if not pages:
        raise HTTPException(
            status_code=400,
            detail="No valid pages were selected"
        )

    return pages


@app.post("/api/page-thumbnails")
async def pp4_page_thumbnails(
    file: UploadFile = File(...),
    max_pages: int = Form(120),
    thumb_width: int = Form(220),
    quality: int = Form(72),
):
    """
    Generate lightweight JPEG thumbnails for the visual page manager.
    Processing is temporary and nothing is stored in a persistent DB.
    """

    try:
        data = await file.read()

        if not data:
            raise HTTPException(status_code=400, detail="Empty PDF")

        max_bytes = MAX_FILE_MB * 1024 * 1024

        if len(data) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"PDF exceeds the {MAX_FILE_MB} MB limit"
            )

        max_pages = max(1, min(int(max_pages), 250))
        thumb_width = max(100, min(int(thumb_width), 500))
        quality = max(35, min(int(quality), 90))

        doc = fitz.open(stream=data, filetype="pdf")

        total_pages = len(doc)
        render_count = min(total_pages, max_pages)

        pages = []

        for index in range(render_count):

            page = doc.load_page(index)

            rect = page.rect

            if rect.width <= 0:
                scale = 1.0
            else:
                scale = thumb_width / float(rect.width)

            scale = max(0.08, min(scale, 1.5))

            matrix = fitz.Matrix(scale, scale)

            pix = page.get_pixmap(
                matrix=matrix,
                alpha=False
            )

            jpeg_bytes = pix.tobytes(
                "jpeg",
                jpg_quality=quality
            )

            encoded = _pp4_base64.b64encode(
                jpeg_bytes
            ).decode("ascii")

            pages.append({
                "page": index + 1,
                "width": int(pix.width),
                "height": int(pix.height),
                "data": "data:image/jpeg;base64," + encoded
            })

        doc.close()

        return {
            "total_pages": total_pages,
            "rendered_pages": render_count,
            "truncated": total_pages > render_count,
            "pages": pages
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate page thumbnails: {exc}"
        )


@app.post("/api/rotate-pages")
async def pp4_rotate_selected_pages(
    file: UploadFile = File(...),
    pages: str = Form(...),
    degrees: int = Form(...),
):
    """
    Rotate only the selected PDF pages.
    Authorized/local files only.
    """

    try:
        data = await file.read()

        if not data:
            raise HTTPException(
                status_code=400,
                detail="Empty PDF"
            )

        degrees = int(degrees)

        if degrees not in (-270, -180, -90, 90, 180, 270):
            raise HTTPException(
                status_code=400,
                detail="Rotation must be 90, 180, 270, -90, -180 or -270 degrees"
            )

        reader = PdfReader(_pp4_io.BytesIO(data))

        total = len(reader.pages)

        selected = _pp4_parse_pages(
            pages,
            total
        )

        normalized = degrees % 360

        writer = PdfWriter()

        selected_set = set(selected)

        for index, page in enumerate(reader.pages, start=1):

            if index in selected_set:
                page.rotate(normalized)

            writer.add_page(page)

        output = _pp4_io.BytesIO()

        writer.write(output)

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="Rotated_Selected_Pages.pdf"'
            }
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to rotate selected pages: {exc}"
        )


# === UPGRADE_4_STREAMING_RESPONSE_IMPORT_FIX ===
try:
    StreamingResponse
except NameError:
    from fastapi.responses import StreamingResponse



# === UPGRADE_5_BATCH_PROCESSING_CENTER_BACKEND ===

@app.post("/api/batch-process")
async def pp5_batch_process(
    files: list[UploadFile] = File(...),
    operation: str = Form(...),
    pages: str = Form(""),
    degrees: int = Form(90),
):
    """
    Professional temporary batch processor.

    Supported operations:
      - rotate
      - extract
      - delete
      - reorder
      - compress

    All input/output files exist only for the duration of processing.
    No persistent document database is used.
    """

    import io as _pp5_io
    import re as _pp5_re
    import zipfile as _pp5_zip

    if not files:
        raise HTTPException(
            status_code=400,
            detail="At least one PDF is required"
        )

    allowed_operations = {
        "rotate",
        "extract",
        "delete",
        "reorder",
        "compress",
    }

    operation = (operation or "").strip().lower()

    if operation not in allowed_operations:
        raise HTTPException(
            status_code=400,
            detail="Unsupported batch operation"
        )

    if len(files) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 PDFs can be processed in one batch"
        )

    total_input_bytes = 0
    payloads = []

    max_bytes = MAX_FILE_MB * 1024 * 1024

    for upload in files:

        name = upload.filename or "document.pdf"

        if not name.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files are supported: {name}"
            )

        data = await upload.read()

        if not data:
            raise HTTPException(
                status_code=400,
                detail=f"Empty PDF: {name}"
            )

        if len(data) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"{name} exceeds the {MAX_FILE_MB} MB limit"
            )

        total_input_bytes += len(data)

        if total_input_bytes > max_bytes * 10:
            raise HTTPException(
                status_code=413,
                detail=f"Batch exceeds the {MAX_FILE_MB * 10} MB total limit"
            )

        payloads.append((name, data))

    # Validate rotation.
    if operation == "rotate":

        try:
            degrees_value = int(degrees)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid rotation angle"
            )

        if degrees_value not in (-270, -180, -90, 90, 180, 270):
            raise HTTPException(
                status_code=400,
                detail="Rotation must be 90, 180, 270, -90, -180 or -270"
            )

    # --------------------------------------------------------
    # Process each file
    # --------------------------------------------------------

    zip_buffer = _pp5_io.BytesIO()

    used_names = set()

    with _pp5_zip.ZipFile(
        zip_buffer,
        mode="w",
        compression=_pp5_zip.ZIP_DEFLATED
    ) as archive:

        for position, (original_name, data) in enumerate(
            payloads,
            start=1
        ):

            try:

                reader = PdfReader(
                    _pp5_io.BytesIO(data)
                )

                total_pages = len(reader.pages)

                safe_base = _pp5_re.sub(
                    r"[^A-Za-z0-9._-]+",
                    "_",
                    original_name
                )

                if safe_base.lower().endswith(".pdf"):
                    safe_base = safe_base[:-4]

                safe_base = safe_base.strip("._- ") or (
                    f"document_{position}"
                )

                if operation in ("extract", "delete", "reorder", "rotate"):

                    if operation == "reorder":

                        selected = _pp4_parse_pages(
                            pages,
                            total_pages
                        )

                        if not selected:
                            raise HTTPException(
                                status_code=400,
                                detail="No page order supplied"
                            )

                        writer = PdfWriter()

                        for page_number in selected:
                            writer.add_page(
                                reader.pages[page_number - 1]
                            )

                        output = _pp5_io.BytesIO()
                        writer.write(output)
                        output_data = output.getvalue()

                        output_name = (
                            safe_base +
                            "_reordered.pdf"
                        )

                    elif operation == "extract":

                        selected = _pp4_parse_pages(
                            pages,
                            total_pages
                        )

                        writer = PdfWriter()

                        for page_number in selected:
                            writer.add_page(
                                reader.pages[page_number - 1]
                            )

                        output = _pp5_io.BytesIO()
                        writer.write(output)
                        output_data = output.getvalue()

                        output_name = (
                            safe_base +
                            "_extracted.pdf"
                        )

                    elif operation == "delete":

                        selected = _pp4_parse_pages(
                            pages,
                            total_pages
                        )

                        selected_set = set(selected)

                        if len(selected_set) >= total_pages:
                            raise HTTPException(
                                status_code=400,
                                detail=(
                                    "Cannot delete every page from "
                                    + original_name
                                )
                            )

                        writer = PdfWriter()

                        for page_number, page in enumerate(
                            reader.pages,
                            start=1
                        ):
                            if page_number not in selected_set:
                                writer.add_page(page)

                        output = _pp5_io.BytesIO()
                        writer.write(output)
                        output_data = output.getvalue()

                        output_name = (
                            safe_base +
                            "_deleted.pdf"
                        )

                    else:
                        # rotate
                        selected = _pp4_parse_pages(
                            pages,
                            total_pages
                        )

                        selected_set = set(selected)

                        normalized = degrees_value % 360

                        writer = PdfWriter()

                        for page_number, page in enumerate(
                            reader.pages,
                            start=1
                        ):

                            if page_number in selected_set:
                                page.rotate(normalized)

                            writer.add_page(page)

                        output = _pp5_io.BytesIO()
                        writer.write(output)
                        output_data = output.getvalue()

                        output_name = (
                            safe_base +
                            f"_rotated_{degrees_value}.pdf"
                        )

                else:
                    # ------------------------------------------------
                    # Structural PDF compression.
                    # This does not rasterize pages and preserves
                    # selectable text/vector content.
                    # ------------------------------------------------

                    doc = fitz.open(
                        stream=data,
                        filetype="pdf"
                    )

                    output = _pp5_io.BytesIO()

                    doc.save(
                        output,
                        garbage=4,
                        deflate=True,
                        clean=True
                    )

                    doc.close()

                    output_data = output.getvalue()

                    output_name = (
                        safe_base +
                        "_compressed.pdf"
                    )

                # Prevent duplicate filenames inside ZIP.
                candidate = output_name
                counter = 2

                while candidate.lower() in used_names:

                    stem = output_name[:-4]

                    candidate = (
                        stem +
                        f"_{counter}.pdf"
                    )

                    counter += 1

                used_names.add(candidate.lower())

                archive.writestr(
                    candidate,
                    output_data
                )

            except HTTPException:
                raise

            except Exception as exc:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Batch processing failed for "
                        f"{original_name}: {exc}"
                    )
                )

    zip_buffer.seek(0)

    zip_bytes = zip_buffer.getvalue()

    if not zip_bytes:
        raise HTTPException(
            status_code=500,
            detail="Batch ZIP generation produced an empty response"
        )

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition":
                'attachment; filename="PrivatePDF_Batch_Results.zip"',
            "Content-Length": str(len(zip_bytes)),
        },
    )




# === UPGRADE_8_PDF_INSPECTOR_BACKEND ===
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse

@app.post("/api/pdf-inspect")
async def pdf_inspect(file: UploadFile = File(...)):
    """
    Professional PDF preflight inspector.
    Reads the uploaded PDF temporarily and returns technical information.
    No persistent document storage is used.
    """
    import tempfile
    import os
    import json

    try:
        from pypdf import PdfReader
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"PDF reader unavailable: {exc}"}
        )

    filename = file.filename or "document.pdf"

    if not filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Please select a PDF file."}
        )

    data = await file.read()

    max_bytes = 250 * 1024 * 1024
    if len(data) > max_bytes:
        return JSONResponse(
            status_code=413,
            content={"error": "PDF exceeds the 250 MB upload limit."}
        )

    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False
        ) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        reader = PdfReader(tmp_path)

        page_count = len(reader.pages)

        encrypted = bool(reader.is_encrypted)

        pdf_version = "Unknown"
        try:
            with open(tmp_path, "rb") as raw:
                header = raw.read(16)
            if header.startswith(b"%PDF-"):
                pdf_version = header[5:8].decode(
                    "ascii",
                    errors="ignore"
                )
        except Exception:
            pass

        metadata = {}

        try:
            raw_meta = reader.metadata
            if raw_meta:
                for key, value in raw_meta.items():
                    clean_key = str(key).replace("/", "")
                    if value is not None:
                        metadata[clean_key] = str(value)
        except Exception:
            metadata = {}

        page_info = []
        text_pages = 0
        image_pages = 0
        portrait_pages = 0
        landscape_pages = 0
        square_pages = 0

        for index, page in enumerate(reader.pages):
            width = None
            height = None

            try:
                box = page.mediabox
                width = float(box.width)
                height = float(box.height)
            except Exception:
                pass

            orientation = "unknown"

            if width is not None and height is not None:
                ratio = width / height if height else 0

                if abs(width - height) < 2:
                    orientation = "square"
                    square_pages += 1
                elif width > height:
                    orientation = "landscape"
                    landscape_pages += 1
                else:
                    orientation = "portrait"
                    portrait_pages += 1

            has_text = False

            try:
                contents = page.get_contents()
                has_text = contents is not None
            except Exception:
                pass

            if has_text:
                text_pages += 1

            has_images = False

            try:
                resources = page.get("/Resources")
                if resources:
                    xobjects = resources.get("/XObject")
                    if xobjects:
                        for _, obj in xobjects.items():
                            try:
                                target = obj.get_object()
                                subtype = target.get("/Subtype")
                                if str(subtype) == "/Image":
                                    has_images = True
                                    break
                            except Exception:
                                continue
            except Exception:
                pass

            if has_images:
                image_pages += 1

            page_info.append({
                "page": index + 1,
                "width_pt": round(width, 2) if width is not None else None,
                "height_pt": round(height, 2) if height is not None else None,
                "orientation": orientation,
                "has_text": has_text,
                "has_images": has_images
            })

        size_bytes = len(data)

        if size_bytes < 1024:
            size_label = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_label = f"{size_bytes / 1024:.1f} KB"
        else:
            size_label = f"{size_bytes / (1024 * 1024):.2f} MB"

        avg_page_kb = (
            size_bytes / page_count / 1024
            if page_count
            else 0
        )

        return {
            "ok": True,
            "filename": filename,
            "size_bytes": size_bytes,
            "size_label": size_label,
            "average_page_kb": round(avg_page_kb, 1),
            "page_count": page_count,
            "encrypted": encrypted,
            "pdf_version": pdf_version,
            "text_pages": text_pages,
            "image_pages": image_pages,
            "portrait_pages": portrait_pages,
            "landscape_pages": landscape_pages,
            "square_pages": square_pages,
            "metadata": metadata,
            "pages": page_info
        }

    except Exception as exc:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unable to inspect PDF: {exc}"}
        )

    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# ============================================================
# SECURITY V5 CLEAN CONFIGURATION
# Production mode is NOT required during local development.
# ============================================================
PP_SECURITY_HARDENING_V5_CLEAN = True

# PRIVATEPDF_PRO_SEO_ROUTES
_PP_SEO_TOOLS = [('merge-pdf', 'Merge PDF', 'Merge PDF files online for free with Private PDF Pro.', 'merge pdf, merge pdf online, combine pdf, pdf merger'), ('compress-pdf', 'Compress PDF', 'Compress PDF files online and reduce document size with Private PDF Pro.', 'compress pdf, reduce pdf size, compress pdf online'), ('split-pdf', 'Split PDF', 'Split PDF pages online and extract selected pages with Private PDF Pro.', 'split pdf, split pdf online, extract pdf pages'), ('pdf-to-word', 'PDF to Word', 'Convert PDF documents to editable Word files with Private PDF Pro.', 'pdf to word, pdf to word converter, convert pdf to word'), ('pdf-to-jpg', 'PDF to JPG', 'Convert PDF pages to JPG images online with Private PDF Pro.', 'pdf to jpg, pdf to image, convert pdf to jpg'), ('jpg-to-pdf', 'JPG to PDF', 'Convert JPG images to PDF online with Private PDF Pro.', 'jpg to pdf, image to pdf, convert jpg to pdf'), ('png-to-pdf', 'PNG to PDF', 'Convert PNG images to PDF online with Private PDF Pro.', 'png to pdf, image to pdf, convert png to pdf'), ('pdf-to-png', 'PDF to PNG', 'Convert PDF pages to PNG images online with Private PDF Pro.', 'pdf to png, pdf to image, convert pdf to png'), ('rotate-pdf', 'Rotate PDF', 'Rotate PDF pages online with Private PDF Pro.', 'rotate pdf, rotate pdf online, rotate pdf pages'), ('watermark-pdf', 'Watermark PDF', 'Add a watermark to PDF documents with Private PDF Pro.', 'watermark pdf, add watermark to pdf'), ('pdf-to-text', 'PDF to Text', 'Extract text from PDF documents with Private PDF Pro.', 'pdf to text, extract text from pdf'), ('pdf-inspector', 'PDF Inspector', 'Inspect PDF metadata and document properties with Private PDF Pro.', 'pdf inspector, pdf metadata viewer')]

def _pp_seo_find(slug):
    for item in _PP_SEO_TOOLS:
        if item[0] == slug: return item
    return None

def _pp_seo_jsonld(item, canonical):
    return {"@context":"https://schema.org","@graph":[
        {"@type":"WebSite","name":"Private PDF Pro","url":canonical},
        {"@type":"SoftwareApplication","name":"Private PDF Pro","applicationCategory":"BusinessApplication","operatingSystem":"Web","description":item[2],"url":canonical},
        {"@type":"FAQPage","mainEntity":[
            {"@type":"Question","name":"Can I use " + item[1] + " online?","acceptedAnswer":{"@type":"Answer","text":item[2]}},
            {"@type":"Question","name":"Does Private PDF Pro provide PDF tools?","acceptedAnswer":{"@type":"Answer","text":"Private PDF Pro provides PDF and image workflows for common document tasks."}}
        ]}
    ]}

def _pp_seo_page(item):
    index_file = Path(__file__).resolve().parents[1] / "static" / "index.html"
    source = index_file.read_text(encoding="utf-8")
    slug, name, description, keywords = item
    title = name + " Online Free | Private PDF Pro"
    canonical = "/" + slug
    source = re.sub(r"<!-- PRIVATEPDF_PRO_SEO_HEAD -->.*?<!-- PRIVATEPDF_PRO_SEO_HEAD -->","",source,flags=re.S)
    source = re.sub(r"<title>.*?</title>","<title>"+title+"</title>",source,count=1,flags=re.I|re.S)
    meta = ("<meta name=\"description\" content=\"" + description + "\">\n"
            "<meta name=\"keywords\" content=\"" + keywords + "\">\n"
            "<meta name=\"robots\" content=\"index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1\">\n"
            "<link rel=\"canonical\" href=\"" + canonical + "\">\n"
            "<meta property=\"og:type\" content=\"website\">\n"
            "<meta property=\"og:title\" content=\"" + title + "\">\n"
            "<meta property=\"og:description\" content=\"" + description + "\">\n"
            "<meta property=\"og:site_name\" content=\"Private PDF Pro\">\n"
            "<meta property=\"og:url\" content=\"" + canonical + "\">\n"
            "<meta name=\"twitter:card\" content=\"summary\">\n"
            "<meta name=\"twitter:title\" content=\"" + title + "\">\n"
            "<meta name=\"twitter:description\" content=\"" + description + "\">\n"
            "<script type=\"application/ld+json\">" + json.dumps(_pp_seo_jsonld(item,canonical),ensure_ascii=False) + "</script>\n")
    head = re.search(r"</head\s*>",source,re.I)
    if head: source = source[:head.start()] + meta + source[head.start():]
    landing = ("<section aria-label=\"Tool information\" style=\"max-width:1100px;margin:18px auto;padding:18px 20px;line-height:1.6\">"
               "<h1>"+title+"</h1><p>"+description+"</p>"
               "<p><a href=\"/\">Private PDF Pro home</a> · <a href=\"/merge-pdf\">Merge PDF</a> · <a href=\"/compress-pdf\">Compress PDF</a> · <a href=\"/split-pdf\">Split PDF</a></p></section>")
    body = re.search(r"<body[^>]*>",source,re.I)
    if body: source = source[:body.end()] + landing + source[body.end():]
    return HTMLResponse(content=source)

def _pp_seo_handler_factory(slug):
    async def _handler():
        item = _pp_seo_find(slug)
        if item is None: return HTMLResponse(content="Not Found",status_code=404)
        return _pp_seo_page(item)
    return _handler

for _pp_item in _PP_SEO_TOOLS:
    app.add_api_route("/"+_pp_item[0],_pp_seo_handler_factory(_pp_item[0]),methods=["GET"],include_in_schema=False)

@app.get("/robots.txt",include_in_schema=False)
async def _pp_robots_txt():
    return Response(content="User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n",media_type="text/plain")

@app.get("/sitemap.xml",include_in_schema=False)
async def _pp_sitemap_xml():
    urls = ["/"] + ["/"+x[0] for x in _PP_SEO_TOOLS]
    body = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>","<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"]
    for u in urls: body.append("  <url><loc>"+u+"</loc></url>")
    body.append("</urlset>")
    return Response(content="\n".join(body),media_type="application/xml")

# PRIVATEPDF_PRO_SEO_ROUTES_END

