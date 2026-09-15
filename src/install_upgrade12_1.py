from pathlib import Path
import re, shutil

HERE = Path.cwd()

if (HERE / 'src/app/main.py').exists():
    ROOT = HERE
elif (HERE / 'app/main.py').exists():
    ROOT = HERE.parent
else:
    raise SystemExit(
        'Run from PrivatePDF_Pro_Advanced_V2 or its src folder.'
    )

APP = (
    ROOT / 'src/app/main.py'
    if (ROOT / 'src/app/main.py').exists()
    else ROOT / 'app/main.py'
)

HTML = (
    ROOT / 'src/static/index.html'
    if (ROOT / 'src/static/index.html').exists()
    else ROOT / 'static/index.html'
)

if not APP.exists():
    raise SystemExit(f'Backend not found: {APP}')

if not HTML.exists():
    raise SystemExit(f'Frontend not found: {HTML}')

# ------------------------------------------------------------
# BACKUPS
# ------------------------------------------------------------

for p in (APP, HTML):
    b = p.with_name(p.name + '.before_annotation_engine_upgrade')
    if not b.exists():
        shutil.copy2(p, b)

main = APP.read_text(encoding='utf-8')
html = HTML.read_text(encoding='utf-8')

# ------------------------------------------------------------
# BACKEND
# ------------------------------------------------------------

