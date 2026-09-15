from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parent
INDEX=next((x for x in (ROOT/"index.html",ROOT/"static"/"index.html") if x.exists()),None)
if not INDEX: raise SystemExit("ERROR: index.html not found")
h=INDEX.read_text(encoding="utf-8")
if "PP_IMAGE_STUDIO_2_0_STAGE6_CSS" not in h: raise SystemExit("ERROR: Stage 6 marker not found")
if "PP_IMAGE_STUDIO_2_0_STAGE7_CSS" in h:
 print("IMAGE_STUDIO_2_0_STAGE7_ALREADY_APPLIED"); raise SystemExit

backup=INDEX.with_name("index_before_image_studio_2_0_stage7_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".html")
backup.write_text(h,encoding="utf-8")

css=r"""<style id="pp-image-studio-stage7-css">
/* PP_IMAGE_STUDIO_2_0_STAGE7_CSS */
.pp-s7-shell{display:flex;flex-direction:column;gap:10px}
.pp-s7-menu{display:flex;gap:6px;overflow-x:auto;scrollbar-width:thin;padding:4px;border:1px solid var(--border,#d8dde6);border-radius:10px;background:var(--card,#fff);position:sticky;top:0;z-index:20}
.pp-s7-menu button{flex:0 0 auto;border:0;border-radius:7px;background:transparent;padding:8px 11px;font-size:12px;cursor:pointer;white-space:nowrap}
.pp-s7-menu button.active{background:rgba(80,120,255,.12);font-weight:700}
.pp-s7-content{min-width:0}
.pp-s7-pane{display:none}.pp-s7-pane.active{display:block}
.pp-s7-submenu{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:9px}
.pp-s7-submenu button{border:1px solid var(--border,#d8dde6);border-radius:7px;background:var(--card,#fff);padding:7px 10px;font-size:11px;cursor:pointer}
.pp-s7-submenu button.active{outline:2px solid rgba(80,120,255,.2);font-weight:700}
.pp-s7-mobilebar{display:none}
@media(max-width:700px){
 .pp-s7-menu{gap:3px;padding:3px;border-radius:8px}
 .pp-s7-menu button{padding:8px 9px;font-size:11px}
 .pp-s7-submenu{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}
 .pp-s7-submenu button{width:100%}
}
@media(max-width:430px){
 .pp-s7-menu button{font-size:10px;padding:7px 8px}
 .pp-s7-submenu{grid-template-columns:1fr 1fr}
}
</style>"""
h=h.replace("</head>",css+"</head>",1)

# Add a unified Image Studio navigation shell. It controls visibility of existing tool sections
# by moving/categorizing them visually without rewriting their existing functionality.
shell=r"""<div id="ppImgStage7Shell" class="pp-s7-shell">
<div class="pp-s7-menu" role="tablist" aria-label="Image Studio tools">
<button class="active" data-s7tab="editor" onclick="ppImgS7Tab('editor',this)">Editor</button>
<button data-s7tab="adjust" onclick="ppImgS7Tab('adjust',this)">Adjust</button>
<button data-s7tab="crop" onclick="ppImgS7Tab('crop',this)">Crop</button>
<button data-s7tab="text" onclick="ppImgS7Tab('text',this)">Text</button>
<button data-s7tab="draw" onclick="ppImgS7Tab('draw',this)">Draw</button>
<button data-s7tab="shapes" onclick="ppImgS7Tab('shapes',this)">Shapes</button>
<button data-s7tab="frame" onclick="ppImgS7Tab('frame',this)">Frame</button>
<button data-s7tab="presets" onclick="ppImgS7Tab('presets',this)">Presets</button>
<button data-s7tab="export" onclick="ppImgS7Tab('export',this)">Export</button>
</div>
<div class="pp-s7-content">
<div class="pp-s7-pane active" data-s7pane="editor">
<div class="pp-s7-submenu">
<button onclick="ppImgS7Focus('Transform')">Transform</button>
<button onclick="ppImgS7Focus('Filters')">Filters</button>
<button onclick="ppImgS7Focus('Objects & Layers')">Layers</button>
<button onclick="ppImgS7Focus('Professional Tools')">Pro Tools</button>
</div>
</div>
<div class="pp-s7-pane" data-s7pane="adjust">
<div class="pp-s7-submenu"><button onclick="ppImgS7Focus('Advanced Adjustments')">Advanced Adjustments</button><button onclick="ppImgS7Focus('Adjustments')">Basic Adjustments</button><button onclick="ppImgS7Focus('Filters')">Filters</button></div>
</div>
<div class="pp-s7-pane" data-s7pane="crop"><div class="pp-s7-submenu"><button onclick="ppImgS7Focus('Crop Studio')">Crop Studio</button><button onclick="ppImgS7Focus('Transform')">Rotate / Flip</button></div></div>
<div class="pp-s7-pane" data-s7pane="text"><div class="pp-s7-submenu"><button onclick="ppImgS7Focus('Text Studio Pro')">Text Studio Pro</button><button onclick="ppImgS7Focus('Text Studio')">Text Studio</button></div></div>
<div class="pp-s7-pane" data-s7pane="draw"><div class="pp-s7-submenu"><button onclick="ppImgS7Focus('Drawing')">Drawing</button><button onclick="ppImgS7Focus('Pen')">Pen</button></div></div>
<div class="pp-s7-pane" data-s7pane="shapes"><div class="pp-s7-submenu"><button onclick="ppImgS7Focus('Shapes')">Shapes</button><button onclick="ppImgS7Focus('Objects & Layers')">Layers</button></div></div>
<div class="pp-s7-pane" data-s7pane="frame"><div class="pp-s7-submenu"><button onclick="ppImgS7Focus('Frame')">Frame</button><button onclick="ppImgS7Focus('Watermark')">Watermark</button></div></div>
<div class="pp-s7-pane" data-s7pane="presets"><div class="pp-s7-submenu"><button onclick="ppImgS7Focus('Professional Tools')">Social / Print presets</button><button onclick="ppImgS7Focus('Resize')">Resize Pro</button></div></div>
<div class="pp-s7-pane" data-s7pane="export"><div class="pp-s7-submenu"><button onclick="ppImgS7Focus('Export Pro')">Export Pro</button><button onclick="ppImgS7Focus('Export')">Quick Export</button></div></div>
</div></div>"""
# Insert at beginning of the Image Studio editor area, immediately before the first Transform section.
needle='<div class="tool-section">\n          <h4>Transform</h4>'
if needle in h:
    h=h.replace(needle,shell+"\n"+needle,1)
else:
    # fallback: before Stage 6 professional tools
    pos=h.find('id="ppImgStage6ProTools"')
    if pos>=0:
        start=h.rfind('<div',0,pos)
        h=h[:start]+shell+"\n"+h[start:]
    else:
        h=h.replace("</body>",shell+"</body>",1)

js=r"""<script id="pp-image-studio-stage7-js">
/* PP_IMAGE_STUDIO_2_0_STAGE7_JS */
(function(){
"use strict";
function panes(){return document.querySelectorAll("#ppImgStage7Shell .pp-s7-pane")}
window.ppImgS7Tab=function(name,btn){
 document.querySelectorAll("#ppImgStage7Shell .pp-s7-menu button").forEach(x=>x.classList.toggle("active",x===btn));
 panes().forEach(x=>x.classList.toggle("active",x.dataset.s7pane===name));
};
window.ppImgS7Focus=function(label){
 const all=[...document.querySelectorAll(".tool-section")];
 let el=all.find(x=>((x.querySelector("h4")?.textContent||"").trim().toLowerCase()===label.toLowerCase()));
 if(!el) el=all.find(x=>((x.textContent||"").trim().toLowerCase().includes(label.toLowerCase())));
 if(el){el.scrollIntoView({behavior:"smooth",block:"start"});el.style.outline="2px solid rgba(80,120,255,.35)";setTimeout(()=>el.style.outline="",900)}
};
window.addEventListener("resize",()=>{document.documentElement.style.setProperty("--pp-s7-vw",window.innerWidth+"px")});
})();
</script>"""
h=h.replace("</body>",js+"</body>",1)
INDEX.write_text(h,encoding="utf-8")

checks={
"STAGE7_CSS":"PP_IMAGE_STUDIO_2_0_STAGE7_CSS" in h,
"STAGE7_JS":"PP_IMAGE_STUDIO_2_0_STAGE7_JS" in h,
"UNIFIED_MENU":"ppImgStage7Shell" in h,
"EDITOR_TAB":"data-s7tab=\"editor\"" in h,
"ADJUST_TAB":"data-s7tab=\"adjust\"" in h,
"CROP_TAB":"data-s7tab=\"crop\"" in h,
"TEXT_TAB":"data-s7tab=\"text\"" in h,
"DRAW_TAB":"data-s7tab=\"draw\"" in h,
"SHAPES_TAB":"data-s7tab=\"shapes\"" in h,
"FRAME_TAB":"data-s7tab=\"frame\"" in h,
"PRESETS_TAB":"data-s7tab=\"presets\"" in h,
"EXPORT_TAB":"data-s7tab=\"export\"" in h,
"RESPONSIVE":"@media(max-width:700px)" in h and "@media(max-width:430px)" in h,
}
print("IMAGE_STUDIO_2_0_STAGE7_APPLIED")
print("backup:",backup.name)
print("index.html bytes:",INDEX.stat().st_size)
for k,v in checks.items(): print(k+":","PASS" if v else "FAIL")
print("main.py was NOT modified.")
print("Security/backend/annotation/batch untouched.")
print("IMAGE STUDIO 2.0 STAGE 7 COMPLETE")
