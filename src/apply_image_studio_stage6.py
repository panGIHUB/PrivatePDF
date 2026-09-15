from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parent
INDEX=next((x for x in (ROOT/"index.html",ROOT/"static"/"index.html") if x.exists()),None)
if not INDEX: raise SystemExit("ERROR: index.html not found")
h=INDEX.read_text(encoding="utf-8")
if "PP_IMAGE_STUDIO_2_0_STAGE5_CSS" not in h: raise SystemExit("ERROR: Stage 5 marker not found")
if "PP_IMAGE_STUDIO_2_0_STAGE6_CSS" in h:
 print("IMAGE_STUDIO_2_0_STAGE6_ALREADY_APPLIED"); raise SystemExit
backup=INDEX.with_name("index_before_image_studio_2_0_stage6_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".html")
backup.write_text(h,encoding="utf-8")

css=r"""<style id="pp-image-studio-stage6-css">
/* PP_IMAGE_STUDIO_2_0_STAGE6_CSS */
.pp-s6-presets{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}
.pp-s6-btn{border:1px solid var(--border,#d8dde6);border-radius:7px;background:var(--card,#fff);padding:8px;cursor:pointer;font-size:12px}
.pp-s6-btn:hover{filter:brightness(.97)}
.pp-s6-panel{margin-top:8px;padding:9px;border:1px solid var(--border,#d8dde6);border-radius:9px}
.pp-s6-note{font-size:11px;opacity:.7;margin-top:6px}
@media(max-width:800px){.pp-s6-presets{grid-template-columns:1fr}}
</style>"""
h=h.replace("</head>",css+"</head>",1)

panel=r"""<div class="tool-section" id="ppImgStage6ProTools">
<h4>Professional Tools</h4>
<div class="pp-s6-panel">
<strong style="font-size:12px">Social presets</strong>
<div class="pp-s6-presets" style="margin-top:7px">
<button class="pp-s6-btn" onclick="ppImgS6Preset(1080,1080)">Instagram Square</button>
<button class="pp-s6-btn" onclick="ppImgS6Preset(1080,1350)">Instagram Portrait</button>
<button class="pp-s6-btn" onclick="ppImgS6Preset(1080,1920)">Story / Reel</button>
<button class="pp-s6-btn" onclick="ppImgS6Preset(1200,628)">Facebook Post</button>
<button class="pp-s6-btn" onclick="ppImgS6Preset(1280,720)">YouTube</button>
<button class="pp-s6-btn" onclick="ppImgS6Preset(1200,675)">LinkedIn</button>
</div></div>
<div class="pp-s6-panel">
<strong style="font-size:12px">Print presets</strong>
<div class="pp-s6-presets" style="margin-top:7px">
<button class="pp-s6-btn" onclick="ppImgS6Preset(2480,3508)">A4 @300 DPI</button>
<button class="pp-s6-btn" onclick="ppImgS6Preset(2550,3300)">Letter @300 DPI</button>
<button class="pp-s6-btn" onclick="ppImgS6Preset(3508,4961)">A3 @300 DPI</button>
<button class="pp-s6-btn" onclick="ppImgS6Preset(4961,7016)">A2 @300 DPI</button>
</div></div>
<div class="pp-s6-panel">
<strong style="font-size:12px">Canvas utilities</strong>
<div class="pp-s6-presets" style="margin-top:7px">
<button class="pp-s6-btn" onclick="ppImgS6Fit()">Fit canvas</button>
<button class="pp-s6-btn" onclick="ppImgS6Center()">Center objects</button>
<button class="pp-s6-btn" onclick="ppImgS6ClearObjects()">Clear objects</button>
<button class="pp-s6-btn" onclick="ppImgS6ResetView()">Reset view</button>
</div>
</div>
<div class="pp-s6-note">Presets prepare the canvas/export target locally. Existing editing, layers, crop and export remain available.</div>
</div>"""
if "ppImgStage6ProTools" not in h:
    h=h.replace("</body>",panel+"</body>",1)

js=r"""<script id="pp-image-studio-stage6-js">
/* PP_IMAGE_STUDIO_2_0_STAGE6_JS */
(function(){
"use strict";
window.ppImgS6Preset=function(w,h){
 const c=window.ppImgCanvas;if(!c||!c.width)return;
 const base=window.ppImgBaseCanvas;
 if(base){const b=base.getContext("2d"),old=document.createElement("canvas");old.width=base.width;old.height=base.height;old.getContext("2d").drawImage(base,0,0);
   base.width=w;base.height=h;const x=base.getContext("2d"),scale=Math.min(w/old.width,h/old.height),nw=old.width*scale,nh=old.height*scale;x.clearRect(0,0,w,h);x.drawImage(old,(w-nw)/2,(h-nh)/2,nw,nh);}
 c.width=w;c.height=h;if(typeof window.ppImgRender==="function")window.ppImgRender();
 if(typeof window.ppImgS3RefreshLayers==="function")window.ppImgS3RefreshLayers();
};
window.ppImgS6Fit=function(){if(typeof window.ppImgZoom==="function")window.ppImgZoom(100);else if(window.ppImgZoomLevel!==undefined){window.ppImgZoomLevel=1;if(window.ppImgRender)window.ppImgRender()}};
window.ppImgS6Center=function(){
 const c=window.ppImgCanvas;if(!c||!Array.isArray(window.ppImgObjects))return;
 window.ppImgObjects.forEach(o=>{o.x=c.width/2;o.y=c.height/2});if(window.ppImgRender)window.ppImgRender();if(window.ppImgS3RefreshLayers)window.ppImgS3RefreshLayers();
};
window.ppImgS6ClearObjects=function(){if(Array.isArray(window.ppImgObjects)){window.ppImgObjects.length=0;if(window.ppImgRender)window.ppImgRender();if(window.ppImgS3RefreshLayers)window.ppImgS3RefreshLayers()}};
window.ppImgS6ResetView=function(){window.ppImgZoomLevel=1;if(window.ppImgRender)window.ppImgRender()};
})();
</script>"""
h=h.replace("</body>",js+"</body>",1)
INDEX.write_text(h,encoding="utf-8")

checks={"STAGE6_CSS":"PP_IMAGE_STUDIO_2_0_STAGE6_CSS" in h,"STAGE6_JS":"PP_IMAGE_STUDIO_2_0_STAGE6_JS" in h,"SOCIAL_PRESETS":"Instagram Square" in h,"PRINT_PRESETS":"A4 @300 DPI" in h,"CANVAS_UTILITIES":"ppImgS6Fit" in h}
print("IMAGE_STUDIO_2_0_STAGE6_APPLIED")
print("backup:",backup.name)
print("index.html bytes:",INDEX.stat().st_size)
for k,v in checks.items(): print(k+":","PASS" if v else "FAIL")
print("main.py was NOT modified.")
print("Security/backend/annotation/batch untouched.")
print("IMAGE STUDIO 2.0 STAGE 6 COMPLETE")