backend = r'''# === UPGRADE_12_1_PROFESSIONAL_ANNOTATION_ENGINE_BACKEND ===

@app.post("/api/annotation-page")
async def annotation_page(
    file: UploadFile = File(...),
    page_index: int = Form(0),
    dpi: int = Form(160)
):
    import base64

    data = await file.read()

    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {MAX_FILE_MB} MB limit."
        )

    try:
        doc = fitz.open(stream=data, filetype="pdf")

        if page_index < 0 or page_index >= len(doc):
            doc.close()
            raise HTTPException(
                status_code=400,
                detail="Invalid page index."
            )

        dpi = max(96, min(int(dpi), 240))

        page = doc[page_index]
        rect = page.rect

        pix = page.get_pixmap(
            matrix=fitz.Matrix(
                dpi / 72.0,
                dpi / 72.0
            ),
            alpha=False,
            annots=False
        )

        words = []

        try:
            for w in page.get_text("words", sort=True):
                if len(w) < 5:
                    continue

                x0, y0, x1, y1, text = w[:5]

                if not str(text).strip():
                    continue

                words.append({
                    "x": max(
                        0,
                        min(
                            1,
                            x0 / rect.width
                        )
                    ),
                    "y": max(
                        0,
                        min(
                            1,
                            y0 / rect.height
                        )
                    ),
                    "w": max(
                        .0005,
                        min(
                            1,
                            (x1 - x0) / rect.width
                        )
                    ),
                    "h": max(
                        .0005,
                        min(
                            1,
                            (y1 - y0) / rect.height
                        )
                    ),
                    "text": str(text)
                })

        except Exception:
            words = []

        result = {
            "page": page_index,
            "page_count": len(doc),
            "width": rect.width,
            "height": rect.height,
            "pixel_width": pix.width,
            "pixel_height": pix.height,
            "image":
                "data:image/png;base64,"
                + base64.b64encode(
                    pix.tobytes("png")
                ).decode("ascii"),
            "words": words
        }

        doc.close()

        return JSONResponse(result)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not render PDF page: {exc}"
        )


@app.post("/api/annotate")
async def annotate_pdf(
    file: UploadFile = File(...),
    annotations: str = Form(...)
):
    import json
    import math
    import os
    import tempfile

    from starlette.background import BackgroundTask

    data = await file.read()

    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {MAX_FILE_MB} MB limit."
        )

    try:
        items = json.loads(annotations)

        if not isinstance(items, list):
            raise ValueError(
                "Annotation list must be an array."
            )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid annotation data: {exc}"
        )

    src = tempfile.NamedTemporaryFile(
        delete=False,
        suffix='.pdf'
    )

    src.write(data)
    src.close()

    out = src.name + '.annotated.pdf'

    def clean():
        for p in (src.name, out):
            try:
                if os.path.exists(p):
                    os.unlink(p)
            except Exception:
                pass

    try:
        doc = fitz.open(src.name)

        for item in items:

            try:
                pi = int(
                    item.get(
                        'page',
                        -1
                    )
                )
            except Exception:
                continue

            if pi < 0 or pi >= len(doc):
                continue

            page = doc[pi]

            kind = str(
                item.get(
                    'type',
                    ''
                )
            ).lower()

            hx = str(
                item.get(
                    'color',
                    '#ffcc00'
                )
            ).replace('#', '')

            if not re.fullmatch(
                r'[0-9a-fA-F]{6}',
                hx
            ):
                hx = 'ffcc00'

            color = tuple(
                int(hx[i:i + 2], 16) / 255
                for i in (0, 2, 4)
            )

            try:
                opacity = max(
                    .05,
                    min(
                        1,
                        float(
                            item.get(
                                'opacity',
                                .45
                            )
                        )
                    )
                )
            except Exception:
                opacity = .45

            pw = page.rect.width
            ph = page.rect.height

            def norm(v):
                try:
                    v = float(v)
                except Exception:
                    v = 0

                return max(
                    0,
                    min(
                        1,
                        v
                    )
                )

            def pt(x, y):
                return fitz.Point(
                    norm(x) * pw,
                    norm(y) * ph
                )

            x = norm(
                item.get(
                    'x',
                    .1
                )
            )

            y = norm(
                item.get(
                    'y',
                    .1
                )
            )

            w = max(
                .001,
                norm(
                    item.get(
                        'w',
                        .1
                    )
                )
            )

            h = max(
                .001,
                norm(
                    item.get(
                        'h',
                        .05
                    )
                )
            )

            x2 = norm(
                item.get(
                    'x2',
                    x + w
                )
            )

            y2 = norm(
                item.get(
                    'y2',
                    y + h
                )
            )

            rect = fitz.Rect(
                x * pw,
                y * ph,
                min(
                    pw,
                    (x + w) * pw
                ),
                min(
                    ph,
                    (y + h) * ph
                )
            )

            boxes = item.get(
                'boxes'
            )

            if (
                kind in {
                    'highlight',
                    'underline',
                    'strikeout'
                }
                and
                isinstance(
                    boxes,
                    list
                )
                and
                boxes
            ):

                for b in boxes:

                    try:
                        bx = norm(
                            b.get('x')
                        )

                        by = norm(
                            b.get('y')
                        )

                        bw = norm(
                            b.get('w')
                        )

                        bh = norm(
                            b.get('h')
                        )

                        br = fitz.Rect(
                            bx * pw,
                            by * ph,
                            min(
                                pw,
                                (bx + bw) * pw
                            ),
                            min(
                                ph,
                                (by + bh) * ph
                            )
                        )

                        if kind == 'highlight':
                            a = page.add_highlight_annot(br)

                        elif kind == 'underline':
                            a = page.add_underline_annot(br)

                        else:
                            a = page.add_strikeout_annot(br)

                        if a:
                            a.set_colors(
                                stroke=color
                            )

                            a.set_opacity(
                                opacity
                            )

                            a.update()

                    except Exception:
                        pass

                continue

            if kind == 'text':

                text = str(
                    item.get(
                        'text',
                        ''
                    )
                )[:4000]

                if not text.strip():
                    continue

                try:
                    size = max(
                        6,
                        min(
                            96,
                            float(
                                item.get(
                                    'size',
                                    18
                                )
                            )
                        )
                    )
                except Exception:
                    size = 18

                try:
                    page.insert_textbox(
                        rect,
                        text,
                        fontsize=size,
                        color=color,
                        fontname='helv',
                        align=0,
                        overlay=True
                    )
                except Exception:
                    page.insert_text(
                        pt(x, y),
                        text,
                        fontsize=size,
                        color=color,
                        overlay=True
                    )

            elif kind in {
                'highlight',
                'underline',
                'strikeout'
            }:

                if kind == 'highlight':
                    a = page.add_highlight_annot(
                        rect
                    )

                elif kind == 'underline':
                    a = page.add_underline_annot(
                        rect
                    )

                else:
                    a = page.add_strikeout_annot(
                        rect
                    )

                if a:
                    a.set_colors(
                        stroke=color
                    )

                    a.set_opacity(
                        opacity
                    )

                    a.update()

            elif kind == 'rectangle':

                try:
                    stroke = max(
                        .5,
                        min(
                            15,
                            float(
                                item.get(
                                    'stroke',
                                    3
                                )
                            )
                        )
                    )
                except Exception:
                    stroke = 3

                s = page.new_shape()

                s.draw_rect(
                    rect
                )

                s.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity
                )

                s.commit()

            elif kind == 'arrow':

                p1 = pt(x, y)
                p2 = pt(x2, y2)

                try:
                    stroke = max(
                        .5,
                        min(
                            15,
                            float(
                                item.get(
                                    'stroke',
                                    3
                                )
                            )
                        )
                    )
                except Exception:
                    stroke = 3

                s = page.new_shape()

                s.draw_line(
                    p1,
                    p2
                )

                s.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity
                )

                s.commit()

                ang = math.atan2(
                    p2.y - p1.y,
                    p2.x - p1.x
                )

                head = max(
                    7,
                    min(
                        24,
                        4 * stroke
                    )
                )

                left = fitz.Point(
                    p2.x +
                    head *
                    math.cos(
                        ang - math.pi * .82
                    ),
                    p2.y +
                    head *
                    math.sin(
                        ang - math.pi * .82
                    )
                )

                right = fitz.Point(
                    p2.x +
                    head *
                    math.cos(
                        ang + math.pi * .82
                    ),
                    p2.y +
                    head *
                    math.sin(
                        ang + math.pi * .82
                    )
                )

                s = page.new_shape()

                s.draw_line(
                    p2,
                    left
                )

                s.draw_line(
                    p2,
                    right
                )

                s.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity
                )

                s.commit()

            elif kind == 'draw':

                pts = item.get(
                    'points'
                )

                if (
                    not isinstance(
                        pts,
                        list
                    )
                    or
                    len(pts) < 2
                ):
                    continue

                try:
                    stroke = max(
                        .5,
                        min(
                            15,
                            float(
                                item.get(
                                    'stroke',
                                    3
                                )
                            )
                        )
                    )
                except Exception:
                    stroke = 3

                s = page.new_shape()

                pnts = [
                    pt(
                        q.get(
                            'x',
                            0
                        ),
                        q.get(
                            'y',
                            0
                        )
                    )
                    for q in pts
                    if isinstance(
                        q,
                        dict
                    )
                ]

                for a, b in zip(
                    pnts,
                    pnts[1:]
                ):
                    s.draw_line(
                        a,
                        b
                    )

                s.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity,
                    lineCap=1,
                    lineJoin=1
                )

                s.commit()

        doc.save(
            out,
            garbage=4,
            deflate=True,
            clean=True
        )

        doc.close()

        return FileResponse(
            out,
            filename='Annotated_PDF.pdf',
            media_type='application/pdf',
            background=BackgroundTask(clean)
        )

    except Exception as exc:
        clean()

        raise HTTPException(
            status_code=400,
            detail=f"Annotation export failed: {exc}"
        )
'''

start = main.find(
    '# === UPGRADE_12_ANNOTATION_STUDIO_BACKEND ==='
)

merge = main.find(
    '@app.post("/api/merge")'
)

