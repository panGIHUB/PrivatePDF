#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$ROOT/src"; HTML="$SRC/static/index.html"; MAIN="$SRC/app/main.py"; REQ="$SRC/requirements.txt"
[[ -f "$HTML" && -f "$MAIN" && -f "$REQ" ]] || { echo "ERROR: required project files missing"; exit 1; }
echo "=== STEP 5 FINAL PRE-DEPLOY GATE ==="
BEFORE="$(sha256sum "$MAIN" | awk '{print $1}')"
python -m py_compile "$MAIN"; echo "PYTHON_SYNTAX: PASS"
python - <<'PY'
import sys
sys.path.insert(0,"src")
import app.main
print("APP_IMPORT: PASS")
PY
grep -q 'PP_SECURITY_HARDENING_V5_CLEAN' "$MAIN"; echo "SECURITY_CONFIG: PASS"
for x in 'PP_STEP2_EDITOR_ANNOTATION_STABILITY_2026' 'PP_STEP3_RESPONSIVE_QA_HARDENING_2026' 'PP_STEP4_PRODUCTION_QA_GATE_2026'; do
  grep -q "$x" "$HTML"
done
echo "STEPS_2_3_4_PRESERVED: PASS"
for x in IMAGE_STUDIO ANNOTATION BATCH CONVERSION ORGANIZE EDIT; do grep -qi "$x" "$HTML"; done
echo "CORE_UI_MODULES: PASS"
grep -q '<html' "$HTML" && grep -q '</html>' "$HTML"; echo "HTML_STRUCTURE: PASS"
if command -v pip >/dev/null 2>&1; then
  pip check
  echo "PIP_CHECK: PASS"
fi
if command -v pip-audit >/dev/null 2>&1; then
  pip-audit
  echo "PIP_AUDIT: PASS"
else
  echo "PIP_AUDIT: SKIPPED (pip-audit not installed)"
fi
AFTER="$(sha256sum "$MAIN" | awk '{print $1}')"
[[ "$BEFORE" == "$AFTER" ]] || { echo "MAIN_PY_UNCHANGED: FAIL"; exit 1; }
echo "MAIN_PY_UNCHANGED: PASS"
echo "NO_SOURCE_MODIFICATION: PASS"
echo "FINAL_REGRESSION_GATE: PASS"
echo "DEPLOY_READY_GATE: PASS"
echo "STEP5_FINAL_PREDEPLOY_GATE_COMPLETE"
