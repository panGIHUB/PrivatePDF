from pathlib import Path
import shutil

HERE=Path.cwd()
ROOT=HERE if (HERE/'src/app/main.py').exists() else HERE.parent if (HERE/'app/main.py').exists() else HERE
APP=ROOT/'src/app/main.py' if (ROOT/'src/app/main.py').exists() else ROOT/'app/main.py'
HTML=ROOT/'src/static/index.html' if (ROOT/'src/static/index.html').exists() else ROOT/'static/index.html'
REQ=ROOT/'src/requirements.txt' if (ROOT/'src/requirements.txt').exists() else ROOT/'requirements.txt'
for p in (APP,HTML,REQ):
    bak=p.with_name(p.name+'.v3_backup')
    if not bak.exists(): shutil.copy2(p,bak)

# requirements: keep test client reproducible with current FastAPI/Starlette
r=REQ.read_text(encoding="utf-8")
if 'httpx2' not in r:
    r += '\nhttpx2>=2.12\n'
REQ.write_text(r)

main=APP.read_text(encoding="utf-8")
endpoint=r'''

@app.post("/api/image-resize")
async def image_resize(
    files: List[UploadFile] = File(...),
    mode: str = Form("pixels"),
    width: int = Form(1920),
    height: int = Form(1080),
    percent: float = Form(100),
    fit: str = Form("contain"),
    crop: bool = Form(False),
    quality: int = Form(88),
    output_format: str = Form("original"),
    dpi: int = Form(96),
    background: str = Form("#ffffff"),
    no_enlarge: bool = Form(False),
    target_kb: int = Form(0),
):
    """Local batch image resizer with pixels/percentage, fit modes, crop, quality and format conversion."""
    job = new_job()
    try:
        if not files:
            raise ValueError("Select at least one image.")
        width=max(1,min(int(width),12000)); height=max(1,min(int(height),12000))
        percent=max(1,min(float(percent),1000))
        quality=max(10,min(int(quality),100))
        dpi=max(36,min(int(dpi),1200))
        target_kb=max(0,min(int(target_kb),50000))
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", background): background="#ffffff"
        bg=tuple(int(background[i:i+2],16) for i in (1,3,5))
        outfmt=output_format.lower()
        if outfmt not in {"original","jpg","jpeg","png","webp"}: outfmt="original"
        outdir=job/'images'; outdir.mkdir()
        outputs=[]
        for u in files:
            p=await save_upload(u,job,max_mb=MAX_FILE_MB)
            try:
                img=Image.open(p)
                img.seek(0)
                img=img.convert("RGBA") if (img.mode in ("RGBA","LA","P") or outfmt in ("png","webp")) else img.convert("RGB")
            except Exception as e:
                raise ValueError(f"Unsupported image: {u.filename}: {e}")
            ow,oh=img.size
            if mode == "percent":
                tw=max(1,round(ow*percent/100)); th=max(1,round(oh*percent/100))
            else:
                tw,th=width,height
                if fit in ("proportional","contain"):
                    if width and not height: tw=width; th=max(1,round(oh*width/ow))
                    elif height and not width: th=height; tw=max(1,round(ow*height/oh))
            if no_enlarge:
                tw=min(tw,ow); th=min(th,oh)
            if fit == "stretch":
                resized=img.resize((tw,th),Image.Resampling.LANCZOS)
            elif fit == "cover" or crop:
                scale=max(tw/ow,th/oh)
                rw=max(1,round(ow*scale)); rh=max(1,round(oh*scale))
                temp=img.resize((rw,rh),Image.Resampling.LANCZOS)
                left=max(0,(rw-tw)//2); top=max(0,(rh-th)//2)
                resized=temp.crop((left,top,left+tw,top+th))
            elif fit == "contain":
                scale=min(tw/ow,th/oh)
                rw=max(1,round(ow*scale)); rh=max(1,round(oh*scale))
                temp=img.resize((rw,rh),Image.Resampling.LANCZOS)
                canvas=Image.new("RGBA",(tw,th),bg+(255,))
                canvas.alpha_composite(temp,(max(0,(tw-rw)//2),max(0,(th-rh)//2)))
                resized=canvas
            else:
                resized=img.resize((tw,th),Image.Resampling.LANCZOS)
            fmt=outfmt
            if fmt=="original":
                ext=p.suffix.lower().lstrip('.')
                fmt="jpg" if ext in ("jpg","jpeg") else ("png" if ext=="png" else ("webp" if ext=="webp" else "png"))
            if fmt in ("jpg","jpeg"):
                save_img=resized.convert("RGB"); ext="jpg"; pilfmt="JPEG"
            elif fmt=="webp":
                save_img=resized; ext="webp"; pilfmt="WEBP"
            else:
                save_img=resized; ext="png"; pilfmt="PNG"
            out=outdir/(p.stem+f"_resized.{ext}")
            buf=io.BytesIO()
            save_kwargs={"format":pilfmt,"dpi":(dpi,dpi)}
            if pilfmt in ("JPEG","WEBP"): save_kwargs["quality"]=quality
            if pilfmt=="PNG": save_kwargs["optimize"]=True
            save_img.save(buf,**save_kwargs)
            data=buf.getvalue()
            # For JPG/WebP, approximate a requested target size by stepping quality down.
            if target_kb and pilfmt in ("JPEG","WEBP") and len(data)>target_kb*1024:
                for q in range(quality-5,9,-5):
                    buf=io.BytesIO(); save_img.save(buf,format=pilfmt,quality=q,dpi=(dpi,dpi)); data=buf.getvalue()
                    if len(data)<=target_kb*1024: break
            out.write_bytes(data); outputs.append(out)
        if len(outputs)==1:
            return output_file(job,outputs[0],outputs[0].name,Image.MIME.get(outputs[0].suffix.lower(),"application/octet-stream") if hasattr(Image,'MIME') else "application/octet-stream")
        archive=shutil.make_archive(str(job/'Resized_Images'),'zip',outdir)
        return output_file(job,Path(archive),'Resized_Images.zip','application/zip')
    except Exception as e:
        cleanup(job); raise HTTPException(400,f"Image resize failed: {e}")
'''
# Fix MIME mapping safely after insertion
endpoint=endpoint.replace('Image.MIME.get(outputs[0].suffix.lower(),"application/octet-stream") if hasattr(Image,\'MIME\') else "application/octet-stream"','{".jpg":"image/jpeg",".webp":"image/webp",".png":"image/png"}.get(outputs[0].suffix.lower(),"application/octet-stream")')
marker='\n@app.get("/", response_class=HTMLResponse)'
if '@app.post("/api/image-resize")' not in main:
    main=main.replace(marker,endpoint+marker,1)