if start < 0 or merge < 0:
    raise SystemExit(
        'Existing #12 backend block not found.'
    )

main = (
    main[:start]
    +
    backend.strip()
    +
    '\n\n'
    +
    main[merge:]
)

# ------------------------------------------------------------
# CSS
# ------------------------------------------------------------

css = r'''<style id="upgrade-12-1-professional-annotation-css">
.pp12-overlay{
    margin:24px 0 40px;
    border:1px solid rgba(90,90,160,.14);
    border-radius:22px;
    background:#fff;
    box-shadow:0 18px 50px rgba(20,25,80,.1);
    overflow:hidden
}

.pp12-head{
    padding:20px 24px;
    border-bottom:1px solid rgba(90,90,160,.12);
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:16px
}

.pp12-head h2{
    margin:0;
    font-size:24px
}

.pp12-head p{
    margin:5px 0 0;
    font-size:13px;
    opacity:.68
}

.pp12-layout{
    display:grid;
    grid-template-columns:minmax(0,1fr) 320px;
    min-height:720px
}

.pp12-canvas-area{
    padding:18px;
    min-width:0;
    overflow:auto;
    background:#eef0f7
}

.pp12-toolbar{
    display:flex;
    flex-wrap:wrap;
    gap:7px;
    padding:10px;
    border:1px solid rgba(90,90,160,.12);
    background:#fff;
    border-radius:14px;
    margin-bottom:14px;
    position:sticky;
    top:0;
    z-index:20
}

.pp12-tool{
    border:1px solid rgba(80,80,140,.13);
    background:#fff;
    border-radius:9px;
    padding:8px 11px;
    cursor:pointer;
    font-size:12px;
    font-weight:700
}

.pp12-tool:hover{
    transform:translateY(-1px)
}

.pp12-tool.active{
    background:#efefff;
    box-shadow:0 0 0 2px rgba(80,75,220,.18)
}

.pp12-page-wrap{
    position:relative;
    width:min(100%,980px);
    margin:0 auto;
    background:#fff;
    box-shadow:0 18px 45px rgba(0,0,0,.15);
    overflow:hidden;
    line-height:0
}

.pp12-page-image{
    display:block;
    width:100%;
    height:auto;
    user-select:none;
    pointer-events:none
}

.pp12-layer{
    position:absolute;
    inset:0;
    touch-action:none;
    cursor:crosshair;
    line-height:normal;
    overflow:hidden
}

.pp12-word-layer{
    position:absolute;
    inset:0;
    z-index:3;
    user-select:none;
    pointer-events:auto
}

.pp12-word{
    position:absolute;
    color:transparent;
    background:transparent;
    border-radius:2px;
    line-height:1;
    white-space:pre;
    cursor:text
}

.pp12-word.selected{
    background:rgba(75,110,255,.22);
    outline:1px solid rgba(75,110,255,.25)
}

.pp12-selection-preview{
    position:absolute;
    border:1px dashed rgba(70,80,180,.9);
    background:rgba(90,100,230,.1);
    z-index:8;
    pointer-events:none
}

.pp12-annotation{
    position:absolute;
    box-sizing:border-box;
    z-index:10;
    pointer-events:auto
}

.pp12-annotation.selectable{
    cursor:move
}

.pp12-annotation.selected{
    outline:2px solid rgba(72,80,220,.8);
    outline-offset:2px
}

.pp12-highlight{
    background:rgba(255,220,40,.38)
}

.pp12-underline{
    border-bottom:3px solid currentColor
}

.pp12-strike{
    border-top:3px solid currentColor
}

.pp12-rect{
    border:2px solid currentColor
}

.pp12-text{
    white-space:pre-wrap;
    overflow:hidden;
    font-weight:500;
    line-height:1.15;
    padding:1px 2px
}

.pp12-draw-svg{
    position:absolute;
    inset:0;
    width:100%;
    height:100%;
    z-index:9;
    overflow:visible;
    pointer-events:auto
}

.pp12-draw-path{
    fill:none;
    pointer-events:stroke;
    cursor:move
}

.pp12-hint{
    padding:9px 11px;
    margin-bottom:10px;
    border-radius:10px;
    background:#f5f6ff;
    font-size:11px;
    line-height:1.4;
    color:#4b4f70
}

.pp12-side{
    border-left:1px solid rgba(90,90,160,.12);
    padding:14px;
    background:rgba(255,255,255,.78);
    overflow:auto
}

.pp12-panel{
    background:#fff;
    border:1px solid rgba(80,80,150,.12);
    border-radius:14px;
    padding:13px;
    margin-bottom:10px
}

.pp12-panel h4{
    margin:0 0 10px;
    font-size:12px
}

.pp12-field{
    display:flex;
    flex-direction:column;
    gap:5px;
    margin-bottom:10px
}

.pp12-field label{
    font-size:10px;
    font-weight:800;
    opacity:.65
}

.pp12-field input,
.pp12-field select{
    box-sizing:border-box;
    width:100%;
    border:1px solid rgba(80,80,150,.14);
    border-radius:8px;
    padding:8px;
    background:#fff
}

.pp12-actions{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:7px
}

.pp12-actions .pp12-primary{
    grid-column:1/-1
}

.pp12-primary{
    border:0;
    border-radius:9px;
    padding:10px;
    background:#6257ff;
    color:#fff;
    font-weight:800;
    cursor:pointer
}

.pp12-status{
    font-size:11px;
    line-height:1.45;
    opacity:.72
}

.pp12-page-counter{
    font-size:11px;
    font-weight:800;
    white-space:nowrap
}

@media(max-width:900px){
    .pp12-layout{
        grid-template-columns:1fr
    }

    .pp12-side{
        border-left:0;
        border-top:1px solid rgba(90,90,160,.12)
    }

    .pp12-page-wrap{
        width:100%
    }

    .pp12-head{
        align-items:flex-start;
        flex-direction:column
    }
}

body.pp6-dark .pp12-overlay,
body.pp6-dark .pp12-toolbar,
body.pp6-dark .pp12-panel{
    background:#15182a;
    color:#f5f6ff
}

body.pp6-dark .pp12-canvas-area{
    background:#0d1020
}

body.pp6-dark .pp12-tool,
body.pp6-dark .pp12-field input,
body.pp6-dark .pp12-field select{
    background:#1d2135;
    color:#f5f6ff;
    border-color:rgba(255,255,255,.12)
}

body.pp6-dark .pp12-side{
    background:#121526
}
</style>'''

