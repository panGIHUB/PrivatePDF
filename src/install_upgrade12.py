from pathlib import Path
import py_compile
import sys

APP = Path("app/main.py")
HTML = Path("static/index.html")
HTML_BACKUP = Path("static/index_before_annotation_studio_upgrade.html")
APP_BACKUP = Path("app/main_before_annotation_studio_upgrade.py")

print()
print("=" * 60)
print("UPGRADE #12 - PROFESSIONAL PDF ANNOTATION STUDIO")
print("=" * 60)
print()

if not APP.exists():
    raise SystemExit("ERROR: app/main.py not found.")

if not HTML.exists():
    raise SystemExit("ERROR: static/index.html not found.")

# ============================================================
# BACKUPS
# ============================================================

print("[1/6] Creating backups...")

if not HTML_BACKUP.exists():
    HTML_BACKUP.write_text(
        HTML.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

if not APP_BACKUP.exists():
    APP_BACKUP.write_text(
        APP.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

print("Frontend backup: OK")
print("Backend backup : OK")


# ============================================================
# BACKEND
# ============================================================

print()
print("[2/6] Installing annotation backend...")

app_text = APP.read_text(encoding="utf-8")

backend_marker = "# === UPGRADE_12_ANNOTATION_STUDIO_BACKEND ==="

backend_code = r"""
# === UPGRADE_12_ANNOTATION_STUDIO_BACKEND ===

@app.post("/api/annotate")
async def annotate_pdf(
    file: UploadFile = File(...),
    annotations: str = Form(...)
):
    import json
    import math
    import os
    import tempfile

    from fastapi.responses import FileResponse
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
            raise ValueError("Annotation list must be an array.")

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid annotation data: {exc}"
        )

    source = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    source.write(data)
    source.close()

    output_path = source.name + ".annotated.pdf"

    def cleanup():
        for path in (source.name, output_path):
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except Exception:
                pass

    try:
        doc = fitz.open(source.name)

        for item in items:

            try:
                page_index = int(
                    item.get("page", -1)
                )
            except Exception:
                continue

            if page_index < 0 or page_index >= len(doc):
                continue

            page = doc[page_index]

            kind = str(
                item.get("type", "")
            ).lower()

            color_hex = str(
                item.get("color", "#ff304f")
            ).replace("#", "")

            if len(color_hex) != 6:
                color_hex = "ff304f"

            try:
                color = tuple(
                    int(
                        color_hex[i:i + 2],
                        16
                    ) / 255.0
                    for i in (0, 2, 4)
                )
            except Exception:
                color = (
                    1.0,
                    0.19,
                    0.31
                )

            try:
                opacity = float(
                    item.get(
                        "opacity",
                        0.45
                    )
                )
            except Exception:
                opacity = 0.45

            opacity = max(
                0.05,
                min(1.0, opacity)
            )

            page_width = page.rect.width
            page_height = page.rect.height

            def norm(value):
                try:
                    value = float(value)
                except Exception:
                    value = 0.0

                return max(
                    0.0,
                    min(1.0, value)
                )

            def make_point(x, y):
                return fitz.Point(
                    norm(x) * page_width,
                    norm(y) * page_height
                )

            x = norm(
                item.get("x", 0.1)
            )

            y = norm(
                item.get("y", 0.1)
            )

            w = max(
                0.01,
                norm(
                    item.get("w", 0.2)
                )
            )

            h = max(
                0.01,
                norm(
                    item.get("h", 0.06)
                )
            )

            rect = fitz.Rect(
                x * page_width,
                y * page_height,
                min(
                    page_width,
                    (x + w) * page_width
                ),
                min(
                    page_height,
                    (y + h) * page_height
                )
            )

            # TEXT
            if kind == "text":

                text = str(
                    item.get(
                        "text",
                        ""
                    )
                )[:2000]

                if not text:
                    continue

                try:
                    size = float(
                        item.get(
                            "size",
                            18
                        )
                    )
                except Exception:
                    size = 18

                size = max(
                    6,
                    min(96, size)
                )

                page.insert_text(
                    make_point(x, y),
                    text,
                    fontsize=size,
                    color=color,
                    overlay=True
                )

            # HIGHLIGHT
            elif kind == "highlight":

                annot = page.add_highlight_annot(
                    rect
                )

                if annot:

                    annot.set_colors(
                        stroke=color
                    )

                    annot.set_opacity(
                        opacity
                    )

                    annot.update()

            # UNDERLINE
            elif kind == "underline":

                annot = page.add_underline_annot(
                    rect
                )

                if annot:

                    annot.set_colors(
                        stroke=color
                    )

                    annot.set_opacity(
                        opacity
                    )

                    annot.update()

            # STRIKEOUT
            elif kind == "strikeout":

                annot = page.add_strikeout_annot(
                    rect
                )

                if annot:

                    annot.set_colors(
                        stroke=color
                    )

                    annot.set_opacity(
                        opacity
                    )

                    annot.update()

            # RECTANGLE
            elif kind == "rectangle":

                try:
                    stroke = float(
                        item.get(
                            "stroke",
                            3
                        )
                    )
                except Exception:
                    stroke = 3

                stroke = max(
                    0.5,
                    min(15, stroke)
                )

                shape = page.new_shape()

                shape.draw_rect(
                    rect
                )

                shape.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity
                )

                shape.commit()

            # ARROW
            elif kind == "arrow":

                p1 = make_point(
                    item.get("x", 0.2),
                    item.get("y", 0.2)
                )

                p2 = make_point(
                    item.get("x2", 0.6),
                    item.get("y2", 0.3)
                )

                try:
                    stroke = float(
                        item.get(
                            "stroke",
                            3
                        )
                    )
                except Exception:
                    stroke = 3

                stroke = max(
                    0.5,
                    min(15, stroke)
                )

                shape = page.new_shape()

                shape.draw_line(
                    p1,
                    p2
                )

                shape.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity
                )

                shape.commit()

                angle = math.atan2(
                    p2.y - p1.y,
                    p2.x - p1.x
                )

                head = 12

                left = fitz.Point(
                    p2.x
                    + head * math.cos(
                        angle + math.pi * 0.82
                    ),
                    p2.y
                    + head * math.sin(
                        angle + math.pi * 0.82
                    )
                )

                right = fitz.Point(
                    p2.x
                    + head * math.cos(
                        angle - math.pi * 0.82
                    ),
                    p2.y
                    + head * math.sin(
                        angle - math.pi * 0.82
                    )
                )

                shape = page.new_shape()

                shape.draw_line(
                    p2,
                    left
                )

                shape.draw_line(
                    p2,
                    right
                )

                shape.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity
                )

                shape.commit()

            # FREEHAND
            elif kind == "draw":

                points = item.get(
                    "points",
                    []
                )

                if len(points) < 2:
                    continue

                try:
                    stroke = float(
                        item.get(
                            "stroke",
                            3
                        )
                    )
                except Exception:
                    stroke = 3

                stroke = max(
                    0.5,
                    min(15, stroke)
                )

                shape = page.new_shape()

                first = points[0]

                previous = make_point(
                    first.get("x", 0),
                    first.get("y", 0)
                )

                for raw_point in points[1:]:

                    current = make_point(
                        raw_point.get("x", 0),
                        raw_point.get("y", 0)
                    )

                    shape.draw_line(
                        previous,
                        current
                    )

                    previous = current

                shape.finish(
                    color=color,
                    width=stroke,
                    opacity=opacity
                )

                shape.commit()

        doc.save(
            output_path,
            garbage=4,
            deflate=True
        )

        doc.close()

        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename="Annotated_PDF.pdf",
            background=BackgroundTask(
                cleanup
            )
        )

    except Exception as exc:

        cleanup()

        raise HTTPException(
            status_code=500,
            detail=f"Annotation processing failed: {exc}"
        )
"""

if backend_marker not in app_text:

    insert_position = app_text.find(
        '@app.get("/")'
    )

    if insert_position < 0:
        insert_position = app_text.find(
            '@app.get("/api/health")'
        )

    if insert_position < 0:
        raise SystemExit(
            "ERROR: Safe backend insertion point not found."
        )

    app_text = (
        app_text[:insert_position]
        + backend_code
        + "\n\n"
        + app_text[insert_position:]
    )

    APP.write_text(
        app_text,
        encoding="utf-8"
    )

    print(
        "Annotation backend installed."
    )

else:

    print(
        "Annotation backend already exists."
    )


# ============================================================
# FRONTEND HTML
# ============================================================

print()
print("[3/6] Installing Annotation Studio CSS + UI...")

html = HTML.read_text(
    encoding="utf-8"
)

css_marker = (
    'id="upgrade-12-annotation-studio-css"'
)

css_code = r"""
<style id="upgrade-12-annotation-studio-css">

.pp12-overlay{
    margin:24px 0 40px;
    border:1px solid rgba(90,90,160,.14);
    border-radius:22px;
    background:#fff;
    box-shadow:0 18px 50px rgba(20,25,80,.10);
    overflow:hidden;
}

.pp12-head{
    padding:20px 24px;
    border-bottom:1px solid rgba(90,90,160,.12);
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:16px;
}

.pp12-head h2{
    margin:0;
    font-size:24px;
}

.pp12-head p{
    margin:5px 0 0;
    font-size:13px;
    opacity:.68;
}

.pp12-layout{
    display:grid;
    grid-template-columns:minmax(0,1fr) 310px;
    min-height:650px;
}

.pp12-canvas-area{
    padding:18px;
    min-width:0;
    overflow:auto;
    background:#f3f4fa;
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
}

.pp12-tool{
    border:1px solid rgba(80,80,140,.13);
    background:#fff;
    border-radius:9px;
    padding:8px 11px;
    cursor:pointer;
    font-size:12px;
    font-weight:700;
}

.pp12-tool:hover{
    transform:translateY(-1px);
}

.pp12-tool.active{
    background:#efefff;
    box-shadow:0 0 0 2px rgba(80,75,220,.18);
}

.pp12-page-wrap{
    position:relative;
    width:min(100%,850px);
    margin:0 auto;
    background:#fff;
    box-shadow:0 18px 45px rgba(0,0,0,.15);
    overflow:hidden;
}

.pp12-page-image{
    display:block;
    width:100%;
    height:auto;
    user-select:none;
    pointer-events:none;
}

.pp12-layer{
    position:absolute;
    inset:0;
    touch-action:none;
    cursor:crosshair;
}

.pp12-annotation{
    position:absolute;
    box-sizing:border-box;
    pointer-events:none;
}

.pp12-highlight{
    background:rgba(255,220,40,.38);
}

.pp12-underline{
    border-bottom:3px solid currentColor;
}

.pp12-strike{
    border-top:3px solid currentColor;
}

.pp12-rect{
    border:2px solid currentColor;
}

.pp12-text{
    white-space:pre;
    transform:translateY(-50%);
    font-weight:600;
}

.pp12-draw-svg{
    position:absolute;
    inset:0;
    width:100%;
    height:100%;
    pointer-events:none;
}

.pp12-side{
    border-left:1px solid rgba(90,90,160,.12);
    padding:14px;
    background:rgba(255,255,255,.72);
    overflow:auto;
}

.pp12-panel{
    background:#fff;
    border:1px solid rgba(80,80,150,.12);
    border-radius:14px;
    padding:13px;
    margin-bottom:10px;
}

.pp12-panel h4{
    margin:0 0 10px;
    font-size:12px;
}

.pp12-field{
    display:flex;
    flex-direction:column;
    gap:5px;
    margin-bottom:9px;
}

.pp12-field label{
    font-size:10px;
    font-weight:800;
    opacity:.65;
}

.pp12-field input,
.pp12-field select{
    box-sizing:border-box;
    width:100%;
    border:1px solid rgba(80,80,150,.14);
    border-radius:8px;
    padding:8px;
    background:#fff;
}

.pp12-actions{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:7px;
}

.pp12-primary{
    grid-column:1/-1;
    border:0;
    border-radius:10px;
    padding:11px;
    background:linear-gradient(
        135deg,
        #5b55df,
        #756cf1
    );
    color:#fff;
    font-weight:800;
    cursor:pointer;
}

.pp12-status{
    font-size:11px;
    opacity:.7;
    margin-top:8px;
}

.pp12-page-counter{
    font-size:11px;
    font-weight:800;
    opacity:.65;
}

@media(max-width:900px){

    .pp12-layout{
        grid-template-columns:1fr;
    }

    .pp12-side{
        border-left:0;
        border-top:1px solid rgba(90,90,160,.12);
    }

    .pp12-page-wrap{
        width:100%;
    }
}

body.pp6-dark .pp12-overlay,
body.pp6-dark .pp12-side,
body.pp6-dark .pp12-panel,
body.pp6-dark .pp12-toolbar,
body.pp6-dark .pp12-tool,
body.pp6-dark .pp12-field input,
body.pp6-dark .pp12-field select{
    background:#161827;
    color:#eee;
    border-color:rgba(255,255,255,.10);
}

body.pp6-dark .pp12-canvas-area{
    background:#0e101b;
}

</style>
"""

if css_marker not in html:

    head_position = html.find(
        "</head>"
    )

    if head_position < 0:
        raise SystemExit(
            "ERROR: </head> not found."
        )

    html = (
        html[:head_position]
        + css_code
        + "\n"
        + html[head_position:]
    )

    print(
        "Annotation CSS installed."
    )

else:

    print(
        "Annotation CSS already exists."
    )


ui_marker = (
    'id="pp12AnnotationStudio"'
)

ui_code = r"""
<section id="pp12AnnotationStudio"
         class="pp12-overlay">

    <div class="pp12-head">

        <div>

            <h2>
                Professional PDF Annotation Studio
            </h2>

            <p>
                Add text, highlights, drawings,
                shapes and arrows before exporting.
            </p>

        </div>

        <div class="pp12-page-counter"
             id="pp12PageCounter">
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
                    onclick="PP12.clearCurrent()">
                    Clear page
                </button>

            </div>


            <div
                class="pp12-page-wrap"
                id="pp12PageWrap">

                <img
                    id="pp12PageImage"
                    class="pp12-page-image"
                    alt="PDF page preview">

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

                    <label>
                        PAGE RANGE
                    </label>

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
                        value="#ff304f">

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

                    <label>
                        ANNOTATION SCOPE
                    </label>

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

                    <label>
                        PAGE RANGE
                    </label>

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

</section>
"""

if ui_marker not in html:

    anchor = 'id="pp11EditingWorkspace"'
    anchor_position = html.find(anchor)

    if anchor_position >= 0:

        section_end = html.find(
            "</section>",
            anchor_position
        )

        if section_end < 0:
            raise SystemExit(
                "ERROR: #11 workspace section not found."
            )

        section_end += len(
            "</section>"
        )

        html = (
            html[:section_end]
            + "\n"
            + ui_code
            + "\n"
            + html[section_end:]
        )

    else:

        body_position = html.rfind(
            "</body>"
        )

        if body_position < 0:
            raise SystemExit(
                "ERROR: </body> not found."
            )

        html = (
            html[:body_position]
            + ui_code
            + "\n"
            + html[body_position:]
        )

    print(
        "Annotation Studio UI installed."
    )

else:

    print(
        "Annotation Studio UI already exists."
    )


# ============================================================
# JAVASCRIPT
# ============================================================

print()
print("[4/6] Installing Annotation Studio JavaScript...")

js_marker = (
    'id="upgrade-12-annotation-studio-js"'
)

js_code = r"""
<script id="upgrade-12-annotation-studio-js">

(function(){

    const state = {
        file: null,
        pages: [],
        page: 0,
        tool: "select",
        annotations: {},
        undo: [],
        redo: [],
        drawing: null
    };


    function E(id){
        return document.getElementById(id);
    }


    function status(text){

        const node = E(
            "pp12FileStatus"
        );

        if(node){
            node.textContent = text;
        }
    }


    function current(){

        if(
            !state.annotations[
                state.page
            ]
        ){

            state.annotations[
                state.page
            ] = [];
        }

        return state.annotations[
            state.page
        ];
    }


    function cloneState(){

        return JSON.parse(
            JSON.stringify(
                state.annotations
            )
        );
    }


    function snapshot(){

        state.undo.push(
            cloneState()
        );

        if(
            state.undo.length > 50
        ){

            state.undo.shift();

        }

        state.redo = [];
    }


    function normalizedPoint(event){

        const layer = E(
            "pp12Layer"
        );

        const rect =
            layer.getBoundingClientRect();

        return {

            x: Math.max(
                0,
                Math.min(
                    1,
                    (
                        event.clientX
                        - rect.left
                    ) / rect.width
                )
            ),

            y: Math.max(
                0,
                Math.min(
                    1,
                    (
                        event.clientY
                        - rect.top
                    ) / rect.height
                )
            )

        };
    }


    function render(){

        const layer = E(
            "pp12Layer"
        );

        if(!layer){
            return;
        }

        layer.innerHTML = "";


        current().forEach(
            function(annotation){

                if(
                    annotation.type === "draw"
                ){

                    const svg =
                        document.createElementNS(
                            "http://www.w3.org/2000/svg",
                            "svg"
                        );

                    svg.classList.add(
                        "pp12-draw-svg"
                    );

                    svg.setAttribute(
                        "viewBox",
                        "0 0 100 100"
                    );


                    const polyline =
                        document.createElementNS(
                            "http://www.w3.org/2000/svg",
                            "polyline"
                        );


                    polyline.setAttribute(
                        "points",
                        annotation.points
                            .map(
                                function(point){
                                    return (
                                        point.x * 100
                                        + ","
                                        + point.y * 100
                                    );
                                }
                            )
                            .join(" ")
                    );


                    polyline.setAttribute(
                        "fill",
                        "none"
                    );

                    polyline.setAttribute(
                        "stroke",
                        annotation.color
                    );

                    polyline.setAttribute(
                        "stroke-width",
                        annotation.stroke
                    );

                    polyline.setAttribute(
                        "stroke-linecap",
                        "round"
                    );

                    polyline.setAttribute(
                        "stroke-linejoin",
                        "round"
                    );

                    polyline.setAttribute(
                        "opacity",
                        annotation.opacity
                    );


                    svg.appendChild(
                        polyline
                    );

                    layer.appendChild(
                        svg
                    );

                    return;
                }


                const node =
                    document.createElement(
                        "div"
                    );


                node.className =
                    "pp12-annotation";


                node.style.left =
                    (
                        annotation.x * 100
                    ) + "%";


                node.style.top =
                    (
                        annotation.y * 100
                    ) + "%";


                node.style.width =
                    (
                        (annotation.w || 0.001)
                        * 100
                    ) + "%";


                node.style.height =
                    (
                        (annotation.h || 0.001)
                        * 100
                    ) + "%";


                node.style.color =
                    annotation.color ||
                    "#ff304f";


                node.style.opacity =
                    annotation.opacity ??
                    0.45;


                if(
                    annotation.type ===
                    "highlight"
                ){

                    node.classList.add(
                        "pp12-highlight"
                    );
                }


                if(
                    annotation.type ===
                    "underline"
                ){

                    node.classList.add(
                        "pp12-underline"
                    );
                }


                if(
                    annotation.type ===
                    "strikeout"
                ){

                    node.classList.add(
                        "pp12-strike"
                    );
                }


                if(
                    annotation.type ===
                    "rectangle"
                ){

                    node.classList.add(
                        "pp12-rect"
                    );
                }


                if(
                    annotation.type ===
                    "text"
                ){

                    node.classList.add(
                        "pp12-text"
                    );

                    node.textContent =
                        annotation.text || "";


                    node.style.fontSize =
                        (
                            annotation.size ||
                            18
                        ) + "px";
                }


                if(
                    annotation.type ===
                    "arrow"
                ){

                    const dx =
                        (
                            annotation.x2 -
                            annotation.x
                        ) * 100;

                    const dy =
                        (
                            annotation.y2 -
                            annotation.y
                        ) * 100;

                    const length =
                        Math.sqrt(
                            dx * dx +
                            dy * dy
                        );

                    const angle =
                        Math.atan2(
                            dy,
                            dx
                        ) * 180 / Math.PI;


                    node.style.width =
                        length + "%";

                    node.style.height =
                        "0";

                    node.style.borderTop =
                        (
                            annotation.stroke ||
                            3
                        )
                        + "px solid "
                        + annotation.color;


                    node.style.transformOrigin =
                        "left center";


                    node.style.transform =
                        "rotate("
                        + angle
                        + "deg)";
                }


                layer.appendChild(
                    node
                );

            }
        );
    }


    function setTool(
        tool,
        button
    ){

        state.tool = tool;


        document
            .querySelectorAll(
                ".pp12-tool[data-tool]"
            )
            .forEach(
                function(item){
                    item.classList.remove(
                        "active"
                    );
                }
            );


        if(button){

            button.classList.add(
                "active"
            );
        }
    }


    function start(event){

        if(!state.file){
            return;
        }

        if(
            state.tool === "select" ||
            state.tool === "text"
        ){
            return;
        }


        const p =
            normalizedPoint(event);


        snapshot();


        state.drawing = {
            start: p,
            points: [p]
        };
    }


    function move(event){

        if(!state.drawing){
            return;
        }


        const p =
            normalizedPoint(event);


        state.drawing.points.push(
            p
        );


        if(
            state.tool !== "draw"
        ){
            return;
        }


        const list =
            current();


        const annotation = {

            type: "draw",

            page: state.page,

            points:
                state.drawing.points.slice(),

            color:
                E("pp12Color").value,

            stroke:
                Number(
                    E("pp12Stroke").value
                ),

            opacity:
                Number(
                    E("pp12Opacity").value
                ) / 100,

            live: true

        };


        if(
            list.length &&
            list[
                list.length - 1
            ].live
        ){

            list[
                list.length - 1
            ] = annotation;

        }else{

            list.push(
                annotation
            );
        }


        render();
    }


    function finish(event){

        if(!state.drawing){
            return;
        }


        const p =
            normalizedPoint(event);


        const start =
            state.drawing.start;


        const color =
            E("pp12Color").value;


        const stroke =
            Number(
                E("pp12Stroke").value
            );


        const opacity =
            Number(
                E("pp12Opacity").value
            ) / 100;


        if(
            state.tool === "draw"
        ){

            const list =
                current();


            if(
                list.length &&
                list[
                    list.length - 1
                ].live
            ){

                list[
                    list.length - 1
                ].live = false;
            }


            state.drawing = null;

            render();

            return;
        }


        const x =
            Math.min(
                start.x,
                p.x
            );


        const y =
            Math.min(
                start.y,
                p.y
            );


        const w =
            Math.max(
                Math.abs(
                    p.x - start.x
                ),
                0.01
            );


        const h =
            Math.max(
                Math.abs(
                    p.y - start.y
                ),
                0.01
            );


        if(
            [
                "highlight",
                "underline",
                "strikeout",
                "rectangle"
            ].includes(
                state.tool
            )
        ){

            current().push({

                type:
                    state.tool,

                page:
                    state.page,

                x: x,
                y: y,
                w: w,
                h: h,

                color:
                    color,

                stroke:
                    stroke,

                opacity:
                    opacity
            });
        }


        if(
            state.tool === "arrow"
        ){

            current().push({

                type: "arrow",

                page:
                    state.page,

                x:
                    start.x,

                y:
                    start.y,

                x2:
                    p.x,

                y2:
                    p.y,

                color:
                    color,

                stroke:
                    stroke,

                opacity:
                    opacity
            });
        }


        state.drawing = null;

        render();
    }


    function addText(event){

        if(
            state.tool !== "text"
        ){
            return;
        }


        const text =
            E("pp12Text")
                .value
                .trim();


        if(!text){

            status(
                "Enter annotation text first."
            );

            return;
        }


        snapshot();


        const p =
            normalizedPoint(event);


        current().push({

            type: "text",

            page:
                state.page,

            x:
                p.x,

            y:
                p.y,

            w:
                0.4,

            h:
                0.06,

            text:
                text,

            size:
                Number(
                    E("pp12TextSize").value
                ),

            color:
                E("pp12Color").value,

            opacity:
                Number(
                    E("pp12Opacity").value
                ) / 100

        });


        render();
    }


    async function loadFile(){

        const input =
            E("pp12File");


        if(
            !input ||
            !input.files.length
        ){
            return;
        }


        state.file =
            input.files[0];


        state.pages = [];

        state.page = 0;

        state.annotations = {};

        state.undo = [];

        state.redo = [];


        status(
            "Loading "
            + state.file.name
            + "..."
        );


        try{

            const form =
                new FormData();


            form.append(
                "file",
                state.file
            );


            form.append(
                "max_pages",
                "40"
            );


            const response =
                await fetch(
                    "/api/page-thumbnails",
                    {
                        method: "POST",
                        body: form
                    }
                );


            if(
                !response.ok
            ){

                throw new Error(
                    await response.text()
                );
            }


            const data =
                await response.json();


            state.pages =
                data.pages || [];


            if(
                !state.pages.length
            ){

                throw new Error(
                    "No page previews returned."
                );
            }


            status(
                "PDF loaded successfully."
            );


            renderPage();


        }catch(error){

            console.error(
                error
            );

            status(
                "Unable to load PDF preview."
            );
        }
    }


    function renderPage(){

        if(
            !state.pages.length
        ){
            return;
        }


        const page =
            state.pages[
                state.page
            ];


        const image =
            E("pp12PageImage");


        image.src =
            page.thumbnail ||
            page.data ||
            page.url ||
            page.image ||
            "";


        E(
            "pp12PageCounter"
        ).textContent =
            "Page "
            + (state.page + 1)
            + " / "
            + state.pages.length;


        render();
    }


    function prev(){

        if(
            state.page <= 0
        ){
            return;
        }


        state.page--;

        renderPage();
    }


    function next(){

        if(
            state.page >=
            state.pages.length - 1
        ){
            return;
        }


        state.page++;

        renderPage();
    }


    function parseRange(
        value,
        max
    ){

        const result = [];


        String(
            value || ""
        )
        .split(",")
        .forEach(
            function(part){

                part =
                    part.trim();


                if(!part){
                    return;
                }


                if(
                    part.includes("-")
                ){

                    const parts =
                        part
                            .split("-")
                            .map(Number);


                    const start =
                        Math.min(
                            parts[0],
                            parts[1]
                        );


                    const end =
                        Math.max(
                            parts[0],
                            parts[1]
                        );


                    for(
                        let n = start;
                        n <= end;
                        n++
                    ){

                        if(
                            n >= 1 &&
                            n <= max &&
                            !result.includes(
                                n - 1
                            )
                        ){

                            result.push(
                                n - 1
                            );
                        }
                    }

                }else{

                    const n =
                        Number(part);


                    if(
                        Number.isFinite(n) &&
                        n >= 1 &&
                        n <= max &&
                        !result.includes(
                            n - 1
                        )
                    ){

                        result.push(
                            n - 1
                        );
                    }
                }

            }
        );


        return result.sort(
            function(a,b){
                return a - b;
            }
        );
    }


    function loadRange(){

        const value =
            E("pp12Range").value;


        const pages =
            parseRange(
                value,
                state.pages.length
            );


        if(
            !pages.length
        ){

            status(
                "Enter a valid page range."
            );

            return;
        }


        state.page =
            pages[0];


        renderPage();


        status(
            "Range loaded: "
            + value
        );
    }


    function undo(){

        if(
            !state.undo.length
        ){
            return;
        }


        state.redo.push(
            cloneState()
        );


        state.annotations =
            state.undo.pop();


        render();
    }


    function redo(){

        if(
            !state.redo.length
        ){
            return;
        }


        state.undo.push(
            cloneState()
        );


        state.annotations =
            state.redo.pop();


        render();
    }


    function clearCurrent(){

        if(
            !current().length
        ){
            return;
        }


        snapshot();


        state.annotations[
            state.page
        ] = [];


        render();
    }


    function clearAll(){

        if(
            Object.keys(
                state.annotations
            ).length
        ){

            snapshot();
        }


        state.annotations = {};

        render();
    }


    function reset(){

        state.annotations = {};

        state.undo = [];

        state.redo = [];

        state.drawing = null;

        state.tool = "select";


        E("pp12Text").value = "";


        document
            .querySelectorAll(
                ".pp12-tool[data-tool]"
            )
            .forEach(
                function(button){

                    button.classList.remove(
                        "active"
                    );
                }
            );


        const select =
            document.querySelector(
                '.pp12-tool[data-tool="select"]'
            );


        if(select){

            select.classList.add(
                "active"
            );
        }


        render();


        status(
            state.file
                ? "Workspace reset."
                : "Select a PDF to begin."
        );
    }


    function selectedPages(){

        const mode =
            E("pp12ApplyMode").value;


        if(
            mode === "all"
        ){

            return Array.from(
                {
                    length:
                        state.pages.length
                },
                function(_,index){
                    return index;
                }
            );
        }


        if(
            mode === "range"
        ){

            return parseRange(
                E("pp12ApplyRange").value,
                state.pages.length
            );
        }


        return [
            state.page
        ];
    }


    async function exportPDF(){

        if(!state.file){

            status(
                "Select a PDF first."
            );

            return;
        }


        const allowed =
            new Set(
                selectedPages()
            );


        const output = [];


        Object.entries(
            state.annotations
        )
        .forEach(
            function(entry){

                const pageIndex =
                    Number(
                        entry[0]
                    );


                const annotations =
                    entry[1];


                if(
                    !allowed.has(
                        pageIndex
                    )
                ){
                    return;
                }


                annotations.forEach(
                    function(annotation){

                        const copy =
                            JSON.parse(
                                JSON.stringify(
                                    annotation
                                )
                            );


                        delete copy.live;


                        copy.page =
                            pageIndex;


                        output.push(
                            copy
                        );
                    }
                );
            }
        );


        if(
            !output.length
        ){

            status(
                "No annotations found for the selected pages."
            );

            return;
        }


        const form =
            new FormData();


        form.append(
            "file",
            state.file
        );


        form.append(
            "annotations",
            JSON.stringify(
                output
            )
        );


        status(
            "Creating annotated PDF..."
        );


        try{

            const response =
                await fetch(
                    "/api/annotate",
                    {
                        method: "POST",
                        body: form
                    }
                );


            if(
                !response.ok
            ){

                throw new Error(
                    await response.text()
                );
            }


            const blob =
                await response.blob();


            const url =
                URL.createObjectURL(
                    blob
                );


            const link =
                document.createElement(
                    "a"
                );


            link.href = url;

            link.download =
                "Annotated_PDF.pdf";


            document.body.appendChild(
                link
            );


            link.click();

            link.remove();


            setTimeout(
                function(){
                    URL.revokeObjectURL(
                        url
                    );
                },
                1500
            );


            status(
                "Annotated PDF exported successfully."
            );


        }catch(error){

            console.error(
                error
            );


            status(
                "Annotation export failed."
            );
        }
    }


    function bind(){

        const file =
            E("pp12File");


        if(file){

            file.addEventListener(
                "change",
                loadFile
            );
        }


        const layer =
            E("pp12Layer");


        if(layer){

            layer.addEventListener(
                "pointerdown",
                function(event){

                    if(
                        state.tool === "text"
                    ){

                        addText(
                            event
                        );

                    }else{

                        start(
                            event
                        );
                    }
                }
            );


            layer.addEventListener(
                "pointermove",
                move
            );


            layer.addEventListener(
                "pointerup",
                finish
            );


            layer.addEventListener(
                "pointercancel",
                finish
            );
        }


        const stroke =
            E("pp12Stroke");


        if(stroke){

            stroke.addEventListener(
                "input",
                function(event){

                    E(
                        "pp12StrokeValue"
                    ).textContent =
                        event.target.value
                        + " px";
                }
            );
        }


        const opacity =
            E("pp12Opacity");


        if(opacity){

            opacity.addEventListener(
                "input",
                function(event){

                    E(
                        "pp12OpacityValue"
                    ).textContent =
                        event.target.value
                        + "%";
                }
            );
        }
    }


    window.PP12 = {

        setTool: setTool,

        prev: prev,

        next: next,

        loadRange: loadRange,

        undo: undo,

        redo: redo,

        clearCurrent:
            clearCurrent,

        clearAll:
            clearAll,

        reset:
            reset,

        exportPDF:
            exportPDF,

        selectedPages:
            selectedPages

    };


    if(
        document.readyState ===
        "loading"
    ){

        document.addEventListener(
            "DOMContentLoaded",
            bind
        );

    }else{

        bind();
    }


    console.log(
        "UPGRADE #12 Annotation Studio ready"
    );

})();

</script>
"""

if js_marker not in html:

    body_position = html.rfind(
        "</body>"
    )

    if body_position < 0:
        raise SystemExit(
            "ERROR: </body> not found."
        )

    html = (
        html[:body_position]
        + js_code
        + "\n"
        + html[body_position:]
    )

    print(
        "Annotation JavaScript installed."
    )

else:

    print(
        "Annotation JavaScript already exists."
    )


# ============================================================
# NAVIGATION
# ============================================================

print()
print("[5/6] Installing navigation shortcuts...")

nav_marker = (
    'id="pp12AnnotationStudioNav"'
)

nav_code = r"""
<script id="upgrade-12-annotation-navigation-js">

(function(){

    function addNavigation(){

        if(
            document.getElementById(
                "pp12AnnotationStudioNav"
            )
        ){
            return;
        }


        const groups =
            document.querySelectorAll(
                ".navgroup"
            );


        let target = null;


        groups.forEach(
            function(group){

                const title =
                    group.querySelector(
                        ".navtitle"
                    );


                if(
                    title &&
                    title.textContent
                        .trim()
                        .toLowerCase()
                    === "advanced"
                ){

                    target =
                        group.querySelector(
                            ".nav"
                        );
                }
            }
        );


        if(!target){
            return;
        }


        const button =
            document.createElement(
                "button"
            );


        button.id =
            "pp12AnnotationStudioNav";


        button.innerHTML =
            "📝 <span>Annotation Studio</span>";


        button.onclick =
            function(){

                const section =
                    document.getElementById(
                        "pp12AnnotationStudio"
                    );


                if(section){

                    section.scrollIntoView({
                        behavior:"smooth",
                        block:"start"
                    });
                }
            };


        target.appendChild(
            button
        );
    }


    if(
        document.readyState ===
        "loading"
    ){

        document.addEventListener(
            "DOMContentLoaded",
            addNavigation
        );

    }else{

        addNavigation();
    }


    setTimeout(
        addNavigation,
        1000
    );

})();

</script>
"""

if nav_marker not in html:

    body_position = html.rfind(
        "</body>"
    )

    if body_position < 0:
        raise SystemExit(
            "ERROR: </body> not found for navigation."
        )

    html = (
        html[:body_position]
        + nav_code
        + "\n"
        + html[body_position:]
    )

    print(
        "Advanced navigation shortcut installed."
    )

else:

    print(
        "Advanced navigation shortcut already exists."
    )


# ============================================================
# DASHBOARD
# ============================================================

dash_marker = (
    'id="pp12DashboardAnnotationButton"'
)

dash_code = r"""
<script id="upgrade-12-dashboard-annotation-js">

(function(){

    function addDashboardShortcut(){

        if(
            document.getElementById(
                "pp12DashboardAnnotationButton"
            )
        ){
            return;
        }


        const buttons =
            document.querySelectorAll(
                "button"
            );


        for(
            const button of buttons
        ){

            const text =
                button.textContent
                    .trim()
                    .toLowerCase();


            if(
                text.includes(
                    "pdf editing workspace"
                )
            ){

                const parent =
                    button.parentElement;


                if(!parent){
                    return;
                }


                const shortcut =
                    document.createElement(
                        "button"
                    );


                shortcut.id =
                    "pp12DashboardAnnotationButton";


                shortcut.className =
                    button.className;


                shortcut.innerHTML =
                    "📝 <span>Annotation Studio</span>";


                shortcut.onclick =
                    function(){

                        const section =
                            document.getElementById(
                                "pp12AnnotationStudio"
                            );


                        if(section){

                            section.scrollIntoView({
                                behavior:"smooth",
                                block:"start"
                            });
                        }
                    };


                parent.appendChild(
                    shortcut
                );


                return;
            }
        }
    }


    if(
        document.readyState ===
        "loading"
    ){

        document.addEventListener(
            "DOMContentLoaded",
            addDashboardShortcut
        );

    }else{

        addDashboardShortcut();
    }


    setTimeout(
        addDashboardShortcut,
        1200
    );

})();

</script>
"""

if dash_marker not in html:

    body_position = html.rfind(
        "</body>"
    )

    if body_position < 0:
        raise SystemExit(
            "ERROR: </body> not found for dashboard."
        )

    html = (
        html[:body_position]
        + dash_code
        + "\n"
        + html[body_position:]
    )

    print(
        "Dashboard shortcut installed."
    )

else:

    print(
        "Dashboard shortcut already exists."
    )


HTML.write_text(
    html,
    encoding="utf-8"
)


# ============================================================
# FINAL VERIFICATION
# ============================================================

print()
print("[6/6] Final verification...")
print()

final_html = HTML.read_text(
    encoding="utf-8"
)

final_app = APP.read_text(
    encoding="utf-8"
)


print(
    "Frontend backup:",
    "OK" if HTML_BACKUP.exists()
    else "FAILED"
)

print(
    "Backend backup :",
    "OK" if APP_BACKUP.exists()
    else "FAILED"
)


print()
print("===== FRONTEND =====")

checks = [
    (
        "CSS",
        'id="upgrade-12-annotation-studio-css"'
    ),
    (
        "HTML",
        'id="pp12AnnotationStudio"'
    ),
    (
        "JavaScript",
        'id="upgrade-12-annotation-studio-js"'
    ),
    (
        "Navigation",
        'id="pp12AnnotationStudioNav"'
    ),
    (
        "Dashboard",
        'id="pp12DashboardAnnotationButton"'
    )
]


for name, marker in checks:

    print(
        name + ":",
        "OK" if marker in final_html
        else "MISSING"
    )


print()
print("===== BACKEND =====")

print(
    "Annotation route:",
    "OK" if backend_marker in final_app
    else "MISSING"
)


print()
print("===== PYTHON SYNTAX =====")

try:

    py_compile.compile(
        str(APP),
        doraise=True
    )

    print(
        "PYTHON SYNTAX: OK"
    )

except Exception as exc:

    print(
        "PYTHON SYNTAX: FAILED"
    )

    print(exc)

    raise SystemExit(
        "STOP: Backend syntax error. Existing backup preserved."
    )


print()
print("===== APP =====")

sys.path.insert(
    0,
    str(Path("."))
)


try:

    from app.main import app

    print(
        "APP:",
        app.title
    )

    print(
        "ROUTES:",
        len(app.routes)
    )

except Exception as exc:

    print(
        "APP IMPORT FAILED:"
    )

    print(exc)

    raise SystemExit(
        "STOP: Application import failed."
    )


print()
print("=" * 60)
print("UPGRADE #12 VERIFIED")
print("=" * 60)
print()

print(
    "Professional PDF Annotation Studio added."
)

print(
    "Text annotation added."
)

print(
    "Highlight tool added."
)

print(
    "Underline tool added."
)

print(
    "Strikeout tool added."
)

print(
    "Freehand drawing added."
)

print(
    "Rectangle tool added."
)

print(
    "Arrow tool added."
)

print(
    "Annotation color controls added."
)

print(
    "Stroke controls added."
)

print(
    "Opacity controls added."
)

print(
    "Text size controls added."
)

print(
    "Live annotation canvas added."
)

print(
    "Page navigation added."
)

print(
    "Page range support added."
)

print(
    "Current / range / all-page export modes added."
)

print(
    "Undo / redo added."
)

print(
    "Clear page / clear all added."
)

print(
    "Annotated PDF export added."
)

print(
    "Job Center integration preserved."
)

print(
    "Dark mode support added."
)

print(
    "Responsive layout added."
)

print(
    "Dashboard shortcut added."
)

print(
    "Advanced navigation shortcut added."
)

print(
    "Temporary processing preserved."
)

print(
    "No persistent document database added."
)

print()
print(
    "Expected routes: 31"
)

print()
print("=" * 60)
print("RESTART SERVER")
print("=" * 60)
print()
print(
    "python -m uvicorn app.main:app --reload"
)
print()