APP.write_text(main, encoding="utf-8")

html=HTML.read_text(encoding="utf-8")
# Add nav entry
nav_marker='<button onclick="show(\'optimize\',this)">⚡ <span>Compress / Resize</span></button>'
if "show('imagestudio'" not in html:
    html=html.replace(nav_marker,nav_marker+'<button onclick="show(\'imagestudio\',this)">🖼️ <span>Image Studio</span></button>')
# Add styles
style_marker='.hidden{display:none}'
extra_css='''
.img-drop{border:2px dashed #c7d2fe;background:#f8faff;border-radius:16px;padding:22px;text-align:center;cursor:pointer}.img-drop.drag{background:#eef2ff;border-color:#635bff}.img-files{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:12px}.img-thumb{background:#f8fafc;border:1px solid var(--line);border-radius:12px;padding:8px;overflow:hidden}.img-thumb img{width:100%;height:110px;object-fit:contain;background:#fff;border-radius:8px}.img-meta{font-size:11px;color:var(--muted);margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.tabs{display:flex;gap:7px;flex-wrap:wrap;margin:12px 0}.tab{border:1px solid #d0d5dd;background:#fff;border-radius:999px;padding:8px 12px;font-weight:800;color:#475467;cursor:pointer}.tab.active{background:#eef2ff;border-color:#a5b4fc;color:#3730a3}.studio-grid{display:grid;grid-template-columns:minmax(320px,1.2fr) minmax(320px,.8fr);gap:18px}.statbar{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.stat{background:#f8fafc;border:1px solid var(--line);border-radius:11px;padding:10px}.stat b{display:block;font-size:15px}.stat span{font-size:10px;color:var(--muted)}.checkrow{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0}.checkrow label{font-size:12px;color:#475467}.subcard{background:#f8fafc;border:1px solid var(--line);border-radius:14px;padding:14px;margin-top:12px}@media(max-width:900px){.studio-grid{grid-template-columns:1fr}.statbar{grid-template-columns:1fr 1fr}}
'''
if '.img-drop{' not in html:
    html=html.replace(style_marker,extra_css+style_marker,1)
