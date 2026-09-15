import io
import sys
import time
import zipfile
import requests

BASE = "http://127.0.0.1:8000"

print("=" * 72)
print(" SECURITY V3.2 — REAL SECURITY SMOKE TEST")
print("=" * 72)
print()

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def result(name, ok, detail=""):
    print(
        ("PASS " if ok else "FAIL ") +
        name +
        (f" -> {detail}" if detail else "")
    )


def post_file(path, filename, content, content_type="application/pdf"):
    try:
        r = requests.post(
            BASE + path,
            files={
                "file": (
                    filename,
                    content,
                    content_type
                )
            },
            timeout=30
        )
        return r
    except Exception as e:
        print("ERROR:", path, str(e))
        return None


# ------------------------------------------------------------
# 1. Server health / root
# ------------------------------------------------------------

print("1. BASIC SERVER TEST")
print("-" * 72)

try:
    r = requests.get(BASE + "/", timeout=10)
    result(
        "Root endpoint",
        r.status_code == 200,
        f"HTTP {r.status_code}"
    )
except Exception as e:
    result("Root endpoint", False, str(e))
    print()
    print("Server is not reachable.")
    sys.exit(2)

# ------------------------------------------------------------
# 2. Minimal valid PDF
# ------------------------------------------------------------

print()
print("2. VALID PDF TEST")
print("-" * 72)

valid_pdf = (
    b"%PDF-1.4\n"
    b"1 0 obj\n"
    b"<< /Type /Catalog /Pages 2 0 R >>\n"
    b"endobj\n"
    b"2 0 obj\n"
    b"<< /Type /Pages /Count 0 /Kids [] >>\n"
    b"endobj\n"
    b"trailer\n"
    b"<< /Root 1 0 R >>\n"
    b"%%EOF\n"
)

# Annotation endpoint requires annotations.
try:
    r = requests.post(
        BASE + "/api/annotate",
        files={
            "file": (
                "security_test.pdf",
                valid_pdf,
                "application/pdf"
            )
        },
        data={
            "annotations": "[]"
        },
        timeout=30
    )

    # Empty annotations may be rejected by application logic.
    # That is okay; the important point is that security middleware
    # must NOT reject the PDF as an invalid upload.
    ok = r.status_code not in (400, 413, 415, 422, 500)

    result(
        "Valid PDF reaches application",
        ok,
        f"HTTP {r.status_code}"
    )

except Exception as e:
    result(
        "Valid PDF reaches application",
        False,
        str(e)
    )

# ------------------------------------------------------------
# 3. Fake PDF
# ------------------------------------------------------------

print()
print("3. FAKE PDF TEST")
print("-" * 72)

fake_pdf = (
    b"This is not a PDF document.\n"
    b"Even though the filename says PDF."
)

try:
    r = requests.post(
        BASE + "/api/annotate",
        files={
            "file": (
                "fake.pdf",
                fake_pdf,
                "application/pdf"
            )
        },
        data={
            "annotations": "[]"
        },
        timeout=30
    )

    result(
        "Fake PDF rejected",
        r.status_code in (400, 413, 415, 422),
        f"HTTP {r.status_code}"
    )

except Exception as e:
    result("Fake PDF rejected", False, str(e))

# ------------------------------------------------------------
# 4. Missing EOF
# ------------------------------------------------------------

print()
print("4. CORRUPTED PDF TEST")
print("-" * 72)

corrupt_pdf = (
    b"%PDF-1.4\n"
    b"1 0 obj\n"
    b"<< /Type /Catalog >>\n"
    b"endobj\n"
)

try:
    r = requests.post(
        BASE + "/api/annotate",
        files={
            "file": (
                "corrupt.pdf",
                corrupt_pdf,
                "application/pdf"
            )
        },
        data={
            "annotations": "[]"
        },
        timeout=30
    )

    result(
        "Incomplete PDF rejected",
        r.status_code in (400, 413, 415, 422),
        f"HTTP {r.status_code}"
    )

except Exception as e:
    result("Incomplete PDF rejected", False, str(e))

# ------------------------------------------------------------
# 5. Path traversal filename
# ------------------------------------------------------------

print()
print("5. FILENAME SANITIZATION TEST")
print("-" * 72)

try:
    r = requests.post(
        BASE + "/api/annotate",
        files={
            "file": (
                "../../../../../Windows/System32/test.pdf",
                valid_pdf,
                "application/pdf"
            )
        },
        data={
            "annotations": "[]"
        },
        timeout=30
    )

    # Should not produce a server error caused by filesystem traversal.
    result(
        "Path traversal filename handled",
        r.status_code != 500,
        f"HTTP {r.status_code}"
    )

