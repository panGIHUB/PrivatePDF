from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parent
INDEX=next((x for x in (ROOT/"index.html",ROOT/"static"/"index.html") if x.exists()),None)
if not INDEX: raise SystemExit("ERROR: index.html not found")
h=INDEX.read_text(encoding="utf-8")
if "PP_IMAGE_STUDIO_2_0_STAGE4_CSS" not in h: raise SystemExit("ERROR: Stage 4 marker not found")
if "PP_IMAGE_STUDIO_2_0_STAGE5_CSS" in h:
 print("IMAGE_STUDIO_2_0_STAGE5_ALREADY_APPLIED"); raise SystemExit
backup=INDEX.with_name("index_before_image_studio_2_0_stage5_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".html")
backup.write_text(h,encoding="utf-8")

css=r"""<style id="pp-image-studio-stage5-css">
/* PP_IMAGE_STUDIO_2_0_STAGE5_CSS */
.pp-s5-export{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
.pp-s5-export label{font-size:12px}.pp-s5-export input,.pp-s5-export select{width:100%;box-sizing:border-box;padding:7px;border:1px solid var(--border,#d8dde6);border-radius:7px;background:var(--card,#fff)}
.pp-s5-export .full{grid-column:1/-1}.pp-s5-btn{width:100%;padding:8px;border:1px solid var(--border,#d8dde6);border-radius:7px;background:var(--card,#fff);cursor:pointer}
.pp-s5-status{font-size:11px;opacity:.72;margin-top:7px}
@media(max-width:800px){.pp-s5-export{grid-template-columns:1fr}}
</style>"""
h=h.replace("</head>",css+"</head>",1)

panel=r"""<div class="tool-section" id="ppImgStage5ExportPro">
<h4>Export Pro</h4>
<div class="pp-s5-export">
<div><label>Format</label><select id="ppS5Format"><option value="image/jpeg">JPG</option><option value="image/png">PNG</option><option value="image/webp">WebP</option></select></div>
<div><label>Quality <span id="ppS5QualityV">92</span>%</label><input id="ppS5Quality" type="range" min="10" max="100" value="92"></div>
<div><label>Scale</label><select id="ppS5Scale"><option value="1">100%</option><option value=".75">75%</option><option value=".5">50%</option><option value=".25">25%</option><option value="2">200%</option></select></div>
<div><label>Filename</label><input id="ppS5Name" value="privatepdf-image"></div>
<div class="full"><button class="pp-s5-btn" type="button" onclick="ppImgS5Export()">Export image</button></div>
</div>
<div id="ppS5Status" class="pp-s5-status">Export stays in your browser.</div>
</div>"""
if '<h4>Export</h4>' in h and "ppImgStage5ExportPro" not in h:
 h=h.replace('<h4>Export</h4>',panel+'<h4>Export</h4>',1)
elif "ppImgStage5ExportPro" not in h:
 h=h.replace("</body>",panel+"</body>",1)

js=r"""<script id="pp-image-studio-stage5-js">
/* PP_IMAGE_STUDIO_2_0_STAGE5_JS */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const q=$("ppS5Quality"),qv=$("ppS5QualityV"); if(q)q.addEventListener("input",()=>{if(qv)qv.textContent=q.value});
window.ppImgS5Export=function(){
 const src=window.ppImgCanvas;if(!src||!src.width)return;
 const scale=+($("ppS5Scale")?.value||1), type=$("ppS5Format")?.value||"image/jpeg", quality=(+$("ppS5Quality")?.value||92)/100;
 const out=document.createElement("canvas");out.width=Math.max(1,Math.round(src.width*scale));out.height=Math.max(1,Math.round(src.height*scale));
 const ctx=out.getContext("2d");ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality="high";ctx.drawImage(src,0,0,out.width,out.height);
 out.toBlob(blob=>{
   if(!blob)return;
   const a=document.createElement("a"), ext=type==="image/png"?"png":type==="image/webp"?"webp":"jpg";
   let name=($("ppS5Name")?.value||"privatepdf-image").trim().replace(/[^a-zA-Z0-9._-]+/g,"-").replace(/^-+|-+$/g,"")||"privatepdf-image";
   a.href=URL.createObjectURL(blob);a.download=name+"."+ext;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1500);
   const st=$("ppS5Status");if(st)st.textContent="Exported "+ext.toUpperCase()+" • "+out.width+"×"+out.height;
 },type,type==="image/png"?undefined:quality);
};
document.addEventListener("keydown",e=>{
 const tag=(e.target?.tagName||"").toLowerCase();if(tag==="input"||tag==="textarea"||tag==="select")return;
 if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="s"){e.preventDefault();window.ppImgS5Export()}
 if(e.key==="Delete"||e.key==="Backspace"){if(typeof window.ppImgS3DeleteSelected==="function")window.ppImgS3DeleteSelected()}
 if(e.key==="Escape"&&typeof window.ppImgS3Select==="function")window.ppImgS3Select(null)}
);
})();
</script>"""
h=h.replace("</body>",js+"</body>",1)
INDEX.write_text(h,encoding="utf-8")

for k,v in {"STAGE5_CSS":"PP_IMAGE_STUDIO_2_0_STAGE5_CSS" in h,"STAGE5_JS":"PP_IMAGE_STUDIO_2_0_STAGE5_JS" in h,"EXPORT_PRO":"ppImgS5Export" in h,"JPG_PNG_WEBP":"image/webp" in h,"QUALITY":"ppS5Quality" in h,"SCALE":"ppS5Scale" in h,"KEYBOARD_SHORTCUTS":"ctrlKey" in h}.items():
 print(k+":","PASS" if v else "FAIL")
print("IMAGE_STUDIO_2_0_STAGE5_APPLIED")
print("backup:",backup.name)
print("index.html bytes:",INDEX.stat().st_size)
print("main.py was NOT modified.")
print("Security/backend/annotation/batch untouched.")
print("IMAGE STUDIO 2.0 STAGE 5 COMPLETE")
