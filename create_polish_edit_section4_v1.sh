#!/usr/bin/env bash
set -euo pipefail

cat > polish_edit_section4.py <<'PY'
#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import hashlib, shutil, re

ROOT=Path.cwd()
INDEX=ROOT/"src"/"static"/"index.html"
MAIN=ROOT/"src"/"app"/"main.py"
MARKER="PP_EDIT_SECTION4_PRO_POLISH_V1"

CSS=r"""
<!-- PP_EDIT_SECTION4_PRO_POLISH_V1 -->
<style id="pp-edit-section4-pro-polish-v1">
/* EDIT & LAYOUT — professional UI/UX; scope is #edit only */
#edit{
 --pp4-text:#172033;--pp4-muted:#667085;--pp4-line:#e3e8f1;
 --pp4-brand:#4f46e5;--pp4-brand2:#6366f1;
 width:100%;box-sizing:border-box;
}
#edit>h2{margin:0;color:var(--pp4-text);font-size:clamp(25px,2.5vw,34px);
 line-height:1.15;letter-spacing:-.035em;font-weight:850}
#edit>p{margin:8px 0 24px;color:var(--pp4-muted);font-size:clamp(13px,1.2vw,15px);
 line-height:1.6;max-width:720px}
#edit>.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
 gap:clamp(14px,1.6vw,22px);align-items:stretch}
#edit>.grid>.card{position:relative;display:flex;flex-direction:column;min-width:0;
 min-height:285px;padding:clamp(19px,2vw,26px);border:1px solid var(--pp4-line);
 border-radius:20px;background:linear-gradient(180deg,#fff,#f9fafc);
 box-shadow:0 12px 34px rgba(15,23,42,.07);overflow:hidden;
 transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease}
#edit>.grid>.card:before{content:"";position:absolute;inset:0 0 auto;height:3px;
 background:linear-gradient(90deg,var(--pp4-brand),var(--pp4-brand2))}
#edit>.grid>.card:hover{transform:translateY(-3px);
 border-color:rgba(79,70,229,.27);box-shadow:0 21px 48px rgba(15,23,42,.12)}
#edit>.grid>.card h3{margin:0 0 8px;color:var(--pp4-text);
 font-size:clamp(16px,1.45vw,19px);line-height:1.25;font-weight:800}
#edit>.grid>.card p{margin:0 0 17px;color:var(--pp4-muted);font-size:13px;
 line-height:1.55;min-height:40px}
#edit>.grid>.card input[type=file],
#edit>.grid>.card input[type=text],
#edit>.grid>.card input:not([type]),
#edit>.grid>.card select{width:100%;box-sizing:border-box;min-height:46px;
 margin:0 0 11px;padding:10px 12px;border:1px solid #d9e0eb;border-radius:12px;
 background:#fff;color:var(--pp4-text);font-size:13px}
#edit>.grid>.card input[type=file]{padding:8px 10px;background:#fbfcfe;
 color:#475467;font-size:12px;cursor:pointer}
#edit>.grid>.card input:focus,
#edit>.grid>.card select:focus{outline:none;border-color:var(--pp4-brand);
 box-shadow:0 0 0 4px rgba(79,70,229,.09)}
#edit>.grid>.card button.primary{width:100%;min-height:46px;margin-top:auto;
 border:1px solid rgba(79,70,229,.12);border-radius:12px;
 background:linear-gradient(135deg,var(--pp4-brand),var(--pp4-brand2));
 color:#fff;font-size:13px;font-weight:800;box-shadow:0 8px 20px rgba(79,70,229,.18);
 cursor:pointer;transition:transform .16s ease,box-shadow .16s ease}
#edit>.grid>.card button.primary:hover{transform:translateY(-1px);
 box-shadow:0 12px 26px rgba(79,70,229,.25)}
#edit>.grid>.card button.primary:focus-visible,
#edit input:focus-visible,#edit select:focus-visible{
 outline:3px solid rgba(79,70,229,.2);outline-offset:2px}
#edit>.grid>.card .row,#edit>.grid>.card .row3{
 gap:9px;margin-bottom:2px}
#edit>.grid>.card .label{color:#475467;font-size:11px;font-weight:800}
#edit>.grid>.card .note{color:#667085;font-size:11px;line-height:1.5}
@media(max-width:900px){
 #edit>.grid{grid-template-columns:1fr 1fr;gap:14px}
 #edit>.grid>.card{min-height:275px;padding:18px;border-radius:17px}
}
@media(max-width:680px){
 #edit>.grid{grid-template-columns:1fr}
 #edit>.grid>.card{min-height:0;padding:18px}
 #edit>.grid>.card p{min-height:0}
}
@media(max-width:430px){
 #edit>h2{font-size:24px}#edit>p{margin-bottom:18px}
 #edit>.grid{gap:11px}#edit>.grid>.card{padding:16px;border-radius:15px}
 #edit>.grid>.card h3{font-size:16px}
 #edit>.grid>.card input[type=file],
 #edit>.grid>.card input[type=text],
 #edit>.grid>.card input:not([type]),
 #edit>.grid>.card select,
 #edit>.grid>.card button.primary{min-height:45px}
}
@media(max-width:350px){
 #edit>.grid>.card{padding:14px}
}
@media(prefers-reduced-motion:reduce){
 #edit *,#edit *:before,#edit *:after{
  transition:none!important;animation:none!important;scroll-behavior:auto!important}
}
</style>
"""

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

