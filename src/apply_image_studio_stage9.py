from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
INDEX = next((x for x in (ROOT/"index.html", ROOT/"static"/"index.html") if x.exists()), None)
if INDEX is None:
    raise SystemExit("ERROR: index.html not found")

h = INDEX.read_text(encoding="utf-8")
if "PP_IMAGE_STUDIO_2_0_STAGE8_CSS" not in h:
    raise SystemExit("ERROR: Stage 8 marker not found")
if "PP_IMAGE_STUDIO_2_0_STAGE9_CSS" in h:
    print("IMAGE_STUDIO_2_0_STAGE9_ALREADY_APPLIED")
    raise SystemExit(0)

backup = INDEX.with_name(
    "index_before_image_studio_2_0_stage9_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") + ".html"
)
backup.write_text(h, encoding="utf-8")

css = r"""<style id="pp-image-studio-stage9-css">
/* PP_IMAGE_STUDIO_2_0_STAGE9_CSS */
:root{--pp9-radius:12px;--pp9-gap:10px}
#ppImgStage7Shell,#ppImgStage8QuickBar{
 width:100%;max-width:100%;box-sizing:border-box
}
#ppImgStage7Shell{
 margin:0 0 12px;
}
#ppImgStage7Shell .pp-s7-menu{
 background:var(--card,#fff);
 border:1px solid var(--border,#d8dde6);
 border-radius:var(--pp9-radius);
 box-shadow:0 5px 18px rgba(0,0,0,.06);
}
#ppImgStage7Shell .pp-s7-menu button{
 min-height:38px;font-weight:600;touch-action:manipulation;
}
#ppImgStage7Shell .pp-s7-menu button.active{
 box-shadow:inset 0 -2px 0 currentColor;
}
#ppImgStage7Shell .pp-s7-pane{
 padding:0;
}
#ppImgStage7Shell .pp-s7-submenu{
 background:var(--surface,#f7f8fc);
 border:1px solid var(--border,#d8dde6);
 border-radius:10px;
 padding:7px;
}
#ppImgStage7Shell .pp-s7-submenu button{
 min-height:36px;font-weight:600;touch-action:manipulation;
}

#ppImgStage8QuickBar{
 display:flex;gap:7px;align-items:center;flex-wrap:wrap;
 background:var(--card,#fff);
 border:1px solid var(--border,#d8dde6);
 border-radius:10px;
 box-shadow:0 3px 12px rgba(0,0,0,.04);
}
#ppImgStage8QuickBar button{
 min-height:36px;touch-action:manipulation;font-weight:600;
}

#ppImgStage5ExportPro,#ppImgStage6ProTools,#ppImgStage4Adjustments,#ppImgStage4TextPro{
 border-radius:var(--pp9-radius);
 box-shadow:0 4px 16px rgba(0,0,0,.045);
 box-sizing:border-box;
}
#ppImgStage5ExportPro .pp-s5-export{
 grid-template-columns:repeat(2,minmax(0,1fr));
}
#ppImgStage5ExportPro input,#ppImgStage5ExportPro select,
#ppImgStage6ProTools button,#ppImgStage5ExportPro button{
 min-height:36px;box-sizing:border-box;
}
#ppImgStage6ProTools .pp-s6-panel{
 background:var(--card,#fff);
}

.tool-section{
 box-sizing:border-box;
 max-width:100%;
}
.tool-section input,.tool-section select,.tool-section textarea,
.tool-section button{
 max-width:100%;
 box-sizing:border-box;
}
.tool-section img,.tool-section canvas,canvas{
 max-width:100%;
}

.pp-s9-hidden{display:none!important}
.pp-s9-visible{display:block!important}
.pp-s9-section-active{
 animation:ppS9In .16s ease-out;
}
@keyframes ppS9In{
 from{opacity:.55;transform:translateY(2px)}
 to{opacity:1;transform:none}
}

@media(min-width:901px){
 #ppImgStage7Shell .pp-s7-menu{justify-content:flex-start}
 #ppImgStage5ExportPro .pp-s5-export{grid-template-columns:1fr 1.35fr}
}
@media(max-width:900px){
 #ppImgStage5ExportPro .pp-s5-export{grid-template-columns:1fr 1fr}
}
@media(max-width:600px){
 #ppImgStage8QuickBar span{width:100%;margin-left:0!important}
 #ppImgStage5ExportPro .pp-s5-export{grid-template-columns:1fr}
 #ppImgStage5ExportPro .pp-s5-export .full{grid-column:auto}
}
@media(max-width:390px){
 #ppImgStage7Shell .pp-s7-menu button{font-size:10px;min-height:38px}
 #ppImgStage7Shell .pp-s7-submenu{grid-template-columns:1fr}
 #ppImgStage8QuickBar{padding:7px}
 #ppImgStage8QuickBar button{flex:1 1 calc(50% - 7px)}
}
</style>"""
h = h.replace("</head>", css + "\n</head>", 1)

