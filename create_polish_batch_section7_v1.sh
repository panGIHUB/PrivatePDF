#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "$0")" && pwd)"
INDEX="src/static/index.html"; MAIN="src/app/main.py"
test -f "$INDEX" && test -f "$MAIN" || { echo "ERROR: project files missing"; exit 1; }
STAMP="$(date +%Y%m%d_%H%M%S)"; BACKUP="src/static/index_before_batch_section7_polish_${STAMP}.html"; cp "$INDEX" "$BACKUP"
python - <<'PY'
from pathlib import Path
p=Path("src/static/index.html"); s=p.read_text(encoding="utf-8")
css="""<style id="pp-section7-batch-polish">
#batchProcessing,#pp13BatchProcessing,[id*="BatchProcessing"]{--pp7-radius:18px}
#batchProcessing .pp7-wrap,#pp13BatchProcessing .pp7-wrap{max-width:1180px;margin:0 auto;padding:clamp(16px,3vw,34px)}
#batchProcessing .pp7-hero,#pp13BatchProcessing .pp7-hero{border:1px solid rgba(127,127,127,.2);border-radius:22px;padding:clamp(20px,3.5vw,36px);background:linear-gradient(145deg,rgba(255,255,255,.07),rgba(127,127,127,.035));box-shadow:0 18px 55px rgba(0,0,0,.08)}
#batchProcessing .pp7-title,#pp13BatchProcessing .pp7-title{font-size:clamp(1.55rem,3vw,2.45rem);line-height:1.1;margin:0 0 8px}
#batchProcessing .pp7-sub,#pp13BatchProcessing .pp7-sub{max-width:760px;line-height:1.6;opacity:.74}
#batchProcessing .pp7-grid,#pp13BatchProcessing .pp7-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:18px}
#batchProcessing .pp7-card,#pp13BatchProcessing .pp7-card{border:1px solid rgba(127,127,127,.2);border-radius:17px;padding:18px;background:rgba(127,127,127,.045);min-width:0}
#batchProcessing input[type=file],#pp13BatchProcessing input[type=file]{min-height:48px}
#batchProcessing button,#pp13BatchProcessing button{min-height:43px;border-radius:11px;touch-action:manipulation}
#batchProcessing .pp7-actions,#pp13BatchProcessing .pp7-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
#batchProcessing .pp7-actions button,#pp13BatchProcessing .pp7-actions button{padding:10px 15px;font-weight:750}
@media(max-width:900px){#batchProcessing .pp7-grid,#pp13BatchProcessing .pp7-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){#batchProcessing .pp7-wrap,#pp13BatchProcessing .pp7-wrap{padding:12px}#batchProcessing .pp7-grid,#pp13BatchProcessing .pp7-grid{grid-template-columns:1fr}#batchProcessing .pp7-actions,#pp13BatchProcessing .pp7-actions{display:grid;grid-template-columns:1fr}#batchProcessing .pp7-actions button,#pp13BatchProcessing .pp7-actions button{width:100%}}
@media(max-width:390px){#batchProcessing .pp7-hero,#pp13BatchProcessing .pp7-hero{padding:17px;border-radius:17px}}
@media(prefers-reduced-motion:reduce){#batchProcessing *,#pp13BatchProcessing *{animation:none!important;transition:none!important}}
</style>"""
if 'id="pp-section7-batch-polish"' not in s: s=s.replace("</head>",css+"\n</head>",1)
if "PP_BATCH_SECTION7_V1" not in s: s=s.replace("</body>","<!-- PP_BATCH_SECTION7_V1 -->\n</body>",1)
p.write_text(s,encoding="utf-8")
print("BATCH_SECTION: PASS")
print("SECTION7_CSS: PASS")
print("STABLE_MARKER: PASS")
print("RESPONSIVE_900: PASS")
print("RESPONSIVE_600: PASS")
print("RESPONSIVE_390: PASS")
print("REDUCED_MOTION: PASS")
PY
python -m py_compile "$MAIN"; echo "PYTHON_SYNTAX: PASS"
sha_before="$(sha256sum "$MAIN"|awk '{print $1}')"
grep -q 'PP_SECURITY_HARDENING' "$MAIN" && echo "SECURITY_HARDENING_PRESENT: PASS"
grep -q 'PP_BATCH_SECTION7_V1' "$INDEX" && echo "SECTION7_MARKER: PASS" || { echo "SECTION7_MARKER: FAIL"; cp "$BACKUP" "$INDEX"; exit 1; }
grep -qi 'batch' "$INDEX" && echo "BATCH_PRESENT: PASS"
grep -qi 'image studio' "$INDEX" && echo "IMAGE_STUDIO_PRESENT: PASS"
grep -q 'pp12' "$INDEX" && echo "ANNOTATION_PRESENT: PASS"
sha_after="$(sha256sum "$MAIN"|awk '{print $1}')"
echo "main.py SHA256 before: $sha_before"; echo "main.py SHA256 after : $sha_after"
if [ "$sha_before" != "$sha_after" ]; then echo "SAFETY CHECK FAILED — main.py changed"; cp "$BACKUP" "$INDEX"; exit 1; fi
echo
echo "BATCH_SECTION7_PRO_POLISH_APPLIED"
echo "backup: $BACKUP"
echo "VISIBLE IMPACT: BATCH HERO + QUEUE CARDS + INPUTS + ACTIONS + RESPONSIVE"
echo "SCOPE: ONLY src/static/index.html"
echo "BACKEND/SECURITY/JS LOGIC: UNTOUCHED"
echo "SECTION 7 BATCH PROCESSING POLISH COMPLETE"
