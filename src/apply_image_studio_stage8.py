from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parent
INDEX=next((x for x in (ROOT/'index.html',ROOT/'static'/'index.html') if x.exists()),None)
if not INDEX: raise SystemExit('ERROR: index.html not found')
h=INDEX.read_text(encoding='utf-8')
if 'PP_IMAGE_STUDIO_2_0_STAGE7_CSS' not in h: raise SystemExit('ERROR: Stage 7 marker not found')
if 'PP_IMAGE_STUDIO_2_0_STAGE8_CSS' in h:
    print('IMAGE_STUDIO_2_0_STAGE8_ALREADY_APPLIED'); raise SystemExit
backup=INDEX.with_name('index_before_image_studio_2_0_stage8_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.html')
backup.write_text(h,encoding='utf-8')

# Remove visible literal newline escape artifacts introduced by earlier HTML patches.
h=h.replace(r'\\n','').replace(r'\\r\\n','')

css='''<style id="pp-image-studio-stage8-css">
/* PP_IMAGE_STUDIO_2_0_STAGE8_CSS */
#ppImgStage7Shell{width:100%;box-sizing:border-box;margin:0 0 10px}
#ppImgStage7Shell .pp-s7-menu{position:sticky;top:8px;z-index:50;display:flex;align-items:center;gap:5px;width:100%;box-sizing:border-box;overflow-x:auto;overflow-y:hidden;padding:5px;background:var(--card,#fff);border:1px solid var(--border,#d8dde6);box-shadow:0 4px 14px rgba(0,0,0,.05);-webkit-overflow-scrolling:touch}
#ppImgStage7Shell .pp-s7-menu button{flex:0 0 auto;min-height:38px;touch-action:manipulation;white-space:nowrap}
#ppImgStage7Shell .pp-s7-content,#ppImgStage7Shell .pp-s7-pane{width:100%;box-sizing:border-box}
#ppImgStage7Shell .pp-s7-submenu{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:7px}
#ppImgStage7Shell .pp-s7-submenu button{min-height:38px;touch-action:manipulation}
#ppImgStage5ExportPro,#ppImgStage6ProTools,#ppImgStage4Adjustments,#ppImgStage4TextPro{width:100%;box-sizing:border-box;overflow:hidden}
#ppImgStage5ExportPro,#ppImgStage6ProTools{background:var(--card,#fff);border:1px solid var(--border,#d8dde6);border-radius:12px;padding:12px;margin-top:10px;box-shadow:0 3px 12px rgba(0,0,0,.04)}
#ppImgStage5ExportPro h4,#ppImgStage6ProTools h4{margin:0 0 10px}
#ppImgStage5ExportPro .pp-s5-export{display:grid;grid-template-columns:minmax(120px,1fr) minmax(160px,1.4fr);gap:10px;align-items:end}
#ppImgStage5ExportPro .pp-s5-export>div{min-width:0}
#ppImgStage5ExportPro input,#ppImgStage5ExportPro select{max-width:100%;box-sizing:border-box}
#ppImgStage5ExportPro .pp-s5-btn{min-height:40px;font-weight:700;touch-action:manipulation}
#ppImgStage6ProTools .pp-s6-panel{background:var(--surface,#f7f8fc);border:1px solid var(--border,#d8dde6);border-radius:10px;padding:10px;margin-top:9px;box-sizing:border-box}
#ppImgStage6ProTools .pp-s6-presets{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}
#ppImgStage6ProTools .pp-s6-btn{min-height:38px;touch-action:manipulation}
#ppImgStage8QuickBar{width:100%;box-sizing:border-box}
#ppImgStage8QuickBar .pp-s5-btn{flex:0 0 auto;min-height:38px}
@media(max-width:900px){#ppImgStage5ExportPro .pp-s5-export{grid-template-columns:1fr 1fr}#ppImgStage6ProTools .pp-s6-presets{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){#ppImgStage7Shell .pp-s7-menu{position:relative;top:auto}#ppImgStage7Shell .pp-s7-menu button{min-height:40px;padding:8px 10px}#ppImgStage7Shell .pp-s7-submenu{grid-template-columns:repeat(2,minmax(0,1fr))}#ppImgStage5ExportPro,#ppImgStage6ProTools{padding:10px;border-radius:10px}#ppImgStage5ExportPro .pp-s5-export{grid-template-columns:1fr}#ppImgStage6ProTools .pp-s6-presets{grid-template-columns:1fr 1fr}}
@media(max-width:390px){#ppImgStage7Shell .pp-s7-menu button{font-size:10px;padding:7px 8px}#ppImgStage7Shell .pp-s7-submenu{grid-template-columns:1fr}#ppImgStage6ProTools .pp-s6-presets{grid-template-columns:1fr}#ppImgStage5ExportPro{padding:9px}#ppImgStage8QuickBar{display:grid!important;grid-template-columns:1fr 1fr;gap:6px!important}#ppImgStage8QuickBar span{grid-column:1/-1;margin-left:0!important}}
</style>'''
h=h.replace('</head>',css+'</head>',1)

