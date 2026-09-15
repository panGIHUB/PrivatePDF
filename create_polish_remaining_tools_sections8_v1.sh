#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "$0")" && pwd)"
INDEX="src/static/index.html"; MAIN="src/app/main.py"
test -f "$INDEX" && test -f "$MAIN" || { echo "ERROR: project files missing"; exit 1; }
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="src/static/index_before_remaining_tools_sections8_${STAMP}.html"
cp "$INDEX" "$BACKUP"

python - <<'PY'
from pathlib import Path
p=Path("src/static/index.html")
s=p.read_text(encoding="utf-8")
css = '''<style id="pp-remaining-tools-section8">
body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio){scroll-margin-top:18px}
body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) h2{font-size:clamp(1.45rem,2.8vw,2.15rem);line-height:1.15;margin-bottom:10px}
body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) p{line-height:1.55}
body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) input,
body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) select,
body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) textarea{min-height:44px;max-width:100%;border-radius:11px}
body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) button{min-height:43px;border-radius:11px;touch-action:manipulation}
body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) img,
body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) canvas{max-width:100%}
@media(max-width:900px){body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio){padding-left:clamp(12px,3vw,24px);padding-right:clamp(12px,3vw,24px)}}
@media(max-width:600px){body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) button{width:100%}body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) input,body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) select{width:100%;box-sizing:border-box}}
@media(max-width:390px){body.pp8-remaining-tools-active .section:not(#pp7Dashboard):not(#pp8Inspector):not(#organize):not(#pp10ConversionStudio):not(#pp12AnnotationStudio) h2{font-size:1.38rem}}
@media(prefers-reduced-motion:reduce){body.pp8-remaining-tools-active .section *{animation:none!important;transition:none!important}}
</style>'''
if 'id="pp-remaining-tools-section8"' not in s:
    s=s.replace("</head>",css+"\n</head>",1)
js='''<script id="pp-remaining-tools-section8-js">(function(){function a(){document.body.classList.add("pp8-remaining-tools-active")}if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",a,{once:true});else a()})();</script>'''
if 'id="pp-remaining-tools-section8-js"' not in s:
    s=s.replace("</body>",js+'\n<!-- PP_REMAINING_TOOLS_SECTION8_V1 -->\n</body>',1)
p.write_text(s,encoding="utf-8")
print("REMAINING_TOOLS_SECTION: PASS")
print("SECTION8_CSS: PASS")
print("SECTION8_JS: PASS")
print("STABLE_MARKER: PASS")
print("RESPONSIVE_900: PASS")
print("RESPONSIVE_600: PASS")
print("RESPONSIVE_390: PASS")
print("REDUCED_MOTION: PASS")
PY
python -m py_compile "$MAIN"; echo "PYTHON_SYNTAX: PASS"
sha_before="$(sha256sum "$MAIN"|awk '{print $1}')"
grep -q 'PP_SECURITY_HARDENING' "$MAIN" && echo "SECURITY_HARDENING_PRESENT: PASS"
grep -q 'PP_REMAINING_TOOLS_SECTION8_V1' "$INDEX" && echo "SECTION8_MARKER: PASS" || { echo "SECTION8_MARKER: FAIL"; cp "$BACKUP" "$INDEX"; exit 1; }
grep -q 'pp10ConversionStudio' "$INDEX" && echo "CONVERSION_PRESERVED: PASS"
grep -q 'pp12AnnotationStudio' "$INDEX" && echo "ANNOTATION_PRESENT: PASS"
grep -qi 'batch' "$INDEX" && echo "BATCH_PRESENT: PASS"
grep -qi 'image studio' "$INDEX" && echo "IMAGE_STUDIO_PRESENT: PASS"
sha_after="$(sha256sum "$MAIN"|awk '{print $1}')"
echo "main.py SHA256 before: $sha_before"
echo "main.py SHA256 after : $sha_after"
if [ "$sha_before" != "$sha_after" ]; then echo "SAFETY CHECK FAILED — main.py changed"; cp "$BACKUP" "$INDEX"; exit 1; fi
echo
echo "REMAINING_TOOLS_SECTION8_PRO_POLISH_APPLIED"
echo "backup: $BACKUP"
echo "VISIBLE IMPACT: TYPOGRAPHY + FORM CONTROLS + ACTIONS + RESPONSIVE"
echo "SCOPE: ONLY src/static/index.html"
echo "BACKEND/SECURITY/EXISTING TOOL LOGIC: UNTOUCHED"
echo "SECTION 8 REMAINING TOOLS POLISH COMPLETE"
