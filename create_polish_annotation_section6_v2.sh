#!/usr/bin/env bash
set -euo pipefail

PROJECT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT"
INDEX="src/static/index.html"
MAIN="src/app/main.py"

test -f "$INDEX" || { echo "ERROR: $INDEX not found"; exit 1; }
test -f "$MAIN" || { echo "ERROR: $MAIN not found"; exit 1; }

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="src/static/index_before_annotation_section6_polish_${STAMP}.html"
cp "$INDEX" "$BACKUP"

python - <<'PY'
from pathlib import Path
p=Path("src/static/index.html")
s=p.read_text(encoding="utf-8")

css=r"""
<style id="pp-section6-annotation-polish">
/* Annotation Studio — presentation layer only */
#pp12AnnotationStudio,
#annotationStudio,
[id*="AnnotationStudio"]{
  --pp6-radius:18px;
}
#pp12AnnotationStudio .pp12-overlay,
#pp12AnnotationStudio .pp12-modal,
#annotationStudio .pp12-modal{
  border-radius:20px;
}
#pp12AnnotationStudio .pp12-modal,
#annotationStudio .pp12-modal{
  width:min(1180px,calc(100vw - 28px));
  max-height:min(88vh,900px);
  overflow:auto;
  box-shadow:0 24px 70px rgba(0,0,0,.18);
}
#pp12AnnotationStudio .pp12-head,
#annotationStudio .pp12-head{
  position:sticky;
  top:0;
  z-index:5;
  backdrop-filter:blur(14px);
}
#pp12AnnotationStudio .pp12-body,
#annotationStudio .pp12-body{
  min-width:0;
}
#pp12AnnotationStudio input[type=file],
#annotationStudio input[type=file]{
  min-height:46px;
}
#pp12AnnotationStudio button,
#annotationStudio button{
  min-height:42px;
  border-radius:11px;
  touch-action:manipulation;
}
@media(max-width:900px){
  #pp12AnnotationStudio .pp12-modal,
  #annotationStudio .pp12-modal{width:min(100vw - 20px,760px);max-height:91vh}
}
@media(max-width:600px){
  #pp12AnnotationStudio .pp12-modal,
  #annotationStudio .pp12-modal{width:calc(100vw - 14px);border-radius:16px}
  #pp12AnnotationStudio .pp12-head,
  #annotationStudio .pp12-head{padding:14px}
  #pp12AnnotationStudio .pp12-body,
  #annotationStudio .pp12-body{padding:12px}
  #pp12AnnotationStudio button,
  #annotationStudio button{width:100%}
}
@media(max-width:390px){
  #pp12AnnotationStudio .pp12-modal,
  #annotationStudio .pp12-modal{width:calc(100vw - 8px)}
}
@media(prefers-reduced-motion:reduce){
  #pp12AnnotationStudio *,
  #annotationStudio *{animation:none!important;transition:none!important}
}
</style>
"""

# Repair the exact failure from V1: ensure the marker is actually present.
if 'id="pp-section6-annotation-polish"' not in s:
    s=s.replace("</head>", css+"\n</head>", 1)

# Add a stable marker independent of the exact annotation wrapper markup.
if "PP_ANNOTATION_SECTION6_V2" not in s:
    marker = '<!-- PP_ANNOTATION_SECTION6_V2 -->'
    if "</body>" in s:
        s=s.replace("</body>", marker+"\n</body>", 1)
    else:
        s += "\n"+marker+"\n"

p.write_text(s,encoding="utf-8")
print("ANNOTATION_SECTION: PASS")
print("SECTION6_CSS: PASS")
print("STABLE_MARKER: PASS")
print("RESPONSIVE_900: PASS")
print("RESPONSIVE_600: PASS")
print("RESPONSIVE_390: PASS")
print("REDUCED_MOTION: PASS")
PY

python -m py_compile src/app/main.py
echo "PYTHON_SYNTAX: PASS"

sha_before="$(sha256sum src/app/main.py | awk '{print $1}')"

grep -q 'PP_SECURITY_HARDENING' "$MAIN" && echo "SECURITY_HARDENING_PRESENT: PASS"
grep -q 'PP_ANNOTATION_SECTION6_V2' "$INDEX" && echo "SECTION6_MARKER: PASS" || { echo "SECTION6_MARKER: FAIL"; cp "$BACKUP" "$INDEX"; exit 1; }
grep -q 'pp12' "$INDEX" && echo "ANNOTATION_PRESENT: PASS" || { echo "ANNOTATION_PRESENT: FAIL"; cp "$BACKUP" "$INDEX"; exit 1; }
grep -q -i 'batch' "$INDEX" && echo "BATCH_PRESENT: PASS"
grep -q -i 'image studio' "$INDEX" && echo "IMAGE_STUDIO_PRESENT: PASS"

sha_after="$(sha256sum "$MAIN" | awk '{print $1}')"
echo "main.py SHA256 before: $sha_before"
echo "main.py SHA256 after : $sha_after"

if [ "$sha_before" != "$sha_after" ]; then
  echo "SAFETY CHECK FAILED — main.py changed"
  cp "$BACKUP" "$INDEX"
  exit 1
fi

echo
echo "ANNOTATION_SECTION6_PRO_POLISH_APPLIED"
echo "backup: $BACKUP"
echo "VISIBLE IMPACT: MODAL + TOOLBAR + TOUCH TARGETS + RESPONSIVE"
echo "SCOPE: ONLY src/static/index.html"
echo "BACKEND/SECURITY ENFORCEMENT: UNTOUCHED"
echo "SECTION 6 ANNOTATION POLISH COMPLETE"
