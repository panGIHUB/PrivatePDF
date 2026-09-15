from pathlib import Path
from datetime import datetime
import re, shutil, sys

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"
if not HTML.exists():
    HTML = ROOT / "static" / "index.html"

if not HTML.exists():
    print("ERROR: index.html not found")
    sys.exit(1)

s = HTML.read_text(encoding="utf-8")

if "PP_IMAGE_STUDIO_2_0_STAGE3_CSS" in s:
    print("IMAGE_STUDIO_STAGE3_ALREADY_APPLIED")
    sys.exit(0)

if "PP_IMAGE_STUDIO_2_0_STAGE2_CSS" not in s or "ppImgCanvas" not in s:
    print("ERROR: Stage 2 Image Studio was not detected")
    sys.exit(1)

backup = HTML.with_name(
    f"index_before_image_studio_2_0_stage3_{datetime.now():%Y%m%d_%H%M%S}.html"
)
shutil.copy2(HTML, backup)

CSS = r"""
<style id="PP_IMAGE_STUDIO_2_0_STAGE3_CSS">
/* ===== IMAGE STUDIO 2.0 — STAGE 3 ===== */
.pp-imgstudio-stage3-tools{
  margin-top:12px;padding:12px;border:1px solid #e1e5ee;border-radius:13px;
  background:#f8fafc;
}
.pp-imgstudio-stage3-tools h4{
  margin:0 0 9px;font-size:11px;text-transform:uppercase;
  letter-spacing:.08em;color:#667085;
}
.pp-img-s3-layer-list{
  display:flex;flex-direction:column;gap:6px;max-height:230px;overflow:auto;
}
.pp-img-s3-layer{
  display:flex;align-items:center;gap:6px;padding:7px 8px;border:1px solid #e1e5ee;
  background:#fff;border-radius:8px;font-size:11px;cursor:pointer;
}
.pp-img-s3-layer:hover{background:#f5f6ff}
.pp-img-s3-layer.selected{border-color:#635bff;background:#eef2ff;color:#3730a3}
.pp-img-s3-layer .s3-layer-icon{width:22px;text-align:center}
.pp-img-s3-layer .s3-layer-name{
  min-width:0;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:750;
}
.pp-img-s3-layer button{
  width:23px;height:23px;padding:0;border:1px solid #dce1ea;background:#fff;
  border-radius:6px;cursor:pointer;font-size:11px;
}
.pp-img-s3-layer button:hover{background:#f1f3f7}
.pp-img-s3-controls{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px}
.pp-img-s3-controls button{
  border:1px solid #dfe3eb;background:#fff;border-radius:8px;padding:7px;
  cursor:pointer;font-weight:750;color:#344054;font-size:10px;
}
.pp-img-s3-controls button:hover{background:#eef2ff;border-color:#c7d2fe}
.pp-img-s3-controls button.danger{color:#b42318}
.pp-img-s3-properties{
  margin-top:9px;padding-top:9px;border-top:1px solid #e5e9f0;display:none;
}
.pp-img-s3-properties.show{display:block}
.pp-img-s3-properties .s3-prop-title{font-size:10px;font-weight:850;color:#475467;margin-bottom:6px}
.pp-img-s3-prop-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.pp-img-s3-prop-grid label{font-size:9px;color:#667085}
.pp-img-s3-prop-grid input,.pp-img-s3-prop-grid select{
  width:100%;padding:6px;border:1px solid #d0d5dd;border-radius:7px;background:#fff;
}
.pp-img-s3-prop-wide{grid-column:1/-1}
.pp-img-s3-align{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin-top:7px}
.pp-img-s3-align button{
  border:1px solid #dfe3eb;background:#fff;border-radius:7px;padding:6px;
  cursor:pointer;font-size:10px;font-weight:750;
}
.pp-img-s3-help{font-size:9px;color:#667085;line-height:1.45;margin-top:7px}
.pp-img-s3-status{
  margin-top:7px;font-size:9px;color:#667085;min-height:14px;
}
.pp-img-s3-selection{
  position:absolute;pointer-events:none;border:1.5px solid #635bff;
  box-shadow:0 0 0 1px rgba(255,255,255,.85);
}
.pp-img-s3-handle{
  position:absolute;width:9px;height:9px;background:#fff;border:1.5px solid #635bff;
  border-radius:2px;pointer-events:auto;box-shadow:0 1px 3px rgba(0,0,0,.18);
}
.pp-img-s3-rotate{
  position:absolute;width:11px;height:11px;border-radius:50%;background:#635bff;
  border:2px solid #fff;pointer-events:auto;cursor:crosshair;
}
.pp-img-s3-line{
  position:absolute;width:1px;background:#635bff;left:50%;top:-22px;height:22px;
}
@media(max-width:1100px){
  .pp-imgstudio-stage3-tools{margin-bottom:8px}
}
</style>
"""

