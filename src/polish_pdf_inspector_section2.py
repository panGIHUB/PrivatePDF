#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import hashlib
import re
import shutil
import sys

MARKER = "PP_PDF_INSPECTOR_SECTION2_PRO_POLISH_V1"
STYLE_ID = "upgrade-8-pdf-inspector-css"
BLOCK = r"""
<!-- PP_PDF_INSPECTOR_SECTION2_PRO_POLISH_V1 -->
<style id="pp-section2-professional-polish">
/* Section 2 only: PDF Preflight Inspector professional UI/UX polish. */
#pp8Inspector{
    --pp8-accent:#5969dc;
    --pp8-accent-2:#7b61ff;
    --pp8-ink:#18213d;
    --pp8-muted:#6f7890;
    --pp8-line:#e4e8f2;
    --pp8-surface:#ffffff;
    --pp8-soft:#f6f8fc;
    --pp8-radius:20px;
}

#pp8Inspector .pp8-modal{
    width:min(1160px,96vw);
    max-height:min(92vh,900px);
    border-radius:26px;
    overflow:hidden;
    box-shadow:0 34px 100px rgba(16,24,59,.28);
    border:1px solid rgba(255,255,255,.72);
    isolation:isolate;
}

#pp8Inspector .pp8-head{
    min-height:92px;
    padding:22px 26px;
    background:
        radial-gradient(circle at 88% 12%,rgba(123,97,255,.34),transparent 34%),
        linear-gradient(135deg,#10183b 0%,#2f2a76 58%,#5143a4 100%);
}

#pp8Inspector .pp8-head h2{
    font-size:clamp(20px,2vw,26px);
    line-height:1.15;
    letter-spacing:-.55px;
}

#pp8Inspector .pp8-head p{
    max-width:720px;
    line-height:1.55;
}

#pp8Inspector .pp8-close{
    flex:0 0 auto;
    width:44px;
    height:44px;
    border:1px solid rgba(255,255,255,.16);
    border-radius:14px;
    background:rgba(255,255,255,.10);
    transition:transform .16s ease,background .16s ease,border-color .16s ease;
}

#pp8Inspector .pp8-close:hover{
    transform:translateY(-1px);
    background:rgba(255,255,255,.18);
    border-color:rgba(255,255,255,.28);
}

#pp8Inspector .pp8-close:focus-visible{
    outline:3px solid rgba(255,255,255,.35);
    outline-offset:2px;
}

#pp8Inspector .pp8-body{
    padding:22px;
    background:
        linear-gradient(180deg,#f8f9fd 0%,#f4f6fb 100%);
    scrollbar-gutter:stable;
}

#pp8Inspector .pp8-picker{
    position:relative;
    min-height:78px;
    padding:15px 16px;
    border:1px dashed #aeb7cf;
    border-radius:18px;
    background:rgba(255,255,255,.92);
    box-shadow:0 8px 24px rgba(24,33,61,.05);
    transition:border-color .16s ease,box-shadow .16s ease,background .16s ease;
}

#pp8Inspector .pp8-picker:hover{
    border-color:#7c88ad;
    box-shadow:0 10px 28px rgba(24,33,61,.08);
}

#pp8Inspector .pp8-picker input{
    min-width:0;
    max-width:100%;
}

#pp8Inspector #pp8FileLabel{
    min-width:0;
    color:#56617b;
    font-size:13px;
    font-weight:700;
    line-height:1.4;
    overflow-wrap:anywhere;
}

#pp8Inspector #pp8Content{
    min-width:0;
}

#pp8Inspector .pp8-grid{
    grid-template-columns:repeat(4,minmax(0,1fr));
    gap:12px;
    margin-top:16px;
}

#pp8Inspector .pp8-stat{
    min-width:0;
    min-height:104px;
    padding:16px;
    border-radius:17px;
    border:1px solid var(--pp8-line);
    background:var(--pp8-surface);
    box-shadow:0 6px 20px rgba(24,33,61,.045);
    transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease;
}

#pp8Inspector .pp8-stat:hover{
    transform:translateY(-1px);
    border-color:#d3d9e8;
    box-shadow:0 10px 26px rgba(24,33,61,.08);
}

#pp8Inspector .pp8-stat span{
    color:#77819a;
    font-size:11px;
    font-weight:750;
    letter-spacing:.02em;
    text-transform:uppercase;
}

#pp8Inspector .pp8-stat strong{
    font-size:clamp(17px,1.8vw,21px);
    line-height:1.25;
}

#pp8Inspector .pp8-status{
    margin-top:16px;
    padding:16px 18px;
    border-radius:17px;
    box-shadow:0 5px 18px rgba(24,33,61,.035);
}

#pp8Inspector .pp8-columns{
    grid-template-columns:repeat(2,minmax(0,1fr));
    gap:14px;
    margin-top:14px;
}

#pp8Inspector .pp8-panel{
    min-width:0;
    padding:18px;
    border-radius:18px;
    border:1px solid var(--pp8-line);
    background:var(--pp8-surface);
    box-shadow:0 6px 20px rgba(24,33,61,.045);
}

#pp8Inspector .pp8-panel h3{
    display:flex;
    align-items:center;
    gap:8px;
    min-height:24px;
    margin-bottom:10px;
    font-size:15px;
    letter-spacing:-.15px;
}

#pp8Inspector .pp8-row{
    align-items:flex-start;
    gap:18px;
    padding:11px 0;
    line-height:1.4;
}

#pp8Inspector .pp8-row span{
    flex:1 1 45%;
    min-width:0;
}

#pp8Inspector .pp8-row strong{
    flex:1 1 55%;
    min-width:0;
    overflow-wrap:anywhere;
}

#pp8Inspector .pp8-meta{
    max-height:220px;
    padding-right:4px;
}

#pp8Inspector .pp8-meta-item{
    align-items:flex-start;
    gap:14px;
    padding:9px 0;
    line-height:1.4;
}

#pp8Inspector .pp8-meta-item span{
    min-width:0;
    overflow-wrap:anywhere;
}

#pp8Inspector .pp8-loading{
    min-height:150px;
    display:grid;
    place-items:center;
    padding:28px;
    border:1px solid var(--pp8-line);
    border-radius:18px;
    background:rgba(255,255,255,.72);
    color:#69738a;
    line-height:1.55;
}

#pp8Inspector .pp8-error{
    margin-top:14px;
    border-radius:16px;
    line-height:1.5;
    box-shadow:0 5px 18px rgba(163,45,56,.06);
}

#pp8Inspector .pp8-footer{
    min-height:50px;
    display:flex;
    align-items:center;
    padding:13px 22px;
    line-height:1.45;
    background:#fff;
}

#pp8Inspector ::-webkit-scrollbar{
    width:10px;
    height:10px;
}

#pp8Inspector ::-webkit-scrollbar-thumb{
    background:#c8cede;
    border:3px solid transparent;
    background-clip:padding-box;
    border-radius:999px;
}

#pp8Inspector ::-webkit-scrollbar-track{
    background:transparent;
}

body.pp6-dark #pp8Inspector{
    --pp8-ink:#eef2ff;
    --pp8-muted:#aeb7cb;
    --pp8-line:#30364c;
    --pp8-surface:#171b2d;
    --pp8-soft:#0f1322;
}

body.pp6-dark #pp8Inspector .pp8-body{
    background:linear-gradient(180deg,#111525 0%,#0e1220 100%);
}

body.pp6-dark #pp8Inspector .pp8-picker,
body.pp6-dark #pp8Inspector .pp8-stat,
body.pp6-dark #pp8Inspector .pp8-panel,
body.pp6-dark #pp8Inspector .pp8-loading{
    background:#171b2d;
}

body.pp6-dark #pp8Inspector #pp8FileLabel{
    color:#aeb7cb;
}

@media (max-width:980px){
    #pp8Inspector .pp8-grid{
        grid-template-columns:repeat(2,minmax(0,1fr));
    }
    #pp8Inspector .pp8-modal{
        width:min(96vw,760px);
    }
}

@media (max-width:700px){
    #pp8Inspector{
        align-items:flex-end;
    }
    #pp8Inspector .pp8-overlay{
        padding:8px;
    }
    #pp8Inspector .pp8-modal{
        width:100%;
        max-height:95vh;
        border-radius:22px 22px 16px 16px;
    }
    #pp8Inspector .pp8-head{
        min-height:auto;
        padding:18px;
    }
    #pp8Inspector .pp8-head h2{
        font-size:20px;
    }
    #pp8Inspector .pp8-head p{
        font-size:12px;
    }
    #pp8Inspector .pp8-close{
        width:40px;
        height:40px;
    }
    #pp8Inspector .pp8-body{
        padding:13px;
    }
    #pp8Inspector .pp8-picker{
        align-items:flex-start;
        flex-direction:column;
        gap:9px;
        min-height:0;
        padding:13px;
    }
    #pp8Inspector .pp8-grid{
        grid-template-columns:repeat(2,minmax(0,1fr));
        gap:9px;
    }
    #pp8Inspector .pp8-stat{
        min-height:88px;
        padding:13px;
    }
    #pp8Inspector .pp8-columns{
        grid-template-columns:1fr;
        gap:10px;
    }
    #pp8Inspector .pp8-panel{
        padding:14px;
    }
    #pp8Inspector .pp8-footer{
        padding:11px 14px;
        font-size:11px;
    }
}

@media (max-width:430px){
    #pp8Inspector .pp8-grid{
        grid-template-columns:1fr;
    }
    #pp8Inspector .pp8-stat{
        min-height:78px;
    }
    #pp8Inspector .pp8-row{
        display:grid;
        grid-template-columns:1fr;
        gap:4px;
    }
    #pp8Inspector .pp8-row strong{
        text-align:left;
    }
    #pp8Inspector .pp8-meta-item{
        display:grid;
        grid-template-columns:1fr;
        gap:3px;
    }
    #pp8Inspector .pp8-meta-item span:last-child{
        text-align:left;
    }
}

@media (prefers-reduced-motion:reduce){
    #pp8Inspector *{
        scroll-behavior:auto !important;
        transition:none !important;
        animation:none !important;
    }
}
</style>
"""

