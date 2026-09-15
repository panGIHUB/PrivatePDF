#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import hashlib, shutil, re

ROOT = Path.cwd()
INDEX = ROOT / "src" / "static" / "index.html"
MAIN = ROOT / "src" / "app" / "main.py"
MARKER = "PP_ORGANIZE_SECTION3_PRO_POLISH_V2"

CSS = r"""
<!-- PP_ORGANIZE_SECTION3_PRO_POLISH_V2 -->
<style id="pp-organize-section3-pro-polish-v2">
#organize{
 --pp3-text:#172033;--pp3-muted:#667085;--pp3-border:#e3e8f1;
 --pp3-accent:#4f46e5;--pp3-shadow:0 14px 38px rgba(15,23,42,.08);
 width:100%;box-sizing:border-box
}
#organize>h2{margin:0;color:var(--pp3-text);font-size:clamp(25px,2.5vw,34px);
 line-height:1.15;letter-spacing:-.035em;font-weight:850}
#organize>p{margin:8px 0 24px;color:var(--pp3-muted);font-size:clamp(13px,1.2vw,15px);
 line-height:1.6;max-width:680px}
#organize>.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
 gap:clamp(14px,1.6vw,22px);align-items:stretch}
#organize>.grid>.card{position:relative;display:flex;flex-direction:column;min-width:0;
 min-height:278px;padding:clamp(19px,2vw,26px);border:1px solid var(--pp3-border);
 border-radius:20px;background:linear-gradient(180deg,#fff,#f9fafc);
 box-shadow:var(--pp3-shadow);overflow:hidden;
 transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease}
#organize>.grid>.card:before{content:"";position:absolute;inset:0 0 auto;height:3px;
 background:linear-gradient(90deg,#4f46e5,#6366f1)}
#organize>.grid>.card:after{position:absolute;top:16px;right:17px;display:grid;place-items:center;
 width:31px;height:31px;border-radius:10px;background:#eef2ff;color:#4f46e5;font-size:12px;font-weight:850}
#organize>.grid>.card:nth-child(1):after{content:"01"}
#organize>.grid>.card:nth-child(2):after{content:"02"}
#organize>.grid>.card:nth-child(3):after{content:"03"}
#organize>.grid>.card:nth-child(4):after{content:"04"}
#organize>.grid>.card:hover{transform:translateY(-3px);border-color:rgba(79,70,229,.28);
 box-shadow:0 22px 50px rgba(15,23,42,.13)}
#organize>.grid>.card h3{margin:0 50px 8px 0;color:var(--pp3-text);
 font-size:clamp(16px,1.45vw,19px);line-height:1.25;font-weight:800}
#organize>.grid>.card p{margin:0 0 17px;color:var(--pp3-muted);font-size:13px;
 line-height:1.55;min-height:40px}
#organize>.grid>.card input[type=file]{width:100%;box-sizing:border-box;min-height:46px;
 margin:0 0 11px;padding:8px 10px;border:1px solid #d9e0eb;border-radius:12px;
 background:#fbfcfe;color:#475467;font-size:12px;cursor:pointer}
#organize>.grid>.card input[type=file]:hover{border-color:#b8c2d2;background:#fff}
#organize>.grid>.card input[type=text],
#organize>.grid>.card input:not([type]){width:100%;box-sizing:border-box;min-height:46px;
 margin:0 0 11px;padding:11px 13px;border:1px solid #d9e0eb;border-radius:12px;
 background:#fff;color:var(--pp3-text);font-size:13px}
#organize>.grid>.card input[type=text]:focus,
#organize>.grid>.card input:not([type]):focus{outline:none;border-color:#4f46e5;
 box-shadow:0 0 0 4px rgba(79,70,229,.09)}
#organize>.grid>.card button.primary{width:100%;min-height:46px;margin-top:auto;
 border:1px solid rgba(79,70,229,.12);border-radius:12px;
 background:linear-gradient(135deg,#4f46e5,#6366f1);color:#fff;font-size:13px;
 font-weight:800;box-shadow:0 8px 20px rgba(79,70,229,.18);cursor:pointer;
 transition:transform .16s ease,box-shadow .16s ease}
#organize>.grid>.card button.primary:hover{transform:translateY(-1px);
 box-shadow:0 12px 26px rgba(79,70,229,.25)}
#organize>.grid>.card button.primary:focus-visible,
#organize input:focus-visible{outline:3px solid rgba(79,70,229,.2);outline-offset:2px}
#organize .drop{display:flex;align-items:center;min-height:64px;margin-bottom:11px;padding:7px;
 border:1px dashed #c8d2e0;border-radius:14px;background:linear-gradient(180deg,#fbfcff,#f7f9fd)}
#organize .drop input[type=file]{margin:0;border:0;background:transparent}
@media(max-width:900px){
 #organize>.grid{grid-template-columns:1fr 1fr;gap:14px}
 #organize>.grid>.card{min-height:270px;padding:18px;border-radius:17px}
}
@media(max-width:680px){
 #organize>.grid{grid-template-columns:1fr}
 #organize>.grid>.card{min-height:0;padding:18px}
 #organize>.grid>.card p{min-height:0}
}
@media(max-width:430px){
 #organize>h2{font-size:24px} #organize>p{margin-bottom:18px}
 #organize>.grid{gap:11px} #organize>.grid>.card{padding:16px;border-radius:15px}
 #organize>.grid>.card h3{font-size:16px}
 #organize>.grid>.card input[type=file],
 #organize>.grid>.card input[type=text],
 #organize>.grid>.card input:not([type]),
 #organize>.grid>.card button.primary{min-height:45px}
}
@media(max-width:350px){
 #organize>.grid>.card{padding:14px}
 #organize>.grid>.card:after{display:none}
 #organize>.grid>.card h3{margin-right:0}
}
@media(prefers-reduced-motion:reduce){
 #organize *,#organize *:before,#organize *:after{
  transition:none!important;animation:none!important;scroll-behavior:auto!important}
}
</style>
"""

