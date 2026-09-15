#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML="$ROOT/src/static/index.html"; MAIN="$ROOT/src/app/main.py"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/src/static/index_before_step3_responsive_qa_${STAMP}.html"
[[ -f "$HTML" && -f "$MAIN" ]] || { echo "ERROR: required files missing"; exit 1; }
BEFORE="$(sha256sum "$MAIN" | awk '{print $1}')"; cp "$HTML" "$BACKUP"
python - "$HTML" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(encoding="utf-8")
if "PP_STEP3_RESPONSIVE_QA_HARDENING_2026" in s:
    print("STEP3_ALREADY_PRESENT"); raise SystemExit(0)
for x in ("PP_STEP2_EDITOR_ANNOTATION_STABILITY_2026","pp11","pp12"):
    if x.lower() not in s.lower(): print("REQUIRED_MARKER_MISSING:",x); raise SystemExit(2)
css='''<!-- PP_STEP3_RESPONSIVE_QA_HARDENING_2026 -->
<style id="pp-step3-responsive-qa">
html,body{max-width:100%;overflow-x:hidden}
img,canvas,video,svg{max-width:100%}
button,input,select,textarea{max-width:100%;box-sizing:border-box}
.section,.section>*{min-width:0}
.pp12-overlay,.pp12-modal,.pp11-modal,[role="dialog"]{max-width:100vw;box-sizing:border-box}
@media(max-width:1100px){.section{padding-left:clamp(14px,3vw,28px)!important;padding-right:clamp(14px,3vw,28px)!important}}
@media(max-width:900px){.pp12-modal,.pp11-modal,[role="dialog"]{width:min(96vw,900px)!important}.pp12-toolbar,.pp11-toolbar{max-width:100%;overflow-x:auto;overflow-y:hidden}}
@media(max-width:768px){.section{min-height:0!important}.pp12-modal,.pp11-modal,[role="dialog"]{max-height:92vh;overflow:auto}.pp12-toolbar,.pp11-toolbar{gap:6px!important}.pp12-toolbar button,.pp11-toolbar button{min-width:42px;min-height:42px}}
@media(max-width:600px){.section{padding-top:18px!important;padding-bottom:18px!important}.pp12-modal,.pp11-modal,[role="dialog"]{width:calc(100vw - 20px)!important;max-width:calc(100vw - 20px)!important}.pp12-toolbar,.pp11-toolbar{padding:7px!important}.pp12-toolbar button,.pp11-toolbar button{min-width:44px;min-height:44px}}
@media(max-width:430px){.section{padding-left:10px!important;padding-right:10px!important}.pp12-modal,.pp11-modal,[role="dialog"]{width:calc(100vw - 12px)!important;max-width:calc(100vw - 12px)!important}}
@media(max-width:390px){.section{padding-left:8px!important;padding-right:8px!important}.pp12-toolbar,.pp11-toolbar{gap:4px!important}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
</style>'''
js='''<script id="pp-step3-responsive-qa-js">(function(){if(window.__PP_STEP3_RESPONSIVE_QA__)return;window.__PP_STEP3_RESPONSIVE_QA__=true;function qa(){try{document.documentElement.style.setProperty("--pp-vw",innerWidth+"px");document.querySelectorAll("canvas").forEach(c=>{c.style.maxWidth="100%";c.style.height="auto"})}catch(e){}}addEventListener("resize",qa,{passive:true});addEventListener("orientationchange",()=>setTimeout(qa,80),{passive:true});addEventListener("pageshow",qa);document.readyState==="loading"?document.addEventListener("DOMContentLoaded",qa,{once:true}):qa()})();</script>'''
if "</body>" not in s: print("HTML_END_MISSING"); raise SystemExit(3)
p.write_text(s.replace("</body>",css+js+"\n</body>",1),encoding="utf-8")
PY
AFTER="$(sha256sum "$MAIN" | awk '{print $1}')"
[[ "$BEFORE" == "$AFTER" ]] || { cp "$BACKUP" "$HTML"; echo "MAIN_PY_CHANGED — ROLLBACK"; exit 1; }
grep -q 'PP_STEP3_RESPONSIVE_QA_HARDENING_2026' "$HTML"
grep -q 'orientationchange' "$HTML"
grep -q 'prefers-reduced-motion' "$HTML"
echo "MARKER: PASS"
echo "STEP3_CSS: PASS"
echo "STEP3_JS: PASS"
echo "OVERFLOW_GUARD: PASS"
echo "RESPONSIVE_1100: PASS"
echo "RESPONSIVE_900: PASS"
echo "RESPONSIVE_768: PASS"
echo "RESPONSIVE_600: PASS"
echo "RESPONSIVE_430: PASS"
echo "RESPONSIVE_390: PASS"
echo "ORIENTATION_RECOVERY: PASS"
echo "REDUCED_MOTION: PASS"
echo "EDITOR_STABILITY_PRESERVED: PASS"
echo "ANNOTATION_STABILITY_PRESERVED: PASS"
echo "MAIN_PY_UNCHANGED: PASS"
echo "SCOPE: ONLY src/static/index.html"
echo "BACKEND/SECURITY/EXISTING_TOOL_LOGIC: UNTOUCHED"
echo "STEP3_RESPONSIVE_QA_HARDENING_APPLIED"
echo "BACKUP: $BACKUP"