if not INDEX.exists(): raise SystemExit(f"ERROR: {INDEX} not found")
if not MAIN.exists(): raise SystemExit(f"ERROR: {MAIN} not found")

before=INDEX.read_text(encoding="utf-8")
main_before=sha(MAIN)

if MARKER in before:
    print("PATCH_ALREADY_PRESENT"); raise SystemExit(0)

if not re.search(r'<section\s+id=["\']edit["\']',before,re.I):
    raise SystemExit("ERROR: existing #edit section not found")

ts=datetime.now().strftime("%Y%m%d_%H%M%S")
backup=INDEX.with_name(f"index_before_edit_section4_polish_{ts}.html")
shutil.copy2(INDEX,backup)

try:
    pos=before.lower().rfind("</head>")
    if pos<0: raise RuntimeError("</head> not found")
    updated=before[:pos]+"\n"+CSS+"\n"+before[pos:]
    INDEX.write_text(updated,encoding="utf-8")

    checks={
      "MARKER":MARKER in updated,
      "EDIT_SECTION":bool(re.search(r'<section\s+id=["\']edit["\']',updated,re.I)),
      "ROTATE_TOOL":"rotFile" in updated,
      "NUMBERING_TOOL":"numFile" in updated or "number" in updated.lower(),
      "WATERMARK_TOOL":"watermark" in updated.lower(),
      "PAGE_NUMBERS":"page" in updated.lower(),
      "SECTION4_CSS":"pp-edit-section4-pro-polish-v1" in updated,
      "RESPONSIVE_900":"@media(max-width:900px)" in updated,
      "RESPONSIVE_680":"@media(max-width:680px)" in updated,
      "RESPONSIVE_430":"@media(max-width:430px)" in updated,
      "RESPONSIVE_350":"@media(max-width:350px)" in updated,
      "REDUCED_MOTION":"prefers-reduced-motion" in updated,
      "ANNOTATION_PRESENT":"annotation" in updated.lower(),
      "BATCH_PRESENT":"batch" in updated.lower(),
      "IMAGE_STUDIO_PRESENT":"image studio" in updated.lower(),
      "MAIN_PY_UNCHANGED":sha(MAIN)==main_before,
      "HTML_END":"</html>" in updated.lower(),
    }
    for k,v in checks.items(): print(f"{k}: {'PASS' if v else 'FAIL'}")
    if not all(checks.values()): raise RuntimeError("One or more safety checks failed")

    print()
    print("EDIT_SECTION4_PRO_POLISH_APPLIED")
    print(f"backup: {backup.name}")
    print(f"main.py SHA256 before: {main_before}")
    print(f"main.py SHA256 after : {sha(MAIN)}")
    print(f"index.html bytes: {INDEX.stat().st_size}")
    print()
    print("VISIBLE IMPACT: EDIT/LAYOUT CARD HIERARCHY + INPUTS + ACTIONS + RESPONSIVE")
    print("SCOPE: ONLY src/static/index.html")
    print("BACKEND/SECURITY/JS LOGIC: UNTOUCHED")
    print("SECTION 4 EDIT & LAYOUT PRO POLISH COMPLETE")
except Exception as exc:
    shutil.copy2(backup,INDEX)
    print()
    print("SAFETY CHECK FAILED — ORIGINAL FILE RESTORED")
    print(f"Reason: {exc}")
    print(f"Restored from: {backup.name}")
    raise SystemExit(1)
PY

python polish_edit_section4.py
