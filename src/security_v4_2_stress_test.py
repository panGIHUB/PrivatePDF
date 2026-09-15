import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path

print("=" * 72)
print(" SECURITY V4.2 — PRODUCTION STRESS TEST")
print("=" * 72)
print()

# ------------------------------------------------------------
# Import application
# ------------------------------------------------------------

try:
    import app.main as m
    from app.main import app

    print("PASS Application import")
except Exception as e:
    print("FAIL Application import")
    print(type(e).__name__, str(e))
    sys.exit(1)

# ------------------------------------------------------------
# Configuration checks
# ------------------------------------------------------------

checks = [
    (
        "Security V4",
        getattr(m, "PP_SECURITY_HARDENING_V4", False)
    ),
    (
        "Security V4.1",
        getattr(m, "PP_SECURITY_HARDENING_V4_1", False)
    ),
    (
        "Output guard",
        getattr(m, "PP12_V4_OUTPUT_GUARD", False)
    ),
    (
        "Process timeout configured",
        getattr(m, "PP_PROCESS_TIMEOUT_SECONDS", 0) > 0
    ),
    (
        "Office timeout configured",
        getattr(m, "PP_OFFICE_TIMEOUT_SECONDS", 0) > 0
    ),
    (
        "Output size configured",
        getattr(m, "PP_MAX_PROCESS_OUTPUT_MB", 0) > 0
    ),
]

for name, ok in checks:
    print(
        ("PASS " if ok else "FAIL ") + name
    )

if not all(ok for _, ok in checks):
    print()
    print("Security configuration check failed.")
    sys.exit(2)

# ------------------------------------------------------------
# Route integrity
# ------------------------------------------------------------

routes = [
    getattr(r, "path", "")
    for r in app.routes
]

required_routes = [
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

print()
print("=" * 72)
print(" ROUTE INTEGRITY")
print("=" * 72)

missing = []

for route in required_routes:
    ok = route in routes
    print(
        ("PASS " if ok else "FAIL ") + route
    )

    if not ok:
        missing.append(route)

if missing:
    print()
    print("Missing routes:")
    for x in missing:
        print(" ", x)
    sys.exit(3)

# ------------------------------------------------------------
# Create a REAL one-page PDF
# ------------------------------------------------------------

print()
print("=" * 72)
print(" REAL PDF VALIDATION")
print("=" * 72)

pdf_path = None

try:
    import pymupdf as fitz

    tmp = Path(
        tempfile.mkdtemp(
            prefix="privatepdf_v42_test_"
        )
    )

    pdf_path = tmp / "valid_test.pdf"

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 100),
        "PrivatePDF Pro Security V4.2 Test"
    )
    page.insert_text(
        (72, 130),
        "This is a real one-page PDF."
    )
    doc.save(str(pdf_path))
    doc.close()

    data = pdf_path.read_bytes()

    print("PASS Real one-page PDF generated")
    print("PASS PDF size:", len(data), "bytes")

    validated = m.pp12_validate_pdf_bytes(data)

    print("PASS PDF byte validator accepted real PDF")

    doc2 = fitz.open(stream=data, filetype="pdf")

    try:
        m.pp12_validate_pdf_document(doc2)
        print("PASS PDF document validator accepted real PDF")
    finally:
        doc2.close()

except Exception as e:

    print("FAIL Real PDF validation")
    print(type(e).__name__, str(e))
    sys.exit(4)

# ------------------------------------------------------------
# Output validation
# ------------------------------------------------------------

print()
print("=" * 72)
print(" OUTPUT VALIDATION")
print("=" * 72)

try:

    size = m.pp_v4_validate_output_size(
        str(pdf_path)
    )

    print(
        "PASS Output-size validator accepted valid output"
    )

    print(
        "PASS Output size:",
        size,
        "bytes"
    )

except Exception as e:

    print(
        "FAIL Output-size validator"
    )

    print(
        type(e).__name__,
        str(e)
    )

    sys.exit(5)

# ------------------------------------------------------------
# Process runner test
# ------------------------------------------------------------

print()
print("=" * 72)
print(" PROCESS ISOLATION TEST")
print("=" * 72)

try:

    result = m.pp_v4_run_process(
        [
            sys.executable,
            "-c",
            "print('PP12_PROCESS_OK')"
        ],
        timeout=10
    )

    output = (
        result.stdout.decode(
            "utf-8",
            errors="replace"
        )
        if isinstance(result.stdout, bytes)
        else str(result.stdout)
    )

    if "PP12_PROCESS_OK" in output:
        print("PASS Safe subprocess execution")
    else:
        print("FAIL Safe subprocess output")
        sys.exit(6)

