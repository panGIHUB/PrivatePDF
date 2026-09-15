from pathlib import Path
from datetime import datetime
import re

ROOT=Path(__file__).resolve().parent
INDEX=next((x for x in (ROOT/"index.html",ROOT/"static"/"index.html") if x.exists()),None)
if INDEX is None:
    raise SystemExit("ERROR: index.html not found")
h=INDEX.read_text(encoding="utf-8")

if "PP_IMAGE_STUDIO_2_0_STAGE9_CSS" not in h:
    raise SystemExit("ERROR: Stage 9 marker not found")
if "PP_IMAGE_STUDIO_2_0_STAGE10_CSS" in h:
    print("IMAGE_STUDIO_2_0_STAGE10_ALREADY_APPLIED")
    raise SystemExit(0)

backup=INDEX.with_name("index_before_image_studio_2_0_stage10_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".html")
backup.write_text(h,encoding="utf-8")

# Remove only accidental literal \n markup artifacts (not JS strings).
h=re.sub(r'\\n(?=\s*<(?:div|section|h[1-6]|button|p|span|label|select|input|option)\b)',"",h,flags=re.I)

css=r"""<style id="pp-image-studio-stage10-css">
/* PP_IMAGE_STUDIO_2_0_STAGE10_CSS */
#ppImgStage7Shell,#ppImgStage8QuickBar{font-family:inherit}
#ppImgStage7Shell .pp-s7-menu{align-items:stretch;scroll-behavior:smooth}
#ppImgStage7Shell .pp-s7-menu button{transition:background .15s ease,box-shadow .15s ease,transform .12s ease}
#ppImgStage7Shell .pp-s7-menu button:active,
#ppImgStage7Shell .pp-s7-submenu button:active,
#ppImgStage8QuickBar button:active{transform:translateY(1px)}
#ppImgStage7Shell .pp-s7-submenu button{background:var(--card,#fff);border-color:var(--border,#d8dde6);text-align:center}
#ppImgStage7Shell .pp-s7-submenu button:hover{background:var(--surface,#f7f8fc)}
#ppImgStage5ExportPro,#ppImgStage6ProTools,#ppImgStage8QuickBar{width:100%;max-width:100%}
#ppImgStage5ExportPro label,#ppImgStage6ProTools label{display:block;min-width:0}
#ppImgStage5ExportPro input[type="range"]{width:100%;max-width:100%}
#ppImgStage5ExportPro select,#ppImgStage5ExportPro input[type="text"],
#ppImgStage5ExportPro input[type="number"]{width:100%}
#ppImgStage6ProTools .pp-s6-panel strong{display:block;margin-bottom:2px}
#ppImgStage6ProTools .pp-s6-btn{white-space:normal;line-height:1.25}
.pp-s10-status{font-size:11px;opacity:.7;padding:4px 2px}
@media(max-width:600px){
 #ppImgStage7Shell .pp-s7-menu{border-radius:9px}
 #ppImgStage7Shell .pp-s7-submenu{gap:6px}
 #ppImgStage8QuickBar{gap:6px}
}
@media(max-width:390px){
 #ppImgStage8QuickBar button{min-width:0}
}
</style>"""
h=h.replace("</head>",css+"\n</head>",1)

# Add a compact status line, without altering existing editor logic.
status=r"""<div id="ppImgStage10Status" class="pp-s10-status" aria-live="polite">Image Studio ready • local editing • responsive workspace</div>"""
if "ppImgStage10Status" not in h:
    pos=h.find('<div id="ppImgStage7Shell"')
    if pos>=0:
        h=h[:pos]+status+"\n"+h[pos:]
    else:
        h=h.replace("</body>",status+"</body>",1)

js=r"""<script id="pp-image-studio-stage10-js">
/* PP_IMAGE_STUDIO_2_0_STAGE10_JS */
(function(){
"use strict";
function status(text){
 const el=document.getElementById("ppImgStage10Status");
 if(el)el.textContent=text;
}
window.ppImgS10Status=status;
function refresh(){
 const active=document.querySelector("#ppImgStage7Shell .pp-s7-menu button.active");
 const name=active?.textContent?.trim()||"Editor";
 status("Image Studio • "+name+" • local editing");
}
window.addEventListener("load",()=>setTimeout(refresh,80));
document.addEventListener("click",e=>{
 const b=e.target.closest("#ppImgStage7Shell .pp-s7-menu button");
 if(b)setTimeout(refresh,30);
});
})();
</script>"""
h=h.replace("</body>",js+"\n</body>",1)

INDEX.write_text(h,encoding="utf-8")

checks={
"STAGE10_CSS":"PP_IMAGE_STUDIO_2_0_STAGE10_CSS" in h,
"STAGE10_JS":"PP_IMAGE_STUDIO_2_0_STAGE10_JS" in h,
"STATUS_BAR":"ppImgStage10Status" in h,
"RESPONSIVE":"@media(max-width:600px)" in h and "@media(max-width:390px)" in h,
"EXPORT_WIDTH":"#ppImgStage5ExportPro" in h,
"PRO_TOOLS_WIDTH":"#ppImgStage6ProTools" in h,
"NO_MARKUP_NEWLINE":not bool(re.search(r'\\n(?=\s*<(?:div|section|h[1-6]|button|p|span|label|select|input|option)\b)',h,re.I)),
}
print("IMAGE_STUDIO_2_0_STAGE10_APPLIED")
print("backup:",backup.name)
print("index.html bytes:",INDEX.stat().st_size)
for k,v in checks.items(): print(k+":","PASS" if v else "FAIL")
print("main.py was NOT modified.")
print("Security/backend/annotation/batch untouched.")
print("IMAGE STUDIO 2.0 STAGE 10 COMPLETE")