panel='''<div id="ppImgStage8QuickBar" style="display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin:8px 0;padding:8px;border:1px solid var(--border,#d8dde6);border-radius:10px;background:var(--card,#fff)"><button type="button" class="pp-s5-btn" onclick="ppImgS8Focus('Choose image')">Add image</button><button type="button" class="pp-s5-btn" onclick="ppImgS8Undo()">Undo</button><button type="button" class="pp-s5-btn" onclick="ppImgS8Redo()">Redo</button><button type="button" class="pp-s5-btn" onclick="ppImgS8Focus('Export Pro')">Export</button><span style="font-size:11px;opacity:.68;margin-left:auto">All editing stays local in your browser.</span></div>'''
if 'ppImgStage8QuickBar' not in h:
    pos=h.find('<div id="ppImgStage7Shell"')
    h=h[:pos]+panel+h[pos:] if pos>=0 else h.replace('</body>',panel+'</body>',1)

js='''<script id="pp-image-studio-stage8-js">
/* PP_IMAGE_STUDIO_2_0_STAGE8_JS */
(function(){'use strict';
window.ppImgS8Focus=function(label){const all=[...document.querySelectorAll('.tool-section')];let el=all.find(x=>(x.querySelector('h4')?.textContent||'').trim().toLowerCase()===label.toLowerCase());if(!el)el=all.find(x=>(x.textContent||'').toLowerCase().includes(label.toLowerCase()));if(el){el.scrollIntoView({behavior:'smooth',block:'center'});el.style.boxShadow='0 0 0 2px rgba(80,120,255,.35)';setTimeout(()=>el.style.boxShadow='',900)}};
window.ppImgS8Undo=function(){if(typeof window.ppImgUndo==='function')window.ppImgUndo();else if(typeof window.ppImgS3Undo==='function')window.ppImgS3Undo()};
window.ppImgS8Redo=function(){if(typeof window.ppImgRedo==='function')window.ppImgRedo();else if(typeof window.ppImgS3Redo==='function')window.ppImgS3Redo()};
})();
</script>'''
h=h.replace('</body>',js+'</body>',1)
INDEX.write_text(h,encoding='utf-8')
checks={'STAGE8_CSS':'PP_IMAGE_STUDIO_2_0_STAGE8_CSS' in h,'STAGE8_JS':'PP_IMAGE_STUDIO_2_0_STAGE8_JS' in h,'QUICK_BAR':'ppImgStage8QuickBar' in h,'EXPORT_PRO_UI':'ppImgStage5ExportPro' in h,'PRO_TOOLS_UI':'ppImgStage6ProTools' in h,'RESPONSIVE_900':'@media(max-width:900px)' in h,'RESPONSIVE_600':'@media(max-width:600px)' in h,'RESPONSIVE_390':'@media(max-width:390px)' in h}
print('IMAGE_STUDIO_2_0_STAGE8_APPLIED');print('backup:',backup.name);print('index.html bytes:',INDEX.stat().st_size)
for k,v in checks.items(): print(k+':','PASS' if v else 'FAIL')
print('main.py was NOT modified.');print('Security/backend/annotation/batch untouched.');print('IMAGE STUDIO 2.0 STAGE 8 COMPLETE')