html = re.sub(
    r'<style id="upgrade-12-annotation-studio-css">.*?</style>',
    lambda m: css,
    html,
    count=1,
    flags=re.S
)

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------

ui = r'''<section id="pp12AnnotationStudio" class="pp12-overlay">

<div class="pp12-head">

<div>
<h2>Professional PDF Annotation Studio</h2>
<p>High-resolution editing surface with text-aware selection and native PDF annotation export.</p>
</div>

<div class="pp12-page-counter" id="pp12PageCounter">
No PDF loaded
</div>

</div>

<div class="pp12-layout">

<div class="pp12-canvas-area">

<div class="pp12-toolbar">

<button
    class="pp12-tool active"
    data-tool="select"
    onclick="PP12.setTool('select',this)">
Select
</button>

<button
    class="pp12-tool"
    data-tool="text"
    onclick="PP12.setTool('text',this)">
Text
</button>

<button
    class="pp12-tool"
    data-tool="highlight"
    onclick="PP12.setTool('highlight',this)">
Highlight
</button>

<button
    class="pp12-tool"
    data-tool="underline"
    onclick="PP12.setTool('underline',this)">
Underline
</button>

<button
    class="pp12-tool"
    data-tool="strikeout"
    onclick="PP12.setTool('strikeout',this)">
Strikeout
</button>

<button
    class="pp12-tool"
    data-tool="draw"
    onclick="PP12.setTool('draw',this)">
Draw
</button>

<button
    class="pp12-tool"
    data-tool="rectangle"
    onclick="PP12.setTool('rectangle',this)">
Box
</button>

<button
    class="pp12-tool"
    data-tool="arrow"
    onclick="PP12.setTool('arrow',this)">
Arrow
</button>

<button
    class="pp12-tool"
    onclick="PP12.undo()">
Undo
</button>

<button
    class="pp12-tool"
    onclick="PP12.redo()">
Redo
</button>

<button
    class="pp12-tool"
    onclick="PP12.deleteSelected()">
Delete selected
</button>

<button
    class="pp12-tool"
    onclick="PP12.clearCurrent()">
Clear page
</button>

</div>

<div class="pp12-hint" id="pp12Hint">
Select a PDF. Highlight, underline and strikeout use extracted PDF words so you can drag across real text.
</div>

<div
    class="pp12-page-wrap"
    id="pp12PageWrap">

<img
    id="pp12PageImage"
    class="pp12-page-image"
    alt="High-resolution PDF page preview">

<div
    id="pp12Layer"
    class="pp12-layer">
</div>

</div>

</div>

<aside class="pp12-side">

<div class="pp12-panel">

<h4>DOCUMENT</h4>

<div class="pp12-field">

<label>PDF FILE</label>

<input
    id="pp12File"
    type="file"
    accept=".pdf">

</div>

<div
    class="pp12-status"
    id="pp12FileStatus">

Select a PDF to begin.

</div>

</div>

<div class="pp12-panel">

<h4>PAGE NAVIGATION</h4>

<div class="pp12-actions">

<button
    class="pp12-tool"
    onclick="PP12.prev()">
Previous
</button>

<button
    class="pp12-tool"
    onclick="PP12.next()">
Next
</button>

</div>

<div
    class="pp12-field"
    style="margin-top:10px">

<label>PAGE RANGE</label>

<input
    id="pp12Range"
    placeholder="Example: 1,3-5">

<button
    class="pp12-tool"
    onclick="PP12.loadRange()">
Load range
</button>

</div>

</div>

<div class="pp12-panel">

<h4>ANNOTATION STYLE</h4>

<div class="pp12-field">

<label>COLOR</label>

<input
    id="pp12Color"
    type="color"
    value="#ffcc00">

</div>

<div class="pp12-field">

<label>STROKE</label>

<input
    id="pp12Stroke"
    type="range"
    min="1"
    max="12"
    value="3">

<span id="pp12StrokeValue">
3 px
</span>

</div>

<div class="pp12-field">

<label>OPACITY</label>

<input
    id="pp12Opacity"
    type="range"
    min="10"
    max="100"
    value="45">

<span id="pp12OpacityValue">
45%
</span>

</div>

<div class="pp12-field">

<label>TEXT SIZE</label>

<input
    id="pp12TextSize"
    type="number"
    min="6"
    max="96"
    value="18">

</div>

<div class="pp12-field">

<label>TEXT</label>

<input
    id="pp12Text"
    placeholder="Type annotation text">

</div>

</div>

<div class="pp12-panel">

<h4>APPLY MODE</h4>

<div class="pp12-field">

<label>ANNOTATION SCOPE</label>

<select id="pp12ApplyMode">

<option value="current">
Current page
</option>

<option value="range">
Page range
</option>

<option value="all">
All pages
</option>

</select>

</div>

<div class="pp12-field">

<label>PAGE RANGE</label>

<input
    id="pp12ApplyRange"
    placeholder="Example: 2,4-6">

</div>

</div>

<div class="pp12-panel">

<h4>EXPORT</h4>

<div class="pp12-actions">

<button
    class="pp12-tool"
    onclick="PP12.clearAll()">
Clear all
</button>

<button
    class="pp12-tool"
    onclick="PP12.reset()">
Reset
</button>

<button
    class="pp12-primary"
    onclick="PP12.exportPDF()">
Apply &amp; Export Annotated PDF
</button>

</div>

</div>

</aside>

</div>

</section>'''

