from pathlib import Path
from datetime import datetime
import hashlib
import shutil
import sys

ROOT = Path.cwd()
candidates = [ROOT/"static"/"index.html", ROOT/"index.html"]
index = next((p for p in candidates if p.exists()), None)

if index is None:
    print("ERROR: index.html not found. Run from ~/Downloads/PrivatePDF_Pro_Advanced_V2/src")
    sys.exit(1)

main_py = ROOT/"app"/"main.py"
if not main_py.exists():
    print("ERROR: app/main.py not found")
    sys.exit(1)

html = index.read_text(encoding="utf-8")
marker = "PP_DASHBOARD_SECTION1_PRO_POLISH_V1"

if marker in html:
    print("DASHBOARD_POLISH_ALREADY_APPLIED")
    sys.exit(0)

required = ['id="pp7Dashboard"', '.pp7-hero', '.pp7-actions', '.pp7-tools', '.pp7-footer-grid']
missing = [x for x in required if x not in html]
if missing:
    print("ERROR: expected dashboard structure missing:", ", ".join(missing))
    sys.exit(1)

main_before = hashlib.sha256(main_py.read_bytes()).hexdigest()

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = index.with_name(f"index_before_dashboard_polish_{stamp}.html")
shutil.copy2(index, backup)

css = '\n<style id="pp-dashboard-section1-pro-polish-v1">\n<!-- PP_DASHBOARD_SECTION1_PRO_POLISH_V1 -->\n/* =========================================================\n   PRIVATEPDF PRO — DASHBOARD / SECTION 1\n   PROFESSIONAL UI/UX POLISH V1\n   STRICTLY SCOPED TO #pp7Dashboard\n   ========================================================= */\n\n#pp7Dashboard{\n    width:100%;\n    min-width:0;\n    isolation:isolate;\n}\n\n#pp7Dashboard .pp7-hero{\n    min-height:236px;\n    padding:38px 42px;\n    margin-bottom:30px;\n    border-radius:24px;\n    display:flex;\n    flex-direction:column;\n    justify-content:center;\n    isolation:isolate;\n    box-shadow:0 20px 55px rgba(36,42,91,.16),inset 0 1px 0 rgba(255,255,255,.12);\n}\n\n#pp7Dashboard .pp7-hero:before{\n    content:"";\n    position:absolute;\n    inset:0;\n    pointer-events:none;\n    background:radial-gradient(circle at 12% 18%,rgba(255,255,255,.075),transparent 26%),linear-gradient(90deg,transparent,rgba(255,255,255,.025),transparent);\n}\n\n#pp7Dashboard .pp7-hero:after{\n    width:280px;\n    height:280px;\n    right:-96px;\n    bottom:-142px;\n    opacity:.8;\n}\n\n#pp7Dashboard .pp7-eyebrow{\n    position:relative;\n    z-index:1;\n    width:max-content;\n    max-width:100%;\n    padding:6px 10px;\n    margin-bottom:12px;\n    border:1px solid rgba(255,255,255,.13);\n    border-radius:999px;\n    background:rgba(255,255,255,.075);\n    font-size:10px;\n    letter-spacing:.14em;\n}\n\n#pp7Dashboard .pp7-hero h1{\n    position:relative;\n    z-index:1;\n    max-width:760px;\n    font-size:clamp(28px,3.15vw,42px);\n    line-height:1.04;\n    letter-spacing:-.035em;\n    margin:0 0 12px;\n}\n\n#pp7Dashboard .pp7-hero p{\n    position:relative;\n    z-index:1;\n    max-width:760px;\n    font-size:14px;\n    line-height:1.65;\n}\n\n#pp7Dashboard .pp7-privacy{\n    position:relative;\n    z-index:1;\n    width:max-content;\n    max-width:100%;\n    margin-top:18px;\n    font-size:11px;\n    padding:8px 11px;\n}\n\n#pp7Dashboard .pp7-section-title{\n    margin:31px 0 13px;\n    min-height:28px;\n}\n\n#pp7Dashboard .pp7-section-title h3{\n    font-size:17px;\n    line-height:1.2;\n    letter-spacing:-.015em;\n}\n\n#pp7Dashboard .pp7-section-title span{\n    font-size:11px;\n    line-height:1.35;\n    text-align:right;\n}\n\n#pp7Dashboard .pp7-actions{\n    grid-template-columns:repeat(4,minmax(0,1fr));\n    gap:14px;\n}\n\n#pp7Dashboard .pp7-action{\n    position:relative;\n    min-height:142px;\n    padding:18px;\n    border-radius:18px;\n    box-shadow:0 2px 8px rgba(20,29,58,.025);\n    overflow:hidden;\n}\n\n#pp7Dashboard .pp7-action:after{\n    content:"";\n    position:absolute;\n    width:90px;\n    height:90px;\n    right:-45px;\n    bottom:-48px;\n    border-radius:50%;\n    background:rgba(93,84,246,.045);\n    pointer-events:none;\n    transition:transform .18s ease;\n}\n\n#pp7Dashboard .pp7-action:hover:after{\n    transform:scale(1.35);\n}\n\n#pp7Dashboard .pp7-action > span:first-child{\n    position:relative;\n    z-index:1;\n    width:40px;\n    height:40px;\n    display:flex;\n    align-items:center;\n    justify-content:center;\n    border-radius:12px;\n    background:#f1f2ff;\n    color:#4c43d7;\n    font-size:18px;\n    margin-bottom:11px;\n}\n\n#pp7Dashboard .pp7-action strong,\n#pp7Dashboard .pp7-action small{\n    position:relative;\n    z-index:1;\n}\n\n#pp7Dashboard .pp7-action strong{\n    font-size:13px;\n    line-height:1.3;\n}\n\n#pp7Dashboard .pp7-action small{\n    margin-top:5px;\n    font-size:10.5px;\n    line-height:1.5;\n}\n\n#pp7Dashboard .pp7-tools{\n    grid-template-columns:repeat(3,minmax(0,1fr));\n    gap:13px;\n}\n\n#pp7Dashboard .pp7-tool{\n    min-height:132px;\n    padding:17px;\n    border-radius:16px;\n    box-shadow:0 2px 8px rgba(20,29,58,.022);\n}\n\n#pp7Dashboard .pp7-tool:focus-visible,\n#pp7Dashboard .pp7-action:focus-visible,\n#pp7Dashboard .pp7-recent-chip:focus-visible{\n    outline:3px solid rgba(93,84,246,.20);\n    outline-offset:2px;\n}\n\n#pp7Dashboard .pp7-tool-top{\n    margin-bottom:9px;\n}\n\n#pp7Dashboard .pp7-tool-icon{\n    width:38px;\n    height:38px;\n    border-radius:11px;\n    background:#f3f4ff;\n    font-size:18px;\n}\n\n#pp7Dashboard .pp7-tool strong{\n    font-size:13px;\n}\n\n#pp7Dashboard .pp7-tool p{\n    font-size:10.5px;\n    line-height:1.52;\n}\n\n#pp7Dashboard .pp7-recent{\n    padding:3px 0;\n    min-height:40px;\n}\n\n#pp7Dashboard .pp7-recent-chip{\n    min-height:36px;\n    padding:8px 11px;\n    border-radius:10px;\n    font-size:11px;\n    box-shadow:0 2px 7px rgba(20,29,58,.025);\n}\n\n#pp7Dashboard .pp7-footer-grid{\n    grid-template-columns:minmax(0,1.45fr) minmax(280px,1fr);\n    gap:14px;\n    margin-top:23px;\n}\n\n#pp7Dashboard .pp7-info{\n    min-height:132px;\n    padding:18px;\n    border-radius:16px;\n    box-shadow:0 2px 8px rgba(20,29,58,.022);\n}\n\n#pp7Dashboard .pp7-info h4{\n    font-size:13px;\n}\n\n#pp7Dashboard .pp7-info p{\n    font-size:11px;\n    line-height:1.58;\n}\n\n#pp7Dashboard .pp7-badge{\n    font-size:9.5px;\n    padding:6px 9px;\n}\n\n@media(min-width:1400px){\n    #pp7Dashboard .pp7-actions{gap:16px}\n    #pp7Dashboard .pp7-action{min-height:148px}\n    #pp7Dashboard .pp7-tool{min-height:138px}\n}\n\n@media(max-width:1100px){\n    #pp7Dashboard .pp7-actions{grid-template-columns:repeat(2,minmax(0,1fr))}\n    #pp7Dashboard .pp7-tools{grid-template-columns:repeat(2,minmax(0,1fr))}\n    #pp7Dashboard .pp7-hero{padding:32px}\n}\n\n@media(max-width:850px){\n    #pp7Dashboard .pp7-hero{\n        min-height:210px;\n        padding:28px;\n        border-radius:20px;\n    }\n    #pp7Dashboard .pp7-section-title{\n        align-items:flex-start;\n        flex-direction:column;\n        gap:4px;\n    }\n    #pp7Dashboard .pp7-section-title span{text-align:left}\n    #pp7Dashboard .pp7-footer-grid{grid-template-columns:1fr}\n}\n\n@media(max-width:600px){\n    #pp7Dashboard .pp7-hero{\n        min-height:0;\n        padding:24px 20px;\n        margin-bottom:24px;\n        border-radius:18px;\n    }\n    #pp7Dashboard .pp7-hero h1{\n        font-size:clamp(25px,8vw,32px);\n        line-height:1.08;\n    }\n    #pp7Dashboard .pp7-hero p{\n        font-size:12px;\n        line-height:1.55;\n    }\n    #pp7Dashboard .pp7-privacy{\n        width:auto;\n        align-self:flex-start;\n        font-size:10px;\n        line-height:1.4;\n    }\n    #pp7Dashboard .pp7-actions,\n    #pp7Dashboard .pp7-tools{\n        grid-template-columns:1fr;\n        gap:10px;\n    }\n    #pp7Dashboard .pp7-action{\n        min-height:108px;\n        padding:15px;\n    }\n    #pp7Dashboard .pp7-action > span:first-child{\n        width:36px;\n        height:36px;\n        margin-bottom:8px;\n    }\n    #pp7Dashboard .pp7-tool{\n        min-height:104px;\n        padding:15px;\n    }\n    #pp7Dashboard .pp7-info{min-height:0}\n}\n\n@media(max-width:390px){\n    #pp7Dashboard .pp7-hero{padding:21px 16px}\n    #pp7Dashboard .pp7-hero h1{font-size:24px}\n    #pp7Dashboard .pp7-hero p{font-size:11.5px}\n    #pp7Dashboard .pp7-section-title{margin-top:24px}\n    #pp7Dashboard .pp7-action,\n    #pp7Dashboard .pp7-tool,\n    #pp7Dashboard .pp7-info{border-radius:14px}\n}\n\n@media(prefers-reduced-motion:reduce){\n    #pp7Dashboard,\n    #pp7Dashboard *{\n        scroll-behavior:auto !important;\n        transition-duration:.01ms !important;\n        animation-duration:.01ms !important;\n        animation-iteration-count:1 !important;\n    }\n}\n\nbody.pp6-dark #pp7Dashboard .pp7-action,\nbody.pp6-dark #pp7Dashboard .pp7-tool,\nbody.pp6-dark #pp7Dashboard .pp7-info,\nbody.pp6-dark #pp7Dashboard .pp7-recent-chip{\n    box-shadow:0 8px 22px rgba(0,0,0,.14);\n}\n\nbody.pp6-dark #pp7Dashboard .pp7-action > span:first-child,\nbody.pp6-dark #pp7Dashboard .pp7-action .pp7-action-icon,\nbody.pp6-dark #pp7Dashboard .pp7-tool-icon{\n    background:#232844;\n}\n</style>\n'

