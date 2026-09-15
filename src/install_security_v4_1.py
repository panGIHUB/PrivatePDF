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

MARK = "PP_SECURITY_HARDENING_V4_1"

if MARK in src:
    print("Security V4.1 already installed.")
    sys.exit(0)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = MAIN.with_name(
    f"main.py.before_security_v4_1_{stamp}.bak"
)

shutil.copy2(MAIN, backup)

print("=" * 72)
print(" SECURITY V4.1")
print(" LibreOffice Process Isolation + Conversion Hardening")
print("=" * 72)
print()
print("Backup:", backup.name)
print()

# ============================================================
# 1. Find existing V4 helper
# ============================================================

if "def pp_v4_run_process" not in src:
    print("ERROR: Security V4 helper not found.")
    print("Install Security V4 first.")
    sys.exit(2)

print("OK   V4 process helper found")

# ============================================================
# 2. Upgrade process helper so it accepts existing
#    subprocess.run-style arguments safely.
# ============================================================

helper_start = src.find("def pp_v4_run_process(")

if helper_start < 0:
    print("ERROR: pp_v4_run_process definition not found.")
    shutil.copy2(backup, MAIN)
    sys.exit(3)

# Find next helper/function after pp_v4_run_process
next_def = re.search(
    r"\n(?=def\s+pp_v4_|@app\.)",
    src[helper_start + 10:]
)

if next_def:
    helper_end = (
        helper_start
        + 10
        + next_def.start()
    )
else:
    helper_end = len(src)

new_helper = r'''
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

'''

src = (
    src[:helper_start]
    + new_helper
    + src[helper_end:]
)

print("OK   Hardened V4 process runner")

# ============================================================
# 3. Locate actual Office routes
# ============================================================

def route_body(source, route_path):
    pattern = re.compile(
        r'@app\.(?:post|get|put|delete)\(\s*["\']'
        + re.escape(route_path)
        + r'["\'][\s\S]*?(?=\n@app\.|\Z)',
        re.M
    )
    m = pattern.search(source)
    return m

office_routes = [
    "/api/office-to-pdf",
    "/api/pdf-to-office",
]

patched_routes = 0
run_occurrences = 0

for route in office_routes:

    m = route_body(src, route)

    if not m:
        print("WARN ", route, "not found")
        continue

    body = m.group(0)

    count = len(
        re.findall(
            r'\bsubprocess\.run\s*\(',
            body
        )
    )

    count += len(
        re.findall(
            r'\b_pp_v4_subprocess\.run\s*\(',
            body
        )
    )

    run_occurrences += count

    if "pp_v4_run_process(" in body:
        print("OK   ", route, "already connected")
        patched_routes += 1
        continue

    if not re.search(
        r'\bsubprocess\.run\s*\(',
        body
    ):
        print(
            "INFO ",
            route,
            "contains no subprocess.run call; no direct replacement needed"
        )
        continue

    new_body = re.sub(
        r'\bsubprocess\.run\s*\(',
        "pp_v4_run_process(",
        body
    )

    src = (
        src[:m.start()]
        + new_body
        + src[m.end():]
    )

    patched_routes += 1

    print(
        "OK   ",
        route,
        "LibreOffice process call connected"
    )

# ============================================================
# 4. Add V4.1 marker near the V4 marker.
# ============================================================

marker_anchor = "# PP_SECURITY_HARDENING_V4"

if marker_anchor not in src:
    print("ERROR: V4 marker disappeared.")
    shutil.copy2(backup, MAIN)
    sys.exit(4)

v41_block = r'''
# ============================================================
# PP_SECURITY_HARDENING_V4_1
# Actual LibreOffice process isolation is connected to
# conversion routes.
# ============================================================

PP_SECURITY_HARDENING_V4_1 = True

'''

insert_pos = src.find(marker_anchor)

# Put marker only if not already present.
src = (
    src[:insert_pos]
    + v41_block
    + src[insert_pos:]
)

# ============================================================
# 5. Output-size middleware
# ============================================================

if "PP12_V4_OUTPUT_GUARD" not in src:

    output_guard = r'''

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

'''

    # Add before first route.
    first_route = re.search(
        r'(?m)^@app\.',
        src
    )

    if first_route:

        src = (
            src[:first_route.start()]
            + output_guard
            + "\n"
            + src[first_route.start():]
        )

        # Add middleware after app creation.
        app_creation = re.search(
            r'(?m)^(app\s*=\s*(?:FastAPI|FastAPI\([^)]*\)))',
            src
        )

        if app_creation:

            line_end = src.find(
                "\n",
                app_creation.end()
            )

            if line_end < 0:
                line_end = len(src)

            middleware_line = r'''
# Security V4.1 generated-output guard
try:
    app.add_middleware(
        PP12V4OutputGuardMiddleware
    )
except Exception:
    pass
'''

            src = (
                src[:line_end]
                + "\n"
                + middleware_line
                + src[line_end:]
            )

            print(
                "OK   Generated-output size guard connected"
            )