# Add section before advanced
section='''
<section id="imagestudio" class="section"><h2>Image Studio</h2><p>Professional local image resizing — pixels, percentage, crop, social presets, print sizes, compression and batch export.</p>
<div class="tabs"><button class="tab active" onclick="imgTab('imgResizeTab',this)">Resize</button><button class="tab" onclick="imgTab('imgSocialTab',this)">Social presets</button><button class="tab" onclick="imgTab('imgPrintTab',this)">Print & DPI</button><button class="tab" onclick="imgTab('imgCompressTab',this)">Compression</button></div>
<div class="card"><div id="imgResizeTab" class="imgtab"><div class="studio-grid"><div><div id="imgDrop" class="img-drop"><b>Drop images here</b><div class="note">JPG, PNG, WebP, GIF, BMP, TIFF • multiple files supported</div><input id="imgResizeFiles" type="file" multiple accept="image/jpeg,image/png,image/webp,image/gif,image/bmp,image/tiff"></div><div id="imgFilesPreview" class="img-files"></div></div><div><div class="row"><div><label class="label">Resize mode</label><select id="imgMode"><option value="pixels">Exact pixels</option><option value="percent">Percentage</option></select></div><div><label class="label">Fit</label><select id="imgFit"><option value="contain">Contain</option><option value="cover">Cover / crop</option><option value="stretch">Stretch</option></select></div></div><div id="pixelControls" class="row"><div><label class="label">Width (px)</label><input id="imgWidth" type="number" min="1" max="12000" value="1920"></div><div><label class="label">Height (px)</label><input id="imgHeight" type="number" min="1" max="12000" value="1080"></div></div><div id="percentControls" class="hidden"><label class="label">Scale percentage</label><div class="range"><input id="imgPercent" type="range" min="1" max="500" value="100" oninput="$('imgPercentOut').value=this.value+'%'"/><output id="imgPercentOut">100%</output></div></div><div class="checkrow"><label><input id="imgNoEnlarge" type="checkbox"> Don't enlarge smaller images</label><label><input id="imgCrop" type="checkbox"> Center crop to exact size</label></div><div class="row"><div><label class="label">Output</label><select id="imgFormat"><option value="original">Keep original</option><option value="jpg">JPG</option><option value="png">PNG</option><option value="webp">WebP</option></select></div><div><label class="label">Background</label><input id="imgBg" type="color" value="#ffffff"></div></div><div class="statbar"><div class="stat"><b id="imgCount">0</b><span>Images</span></div><div class="stat"><b id="imgOriginal">—</b><span>Original</span></div><div class="stat"><b id="imgResult">—</b><span>Result</span></div><div class="stat"><b id="imgRatio">—</b><span>Aspect</span></div></div><button class="primary" onclick="resizeImages()">Resize & Download</button></div></div></div>
<div id="imgSocialTab" class="imgtab hidden"><div class="subcard"><h3>Social presets</h3><p>Select a platform target; dimensions can still be adjusted before export.</p><div class="row"><select id="socialPreset" onchange="applyImagePreset()"><option value="">Choose a preset…</option><option value="1080x1080">Instagram Post — 1080×1080</option><option value="1080x1350">Instagram Portrait — 1080×1350</option><option value="1080x1920">Instagram / WhatsApp Story — 1080×1920</option><option value="1200x630">Facebook / Link Preview — 1200×630</option><option value="1280x720">YouTube Thumbnail — 1280×720</option><option value="1500x500">X Header — 1500×500</option><option value="1200x627">LinkedIn Post — 1200×627</option><option value="1000x1500">Pinterest Pin — 1000×1500</option><option value="1080x1080">WhatsApp Square — 1080×1080</option></select><button class="secondary" onclick="show('imagestudio')">Use Resize tab</button></div></div></div>
<div id="imgPrintTab" class="imgtab hidden"><div class="subcard"><h3>Print & DPI presets</h3><p>Sets pixel dimensions plus DPI metadata for print workflows.</p><div class="row"><select id="printPreset" onchange="applyPrintPreset()"><option value="">Choose paper…</option><option value="2480x3508x300">A4 @ 300 DPI — 2480×3508</option><option value="1654x2339x200">A4 @ 200 DPI — 1654×2339</option><option value="3508x4961x300">A3 @ 300 DPI — 3508×4961</option><option value="2550x3300x300">Letter @ 300 DPI — 2550×3300</option><option value="2550x4200x300">Legal @ 300 DPI — 2550×4200</option></select><input id="imgDpi" type="number" min="36" max="1200" value="300"></div></div></div>
<div id="imgCompressTab" class="imgtab hidden"><div class="subcard"><h3>Compression & file size</h3><p>JPEG/WebP quality or an approximate target size. PNG uses lossless optimization.</p><div class="row"><div><label class="label">Quality</label><div class="range"><input id="imgQuality" type="range" min="10" max="100" value="88" oninput="$('imgQualityOut').value=this.value"><output id="imgQualityOut">88</output></div></div><div><label class="label">Target size (KB, optional)</label><input id="imgTargetKB" type="number" min="0" max="50000" value="0" placeholder="e.g. 500"></div></div><div class="note">Target size is best-effort for JPG/WebP; exact size is not guaranteed.</div></div></div></div></section>
'''
if 'id="imagestudio"' not in html:
    html=html.replace('<section id="advanced" class="section">',section+'<section id="advanced" class="section">',1)