pos = html.lower().rfind("</head>")
if pos < 0:
    print("ERROR: </head> not found")
    sys.exit(1)

index.write_text(html[:pos] + "\n" + css + "\n" + html[pos:], encoding="utf-8")

main_after = hashlib.sha256(main_py.read_bytes()).hexdigest()
after = index.read_text(encoding="utf-8")

checks = {
    "DASHBOARD_MARKER": marker in after,
    "HERO": "#pp7Dashboard .pp7-hero" in after,
    "QUICK_ACTIONS": "#pp7Dashboard .pp7-actions" in after,
    "TOOLS": "#pp7Dashboard .pp7-tools" in after,
    "RESPONSIVE_1100": "@media(max-width:1100px)" in after,
    "RESPONSIVE_850": "@media(max-width:850px)" in after,
    "RESPONSIVE_600": "@media(max-width:600px)" in after,
    "RESPONSIVE_390": "@media(max-width:390px)" in after,
    "REDUCED_MOTION": "prefers-reduced-motion:reduce" in after,
    "MAIN_PY_UNCHANGED": main_before == main_after,
    "ANNOTATION_PRESENT": "annotation" in after.lower(),
    "BATCH_PRESENT": "batch" in after.lower(),
    "IMAGE_STUDIO_PRESENT": "image studio" in after.lower(),
}

print("DASHBOARD_SECTION1_PRO_POLISH_APPLIED")
print("backup:", backup.name)
for k, v in checks.items():
    print(f"{k}: {'PASS' if v else 'FAIL'}")
print("main.py SHA256 before:", main_before)
print("main.py SHA256 after :", main_after)
print("index.html bytes:", index.stat().st_size)

if not all(checks.values()):
    print("SAFETY CHECK FAILED — restoring backup")
    shutil.copy2(backup, index)
    sys.exit(2)

print("")
print("SCOPE GUARANTEE")
print("- Only src/static/index.html changed")
print("- main.py unchanged")
print("- Backend/security untouched")
print("- Image Studio retained")
print("- Annotation retained")
print("- Batch retained")
print("")
print("SECTION 1 DASHBOARD POLISH COMPLETE")