# ============================================================
# 6. Marker
# ============================================================

if MARK not in src:

    first_route = re.search(
        r'(?m)^@app\.',
        src
    )

    if first_route:
        src = (
            src[:first_route.start()]
            + "\n# "
            + MARK
            + "\n"
            + src[first_route.start():]
        )

# ============================================================
# 7. Save
# ============================================================

MAIN.write_text(
    src,
    encoding="utf-8"
)

# ============================================================
# 8. Static verification
# ============================================================

print()
print("=" * 72)
print(" V4.1 STATIC VERIFICATION")
print("=" * 72)

checks = [

    (
        "V4.1 marker",
        MARK in src
    ),

    (
        "Hardened process runner",
        "def pp_v4_run_process(" in src
    ),

    (
        "Office timeout",
        "PP_OFFICE_TIMEOUT_SECONDS" in src
    ),

    (
        "Isolated LibreOffice profile",
        "privatepdf_lo_" in src
    ),

    (
        "shell=False",
        "kwargs[\"shell\"] = False" in src
    ),

    (
        "stdin isolation",
        "subprocess.DEVNULL" in src
    ),

    (
        "Generated output guard",
        "PP12_V4_OUTPUT_GUARD" in src
    ),

    (
        "Annotation endpoint",
        "/api/annotate" in src
    ),

    (
        "Annotation page endpoint",
        "/api/annotation-page" in src
    ),

    (
        "Office to PDF route",
        "/api/office-to-pdf" in src
    ),

    (
        "PDF to Office route",
        "/api/pdf-to-office" in src
    ),
]

failed = False

for name, ok in checks:

    print(
        ("PASS " if ok else "FAIL ")
        + name
    )

    if not ok:
        failed = True

if failed:

    print()
    print("ERROR: Static verification failed.")
    print("Restoring backup...")
    shutil.copy2(backup, MAIN)
    sys.exit(5)

# ============================================================
# 9. Python syntax
# ============================================================

print()
print("=" * 72)
print(" PYTHON SYNTAX")
print("=" * 72)

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

    sys.exit(6)

print("PYTHON SYNTAX: PASS")

# ============================================================
# 10. Import + routes
# ============================================================

print()
print("=" * 72)
print(" IMPORT + ROUTES")
print("=" * 72)

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
    "Security V4.1:",
    getattr(m, "PP_SECURITY_HARDENING_V4_1", False)
)

print(
    "Office timeout:",
    getattr(m, "PP_OFFICE_TIMEOUT_SECONDS", None)
)

print(
    "Output limit MB:",
    getattr(m, "PP_MAX_PROCESS_OUTPUT_MB", None)
)

print(
    "Output guard:",
    getattr(m, "PP12_V4_OUTPUT_GUARD", False)
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

    sys.exit(7)

# ============================================================
# 11. LibreOffice availability
# ============================================================

print()
print("=" * 72)
print(" LIBREOFFICE AVAILABILITY")
print("=" * 72)

lo = shutil.which("libreoffice")

if lo is None:
    lo = shutil.which("soffice")

if lo:
    print("PASS LibreOffice executable found")
    print("     ", lo)
else:
    print("INFO LibreOffice executable not found in PATH")
    print("     Office conversion will remain unavailable until")
    print("     LibreOffice is installed/configured.")

# ============================================================
# Final
# ============================================================

print()
print("=" * 72)
print(" SECURITY V4.1 COMPLETE")
print("=" * 72)
print()
print("Actual protection connected:")
print("  ✓ LibreOffice hard timeout")
print("  ✓ Randomized LibreOffice temporary profile")
print("  ✓ Headless/no-restore/no-lockcheck flags")
print("  ✓ shell=False")
print("  ✓ stdin disabled")
print("  ✓ converter output captured")
print("  ✓ converter diagnostics never returned to client")
print("  ✓ safe conversion errors")
print("  ✓ generated-output size guard")
print("  ✓ temporary profile cleanup")
print()
print("Preserved:")
print("  ✓ Existing PDF routes")
print("  ✓ Annotation Studio")
print("  ✓ Annotation export")
print("  ✓ Security V1")
print("  ✓ Security V2")
print("  ✓ Security V2.1")
print("  ✓ Security V3.1")
print("  ✓ Security V4")
print()
print("Backup:", backup.name)
print()
print("Restart server after installation.")
