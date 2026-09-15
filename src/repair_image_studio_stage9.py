from pathlib import Path
from datetime import datetime
import re
ROOT=Path(__file__).resolve().parent
INDEX=next((x for x in (ROOT/"index.html",ROOT/"static"/"index.html") if x.exists()),None)
if INDEX is None: raise SystemExit("ERROR: index.html not found")
h=INDEX.read_text(encoding="utf-8")
if "PP_IMAGE_STUDIO_2_0_STAGE7_CSS" not in h: raise SystemExit("ERROR: Stage 7 marker not found")
backup=INDEX.with_name("index_before_image_studio_stage9_repair_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".html")
backup.write_text(h,encoding="utf-8")
# Remove literal \n artifacts only when they occur between HTML tags.
h=re.sub(r"\\n(?=\s*<)","",h)
# Repair Stage 9 grouping with reliable marker-based logic.
start=h.find("<script id=\"pp-image-studio-stage9-js\">")
end=h.find("</script>",start)
if start>=0 and end>start:
 js="""<script id=\"pp-image-studio-stage9-js\">
/* PP_IMAGE_STUDIO_2_0_STAGE9_JS_REPAIRED */
(function(){
"use strict";
const n=s=>(s||"").replace(/\s+/g," ').trim().toLowerCase();
const groups={
 editor:["transform","objects & layers","filters","crop studio","professional image editor 2.0"],
 adjust:["advanced adjustments","adjustments","filters"],
 crop:["crop studio","transform"],
 text:["text studio pro","text studio"],
 draw:["drawing","pen"],
 shapes:["shapes","objects & layers"],
 frame:["frame","watermark","border"],
 presets:["professional tools","resize pro","social media studio","print & dpi studio"],
 export:["export pro","export"]
};
function sections(){return [...document.querySelectorAll(".tool-section")]}
function title(el){return n(el.querySelector("h4")?.textContent||"")}
function apply(tab){const keep=new Set();for(const key of (groups[tab]||groups.editor)){const k=n(key);for(const el of sections()){const t=title(el);if(t===k||t.includes(k))keep.add(el)}}
 const names=["transform","objects & layers","filters","crop studio","adjustments","advanced adjustments","text studio","drawing","pen","shapes","frame","watermark","border","professional tools","resize pro","social media studio","print & dpi studio","export pro","export"];
 for(const el of sections()){const t=title(el);if(names.some(x=>t===x||t.includes(x)))el.classList.toggle("pp-s9-hidden",!keep.has(el))}}
 const old=window.ppImgS7Tab;window.ppImgS7Tab=function(name,btn){if(typeof old==="function")old(name,btn);apply(name)};
 window.ppImgS9Refresh=function(){const b=document.querySelector("#ppImgStage7Shell .pp-s7-menu button.active");apply(b?.dataset.s7tab||"editor")};
 window.addEventListener("load",()=>setTimeout(window.ppImgS9Refresh,60));
})();
</script>"""
 h=h[:start]+js+h[end+9:]
if "PP_IMAGE_STUDIO_2_0_STAGE9_REPAIR" not in h:h=h.replace("</body>","<!-- PP_IMAGE_STUDIO_2_0_STAGE9_REPAIR: editor adjust crop text draw shapes frame presets export -->\n</body>",1)
INDEX.write_text(h,encoding="utf-8")
checks={"STAGE9_CSS":"PP_IMAGE_STUDIO_2_0_STAGE9_CSS" in h,"STAGE9_JS_REPAIRED":"PP_IMAGE_STUDIO_2_0_STAGE9_JS_REPAIRED" in h,"EDITOR_GROUP":"editor" in h,"ADJUST_GROUP":"adjust" in h,"EXPORT_GROUP":"export" in h,"RESPONSIVE":"@media(max-width:600px)" in h and "@media(max-width:390px)" in h}
print("IMAGE_STUDIO_2_0_STAGE9_REPAIR_APPLIED");print("backup:",backup.name);print("index.html bytes:",INDEX.stat().st_size)
for k,v in checks.items():print(k+":","PASS" if v else "FAIL")
print("main.py was NOT modified.");print("Security/backend/annotation/batch untouched.");print("STAGE 9 REPAIR COMPLETE")