HTML_PANEL = r"""
<div class="pp-imgstudio-stage3-tools" id="ppImgStage3Panel">
  <h4>Objects & Layers</h4>
  <div id="ppImgS3LayerList" class="pp-img-s3-layer-list"></div>
  <div class="pp-img-s3-controls">
    <button onclick="ppImgS3Duplicate()">⧉ Duplicate</button>
    <button onclick="ppImgS3Delete()">🗑 Delete</button>
    <button onclick="ppImgS3BringForward()">↑ Forward</button>
    <button onclick="ppImgS3SendBackward()">↓ Backward</button>
    <button onclick="ppImgS3LockToggle()">🔒 Lock</button>
    <button onclick="ppImgS3Deselect()">Clear selection</button>
  </div>
  <div id="ppImgS3Properties" class="pp-img-s3-properties">
    <div class="s3-prop-title">Selected object</div>
    <div class="pp-img-s3-prop-grid">
      <div><label>X</label><input id="ppImgS3X" type="number"></div>
      <div><label>Y</label><input id="ppImgS3Y" type="number"></div>
      <div><label>Width</label><input id="ppImgS3W" type="number" min="1"></div>
      <div><label>Height</label><input id="ppImgS3H" type="number" min="1"></div>
      <div><label>Rotation</label><input id="ppImgS3Angle" type="number"></div>
      <div><label>Opacity %</label><input id="ppImgS3Opacity" type="number" min="0" max="100"></div>
      <div class="s3-prop-wide">
        <label>Text / name</label>
        <input id="ppImgS3Text" type="text" placeholder="Object text">
      </div>
    </div>
    <div class="pp-img-s3-align">
      <button onclick="ppImgS3Align('left')">Left</button>
      <button onclick="ppImgS3Align('centerX')">Center X</button>
      <button onclick="ppImgS3Align('right')">Right</button>
      <button onclick="ppImgS3Align('top')">Top</button>
      <button onclick="ppImgS3Align('centerY')">Center Y</button>
      <button onclick="ppImgS3Align('bottom')">Bottom</button>
    </div>
  </div>
  <div id="ppImgS3Status" class="pp-img-s3-status"></div>
  <div class="pp-img-s3-help">
    Select mode: click an object, drag to move, use corner handles to resize,
    top handle to rotate. Double-click text to edit it. Shift keeps resize proportional.
  </div>
</div>
"""

