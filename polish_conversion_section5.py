#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import hashlib, shutil, re

ROOT=Path.cwd()
INDEX=ROOT/"src"/"static"/"index.html"
MAIN=ROOT/"src"/"app"/"main.py"
MARKER="PP_CONVERSION_SECTION5_PRO_POLISH_V1"

CSS=r"""
<!-- PP_CONVERSION_SECTION5_PRO_POLISH_V1 -->
<style id="pp-conversion-section5-pro-polish-v1">
/* =========================================================
   CONVERSION STUDIO — PROFESSIONAL UI/UX POLISH
   Scope: #pp10ConversionStudio only.
   No JS/event handlers/backend routes are modified.
   ========================================================= */
#pp10ConversionStudio{
 --pp10-text:#172033;--pp10-muted:#667085;--pp10-line:#e3e8f1;
 --pp10-brand:#4f46e5;--pp10-brand2:#6366f1;
 --pp10-card:#fff;--pp10-soft:#f8faff;
 width:100%;box-sizing:border-box;color:var(--pp10-text)
}
#pp10ConversionStudio .pp10-conversion-shell{width:100%;max-width:1280px;margin:0 auto}
#pp10ConversionStudio .pp10-hero{
 padding:clamp(22px,3vw,36px);border:1px solid var(--pp10-line);
 border-radius:24px;background:linear-gradient(135deg,#fff,#f7f8ff);
 box-shadow:0 14px 42px rgba(15,23,42,.07);margin-bottom:22px
}
#pp10ConversionStudio .pp10-hero h2{
 margin:0;color:var(--pp10-text);font-size:clamp(25px,2.7vw,36px);
 line-height:1.12;letter-spacing:-.04em;font-weight:850
}
#pp10ConversionStudio .pp10-hero>p{
 margin:9px 0 22px;max-width:760px;color:var(--pp10-muted);
 font-size:clamp(13px,1.2vw,15px);line-height:1.65
}
#pp10ConversionStudio .pp10-info-strip{
 display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px
}
#pp10ConversionStudio .pp10-info{
 min-width:0;padding:13px 15px;border:1px solid var(--pp10-line);
 border-radius:14px;background:rgba(255,255,255,.78)
}
#pp10ConversionStudio .pp10-info strong{
 display:block;font-size:12px;font-weight:850;letter-spacing:.03em
}
#pp10ConversionStudio .pp10-info span{
 display:block;margin-top:4px;color:var(--pp10-muted);font-size:11px;line-height:1.35
}
#pp10ConversionStudio .pp10-converter-grid{
 display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
 gap:clamp(14px,1.6vw,22px);align-items:stretch
}
#pp10ConversionStudio .pp10-converter-card{
 position:relative;display:flex;flex-direction:column;min-width:0;
 min-height:360px;padding:clamp(19px,2vw,26px);
 border:1px solid var(--pp10-line);border-radius:20px;
 background:linear-gradient(180deg,#fff,#f9fafc);
 box-shadow:0 12px 34px rgba(15,23,42,.07);
 overflow:hidden;transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease
}
#pp10ConversionStudio .pp10-converter-card:before{
 content:"";position:absolute;inset:0 0 auto;height:3px;
 background:linear-gradient(90deg,var(--pp10-brand),var(--pp10-brand2))
}
#pp10ConversionStudio .pp10-converter-card:hover{
 transform:translateY(-3px);border-color:rgba(79,70,229,.27);
 box-shadow:0 21px 48px rgba(15,23,42,.12)
}
#pp10ConversionStudio .pp10-converter-icon{
 width:48px;height:48px;display:grid;place-items:center;margin-bottom:15px;
 border-radius:14px;background:#eef2ff;color:var(--pp10-brand);
 font-size:12px;font-weight:900;letter-spacing:.04em
}
#pp10ConversionStudio .pp10-converter-card h3{
 margin:0 52px 8px 0;font-size:clamp(17px,1.5vw,20px);
 line-height:1.25;font-weight:820;letter-spacing:-.02em
}
#pp10ConversionStudio .pp10-converter-card>p{
 margin:0 0 17px;color:var(--pp10-muted);font-size:13px;line-height:1.55;
 min-height:40px
}
#pp10ConversionStudio .pp10-drop{
 display:flex!important;flex-direction:column!important;justify-content:center!important;
 align-items:center!important;gap:5px!important;width:100%;min-height:112px;
 box-sizing:border-box;margin:0 0 12px;padding:18px;
 border:1.5px dashed #c6d0df!important;border-radius:16px!important;
 background:linear-gradient(180deg,#fbfcff,#f6f8fc)!important;
 text-align:center;cursor:pointer;transition:border-color .18s ease,background .18s ease
}
#pp10ConversionStudio .pp10-drop:hover{
 border-color:rgba(79,70,229,.55)!important;background:#f5f6ff!important
}
#pp10ConversionStudio .pp10-drop strong{font-size:13px;font-weight:800;color:var(--pp10-text)}
#pp10ConversionStudio .pp10-drop span{font-size:11px;color:var(--pp10-muted)}
#pp10ConversionStudio .pp10-drop input[type=file]{
 position:absolute;width:1px;height:1px;opacity:0;pointer-events:none
}
#pp10ConversionStudio .pp10-files{
 min-height:0;margin-bottom:10px;color:var(--pp10-muted);font-size:11px
}
#pp10ConversionStudio .pp10-converter-card select{
 width:100%!important;box-sizing:border-box;min-height:46px!important;
 margin:0 0 12px!important;padding:10px 12px!important;
 border:1px solid #d9e0eb!important;border-radius:12px!important;
 background:#fff!important;color:var(--pp10-text);font-size:13px
}
#pp10ConversionStudio .pp10-converter-card select:focus{
 outline:none;border-color:var(--pp10-brand);
 box-shadow:0 0 0 4px rgba(79,70,229,.09)
}
#pp10ConversionStudio .pp10-convert-btn{
 width:100%;min-height:47px!important;margin-top:auto;
 border:1px solid rgba(79,70,229,.12)!important;border-radius:12px!important;
 background:linear-gradient(135deg,var(--pp10-brand),var(--pp10-brand2))!important;
 color:#fff!important;font-size:13px!important;font-weight:800!important;
 box-shadow:0 8px 20px rgba(79,70,229,.18);
 cursor:pointer;transition:transform .16s ease,box-shadow .16s ease,filter .16s ease
}
#pp10ConversionStudio .pp10-convert-btn:hover{
 transform:translateY(-1px);filter:brightness(1.02);
 box-shadow:0 12px 27px rgba(79,70,229,.25)
}
#pp10ConversionStudio .pp10-convert-btn:focus-visible{
 outline:3px solid rgba(79,70,229,.2);outline-offset:2px
}
#pp10ConversionStudio .pp10-badge{
 position:absolute;top:17px;right:17px;padding:6px 9px;
 border-radius:999px;background:#eef2ff;color:var(--pp10-brand);
 font-size:10px;font-weight:850;letter-spacing:.04em
}
@media(max-width:980px){
 #pp10ConversionStudio .pp10-info-strip{grid-template-columns:repeat(2,1fr)}
 #pp10ConversionStudio .pp10-converter-grid{gap:14px}
}
@media(max-width:700px){
 #pp10ConversionStudio .pp10-hero{padding:20px;border-radius:19px}
 #pp10ConversionStudio .pp10-converter-grid{grid-template-columns:1fr}
 #pp10ConversionStudio .pp10-converter-card{min-height:0;padding:19px;border-radius:17px}
 #pp10ConversionStudio .pp10-converter-card>p{min-height:0}
}
@media(max-width:480px){
 #pp10ConversionStudio .pp10-hero{padding:17px;margin-bottom:14px}
 #pp10ConversionStudio .pp10-hero h2{font-size:24px}
 #pp10ConversionStudio .pp10-hero>p{font-size:13px;margin-bottom:17px}
 #pp10ConversionStudio .pp10-info-strip{grid-template-columns:1fr 1fr;gap:8px}
 #pp10ConversionStudio .pp10-info{padding:11px 12px}
 #pp10ConversionStudio .pp10-converter-grid{gap:10px}
 #pp10ConversionStudio .pp10-converter-card{padding:16px;border-radius:15px}
 #pp10ConversionStudio .pp10-drop{min-height:105px!important}
}
@media(max-width:350px){
 #pp10ConversionStudio .pp10-info-strip{grid-template-columns:1fr}
 #pp10ConversionStudio .pp10-converter-card{padding:14px}
}
@media(prefers-reduced-motion:reduce){
 #pp10ConversionStudio *,#pp10ConversionStudio *:before,#pp10ConversionStudio *:after{
  transition:none!important;animation:none!important;scroll-behavior:auto!important
 }
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

if not re.search(r'id=["\']pp10ConversionStudio["\']',before,re.I):
 raise SystemExit("ERROR: pp10ConversionStudio not found")

ts=datetime.now().strftime("%Y%m%d_%H%M%S")
backup=INDEX.with_name(f"index_before_conversion_section5_polish_{ts}.html")
shutil.copy2(INDEX,backup)

try:
 pos=before.lower().rfind("</head>")
 if pos<0: raise RuntimeError("</head> not found")
 updated=before[:pos]+"\n"+CSS+"\n"+before[pos:]
 INDEX.write_text(updated,encoding="utf-8")

 checks={
  "MARKER":MARKER in updated,
  "CONVERSION_STUDIO":'id="pp10ConversionStudio"' in updated,
  "PDF_TO_JPG":"pp10PdfJpgFile" in updated,
  "PDF_TO_OFFICE":"pp10PdfOfficeFile" in updated,
  "OFFICE_TO_PDF":"pp10OfficePdfFile" in updated,
  "IMAGES_TO_PDF":"pp10ImagesPdfFilesInput" in updated,
  "PRO_CSS":"pp-conversion-section5-pro-polish-v1" in updated,
  "RESPONSIVE_980":"@media(max-width:980px)" in updated,
  "RESPONSIVE_700":"@media(max-width:700px)" in updated,
  "RESPONSIVE_480":"@media(max-width:480px)" in updated,
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
 print("CONVERSION_SECTION5_PRO_POLISH_APPLIED")
 print(f"backup: {backup.name}")
 print(f"main.py SHA256 before: {main_before}")
 print(f"main.py SHA256 after : {sha(MAIN)}")
 print(f"index.html bytes: {INDEX.stat().st_size}")
 print()
 print("VISIBLE IMPACT: HERO + INFO STRIP + CONVERSION CARDS + DROP ZONES + ACTIONS")
 print("SCOPE: ONLY src/static/index.html")
 print("BACKEND/SECURITY/JS LOGIC: UNTOUCHED")
 print("SECTION 5 CONVERSION STUDIO PRO POLISH COMPLETE")
except Exception as exc:
 shutil.copy2(backup,INDEX)
 print()
 print("SAFETY CHECK FAILED — ORIGINAL FILE RESTORED")
 print(f"Reason: {exc}")
 print(f"Restored from: {backup.name}")
 raise SystemExit(1)