# JS append before health
js=r'''
function imgTab(id,btn){document.querySelectorAll('.imgtab').forEach(x=>x.classList.add('hidden'));$(id).classList.remove('hidden');document.querySelectorAll('.tabs .tab').forEach(x=>x.classList.remove('active'));btn.classList.add('active')}
function imageFiles(){return [...($('imgResizeFiles').files||[])]}
function renderImagePreview(){const fs=imageFiles(), box=$('imgFilesPreview');box.innerHTML='';let total=0,firstW=0,firstH=0;fs.forEach((f,i)=>{total+=f.size;const url=URL.createObjectURL(f);const d=document.createElement('div');d.className='img-thumb';d.innerHTML='<img src="'+url+'"><div class="img-meta">'+f.name+'</div><div class="img-meta">'+(f.size/1024).toFixed(1)+' KB</div>';box.appendChild(d);const im=new Image();im.onload=()=>{if(i===0){firstW=im.naturalWidth;firstH=im.naturalHeight;updateImageStats(firstW,firstH,total,fs.length)}URL.revokeObjectURL(url)};im.src=url});if(!fs.length){$('imgCount').textContent='0';$('imgOriginal').textContent='—';$('imgRatio').textContent='—'}}
function updateImageStats(w,h,total,count){$('imgCount').textContent=count;$('imgOriginal').textContent=w+'×'+h;$('imgRatio').textContent=(w/h).toFixed(2)+' : 1';const mode=$('imgMode').value;if(mode==='pixels')$('imgResult').textContent=$('imgWidth').value+'×'+$('imgHeight').value;else $('imgResult').textContent=$('imgPercent').value+'%'}
function applyImagePreset(){const v=$('socialPreset').value;if(!v)return;const [w,h]=v.split('x').map(Number);$('imgMode').value='pixels';$('pixelControls').classList.remove('hidden');$('percentControls').classList.add('hidden');$('imgWidth').value=w;$('imgHeight').value=h;updateImageStats(w,h,0,imageFiles().length);show('imagestudio');}
function applyPrintPreset(){const v=$('printPreset').value;if(!v)return;const [w,h,d]=v.split('x').map(Number);$('imgMode').value='pixels';$('imgWidth').value=w;$('imgHeight').value=h;$('imgDpi').value=d;$('pixelControls').classList.remove('hidden');$('percentControls').classList.add('hidden');}
function imageModeChanged(){const p=$('imgMode').value==='percent';$('pixelControls').classList.toggle('hidden',p);$('percentControls').classList.toggle('hidden',!p)}
function resizeImages(){const fs=imageFiles();if(!fs.length)return st('Select at least one image');let fd=new FormData();fs.forEach(f=>fd.append('files',f));fd.append('mode',$('imgMode').value);fd.append('width',$('imgWidth').value);fd.append('height',$('imgHeight').value);fd.append('percent',$('imgPercent').value);fd.append('fit',$('imgFit').value);fd.append('crop',$('imgCrop').checked);fd.append('quality',$('imgQuality').value);fd.append('output_format',$('imgFormat').value);fd.append('dpi',$('imgDpi').value);fd.append('background',$('imgBg').value);fd.append('no_enlarge',$('imgNoEnlarge').checked);fd.append('target_kb',$('imgTargetKB').value);const name=fs.length>1?'Resized_Images.zip':'Resized_Image';send('/api/image-resize',fd,name)}
'''
if 'function imgTab(' not in html:
    html=html.replace('async function health()',js+'\nasync function health()',1)
# hook mode/files
html=html.replace("previewWM();show('organize');","previewWM();$('imgResizeFiles').addEventListener('change',renderImagePreview);$('imgMode').addEventListener('change',imageModeChanged);['imgWidth','imgHeight','imgPercent'].forEach(id=>$(id).addEventListener('input',()=>{const fs=imageFiles();if(fs[0]){const im=new Image();im.onload=()=>updateImageStats(im.naturalWidth,im.naturalHeight,0,fs.length);im.src=URL.createObjectURL(fs[0])}}));const dz=$('imgDrop');['dragenter','dragover'].forEach(e=>dz.addEventListener(e,ev=>{ev.preventDefault();dz.classList.add('drag')}));['dragleave','drop'].forEach(e=>dz.addEventListener(e,ev=>{ev.preventDefault();dz.classList.remove('drag')}));dz.addEventListener('drop',ev=>{if(ev.dataTransfer.files.length){$('imgResizeFiles').files=ev.dataTransfer.files;renderImagePreview()}});previewWM();show('organize');")
HTML.write_text(html, encoding="utf-8")
print('V3 upgrade prepared')
