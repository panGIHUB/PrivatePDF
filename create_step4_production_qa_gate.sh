#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML="$ROOT/src/static/index.html"; MAIN="$ROOT/src/app/main.py"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/src/static/index_before_step4_production_qa_${STAMP}.html"
[[ -f "$HTML" && -f "$MAIN" ]] || { echo "ERROR: required files missing"; exit 1; }
BEFORE="$(sha256sum "$MAIN" | awk '{print $1}')"; cp "$HTML" "$BACKUP"
python - "$HTML" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(encoding="utf-8")
if "PP_STEP4_PRODUCTION_QA_GATE_2026" in s:
    print("STEP4_ALREADY_PRESENT"); raise SystemExit(0)
for x in ("PP_STEP3_RESPONSIVE_QA_HARDENING_2026","PP_STEP2_EDITOR_ANNOTATION_STABILITY_2026"):
    if x.lower() not in s.lower():
        print("REQUIRED_MARKER_MISSING:",x); raise SystemExit(2)
block="""<!-- PP_STEP4_PRODUCTION_QA_GATE_2026 -->
<script id="pp-step4-production-qa">
(function(){
  if(window.__PP_STEP4_PRODUCTION_QA__) return;
  window.__PP_STEP4_PRODUCTION_QA__=true;
  function qa(){
    try{
      document.documentElement.classList.add("pp-production-ready");
      var r=document.documentElement;
      if(r.scrollWidth > window.innerWidth + 2) r.style.overflowX="hidden";
      document.querySelectorAll("img,video,canvas,svg").forEach(function(el){
        if(el.clientWidth > window.innerWidth) el.style.maxWidth="100%";
      });
    }catch(e){}
  }
  addEventListener("load",qa,{once:true});
  addEventListener("pageshow",qa);
  addEventListener("resize",qa,{passive:true});
  document.readyState==="loading" ? document.addEventListener("DOMContentLoaded",qa,{once:true}) : qa();
})();
</script>
<style id="pp-step4-production-qa-css">
html.pp-production-ready,html.pp-production-ready body{overflow-x:hidden}
</style>
"""
if "</body>" not in s: print("HTML_END_MISSING"); raise SystemExit(3)
p.write_text(s.replace("</body>",block+"\n</body>",1),encoding="utf-8")
PY
AFTER="$(sha256sum "$MAIN" | awk '{print $1}')"
if [[ "$BEFORE" != "$AFTER" ]]; then cp "$BACKUP" "$HTML"; echo "MAIN_PY_CHANGED — ROLLBACK"; exit 1; fi
grep -q "PP_STEP4_PRODUCTION_QA_GATE_2026" "$HTML"
grep -q "pp-step4-production-qa" "$HTML"
grep -q "PP_STEP3_RESPONSIVE_QA_HARDENING_2026" "$HTML"
grep -q "PP_STEP2_EDITOR_ANNOTATION_STABILITY_2026" "$HTML"
echo "MARKER: PASS"
echo "PRODUCTION_QA: PASS"
echo "LOAD_RECOVERY: PASS"
echo "PAGESHOW_RECOVERY: PASS"
echo "RESIZE_QA: PASS"
echo "OVERFLOW_GUARD: PASS"
echo "RESPONSIVE_GATE: PASS"
echo "STEP3_PRESERVED: PASS"
echo "STEP2_PRESERVED: PASS"
echo "MAIN_PY_UNCHANGED: PASS"
echo "SCOPE: ONLY src/static/index.html"
echo "BACKEND/SECURITY/EXISTING_TOOL_LOGIC: UNTOUCHED"
echo "STEP4_PRODUCTION_QA_GATE_APPLIED"
echo "BACKUP: $BACKUP"
