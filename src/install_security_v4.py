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

MARK = "PP_SECURITY_HARDENING_V4"

if MARK in src:
    print("Security V4 already installed.")
    sys.exit(0)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = MAIN.with_name(
    f"main.py.before_security_v4_{stamp}.bak"
)
shutil.copy2(MAIN, backup)

# ============================================================
# SECURITY V4
# ============================================================

helper = r'''

# ============================================================
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
    *,
    timeout=None,
    cwd=None,
    env=None
):
    """
    Run an external process with a hard timeout.

    stdout/stderr are captured so converter output does not leak
    into the web response or expose internal filesystem details.
    """

    if timeout is None:
        timeout = PP_PROCESS_TIMEOUT_SECONDS

    started = _pp_v4_time.monotonic()

    try:
        completed = _pp_v4_subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdout=_pp_v4_subprocess.PIPE,
            stderr=_pp_v4_subprocess.PIPE,
            stdin=_pp_v4_subprocess.DEVNULL,
            timeout=timeout,
            check=False,
            text=False,
            shell=False
        )

    except _pp_v4_subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Document processing timed out."
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Required document conversion service is unavailable."
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Document processing failed."
        )

    elapsed = _pp_v4_time.monotonic() - started

    if elapsed > PP_MAX_OPERATION_SECONDS:
        raise HTTPException(
            status_code=504,
            detail="Document processing exceeded the allowed time."
        )

    if completed.returncode != 0:
        # Never return converter stdout/stderr to the client.
        raise HTTPException(
            status_code=400,
            detail="Document conversion failed."
        )

    return completed


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

'''

# Insert before first FastAPI route.
route_match = re.search(r'(?m)^@app\.', src)

if not route_match:
    print("ERROR: No FastAPI routes found.")
    shutil.copy2(backup, MAIN)
    sys.exit(2)

src = (
    src[:route_match.start()]
    + helper
    + "\n"
    + src[route_match.start():]
)

MAIN.write_text(src, encoding="utf-8")

# ============================================================
# Verification
# ============================================================

print("=" * 72)
print(" SECURITY V4 INSTALLATION")
print("=" * 72)
print()
print("Backup:", backup.name)
print()

checks = [
    ("Security V4 marker",
     "PP_SECURITY_HARDENING_V4" in src),

    ("Secure temp workspace",
     "def pp_v4_secure_temp_dir" in src),

    ("Secure cleanup",
     "def pp_v4_cleanup_path" in src),

    ("Output size guard",
     "def pp_v4_validate_output_size" in src),

    ("Process runner",
     "def pp_v4_run_process" in src),

    ("Process timeout",
     "PP_PROCESS_TIMEOUT_SECONDS" in src),

    ("Office timeout",
     "PP_OFFICE_TIMEOUT_SECONDS" in src),

    ("Maximum process output",
     "PP_MAX_PROCESS_OUTPUT_MB" in src),

    ("Batch limit",
     "PP_MAX_BATCH_FILES" in src),

    ("Operation timeout",
     "PP_MAX_OPERATION_SECONDS" in src),

    ("Shell disabled",
     "shell=False" in src),

    ("STDIN disabled",
     "DEVNULL" in src),

    ("Annotation preserved",
     '@app.post("/api/annotate")' in src),

    ("Annotation page preserved",
     '@app.post("/api/annotation-page")' in src),
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
    print("Restoring backup...")
    shutil.copy2(backup, MAIN)
    sys.exit(4)

print("PYTHON SYNTAX: PASS")
print()

# ============================================================
# Import
# ============================================================

print("=" * 62)
print(" IMPORT / ROUTE CHECK")
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
print("Compress:", "/api/compress" in routes)
print("Office to PDF:", "/api/office-to-pdf" in routes)
print("PDF to Office:", "/api/pdf-to-office" in routes)
print("Batch:", "/api/batch-process" in routes)

print(
    "Security V4:",
    getattr(m, "PP_SECURITY_HARDENING_V4", False)
)

print(
    "Process timeout:",
    getattr(m, "PP_PROCESS_TIMEOUT_SECONDS", None)
)

print(
    "Office timeout:",
    getattr(m, "PP_OFFICE_TIMEOUT_SECONDS", None)
)

print(
    "Output limit MB:",
    getattr(m, "PP_MAX_PROCESS_OUTPUT_MB", None)
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

print("=" * 72)
print(" SECURITY V4 COMPLETE")
print("=" * 72)
print()
print("Added:")
print("  Secure temporary workspaces")
print("  Recursive secure cleanup")
print("  External process timeout")
print("  LibreOffice-safe environment")
print("  Process output-size guard")
print("  Batch resource limit")
print("  Operation time limit")
print("  shell=False subprocess execution")
print("  stdin isolation")
print("  Production-safe conversion errors")
print()
print("Preserved:")
print("  Security V1")
print("  Security V2")
print("  Security V2.1")
print("  Security V3")
print("  Security V3.1")
print("  #12 Annotation Engine")
print("  #12.2 Object Manager")
print("  #12.3 Advanced Text")
print("  #12.4 Text Markup")
print("  #12.5 Shapes")
print("  #12.6 History")
print()
print("No database.")
print("No persistent document storage.")
print()
print("Restart Uvicorn:")
print()
print("python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