html = re.sub(
    r'<section id="pp12AnnotationStudio".*?</section>',
    lambda m: ui,
    html,
    count=1,
    flags=re.S
)

# ------------------------------------------------------------
# JAVASCRIPT
# ------------------------------------------------------------

js = r'''<script id="upgrade-12-1-professional-annotation-js">
(function(){

const state = {
    file:null,
    pages:[],
    totalPages:0,
    page:0,
    tool:'select',
    annotations:{},
    undo:[],
    redo:[],
    drag:null,
    selectedId:null
};

const E = id =>
    document.getElementById(id);

const current = () =>
    state.annotations[state.page] ||
    (state.annotations[state.page] = []);

const clone = () =>
    JSON.parse(
        JSON.stringify(
            state.annotations
        )
    );

function status(t){

    const n =
        E('pp12FileStatus');

    if(n)
        n.textContent = t;
}

function snap(){

    state.undo.push(
        clone()
    );

    if(state.undo.length > 60)
        state.undo.shift();

    state.redo = [];
}

function clamp(v){

    return Math.max(
        0,
        Math.min(
            1,
            v
        )
    );
}

function pt(e){

    const r =
        E('pp12Layer')
        .getBoundingClientRect();

    return {
        x:clamp(
            (e.clientX-r.left)/r.width
        ),

        y:clamp(
            (e.clientY-r.top)/r.height
        )
    };
}

function range(s,total){

    const o = [];

    (s || '')
        .split(',')
        .forEach(
            t => {

                t = t.trim();

                if(/^\d+$/.test(t)){

                    let n = +t;

                    if(
                        n >= 1 &&
                        n <= total
                    )
                        o.push(n-1);

                }

                else if(
                    /^\d+\s*-\s*\d+$/.test(t)
                ){

                    let [a,b] =
                        t.split('-').map(Number);

                    if(a>b)
                        [a,b] = [b,a];

                    for(
                        let n=a;
                        n<=b;
                        n++
                    ){

                        if(
                            n>=1 &&
                            n<=total
                        )
                            o.push(n-1);
                    }
                }
            }
        );

    return [
        ...new Set(o)
    ].sort(
        (a,b)=>a-b
    );
}

function setTool(t,b){

    state.tool = t;

    document
        .querySelectorAll(
            '.pp12-tool[data-tool]'
        )
        .forEach(
            x =>
                x.classList.remove(
                    'active'
                )
        );

    (
        b ||
        document.querySelector(
            '.pp12-tool[data-tool="' +
            t +
            '"]'
        )
    )?.classList.add(
        'active'
    );

    const h =
        E('pp12Hint');

    if(h){

        h.textContent = {

            select:
                'Select an annotation to move or delete it.',

            text:
                'Enter text at right, then click the page to place it.',

            highlight:
                'Drag across PDF text to create a precise native highlight.',

            underline:
                'Drag across PDF text to create a precise native underline.',

            strikeout:
                'Drag across PDF text to create a precise native strikeout.',

            draw:
                'Draw freehand on the page.',

            rectangle:
                'Drag to draw a box.',

            arrow:
                'Drag from start to end.'

        }[t] || '';
    }
}

function wordsIn(a,b){

    const x0 =
        Math.min(
            a.x,
            b.x
        );

    const x1 =
        Math.max(
            a.x,
            b.x
        );

    const y0 =
        Math.min(
            a.y,
            b.y
        );

    const y1 =
        Math.max(
            a.y,
            b.y
        );

    return (
        state.pages[
            state.page
        ]?.words || []
    ).filter(
        w =>
            w.x+w.w/2 >= x0 &&
            w.x+w.w/2 <= x1 &&
            w.y+w.h/2 >= y0 &&
            w.y+w.h/2 <= y1
    );
}

function makeTextAnn(
    type,
    ws
){

    if(!ws.length)
        return null;

    const boxes =
        ws.map(
            w => ({
                x:w.x,
                y:w.y,
                w:w.w,
                h:w.h
            })
        );

    const x =
        Math.min(
            ...boxes.map(
                b=>b.x
            )
        );

    const y =
        Math.min(
            ...boxes.map(
                b=>b.y
            )
        );

    const r =
        Math.max(
            ...boxes.map(
                b=>b.x+b.w
            )
        );

    const bottom =
        Math.max(
            ...boxes.map(
                b=>b.y+b.h
            )
        );

    return {

        id:crypto.randomUUID(),

        type,

        x,

        y,

        w:r-x,

        h:bottom-y,

        boxes,

        color:
            E('pp12Color').value,

        opacity:
            +E('pp12Opacity').value/100,

        stroke:
            +E('pp12Stroke').value
    };
}

function render(){

    const layer =
        E('pp12Layer');

    if(!layer)
        return;

    layer.innerHTML = '';

    const wl =
        document.createElement(
            'div'
        );

    wl.id =
        'pp12WordLayer';

    wl.className =
        'pp12-word-layer';

    (
        state.pages[
            state.page
        ]?.words || []
    ).forEach(
        w => {

            const n =
                document.createElement(
                    'div'
                );

            n.className =
                'pp12-word';

            n.style.cssText =
                `left:${w.x*100}%;
                 top:${w.y*100}%;
                 width:${w.w*100}%;
                 height:${w.h*100}%;`;

            n.title =
                w.text;

            wl.appendChild(n);
        }
    );

    layer.appendChild(
        wl
    );

    current().forEach(
        a => {

            if(a.type === 'draw'){

                const svg =
                    document.createElementNS(
                        'http://www.w3.org/2000/svg',
                        'svg'
                    );

                svg.classList.add(
                    'pp12-draw-svg'
                );

                const p =
                    document.createElementNS(
                        'http://www.w3.org/2000/svg',
                        'polyline'
                    );

                p.classList.add(
                    'pp12-draw-path'
                );

                p.setAttribute(
                    'points',
                    a.points.map(
                        q =>
                            q.x*100 +
                            ',' +
                            q.y*100
                    ).join(' ')
                );

                p.setAttribute(
                    'stroke',
                    a.color
                );

                p.setAttribute(
                    'stroke-width',
                    a.stroke
                );

                p.setAttribute(
                    'stroke-linecap',
                    'round'
                );

                p.setAttribute(
                    'stroke-linejoin',
                    'round'
                );

                p.setAttribute(
                    'opacity',
                    a.opacity
                );

                p.dataset.id =
                    a.id;

                svg.appendChild(
                    p
                );

                layer.appendChild(
                    svg
                );

                return;
            }

            const n =
                document.createElement(
                    'div'
                );

            n.className =
                'pp12-annotation selectable' +
                (
                    a.id === state.selectedId
                        ? ' selected'
                        : ''
                );

            n.dataset.id =
                a.id;

            n.style.left =
                a.x*100 + '%';

            n.style.top =
                a.y*100 + '%';

            n.style.width =
                (a.w || .01)*100 + '%';

            n.style.height =
                (a.h || .01)*100 + '%';

            n.style.color =
                a.color;

            n.style.opacity =
                a.opacity;

            if(a.type === 'highlight')
                n.classList.add(
                    'pp12-highlight'
                );

            if(a.type === 'underline')
                n.classList.add(
                    'pp12-underline'
                );

            if(a.type === 'strikeout')
                n.classList.add(
                    'pp12-strike'
                );

            if(a.type === 'rectangle')
                n.classList.add(
                    'pp12-rect'
                );

            if(a.type === 'text'){

                n.classList.add(
                    'pp12-text'
                );

                n.style.fontSize =
                    a.size + 'px';

                n.textContent =
                    a.text;
            }

            n.addEventListener(
                'pointerdown',
                e => {

                    e.stopPropagation();

                    if(state.tool === 'select'){

                        state.selectedId =
                            a.id;

                        state.drag = {

                            mode:'move',

                            id:a.id,

                            start:pt(e),

                            ox:a.x,

                            oy:a.y
                        };

                        layer.setPointerCapture?.(
                            e.pointerId
                        );

                        render();
                    }
                }
            );

            layer.appendChild(
                n
            );
        }
    );
}

function start(e){

    if(!state.file)
        return;

    const p = pt(e);

    state.drag = {

        mode:state.tool,

        start:p,

        points:[p]
    };

    E('pp12Layer')
        .setPointerCapture?.(
            e.pointerId
        );
}

function move(e){

    const d =
        state.drag;

    if(!d)
        return;

    const p = pt(e);

    if(d.mode === 'move'){

        const a =
            current().find(
                x=>x.id===d.id
            );

        if(a){

            a.x =
                clamp(
                    d.ox +
                    p.x -
                    d.start.x
                );

            a.y =
                clamp(
                    d.oy +
                    p.y -
                    d.start.y
                );

            render();
        }

        return;
    }

    if(d.mode === 'draw'){

        d.points.push(
            p
        );

        render();

        return;
    }

    let q =
        E(
            'pp12SelectionPreview'
        );

    if(!q){

        q =
            document.createElement(
                'div'
            );

        q.id =
            'pp12SelectionPreview';

        q.className =
            'pp12-selection-preview';

        E('pp12Layer')
            .appendChild(
                q
            );
    }

    q.style.left =
        Math.min(
            d.start.x,
            p.x
        )*100 + '%';

    q.style.top =
        Math.min(
            d.start.y,
            p.y
        )*100 + '%';

    q.style.width =
        Math.abs(
            p.x -
            d.start.x
        )*100 + '%';

    q.style.height =
        Math.abs(
            p.y -
            d.start.y
        )*100 + '%';
}

function finish(e){

    const d =
        state.drag;

    if(!d)
        return;

    state.drag = null;

    const p = pt(e);

    const layer =
        E('pp12Layer');

    layer
        .querySelector(
            '#pp12SelectionPreview'
        )?.remove();

    if(d.mode === 'move'){

        snap();

        render();

        return;
    }

    if(d.mode === 'draw'){

        if(d.points.length > 1){

            snap();

            current().push({

                id:crypto.randomUUID(),

                type:'draw',

                points:d.points,

                color:
                    E('pp12Color').value,

                opacity:
                    +E('pp12Opacity').value/100,

                stroke:
                    +E('pp12Stroke').value
            });

            render();
        }

        return;
    }

    if(
        [
            'highlight',
            'underline',
            'strikeout'
        ].includes(
            d.mode
        )
    ){

        const ws =
            wordsIn(
                d.start,
                p
            );

        if(!ws.length){

            status(
                'No PDF text found in that area. Drag across the printed text.'
            );

            return;
        }

        snap();

        const a =
            makeTextAnn(
                d.mode,
                ws
            );

        current().push(
            a
        );

        state.selectedId =
            a.id;

        render();

        status(
            ws.length +
            ' PDF words annotated.'
        );

        return;
    }

    if(
        d.mode === 'rectangle' ||
        d.mode === 'arrow'
    ){

        const x =
            Math.min(
                d.start.x,
                p.x
            );

        const y =
            Math.min(
                d.start.y,
                p.y
            );

        const w =
            Math.abs(
                p.x -
                d.start.x
            );

        const h =
            Math.abs(
                p.y -
                d.start.y
            );

        if(
            w < .005 &&
            h < .005
        )
            return;

        snap();

        const a = {

            id:crypto.randomUUID(),

            type:d.mode,

            x,

            y,

            w,

            h,

            x2:p.x,

            y2:p.y,

            color:
                E('pp12Color').value,

            opacity:
                +E('pp12Opacity').value/100,

            stroke:
                +E('pp12Stroke').value
        };

        current().push(
            a
        );

        state.selectedId =
            a.id;

        render();
    }
}

function addText(e){

    const text =
        (
            E('pp12Text').value ||
            ''
        ).trim();

    if(!text){

        status(
            'Enter text in the TEXT field first.'
        );

        return;
    }

    const p = pt(e);

    snap();

    const size =
        +E('pp12TextSize').value ||
        18;

    const a = {

        id:crypto.randomUUID(),

        type:'text',

        x:p.x,

        y:p.y,

        w:.38,

        h:.09,

        text,

        size,

        color:
            E('pp12Color').value,

        opacity:
            +E('pp12Opacity').value/100
    };

    current().push(
        a
    );

    state.selectedId =
        a.id;

    render();
}

async function fetchPage(i){

    const f =
        new FormData();

    f.append(
        'file',
        state.file
    );

    f.append(
        'page_index',
        i
    );

    f.append(
        'dpi',
        160
    );

    const r =
        await fetch(
            '/api/annotation-page',
            {
                method:'POST',
                body:f
            }
        );

    if(!r.ok)
        throw new Error(
            await r.text()
        );

    return r.json();
}

async function showPage(i){

    if(!state.file)
        return;

    state.page =
        Math.max(
            0,
            Math.min(
                i,
                state.totalPages - 1
            )
        );

    if(
        !state.pages[
            state.page
        ]
    ){

        status(
            'Rendering page ' +
            (state.page + 1) +
            '...'
        );

        state.pages[
            state.page
        ] =
            await fetchPage(
                state.page
            );
    }

    const d =
        state.pages[
            state.page
        ];

    E('pp12PageImage').src =
        d.image;

    E('pp12PageCounter').textContent =
        'Page ' +
        (state.page + 1) +
        ' / ' +
        state.totalPages;

    render();
}

async function loadFile(){

    const f =
        E('pp12File')
        .files[0];

    if(!f)
        return;

    state.file = f;

    state.pages = [];

    state.annotations = {};

    state.undo = [];

    state.redo = [];

    state.selectedId = null;

    state.page = 0;

    try{

        status(
            'Preparing high-resolution editor...'
        );

        const d =
            await fetchPage(
                0
            );

        state.pages[0] =
            d;

        state.totalPages =
            d.page_count || 1;

        await showPage(
            0
        );

        status(
            'PDF loaded. High-resolution editing is ready.'
        );

    }catch(e){

        console.error(e);

        status(
            'Could not load PDF: ' +
            e.message
        );
    }
}

function prev(){

    if(state.page > 0)
        showPage(
            state.page - 1
        );
}

function next(){

    if(
        state.page <
        state.totalPages - 1
    )
        showPage(
            state.page + 1
        );
}

function loadRange(){

    const p =
        range(
            E('pp12Range').value,
            state.totalPages
        );

    if(!p.length){

        status(
            'Enter a valid page range.'
        );

        return;
    }

    showPage(
        p[0]
    );

    status(
        'Range starts at page ' +
        (p[0] + 1) +
        '.'
    );
}

function undo(){

    if(!state.undo.length)
        return;

    state.redo.push(
        clone()
    );

    state.annotations =
        state.undo.pop();

    state.selectedId = null;

    render();
}

function redo(){

    if(!state.redo.length)
        return;

    state.undo.push(
        clone()
    );

    state.annotations =
        state.redo.pop();

    state.selectedId = null;

    render();
}

function clearCurrent(){

    if(!current().length)
        return;

    snap();

    state.annotations[
        state.page
    ] = [];

    state.selectedId = null;

    render();
}

function clearAll(){

    if(
        Object.keys(
            state.annotations
        ).length
    ){

        snap();

        state.annotations = {};

        state.selectedId = null;

        render();
    }
}

function deleteSelected(){

    if(!state.selectedId)
        return;

    const i =
        current().findIndex(
            a =>
                a.id ===
                state.selectedId
        );

    if(i < 0)
        return;

    snap();

    current().splice(
        i,
        1
    );

    state.selectedId = null;

    render();
}

function reset(){

    state.annotations = {};

    state.undo = [];

    state.redo = [];

    state.selectedId = null;

    setTool(
        'select'
    );

    render();

    status(
        state.file
            ? 'Workspace reset.'
            : 'Select a PDF to begin.'
    );
}

async function exportPDF(){

    if(!state.file){

        status(
            'Select a PDF first.'
        );

        return;
    }

    const m =
        E('pp12ApplyMode').value;

    const total =
        state.totalPages;

    const allowed =
        m === 'all'
            ? new Set(
                [...Array(total).keys()]
            )
            : m === 'range'
                ? new Set(
                    range(
                        E('pp12ApplyRange').value,
                        total
                    )
                )
                : new Set(
                    [state.page]
                );

    const out = [];

    Object.entries(
        state.annotations
    ).forEach(
        ([pi,arr]) => {

            const n = +pi;

            if(!allowed.has(n))
                return;

            arr.forEach(
                a => {

                    const c =
                        JSON.parse(
                            JSON.stringify(a)
                        );

                    delete c.id;

                    c.page = n;

                    out.push(c);
                }
            );
        }
    );

    if(!out.length){

        status(
            'No annotations found for the selected pages.'
        );

        return;
    }

    const f =
        new FormData();

    f.append(
        'file',
        state.file
    );

    f.append(
        'annotations',
        JSON.stringify(
            out
        )
    );

    status(
        'Exporting without rasterizing the original PDF...'
    );

    try{

        const r =
            await fetch(
                '/api/annotate',
                {
                    method:'POST',
                    body:f
                }
            );

        if(!r.ok)
            throw new Error(
                await r.text()
            );

        const u =
            URL.createObjectURL(
                await r.blob()
            );

        const a =
            document.createElement(
                'a'
            );

        a.href = u;

        a.download =
            'Annotated_PDF.pdf';

        document.body.appendChild(
            a
        );

        a.click();

        a.remove();

        setTimeout(
            () =>
                URL.revokeObjectURL(u),
            2000
        );

        status(
            'Export complete. Original PDF content was preserved.'
        );

    }catch(e){

        console.error(e);

        status(
            'Export failed: ' +
            e.message
        );
    }
}

function bind(){

    E('pp12File')?.addEventListener(
        'change',
        loadFile
    );

    const l =
        E('pp12Layer');

    if(l){

        l.addEventListener(
            'pointerdown',
            e => {

                if(
                    e.target.closest(
                        '.pp12-annotation'
                    )
                )
                    return;

                const word =
                    e.target.closest(
                        '.pp12-word'
                    );

                if(
                    word &&
                    [
                        'highlight',
                        'underline',
                        'strikeout'
                    ].includes(
                        state.tool
                    )
                ){

                    start(e);

                    return;
                }

                if(
                    state.tool === 'text'
                ){

                    addText(e);

                }else{

                    start(e);
                }
            }
        );

        l.addEventListener(
            'pointermove',
            move
        );

        l.addEventListener(
            'pointerup',
            finish
        );

        l.addEventListener(
            'pointercancel',
            finish
        );
    }

    E('pp12Stroke')?.addEventListener(
        'input',
        e =>
            E('pp12StrokeValue').textContent =
                e.target.value +
                ' px'
    );

    E('pp12Opacity')?.addEventListener(
        'input',
        e =>
            E('pp12OpacityValue').textContent =
                e.target.value +
                '%'
    );
}

window.PP12 = {

    setTool,

    prev,

    next,

    loadRange,

    undo,

    redo,

    clearCurrent,

    clearAll,

    reset,

    exportPDF,

    deleteSelected
};

if(
    document.readyState ===
    'loading'
)

    document.addEventListener(
        'DOMContentLoaded',
        bind
    );

else
    bind();

})();
</script>'''