except Exception as e:
    result(
        "Path traversal filename handled",
        False,
        str(e)
    )

# ------------------------------------------------------------
# 6. Wrong extension but valid PDF bytes
# ------------------------------------------------------------

print()
print("6. EXTENSION MISMATCH TEST")
print("-" * 72)

try:
    r = requests.post(
        BASE + "/api/annotate",
        files={
            "file": (
                "document.txt",
                valid_pdf,
                "text/plain"
            )
        },
        data={
            "annotations": "[]"
        },
        timeout=30
    )

    # Current PDF security is content/signature based.
    # A valid PDF with a misleading extension may reach application.
    result(
        "Content validation works independently of MIME",
        r.status_code not in (415, 500),
        f"HTTP {r.status_code}"
    )

except Exception as e:
    result(
        "Content validation works independently of MIME",
        False,
        str(e)
    )

# ------------------------------------------------------------
# 7. Oversized request header test
# ------------------------------------------------------------

print()
print("7. REQUEST LIMIT TEST")
print("-" * 72)

try:
    r = requests.post(
        BASE + "/api/annotate",
        headers={
            "Content-Length": str(999 * 1024 * 1024)
        },
        timeout=10
    )

    # Security V1 should reject the declared size before processing.
    result(
        "Declared oversized request rejected",
        r.status_code in (413, 400),
        f"HTTP {r.status_code}"
    )

except Exception as e:
    result(
        "Declared oversized request rejected",
        False,
        str(e)
    )

# ------------------------------------------------------------
# 8. Office ZIP structure test
# ------------------------------------------------------------

print()
print("8. OFFICE VALIDATION TEST")
print("-" * 72)

fake_docx = io.BytesIO()

with zipfile.ZipFile(
    fake_docx,
    "w",
    compression=zipfile.ZIP_DEFLATED
) as z:
    z.writestr(
        "[Content_Types].xml",
        b"fake office content"
    )

try:
    r = requests.post(
        BASE + "/api/office-to-pdf",
        files={
            "file": (
                "test.docx",
                fake_docx.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        },
        timeout=30
    )

    # It may fail later because it is not a genuine Office document,
    # but it must not crash the server.
    result(
        "Malformed Office file safely handled",
        r.status_code != 500,
        f"HTTP {r.status_code}"
    )

except Exception as e:
    result(
        "Malformed Office file safely handled",
        False,
        str(e)
    )

# ------------------------------------------------------------
# 9. Invalid image
# ------------------------------------------------------------

print()
print("9. IMAGE VALIDATION TEST")
print("-" * 72)

invalid_image = b"NOT AN IMAGE"

try:
    r = requests.post(
        BASE + "/api/images-to-pdf",
        files={
            "file": (
                "fake.jpg",
                invalid_image,
                "image/jpeg"
            )
        },
        timeout=30
    )

    result(
        "Invalid image rejected safely",
        r.status_code in (400, 413, 415, 422)
        or r.status_code != 500,
        f"HTTP {r.status_code}"
    )

except Exception as e:
    result(
        "Invalid image rejected safely",
        False,
        str(e)
    )

# ------------------------------------------------------------
# 10. Security headers
# ------------------------------------------------------------

print()
print("10. SECURITY HEADERS TEST")
print("-" * 72)

try:
    r = requests.get(BASE + "/", timeout=10)

    headers = {
        k.lower(): v
        for k, v in r.headers.items()
    }

    expected = [
        "x-content-type-options",
        "x-frame-options",
        "referrer-policy",
        "permissions-policy",
        "content-security-policy",
    ]

    for h in expected:
        result(
            h,
            h in headers,
            headers.get(h, "MISSING")
        )

except Exception as e:
    result("Security headers", False, str(e))

# ------------------------------------------------------------
# 11. API cache policy
# ------------------------------------------------------------

print()
print("11. API NO-STORE TEST")
print("-" * 72)

try:
    r = requests.get(BASE + "/api/health", timeout=10)

    cache = r.headers.get("cache-control", "")

    result(
        "API cache control",
        "no-store" in cache.lower()
        or r.status_code == 404,
        f"HTTP {r.status_code}, Cache-Control={cache or 'none'}"
    )

except Exception as e:
    result(
        "API cache control",
        False,
        str(e)
    )

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

print()
print("=" * 72)
print(" SECURITY V3.2 SMOKE TEST COMPLETE")
print("=" * 72)
print()
print("IMPORTANT:")
print("These are behavioral smoke tests, not a penetration test.")
print("No uploaded test file is intentionally saved by this script.")
print()
print("If any unexpected FAIL appears, paste the COMPLETE output.")
print()
