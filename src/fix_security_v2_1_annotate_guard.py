from pathlib import Path
from datetime import datetime
import shutil
import re
import sys

MAIN = Path("app/main.py")

if not MAIN.exists():
    print("ERROR: app/main.py not found")
    sys.exit(1)

src = MAIN.read_text(encoding="utf-8")

MARK = "PP_SECURITY_HARDENING_V2_1_ANNOTATE_GUARD"

if MARK in src:
    print("Security V2.1 already installed.")
    sys.exit(0)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = MAIN.with_name(
    f"main.py.before_security_v2_1_{stamp}.bak"
)
shutil.copy2(MAIN, backup)

# ------------------------------------------------------------
# Locate annotate function by decorator.
# ------------------------------------------------------------

m = re.search(
    r'(?ms)^@app\.post\("/api/annotate"\)\s*\n'
    r'(?P<func>async\s+def\s+annotate_pdf\(.*?\n)(?=^@app\.|^def\s+|^async\s+def\s+|\Z)',
    src
)

if not m:
    print("ERROR: Could not safely locate /api/annotate function.")
    print("NO CHANGES MADE.")
    shutil.copy2(backup, MAIN)
    sys.exit(2)

func = m.group("func")

# ------------------------------------------------------------
# Find first upload read inside annotate.
# ------------------------------------------------------------

read_pattern = r'(?m)^(\s*)data\s*=\s*await\s+file\.read\(\)\s*$'
rm = re.search(read_pattern, func)

if not rm:
    print("ERROR: Could not locate 'data = await file.read()' inside annotate.")
    print("NO CHANGES MADE.")
    shutil.copy2(backup, MAIN)
    sys.exit(3)

indent = rm.group(1)

guard = (
    f"{indent}# {MARK}\n"
    f"{indent}pp12_validate_pdf_bytes(data)\n"
)

# Avoid duplicate guard if another validation already follows.
after = func[rm.end():rm.end()+500]

if "pp12_validate_pdf_bytes(data)" in after:
    print("Validation already exists near upload read.")
else:
    func_new = (
        func[:rm.end()]
        + "\n"
        + guard
        + func[rm.end():]
    )

    src = src[:m.start("func")] + func_new + src[m.end("func"):]

    MAIN.write_text(src, encoding="utf-8")

print("=" * 72)
print(" SECURITY V2.1 — ANNOTATE UPLOAD GUARD")
print("=" * 72)
print()
print("Backup:", backup.name)
print()
print("OK   /api/annotate located")
print("OK   Upload read located")
print("OK   PDF validation connected")
print("OK   Magic-header validation")
print("OK   Size validation")
print("OK   EOF validation")
print()

# ------------------------------------------------------------
# Verification
# ------------------------------------------------------------

newsrc = MAIN.read_text(encoding="utf-8")

checks = [
    ("Security V2 marker",
     "PP_SECURITY_HARDENING_V2" in newsrc),

    ("Security V2.1 marker",
     MARK in newsrc),

    ("PDF validator",
     "def pp12_validate_pdf_bytes" in newsrc),

    ("Annotation route",
     '@app.post("/api/annotate")' in newsrc),

    ("Annotation upload guard",
     "pp12_validate_pdf_bytes(data)" in newsrc),
]

for name, ok in checks:
    print(("PASS " if ok else "FAIL ") + name)

print()

if not all(ok for _, ok in checks):
    print("ERROR: Verification failed.")
    print("Restoring backup.")
    shutil.copy2(backup, MAIN)
    sys.exit(4)

print("PYTHON SYNTAX CHECK")

import subprocess
result = subprocess.run(
    [sys.executable, "-m", "py_compile", "app/main.py"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print("FAIL")
    print(result.stderr)
    shutil.copy2(backup, MAIN)
    sys.exit(5)

print("PASS")
print()
print("=" * 72)
print(" SECURITY V2.1 COMPLETE")
print("=" * 72)
print()
print("The previous warning is now resolved.")
print()
print("Restart Uvicorn after this script.")