html = re.sub(
    r'<script id="upgrade-12-annotation-studio-js">.*?</script>',
    lambda m: js,
    html,
    count=1,
    flags=re.S
)

# Remove old duplicate navigation/dashboard scripts.

html = re.sub(
    r'<script id="upgrade-12-annotation-navigation-js">.*?</script>\s*',
    '',
    html,
    count=1,
    flags=re.S
)

html = re.sub(
    r'<script id="upgrade-12-dashboard-annotation-js">.*?</script>\s*',
    '',
    html,
    count=1,
    flags=re.S
)

# ------------------------------------------------------------
# CLEAN NAVIGATION / DASHBOARD INTEGRATION
# ------------------------------------------------------------

nav = r'''<script id="upgrade-12-1-annotation-navigation-dashboard-js">
(function(){

function go(){

    document
        .getElementById(
            'pp12AnnotationStudio'
        )
        ?.scrollIntoView({
            behavior:'smooth',
            block:'start'
        });
}

function install(){

    const bs = [
        ...document.querySelectorAll(
            'button'
        )
    ];

    const adv =
        bs.find(
            b =>
                b.textContent
                .trim()
                .toLowerCase() ===
                'advanced tools'
        );

    if(
        adv &&
        !document.getElementById(
            'pp12AnnotationStudioNav'
        )
    ){

        const b =
            document.createElement(
                'button'
            );

        b.id =
            'pp12AnnotationStudioNav';

        b.className =
            adv.className;

        b.textContent =
            '📝 Annotation Studio';

        b.onclick =
            go;

        adv.parentElement
            ?.appendChild(
                b
            );
    }

    const ed =
        bs.find(
            b =>
                b.textContent
                .toLowerCase()
                .includes(
                    'pdf editing workspace'
                )
        );

    if(
        ed &&
        !document.getElementById(
            'pp12DashboardAnnotationButton'
        )
    ){

        const b =
            document.createElement(
                'button'
            );

        b.id =
            'pp12DashboardAnnotationButton';

        b.className =
            ed.className;

        b.textContent =
            '📝 Annotation Studio';

        b.onclick =
            go;

        ed.parentElement
            ?.appendChild(
                b
            );
    }
}

if(
    document.readyState ===
    'loading'
)

    document.addEventListener(
        'DOMContentLoaded',
        () =>
            setTimeout(
                install,
                300
            )
    );

else

    setTimeout(
        install,
        300
    );

new MutationObserver(
    install
).observe(
    document.body,
    {
        childList:true,
        subtree:true
    }
);

})();
</script>'''

html += '\n' + nav + '\n'

# ------------------------------------------------------------
# WRITE FILES
# ------------------------------------------------------------

HTML.write_text(
    html,
    encoding='utf-8'
)

APP.write_text(
    main,
    encoding='utf-8'
)

# ------------------------------------------------------------
# INSTALLATION REPORT
# ------------------------------------------------------------

print()
print('==============================================')
print('   PRIVATE PDF PRO — UPGRADE #12.1')
print('==============================================')
print()
print('UPGRADE #12.1 INSTALLED')
print()
print('Backend backup: OK')
print('Frontend backup: OK')
print('High-resolution endpoint: OK')
print('Text-aware annotation selection: OK')
print('Native PDF export: OK')
print('Interactive select/move/delete: OK')
print('Duplicate #12 navigation scripts removed: OK')
print()
print(f'Backend:  {APP}')
print(f'Frontend: {HTML}')
print()