js = r"""<script id="pp-image-studio-stage9-js">
/* PP_IMAGE_STUDIO_2_0_STAGE9_JS */
(function(){
"use strict";
const norm=s=>(s||"").replace(/\s+/g," ").trim().toLowerCase();
const sectionData=()=>[...document.querySelectorAll(".tool-section")].map((el,i)=>({
 el,i,title:norm(el.querySelector("h4")?.textContent)
}));
const groups={
 editor:["transform","objects & layers","filters","crop studio"],
 adjust:["advanced adjustments","adjustments","filters"],
 crop:["crop studio","transform"],
 text:["text studio pro","text studio"],
 draw:["drawing","pen"],
 shapes:["shapes","objects & layers"],
 frame:["frame","watermark","border"],
 presets:["professional tools","resize pro","social media studio","print & dpi studio"],
 export:["export pro","export"]
};
function findSections(keys){
 const data=sectionData(),out=[];
 keys.forEach(k=>{
   const n=norm(k);
   data.forEach(x=>{
     if(x.title===n || x.title.includes(n)) out.push(x.el);
   });
 });
 return [...new Set(out)];
}
function applyVisibility(tab){
 const shell=document.getElementById("ppImgStage7Shell");
 if(!shell)return;
 const keys=groups[tab]||groups.editor;
 const keep=new Set(findSections(keys));
 document.querySelectorAll(".tool-section").forEach(el=>{
   const title=norm(el.querySelector("h4")?.textContent);
   const imageStudioTitles=[
     "transform","objects & layers","filters","crop studio","adjustments",
     "advanced adjustments","text studio","text studio pro","drawing","pen",
     "shapes","frame","watermark","border","professional tools","resize pro",
     "social media studio","print & dpi studio","export pro","export"
   ];
   if(imageStudioTitles.some(x=>title===x||title.includes(x))){
     el.classList.toggle("pp-s9-hidden",!keep.has(el));
     el.classList.toggle("pp-s9-visible",keep.has(el));
     el.classList.toggle("pp-s9-section-active",keep.has(el));
   }
 });
}
const oldTab=window.ppImgS7Tab;
window.ppImgS7Tab=function(name,btn){
 if(typeof oldTab==="function")oldTab(name,btn);
 applyVisibility(name);
 setTimeout(()=>applyVisibility(name),0);
};
window.ppImgS9ShowAll=function(){
 document.querySelectorAll(".tool-section.pp-s9-hidden").forEach(el=>{
   el.classList.remove("pp-s9-hidden");el.classList.add("pp-s9-visible");
 });
};
window.ppImgS9Refresh=function(){
 const active=document.querySelector("#ppImgStage7Shell .pp-s7-menu button.active");
 applyVisibility(active?.dataset.s7tab||"editor");
};
window.addEventListener("load",()=>setTimeout(()=>window.ppImgS9Refresh(),50));
window.addEventListener("resize",()=>{document.documentElement.style.setProperty("--pp-s9-width",window.innerWidth+"px")});
})();
</script>"""
h = h.replace("</body>", js + "\n</body>", 1)
INDEX.write_text(h, encoding="utf-8")

checks = {
    "STAGE9_CSS": "PP_IMAGE_STUDIO_2_0_STAGE9_CSS" in h,
    "STAGE9_JS": "PP_IMAGE_STUDIO_2_0_STAGE9_JS" in h,
    "MENU_POLISH": "pp9-radius" in h,
    "RESPONSIVE": "@media(max-width:600px)" in h and "@media(max-width:390px)" in h,
    "SUBMENU_VISIBILITY": "applyVisibility" in h,
    "EDITOR_GROUP": '"editor":' in h,
    "ADJUST_GROUP": '"adjust":' in h,
    "EXPORT_GROUP": '"export":' in h,
    "NO_LITERAL_N": r"\n" not in h,
}
print("IMAGE_STUDIO_2_0_STAGE9_APPLIED")
print("backup:", backup.name)
print("index.html bytes:", INDEX.stat().st_size)
for k,v in checks.items():
    print(k + ":", "PASS" if v else "FAIL")
print("main.py was NOT modified.")
print("Security/backend/annotation/batch untouched.")
print("IMAGE STUDIO 2.0 STAGE 9 COMPLETE")