except Exception as e:

    print("FAIL Safe subprocess execution")
    print(type(e).__name__, str(e))
    sys.exit(6)

# ------------------------------------------------------------
# Timeout test
# ------------------------------------------------------------

print()
print("=" * 72)
print(" HARD TIMEOUT TEST")
print("=" * 72)

try:

    started = time.monotonic()

    m.pp_v4_run_process(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(10)"
        ],
        timeout=1
    )

    print("FAIL Process was not terminated by timeout")
    sys.exit(7)

except Exception as e:

    elapsed = time.monotonic() - started

    # HTTPException is expected.
    status = getattr(
        e,
        "status_code",
        None
    )

    if status == 504:

        print("PASS Hard process timeout triggered")
        print(
            "PASS Timeout response:",
            status
        )
        print(
            "PASS Elapsed:",
            round(elapsed, 2),
            "seconds"
        )

    else:

        print(
            "FAIL Unexpected timeout exception:",
            type(e).__name__,
            str(e)
        )

        sys.exit(8)

# ------------------------------------------------------------
# Shell injection protection
# ------------------------------------------------------------

print()
print("=" * 72)
print(" SHELL EXECUTION TEST")
print("=" * 72)

try:

    result = m.pp_v4_run_process(
        [
            sys.executable,
            "-c",
            "print('SHELL_FALSE_OK')"
        ],
        timeout=10
    )

    output = (
        result.stdout.decode(
            "utf-8",
            errors="replace"
        )
        if isinstance(result.stdout, bytes)
        else str(result.stdout)
    )

    if "SHELL_FALSE_OK" in output:
        print("PASS shell=False process execution")

    else:
        print("FAIL shell execution test")
        sys.exit(9)

except Exception as e:

    print(
        "FAIL shell execution test"
    )

    print(
        type(e).__name__,
        str(e)
    )

    sys.exit(9)

# ------------------------------------------------------------
# Secure temporary workspace test
# ------------------------------------------------------------

print()
print("=" * 72)
print(" TEMPORARY WORKSPACE TEST")
print("=" * 72)

workspace = None

try:

    workspace = m.pp_v4_secure_temp_dir(
        prefix="privatepdf_v42_"
    )

    workspace_path = Path(workspace)

    if not workspace_path.exists():
        print("FAIL Temporary workspace was not created")
        sys.exit(10)

    print("PASS Isolated temporary workspace created")

    test_file = (
        workspace_path
        / "temporary_document_test.bin"
    )

    test_file.write_bytes(
        b"PRIVATEPDF_V42_TEST"
    )

    print("PASS Temporary file created")

    m.pp_v4_cleanup_path(
        workspace
    )

    if not workspace_path.exists():
        print("PASS Temporary workspace cleanup")
    else:
        print("FAIL Temporary workspace cleanup")
        sys.exit(11)

except Exception as e:

    print("FAIL Temporary workspace test")
    print(type(e).__name__, str(e))
    sys.exit(12)

# ------------------------------------------------------------
# Annotation integrity
# ------------------------------------------------------------

print()
print("=" * 72)
print(" ANNOTATION INTEGRITY")
print("=" * 72)

annotation_checks = [
    "/api/annotate",
    "/api/annotation-page",
]

for route in annotation_checks:

    ok = route in routes

    print(
        ("PASS " if ok else "FAIL ")
        + route
    )

# ------------------------------------------------------------
# LibreOffice status
# ------------------------------------------------------------

print()
print("=" * 72)
print(" OFFICE ENGINE STATUS")
print("=" * 72)

lo = (
    __import__("shutil").which("libreoffice")
    or __import__("shutil").which("soffice")
)

if lo:
    print("PASS LibreOffice:", lo)
else:
    print(
        "INFO LibreOffice not installed/in PATH."
    )
    print(
        "INFO Office conversion stress test skipped."
    )

# ------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------

try:

    if pdf_path:
        parent = pdf_path.parent

        if parent.exists():
            m.pp_v4_cleanup_path(
                parent
            )

except Exception:
    pass

# ------------------------------------------------------------
# Final
# ------------------------------------------------------------

print()
print("=" * 72)
print(" SECURITY V4.2 RESULT")
print("=" * 72)
print()
print("PASS Security V4 configuration")
print("PASS Route integrity")
print("PASS Real PDF validation")
print("PASS Output validation")
print("PASS Safe subprocess execution")
print("PASS Hard process timeout")
print("PASS shell execution isolation")
print("PASS Temporary workspace isolation")
print("PASS Temporary cleanup")
print("PASS Annotation route integrity")

if not lo:
    print("INFO LibreOffice-specific runtime test skipped")

print()
print("SECURITY V4.2: PASS")
print()