def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

if not INDEX.exists():
    raise SystemExit(f"ERROR: {INDEX} not found")
if not MAIN.exists():
    raise SystemExit(f"ERROR: {MAIN} not found")

before = INDEX.read_text(encoding="utf-8")
main_before = sha256(MAIN)

if MARKER in before:
    print("PATCH_ALREADY_PRESENT")
    raise SystemExit(0)

if not re.search(r'<section\s+id=["\']organize["\']', before, re.I):
    raise SystemExit("ERROR: existing #organize section not found")

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = INDEX.with_name(f"index_before_organize_section3_polish_{ts}.html")
shutil.copy2(INDEX, backup)

try:
    pos = before.lower().rfind("</head>")
    if pos < 0:
        raise RuntimeError("</head> not found")

    updated = before[:pos] + "\n" + CSS + "\n" + before[pos:]
    INDEX.write_text(updated, encoding="utf-8")

    checks = {
      "MARKER": MARKER in updated,
      "ORGANIZE_SECTION": bool(re.search(r'<section\s+id=["\']organize["\']',updated,re.I)),
      "MERGE_TOOL": "mergeFiles" in updated,
      "EXTRACT_TOOL": "pagesFile" in updated and "pageOp('extract')" in updated,
      "DELETE_TOOL": "delFile" in updated and "pageOp2('delete')" in updated,
      "REORDER_TOOL": "reorderFile" in updated and "pageOp3('reorder')" in updated,
      "SECTION3_CSS": "pp-organize-section3-pro-polish-v2" in updated,
      "RESPONSIVE_900": "@media(max-width:900px)" in updated,
      "RESPONSIVE_680": "@media(max-width:680px)" in updated,
      "RESPONSIVE_430": "@media(max-width:430px)" in updated,
      "RESPONSIVE_350": "@media(max-width:350px)" in updated,
      "REDUCED_MOTION": "prefers-reduced-motion" in updated,
      "ANNOTATION_PRESENT": "annotation" in updated.lower(),
      "BATCH_PRESENT": "batch" in updated.lower(),
      "IMAGE_STUDIO_PRESENT": "image studio" in updated.lower(),
      "MAIN_PY_UNCHANGED": sha256(MAIN) == main_before,
      "HTML_END": "</html>" in updated.lower(),
    }

    for k,v in checks.items():
        print(f"{k}: {'PASS' if v else 'FAIL'}")

    if not all(checks.values()):
        raise RuntimeError("One or more safety checks failed")

    print()
    print("ORGANIZE_SECTION3_PRO_POLISH_APPLIED")
    print(f"backup: {backup.name}")
    print(f"main.py SHA256 before: {main_before}")
    print(f"main.py SHA256 after : {sha256(MAIN)}")
    print(f"index.html bytes: {INDEX.stat().st_size}")
    print()
    print("VISIBLE IMPACT: PRO CARD LAYOUT + INPUTS + ACTIONS + RESPONSIVE")
    print("SCOPE: ONLY src/static/index.html")
    print("BACKEND/SECURITY/JS LOGIC: UNTOUCHED")
    print("SECTION 3 ORGANIZE PDFs PRO POLISH COMPLETE")

except Exception as exc:
    shutil.copy2(backup, INDEX)
    print()
    print("SAFETY CHECK FAILED — ORIGINAL FILE RESTORED")
    print(f"Reason: {exc}")
    print(f"Restored from: {backup.name}")
    raise SystemExit(1)