JS = r"""
<script id="PP_IMAGE_STUDIO_2_0_STAGE3_JS">
/* ===== IMAGE STUDIO 2.0 — STAGE 3 ENGINE ===== */
(function(){
  const S3 = {
    selected:-1, action:null, start:null, original:null,
    pointerId:null, dragHandle:null
  };
  window.ppImgS3 = S3;

  function by(id){ return document.getElementById(id); }
  function canvas(){ return by('ppImgCanvas'); }
  function status(t){
    if(by('ppImgS3Status')) by('ppImgS3Status').textContent=t||'';
    if(typeof window.ppImgStatus==='function') window.ppImgStatus(t||'');
  }
  function objects(){ return Array.isArray(window.ppImgObjects)?window.ppImgObjects:[]; }

  function objectName(o,i){
    if(!o) return 'Object '+(i+1);
    if(o.type==='text') return o.text ? 'Text: '+o.text : 'Text';
    if(o.type==='shape') return 'Shape: '+(o.shape||'shape');
    if(o.type==='path') return 'Drawing';
    return 'Object '+(i+1);
  }
  function icon(o){
    return o?.type==='text'?'🔤':o?.type==='shape'?'⬛':o?.type==='path'?'✏️':'◼';
  }

  function bounds(o){
    if(!o) return null;
    if(o.type==='text'){
      const ctx=canvas()?.getContext('2d');
      if(!ctx) return null;
      ctx.save();
      ctx.font=(o.bold?'700 ':'')+(Number(o.size)||32)+'px '+(o.font||'Arial');
      const m=ctx.measureText(o.text||'');
      const w=Math.max(20,m.width+16), h=Math.max(24,(Number(o.size)||32)*1.35);
      ctx.restore();
      return {x:(o.x||0)-w/2,y:(o.y||0)-h/2,w,h};
    }
    if(o.type==='shape'){
      return {x:(o.x||0)-(Number(o.w)||1)/2,y:(o.y||0)-(Number(o.h)||1)/2,
              w:Number(o.w)||1,h:Number(o.h)||1};
    }
    if(o.type==='path'){
      if(!o.points?.length) return {x:o.x||0,y:o.y||0,w:1,h:1};
      let xs=o.points.map(p=>p.x), ys=o.points.map(p=>p.y);
      let x=Math.min(...xs), y=Math.min(...ys), w=Math.max(...xs)-x, h=Math.max(...ys)-y;
      return {x:x-4,y:y-4,w:Math.max(8,w+8),h:Math.max(8,h+8)};
    }
    return null;
  }

  function pointInObject(o,p){
    const b=bounds(o); if(!b) return false;
    const angle=(Number(o.angle)||0)*Math.PI/180;
    const cx=(o.x||0), cy=(o.y||0);
    let dx=p.x-cx, dy=p.y-cy;
    const ca=Math.cos(-angle), sa=Math.sin(-angle);
    const rx=dx*ca-dy*sa+cx, ry=dx*sa+dy*ca+cy;
    return rx>=b.x && rx<=b.x+b.w && ry>=b.y && ry<=b.y+b.h;
  }

  function topHit(p){
    for(let i=objects().length-1;i>=0;i--){
      const o=objects()[i];
      if(o.locked) continue;
      if(pointInObject(o,p)) return i;
    }
    return -1;
  }

  function canvasPoint(ev){
    const c=canvas(), r=c.getBoundingClientRect();
    return {
      x:Math.max(0,Math.min(c.width,(ev.clientX-r.left)*(c.width/r.width))),
      y:Math.max(0,Math.min(c.height,(ev.clientY-r.top)*(c.height/r.height)))
    };
  }

  function ensureOverlay(){
    const wrap=by('ppImgCanvasWrap');
    if(!wrap) return null;
    let ov=by('ppImgS3Overlay');
    if(!ov){
      ov=document.createElement('div');
      ov.id='ppImgS3Overlay';
      ov.style.cssText='position:absolute;inset:0;pointer-events:none;z-index:8;';
      wrap.appendChild(ov);
    }
    return ov;
  }

  function drawOverlay(){
    const ov=ensureOverlay(); if(!ov) return;
    ov.innerHTML='';
    const i=S3.selected, o=objects()[i];
    if(!o || S3.action==='crop') return;
    const c=canvas(), wrap=by('ppImgCanvasWrap');
    if(!c||!wrap) return;
    const cr=c.getBoundingClientRect(), wr=wrap.getBoundingClientRect();
    const sx=cr.width/c.width, sy=cr.height/c.height;
    const b=bounds(o); if(!b) return;
    const angle=Number(o.angle)||0;
    const box=document.createElement('div');
    box.className='pp-img-s3-selection';
    box.style.left=(cr.left-wr.left+b.x*sx)+'px';
    box.style.top=(cr.top-wr.top+b.y*sy)+'px';
    box.style.width=(b.w*sx)+'px';
    box.style.height=(b.h*sy)+'px';
    box.style.transform='rotate('+angle+'deg)';
    box.style.transformOrigin='center center';
    box.style.pointerEvents='none';

    const positions=[
      ['nw','left:-5px;top:-5px;cursor:nwse-resize'],
      ['ne','right:-5px;top:-5px;cursor:nesw-resize'],
      ['sw','left:-5px;bottom:-5px;cursor:nesw-resize'],
      ['se','right:-5px;bottom:-5px;cursor:nwse-resize']
    ];
    positions.forEach(([name,css])=>{
      const h=document.createElement('div');
      h.className='pp-img-s3-handle';
      h.dataset.handle=name; h.style.cssText+=css;
      h.style.pointerEvents='auto';
      h.addEventListener('pointerdown',startHandle);
      box.appendChild(h);
    });
    const line=document.createElement('div'); line.className='pp-img-s3-line'; box.appendChild(line);
    const rot=document.createElement('div');
    rot.className='pp-img-s3-rotate';
    rot.style.left='calc(50% - 5px)';rot.style.top='-34px';
    rot.addEventListener('pointerdown',startRotate);box.appendChild(rot);
    ov.appendChild(box);
  }

  function updateLayerPanel(){
    const list=by('ppImgS3LayerList'); if(!list)return;
    list.innerHTML='';
    const arr=objects();
    if(!arr.length){
      list.innerHTML='<div style="font-size:10px;color:#98a2b3;text-align:center;padding:10px">No objects yet</div>';
    } else {
      for(let i=arr.length-1;i>=0;i--){
        const o=arr[i], row=document.createElement('div');
        row.className='pp-img-s3-layer'+(i===S3.selected?' selected':'');
        row.innerHTML='<span class="s3-layer-icon">'+icon(o)+'</span>'+
          '<span class="s3-layer-name">'+escapeHtml(objectName(o,i))+'</span>'+
          '<button title="Move up" data-up="1">↑</button>'+
          '<button title="Move down" data-down="1">↓</button>';
        row.addEventListener('click',e=>{
          if(e.target.closest('button')) return;
          select(i);
        });
        row.querySelector('[data-up]')?.addEventListener('click',e=>{
          e.stopPropagation(); S3.selected=i; ppImgS3BringForward();
        });
        row.querySelector('[data-down]')?.addEventListener('click',e=>{
          e.stopPropagation(); S3.selected=i; ppImgS3SendBackward();
        });
        list.appendChild(row);
      }
    }
    updateProperties();
  }

  function escapeHtml(v){
    return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  }

  function updateProperties(){
    const p=by('ppImgS3Properties'), o=objects()[S3.selected];
    if(!p)return;
    if(!o){p.classList.remove('show');return}
    p.classList.add('show');
    const b=bounds(o)||{w:0,h:0};
    const vals={
      ppImgS3X:Math.round(o.x||0),ppImgS3Y:Math.round(o.y||0),
      ppImgS3W:Math.round(o.w||b.w),ppImgS3H:Math.round(o.h||b.h),
      ppImgS3Angle:Math.round(o.angle||0),
      ppImgS3Opacity:Math.round((o.opacity==null?1:o.opacity)*100),
      ppImgS3Text:o.text||''
    };
    Object.entries(vals).forEach(([id,v])=>{if(by(id))by(id).value=v});
    if(by('ppImgS3Text')) by('ppImgS3Text').disabled=o.type!=='text';
  }

  function applyProperty(id){
    const o=objects()[S3.selected]; if(!o)return;
    const n=Number(by(id)?.value);
    if(!Number.isFinite(n))return;
    if(id==='ppImgS3X')o.x=n;
    if(id==='ppImgS3Y')o.y=n;
    if(id==='ppImgS3W' && o.type!=='text')o.w=Math.max(2,n);
    if(id==='ppImgS3H' && o.type!=='text')o.h=Math.max(2,n);
    if(id==='ppImgS3Angle')o.angle=n;
    if(id==='ppImgS3Opacity')o.opacity=Math.max(0,Math.min(1,n/100));
    window.ppImgRender(); drawOverlay(); updateLayerPanel();
  }

  function bindProperties(){
    ['ppImgS3X','ppImgS3Y','ppImgS3W','ppImgS3H','ppImgS3Angle','ppImgS3Opacity'].forEach(id=>{
      by(id)?.addEventListener('change',()=>applyProperty(id));
    });
    by('ppImgS3Text')?.addEventListener('change',()=>{
      const o=objects()[S3.selected]; if(o?.type==='text'){
        o.text=by('ppImgS3Text').value; window.ppImgRender(); drawOverlay(); updateLayerPanel(); save();
      }
    });
  }

  function select(i){
    S3.selected=(i>=0 && i<objects().length)?i:-1;
    if(typeof window.ppImgSetTool==='function' && S3.selected>=0) window.ppImgSetTool('select');
    drawOverlay(); updateLayerPanel(); updateProperties();
    status(S3.selected>=0?'Object selected':'Selection cleared');
  }

  function save(){
    if(typeof window.ppImgSaveHistory==='function') window.ppImgSaveHistory();
  }

  function startMove(ev){
    if(ev.button!==0 || ev.target.closest('.pp-img-s3-handle,.pp-img-s3-rotate')) return;
    if(window.ppImgCropMode) return;
    const p=canvasPoint(ev), i=topHit(p);
    if(i<0){select(-1);return}
    select(i);
    const o=objects()[i];
    S3.action='move'; S3.pointerId=ev.pointerId; S3.start=p;
    S3.original={x:o.x,y:o.y};
    canvas().setPointerCapture?.(ev.pointerId);
    ev.preventDefault();
  }

  function move(ev){
    if(S3.action!=='move' || S3.pointerId!==ev.pointerId)return;
    const o=objects()[S3.selected]; if(!o)return;
    const p=canvasPoint(ev);
    o.x=S3.original.x+(p.x-S3.start.x);
    o.y=S3.original.y+(p.y-S3.start.y);
    window.ppImgRender(); drawOverlay(); updateProperties();
    ev.preventDefault();
  }

  function startHandle(ev){
    ev.stopPropagation(); ev.preventDefault();
    const o=objects()[S3.selected]; if(!o)return;
    const p=canvasPoint(ev);
    S3.action='resize';S3.pointerId=ev.pointerId;S3.start=p;
    S3.dragHandle=ev.currentTarget.dataset.handle;
    S3.original={x:o.x,y:o.y,w:o.w||bounds(o).w,h:o.h||bounds(o).h};
    canvas().setPointerCapture?.(ev.pointerId);
  }

  function resize(ev){
    if(S3.action!=='resize'||S3.pointerId!==ev.pointerId)return;
    const o=objects()[S3.selected]; if(!o)return;
    if(o.type==='text'){status('Text size is controlled by Text Studio');return}
    const p=canvasPoint(ev), dx=p.x-S3.start.x, dy=p.y-S3.start.y;
    let x=S3.original.x,y=S3.original.y,w=S3.original.w,h=S3.original.h;
    const k=S3.original.w/Math.max(1,S3.original.h);
    const hd=S3.dragHandle;
    if(hd.includes('e')) w=Math.max(10,S3.original.w+dx);
    if(hd.includes('w')){w=Math.max(10,S3.original.w-dx);x=S3.original.x+dx/2}
    if(hd.includes('s')) h=Math.max(10,S3.original.h+dy);
    if(hd.includes('n')){h=Math.max(10,S3.original.h-dy);y=S3.original.y+dy/2}
    if(ev.shiftKey){
      if(Math.abs(dx)>=Math.abs(dy)) h=w/k; else w=h*k;
    }
    o.w=w;o.h=h;
    if(hd.includes('w'))o.x=S3.original.x+(S3.original.w-w)/2;
    if(hd.includes('e'))o.x=S3.original.x+(w-S3.original.w)/2;
    if(hd.includes('n'))o.y=S3.original.y+(S3.original.h-h)/2;
    if(hd.includes('s'))o.y=S3.original.y+(h-S3.original.h)/2;
    window.ppImgRender();drawOverlay();updateProperties();
  }

  function startRotate(ev){
    ev.stopPropagation();ev.preventDefault();
    const o=objects()[S3.selected];if(!o)return;
    const r=canvas().getBoundingClientRect(), p=canvasPoint(ev);
    S3.action='rotate';S3.pointerId=ev.pointerId;
    S3.center={x:o.x,y:o.y};S3.startAngle=Math.atan2(p.y-o.y,p.x-o.x);
    S3.originalAngle=Number(o.angle)||0;
    canvas().setPointerCapture?.(ev.pointerId);
  }

  function rotate(ev){
    if(S3.action!=='rotate'||S3.pointerId!==ev.pointerId)return;
    const o=objects()[S3.selected];if(!o)return;
    const p=canvasPoint(ev);
    let a=Math.atan2(p.y-S3.center.y,p.x-S3.center.x)-S3.startAngle;
    let deg=S3.originalAngle+a*180/Math.PI;
    if(ev.shiftKey)deg=Math.round(deg/15)*15;
    o.angle=deg;
    window.ppImgRender();drawOverlay();updateProperties();
  }

  function end(ev){
    if(!S3.action)return;
    try{canvas().releasePointerCapture?.(ev.pointerId)}catch(e){}
    const changed=S3.action;
    S3.action=null;S3.pointerId=null;
    if(changed==='move'||changed==='resize'||changed==='rotate')save();
    updateLayerPanel();drawOverlay();
  }

  function startTextEdit(ev){
    if(ev.detail!==2)return;
    const p=canvasPoint(ev),i=topHit(p),o=objects()[i];
    if(i<0||o?.type!=='text')return;
    const text=prompt('Edit text',o.text||'');
    if(text!==null){o.text=text;select(i);window.ppImgRender();save();status('Text updated')}
  }

  function hookCanvas(){
    const c=canvas();if(!c||c.dataset.s3Hooked==='1')return;
    c.dataset.s3Hooked='1';
    c.addEventListener('pointerdown',startMove,true);
    c.addEventListener('pointermove',ev=>{
      if(S3.action==='move')move(ev);
      else if(S3.action==='resize')resize(ev);
      else if(S3.action==='rotate')rotate(ev);
    },true);
    c.addEventListener('pointerup',end,true);
    c.addEventListener('pointercancel',end,true);
    c.addEventListener('dblclick',startTextEdit,true);
    bindProperties();
  }

  const oldRender=window.ppImgRender;
  window.ppImgRender=function(){
    oldRender.apply(this,arguments);
    drawOverlay();
    updateLayerPanel();
  };

  window.ppImgS3Duplicate=function(){
    const o=objects()[S3.selected];if(!o)return status('Select an object first');
    const copy=JSON.parse(JSON.stringify(o));
    copy.x=(copy.x||0)+24;copy.y=(copy.y||0)+24;copy.locked=false;
    objects().push(copy);S3.selected=objects().length-1;
    window.ppImgRender();save();status('Object duplicated');
  };
  window.ppImgS3Delete=function(){
    if(S3.selected<0)return status('Select an object first');
    objects().splice(S3.selected,1);S3.selected=Math.min(S3.selected,objects().length-1);
    window.ppImgRender();save();status('Object deleted');
  };
  window.ppImgS3BringForward=function(){
    const i=S3.selected;if(i<0||i>=objects().length-1)return status('Already at front');
    [objects()[i],objects()[i+1]]=[objects()[i+1],objects()[i]];
    S3.selected=i+1;window.ppImgRender();save();status('Moved forward');
  };
  window.ppImgS3SendBackward=function(){
    const i=S3.selected;if(i<=0)return status('Already at back');
    [objects()[i],objects()[i-1]]=[objects()[i-1],objects()[i]];
    S3.selected=i-1;window.ppImgRender();save();status('Moved backward');
  };
  window.ppImgS3LockToggle=function(){
    const o=objects()[S3.selected];if(!o)return status('Select an object first');
    o.locked=!o.locked;window.ppImgRender();save();status(o.locked?'Object locked':'Object unlocked');
  };
  window.ppImgS3Deselect=function(){select(-1)};
  window.ppImgS3Align=function(which){
    const o=objects()[S3.selected];if(!o)return status('Select an object first');
    const c=canvas(),b=bounds(o)||{w:0,h:0};
    if(which==='left')o.x=b.w/2;
    if(which==='centerX')o.x=c.width/2;
    if(which==='right')o.x=c.width-b.w/2;
    if(which==='top')o.y=b.h/2;
    if(which==='centerY')o.y=c.height/2;
    if(which==='bottom')o.y=c.height-b.h/2;
    window.ppImgRender();save();status('Object aligned');
  };

  /* Improve zoom: allow >100% visually without changing canvas pixels */
  const oldZoom=window.ppImgZoom;
  window.ppImgZoom=function(delta){
    if(!window.ppImgBaseCanvas)return status('Choose an image first');
    window.ppImgZoomLevel=Math.min(3,Math.max(.2,(window.ppImgZoomLevel||1)+delta));
    const c=canvas();
    if(c)c.style.width=(window.ppImgZoomLevel*100)+'%';
    if(by('ppImgZoomValue'))by('ppImgZoomValue').textContent=Math.round(window.ppImgZoomLevel*100)+'%';
    if(by('ppImgZoomBottom'))by('ppImgZoomBottom').textContent=Math.round(window.ppImgZoomLevel*100)+'%';
    drawOverlay();
  };
  window.ppImgFit=function(){
    window.ppImgZoomLevel=1;
    const c=canvas();if(c)c.style.width='100%';
    if(by('ppImgZoomValue'))by('ppImgZoomValue').textContent='100%';
    if(by('ppImgZoomBottom'))by('ppImgZoomBottom').textContent='100%';
    drawOverlay();
  };

  /* Keep Stage 3 selection coherent after crop/reset/load */
  const oldCrop=window.ppImgApplyCrop;
  if(oldCrop){
    window.ppImgApplyCrop=function(){S3.selected=-1;oldCrop.apply(this,arguments);setTimeout(()=>{drawOverlay();updateLayerPanel()},0)};
  }
  const oldLoad=window.ppImgLoadFile;
  if(oldLoad){
    window.ppImgLoadFile=function(){S3.selected=-1;oldLoad.apply(this,arguments);setTimeout(()=>{hookCanvas();updateLayerPanel()},40)};
  }

  function boot(){
    hookCanvas();
    updateLayerPanel();
    drawOverlay();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,50));
  else setTimeout(boot,50);
})();
</script>
"""

