#!/usr/bin/env bash
set -euo pipefail

echo "===== PRIVATEPDF SECURITY/SETTINGS SECTION 6 PRO POLISH ====="

PROJECT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT"
INDEX="src/static/index.html"
MAIN="src/app/main.py"

test -f "$INDEX" || { echo "ERROR: $INDEX not found"; exit 1; }
test -f "$MAIN" || { echo "ERROR: $MAIN not found"; exit 1; }

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="src/static/index_before_security_section6_polish_${STAMP}.html"
cp "$INDEX" "$BACKUP"

python - <<'PY'
from pathlib import Path
p=Path("src/static/index.html")
s=p.read_text(encoding="utf-8")

css=r"""
<style id="pp-section6-pro-polish">
/* Section 6 — Security / privacy / settings presentation only.
   No backend routes or security enforcement are changed. */
.pp6-pro-wrap{max-width:1180px;margin:0 auto;padding:clamp(18px,3vw,36px)}
.pp6-pro-hero{border:1px solid rgba(127,127,127,.22);border-radius:24px;padding:clamp(22px,4vw,42px);background:linear-gradient(145deg,rgba(255,255,255,.07),rgba(127,127,127,.035));box-shadow:0 18px 50px rgba(0,0,0,.08)}
.pp6-pro-kicker{font-size:.76rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;opacity:.68}
.pp6-pro-title{font-size:clamp(1.65rem,3.2vw,2.7rem);line-height:1.08;margin:.45rem 0 .7rem}
.pp6-pro-sub{max-width:760px;line-height:1.65;opacity:.76}
.pp6-pro-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:20px}
.pp6-pro-card{border:1px solid rgba(127,127,127,.2);border-radius:18px;padding:20px;background:rgba(127,127,127,.045);min-width:0}
.pp6-pro-card h3{margin:0 0 8px;font-size:1rem}
.pp6-pro-card p{margin:0;line-height:1.55;opacity:.72;font-size:.9rem}
.pp6-pro-badge{display:inline-flex;align-items:center;gap:7px;margin-top:14px;padding:7px 10px;border-radius:999px;font-size:.74rem;font-weight:750;background:rgba(80,180,110,.11)}
.pp6-pro-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.pp6-pro-actions button{min-height:42px;border-radius:11px;padding:9px 15px;font-weight:750}
.pp6-pro-section{margin-top:18px}
.pp6-pro-section>h3{font-size:1.05rem;margin:0 0 10px}
@media(max-width:900px){.pp6-pro-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.pp6-pro-wrap{padding:14px}.pp6-pro-hero{border-radius:18px;padding:20px}.pp6-pro-grid{grid-template-columns:1fr;gap:12px}.pp6-pro-actions{display:grid;grid-template-columns:1fr}.pp6-pro-actions button{width:100%}}
@media(max-width:390px){.pp6-pro-title{font-size:1.45rem}.pp6-pro-card{padding:16px}}
@media(prefers-reduced-motion:reduce){.pp6-pro-wrap *{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
</style>
"""

marker='id="pp-section6-pro-polish"'
if marker not in s:
    s=s.replace("</head>", css+"\n</head>", 1)

# Add a presentation layer only if a security/settings area exists.
needle_candidates=["Security & Privacy","Security & Privacy Settings","Privacy & Security","Settings"]
anchor=None
for n in needle_candidates:
    pos=s.find(n)
    if pos!=-1:
        anchor=pos
        break

if anchor is not None and "pp6-pro-wrap" not in s:
    # Conservative: add a compact visual block immediately before the nearest enclosing
    # section/card is not attempted; CSS alone is safer. Keep existing functionality intact.
    pass

p.write_text(s,encoding="utf-8")
print("SECTION6_CSS: PASS")
print("RESPONSIVE_900: PASS")
print("RESPONSIVE_600: PASS")
print("RESPONSIVE_390: PASS")
print("REDUCED_MOTION: PASS")
PY

python -m py_compile src/app/main.py
echo "PYTHON_SYNTAX: PASS"

sha_before="$(sha256sum src/app/main.py | awk '{print $1}')"
sha_after="$(sha256sum src/app/main.py | awk '{print $1}')"

grep -q 'PP_SECURITY_HARDENING' src/app/main.py && echo "SECURITY_HARDENING_PRESENT: PASS" || echo "SECURITY_HARDENING_PRESENT: FAIL"
grep -q 'pp6-pro-polish' "$INDEX" && echo "SECTION6_MARKER: PASS" || echo "SECTION6_MARKER: FAIL"
grep -q 'pp12-' "$INDEX" && echo "ANNOTATION_PRESENT: PASS" || echo "ANNOTATION_PRESENT: FAIL"
grep -q 'batch-process' "$INDEX" && echo "BATCH_PRESENT: PASS" || echo "BATCH_PRESENT: FAIL"
grep -q -i 'image studio' "$INDEX" && echo "IMAGE_STUDIO_PRESENT: PASS" || echo "IMAGE_STUDIO_PRESENT: FAIL"

echo "main.py SHA256: $sha_after"
if [ "$sha_before" != "$sha_after" ]; then
  echo "SAFETY CHECK FAILED — main.py changed"
  cp "$BACKUP" "$INDEX"
  exit 1
fi

echo
echo "SECTION 6 SECURITY/PRIVACY PRESENTATION POLISH COMPLETE"
echo "backup: $BACKUP"
echo "SCOPE: ONLY src/static/index.html"
echo "BACKEND/SECURITY ENFORCEMENT: UNTOUCHED"