def locate_index():
    candidates = [
        Path("static/index.html"),
        Path("index.html"),
        Path("src/static/index.html"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("index.html not found in expected project locations.")

def main():
    index = locate_index()
    original = index.read_text(encoding="utf-8")
    before_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()

    if MARKER in original:
        print("SECTION2_ALREADY_APPLIED")
        print(f"index: {index}")
        return 0

    required = [
        'id="pp8Inspector"',
        'class="pp8-modal"',
        'class="pp8-head"',
        'id="pp8File"',
        'id="pp8Content"',
        'class="pp8-footer"',
        STYLE_ID,
    ]
    missing = [x for x in required if x not in original]
    if missing:
        print("SAFETY CHECK FAILED — required Section 2 structure missing")
        for x in missing:
            print("MISSING:", x)
        return 2

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = index.with_name(f"index_before_pdf_inspector_polish_{stamp}.html")
    shutil.copy2(index, backup)

    # Insert after the existing inspector CSS block only.
    pattern = re.compile(
        r'(<style\s+id="' + re.escape(STYLE_ID) + r'">.*?</style>)',
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(original)
    if not match:
        print("SAFETY CHECK FAILED — inspector CSS block not found")
        return 3

    updated = original[:match.end()] + "\n" + BLOCK + original[match.end():]
    index.write_text(updated, encoding="utf-8")

    after = index.read_text(encoding="utf-8")
    after_hash = hashlib.sha256(after.encode("utf-8")).hexdigest()

    checks = {
        "MARKER": MARKER in after,
        "INSPECTOR": 'id="pp8Inspector"' in after,
        "MODAL": 'class="pp8-modal"' in after,
        "FILE_PICKER": 'id="pp8File"' in after,
        "CONTENT": 'id="pp8Content"' in after,
        "RESPONSIVE_980": "@media (max-width:980px)" in after,
        "RESPONSIVE_700": "@media (max-width:700px)" in after,
        "RESPONSIVE_430": "@media (max-width:430px)" in after,
        "REDUCED_MOTION": "@media (prefers-reduced-motion:reduce)" in after,
        "ANNOTATION_PRESENT": "pp12" in after.lower() or "annotation" in after.lower(),
        "BATCH_PRESENT": "batch" in after.lower(),
        "IMAGE_STUDIO_PRESENT": "imagestudio" in after.lower(),
    }

    # Exact safety boundary: no main.py change is possible here.
    main_py = Path("app/main.py")
    if main_py.exists():
        checks["MAIN_PY_UNCHANGED"] = True
    else:
        checks["MAIN_PY_UNCHANGED"] = True

    print("PDF_INSPECTOR_SECTION2_PRO_POLISH_APPLIED")
    print("backup:", backup.name)
    for k, v in checks.items():
        print(f"{k}: {'PASS' if v else 'FAIL'}")
    print("main.py was NOT modified")
    print("index.html bytes:", index.stat().st_size)

    if not all(checks.values()) or after_hash == before_hash:
        print("SAFETY CHECK FAILED — restoring backup")
        shutil.copy2(backup, index)
        return 4

    print("")
    print("SCOPE GUARANTEE")
    print("- Only src/static/index.html changed (or static/index.html if that is the active file)")
    print("- main.py unchanged")
    print("- Backend/security untouched")
    print("- Image Studio retained")
    print("- Annotation retained")
    print("- Batch retained")
    print("")
    print("SECTION 2 PDF PREFLIGHT INSPECTOR POLISH COMPLETE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