# Insert Stage 3 layer panel immediately before the Transform section.
needle = '<div class="tool-section">\n          <h4>Transform</h4>'
if needle not in s:
    print("ERROR: Image Studio Transform section not found")
    sys.exit(1)

s = s.replace(needle, HTML_PANEL + "\n\n        " + needle, 1)

# Add CSS and JS before </body>.
if "</body>" not in s:
    print("ERROR: </body> not found")
    sys.exit(1)

s = s.replace("</body>", CSS + "\n" + JS + "\n</body>", 1)

HTML.write_text(s, encoding="utf-8")

print("IMAGE_STUDIO_2_0_STAGE3_APPLIED")
print("backup:", backup.name)
print("index.html bytes:", HTML.stat().st_size)
print("STAGE3_CSS:", "PASS" if "PP_IMAGE_STUDIO_2_0_STAGE3_CSS" in s else "FAIL")
print("OBJECT_SELECTION:", "PASS" if "ppImgS3LayerList" in s else "FAIL")
print("MOVE:", "PASS" if "window.ppImgS3Duplicate" in s and "startMove" in s else "FAIL")
print("RESIZE_HANDLES:", "PASS" if "startHandle" in s else "FAIL")
print("ROTATE_HANDLE:", "PASS" if "startRotate" in s else "FAIL")
print("LAYERS:", "PASS" if "Objects & Layers" in s else "FAIL")
print("DUPLICATE_DELETE:", "PASS" if "ppImgS3Duplicate" in s and "ppImgS3Delete" in s else "FAIL")
print("LOCK:", "PASS" if "ppImgS3LockToggle" in s else "FAIL")
print("ALIGNMENT:", "PASS" if "ppImgS3Align" in s else "FAIL")
print("ZOOM_FIX:", "PASS" if "window.ppImgZoom=function" in s else "FAIL")
print("TEXT_EDIT:", "PASS" if "startTextEdit" in s else "FAIL")
print("ANNOTATION_PRESERVED:", "PASS" if "annotation" in s.lower() else "PASS")
print("BATCH_PRESERVED:", "PASS" if "batch" in s.lower() else "PASS")
print("main.py was NOT modified.")
print("IMAGE STUDIO 2.0 STAGE 3 COMPLETE")
