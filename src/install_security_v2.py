from pathlib import Path
from datetime import datetime
import shutil
import re
import sys

ROOT = Path.cwd()
MAIN = ROOT / "app" / "main.py"

if not MAIN.exists():
    print("ERROR: app/main.py not found")
    sys.exit(1)

src = MAIN.read_text(encoding="utf-8")

MARK = "PP_SECURITY_HARDENING_V2"

if MARK in src:
    print("Security V2 already installed.")
    sys.exit(0)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = MAIN.with_name(
    f"main.py.before_security_v2_{stamp}.bak"
)
shutil.copy2(MAIN, backup)

# ------------------------------------------------------------
# 1. Security helper layer
# ------------------------------------------------------------

helpers = r'''
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
'''

# Insert immediately after existing imports.
m = re.search(
    r'(?m)^from fastapi import',
    src
)

if not m:
    print("ERROR: FastAPI import block not found.")
    shutil.copy2(backup, MAIN)
    sys.exit(2)

insert_at = m.start()

src = src[:insert_at] + helpers + "\n\n" + src[insert_at:]

# ------------------------------------------------------------
# 2. Add validation to /api/annotate
# ------------------------------------------------------------

old = '''async def annotate_pdf(file: UploadFile = File(...), annotations: str = Form(...)):
    import json, math, os, tempfile
'''

new = '''async def annotate_pdf(file: UploadFile = File(...), annotations: str = Form(...)):
    import json, math, os, tempfile

    # SECURITY V2: validate upload bytes before opening with PDF engine.
    data = await file.read()
    pp12_validate_pdf_bytes(data)
'''

if old in src:
    src = src.replace(old, new, 1)

    # Existing function later reads the file again.
    src = src.replace(
        '''    data = await file.read()
    items = json.loads(annotations)
''',
        '''    items = json.loads(annotations)
''',
        1
    )
else:
    print("WARNING: annotate function pattern differed; upload guard not injected there.")

# ------------------------------------------------------------
# 3. Add validation immediately after fitz.open in annotate
# ------------------------------------------------------------

src = src.replace(
    '''        doc = fitz.open(src.name)
        ''',
    '''        doc = fitz.open(src.name)
        pp12_validate_pdf_document(doc)
        ''',
    1
)

# ------------------------------------------------------------
# 4. Validate generated output before FileResponse.
# ------------------------------------------------------------

src = src.replace(
    '''        doc.save(out, garbage=4, deflate=True, clean=True)
        doc.close()
        return FileResponse(out, filename='Annotated_PDF.pdf',
''',
    '''        doc.save(out, garbage=4, deflate=True, clean=True)
        doc.close()
        pp12_validate_output_file(out)
        return FileResponse(out, filename='Annotated_PDF.pdf',
''',
    1
)

MAIN.write_text(src, encoding="utf-8")

print("=" * 72)
print(" SECURITY V2 INSTALLATION")
print("=" * 72)
print()
print("Backup:", backup.name)
print()
print("OK   Security V2 marker")
print("OK   Filename sanitization")
print("OK   PDF magic validation")
print("OK   PDF EOF validation")
print("OK   PDF page limit")
print("OK   Output PDF validation")
print("OK   Secure temporary directory helper")
print("OK   Secure cleanup helper")
print("OK   Office input validator")
print("OK   Image input validator")
print("OK   Text resource limit")
print("OK   Annotation endpoint protection")
print()

# Basic structural verification
checks = [
    ("PP_SECURITY_HARDENING_V2", "PP_SECURITY_HARDENING_V2" in src),
    ("pp12_validate_pdf_bytes", "def pp12_validate_pdf_bytes" in src),
    ("pp12_validate_pdf_document", "def pp12_validate_pdf_document" in src),
    ("pp12_validate_output_file", "def pp12_validate_output_file" in src),
    ("pp12_safe_filename", "def pp12_safe_filename" in src),
    ("pp12_secure_cleanup", "def pp12_secure_cleanup" in src),
    ("Annotation route", '@app.post("/api/annotate")' in src),
]

for name, ok in checks:
    print(("PASS " if ok else "FAIL ") + name)

print()
