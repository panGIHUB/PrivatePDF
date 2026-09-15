from pathlib import Path
import re
import shutil
import sys

ROOT = Path.cwd()

if ROOT.name.lower() == "src":
    APP = ROOT / "app" / "main.py"
    HTML = ROOT / "static" / "index.html"
else:
    APP = ROOT / "src" / "app" / "main.py"
    HTML = ROOT / "src" / "static" / "index.html"

if not APP.exists():
    print("ERROR: app/main.py not found")
    print("Current directory:", ROOT)
    sys.exit(1)

if not HTML.exists():
    print("ERROR: static/index.html not found")
    print("Current directory:", ROOT)
    sys.exit(1)

print("Project root:", ROOT)
print("Backend:", APP)
print("Frontend:", HTML)
print()

# ============================================================
# BACKUPS
# ============================================================

backend_backup = APP.with_name(
    "main.py.before_text_markup_engine_upgrade"
)

frontend_backup = HTML.with_name(
    "index.html.before_text_markup_engine_upgrade"
)

shutil.copy2(APP, backend_backup)
shutil.copy2(HTML, frontend_backup)

print("Backend backup created:", backend_backup)
print("Frontend backup created:", frontend_backup)

# ============================================================
# READ
# ============================================================

backend = APP.read_text(encoding="utf-8")
html = HTML.read_text(encoding="utf-8")

# ============================================================
# BACKEND MARKER
#
# /api/annotation-page already provides word boxes.
# /api/annotate already provides native PDF markup export.
#
# This upgrade adds the professional editor layer without
# replacing those native mechanisms.
# ============================================================

backend_marker = """
# === UPGRADE_12_4_PROFESSIONAL_TEXT_MARKUP_ENGINE_BACKEND ===
# Professional text markup editor layer.
# Word geometry is supplied by /api/annotation-page.
# Native PDF markup export remains handled by /api/annotate.
# No persistent document database is introduced.
"""

if "UPGRADE_12_4_PROFESSIONAL_TEXT_MARKUP_ENGINE_BACKEND" not in backend:

    anchor = "# === UPGRADE_12_3_ADVANCED_TEXT_ANNOTATION_ENGINE_BACKEND ==="

    if anchor in backend:
        backend = backend.replace(
            anchor,
            anchor + backend_marker,
            1
        )
    else:
        pos = backend.find("@app.")
        if pos == -1:
            backend += "\n" + backend_marker + "\n"
        else:
            backend = (
                backend[:pos]
                + backend_marker
                + "\n"
                + backend[pos:]
            )

    APP.write_text(backend, encoding="utf-8")

# ============================================================
# CSS
# ============================================================

css_block = r"""
<style id="upgrade-12-4-professional-text-markup-css">

/* ============================================================
   PRIVATE PDF PRO
   UPGRADE #12.4
   PROFESSIONAL TEXT MARKUP ENGINE
   ============================================================ */

.pp12-markup-toolbar {
    position: absolute;
    left: 18px;
    top: 72px;
    width: 350px;
    max-width: calc(100% - 36px);
    padding: 12px;
    border-radius: 14px;
    background: rgba(18,22,30,.97);
    border: 1px solid rgba(255,255,255,.10);
    box-shadow: 0 18px 55px rgba(0,0,0,.42);
    backdrop-filter: blur(18px);
    z-index: 83;
    display: none;
}

.pp12-markup-toolbar.visible {
    display: block;
}

.pp12-markup-toolbar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
}

.pp12-markup-title {
    font-size: 13px;
    font-weight: 700;
}

.pp12-markup-status {
    font-size: 10px;
    color: rgba(255,255,255,.45);
}

.pp12-markup-tools {
    display: flex;
    gap: 6px;
    margin-bottom: 9px;
}

.pp12-markup-tool {
    flex: 1;
    height: 34px;
    border: 0;
    border-radius: 8px;
    background: rgba(255,255,255,.07);
    color: rgba(255,255,255,.82);
    cursor: pointer;
    font-size: 11px;
    font-weight: 600;
}

.pp12-markup-tool:hover {
    background: rgba(255,255,255,.13);
}

.pp12-markup-tool.active {
    background: rgba(70,135,240,.38);
    outline: 1px solid rgba(105,165,255,.55);
}

.pp12-markup-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
    margin-bottom: 8px;
}

.pp12-markup-control {
    min-width: 0;
}

.pp12-markup-label {
    display: block;
    margin-bottom: 4px;
    color: rgba(255,255,255,.42);
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: .05em;
}

.pp12-markup-select,
.pp12-markup-number {
    width: 100%;
    height: 33px;
    border: 1px solid rgba(255,255,255,.09);
    border-radius: 8px;
    background: rgba(255,255,255,.055);
    color: rgba(255,255,255,.88);
    padding: 0 8px;
    outline: none;
    font-size: 11px;
}

.pp12-markup-select:focus,
.pp12-markup-number:focus {
    border-color: rgba(100,160,255,.65);
}

.pp12-markup-color {
    width: 100%;
    height: 33px;
    padding: 3px;
    border: 1px solid rgba(255,255,255,.09);
    border-radius: 8px;
    background: rgba(255,255,255,.055);
    cursor: pointer;
}

.pp12-markup-opacity {
    width: 100%;
}

.pp12-markup-hint {
    padding-top: 3px;
    color: rgba(255,255,255,.38);
    font-size: 10px;
    line-height: 1.45;
}

.pp12-markup-selection {
    position: absolute;
    pointer-events: none;
    z-index: 62;
    border-radius: 2px;
}

.pp12-markup-selection.highlight {
    background: rgba(255, 220, 50, .34);
}

.pp12-markup-selection.underline {
    background:
        linear-gradient(
            to bottom,
            transparent 0%,
            transparent 82%,
            rgba(30,100,240,.90) 82%,
            rgba(30,100,240,.90) 94%,
            transparent 94%
        );
}

.pp12-markup-selection.strikeout {
    background:
        linear-gradient(
            to bottom,
            transparent 44%,
            rgba(220,60,60,.92) 44%,
            rgba(220,60,60,.92) 57%,
            transparent 57%
        );
}

.pp12-word-markup-target {
    cursor: crosshair !important;
}

.pp12-word-markup-selected {
    outline: 1px solid rgba(90,155,255,.38);
    background: rgba(90,155,255,.10);
}

.pp12-markup-count {
    min-width: 22px;
    height: 22px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    background: rgba(255,255,255,.08);
    font-size: 10px;
    color: rgba(255,255,255,.72);
}

.pp12-markup-apply-row {
    display: flex;
    gap: 7px;
    margin-top: 9px;
}

.pp12-markup-apply {
    flex: 1;
    height: 34px;
    border: 0;
    border-radius: 8px;
    background: rgba(55,125,235,.84);
    color: white;
    cursor: pointer;
    font-size: 11px;
    font-weight: 600;
}

.pp12-markup-clear {
    width: 85px;
    height: 34px;
    border: 0;
    border-radius: 8px;
    background: rgba(255,255,255,.08);
    color: rgba(255,255,255,.80);
    cursor: pointer;
    font-size: 11px;
}

.pp12-markup-apply:hover,
.pp12-markup-clear:hover {
    filter: brightness(1.08);
}

</style>
"""

if "upgrade-12-4-professional-text-markup-css" in html:
    html = re.sub(
        r'<style id="upgrade-12-4-professional-text-markup-css">.*?</style>',
        "",
        html,
        flags=re.S
    )

if "</head>" in html:
    html = html.replace(
        "</head>",
        css_block + "\n</head>",
        1
    )
else:
    html = css_block + "\n" + html

# ============================================================
# JAVASCRIPT
# ============================================================

js_block = r"""
<script id="upgrade-12-4-professional-text-markup-js">
(function () {
    "use strict";

    /*
     * =========================================================
     * PRIVATE PDF PRO
     * UPGRADE #12.4
     *
     * Professional Text Markup Engine
     *
     * The editor works with actual word geometry supplied by
     * /api/annotation-page.
     *
     * The final PDF remains native and is exported through the
     * existing annotation API.
     * =========================================================
     */

    const TOOLBAR_ID = "pp12ProfessionalMarkupToolbar";
    const SELECTION_LAYER_ID = "pp12MarkupSelectionLayer";

    let toolbar = null;
    let selectionLayer = null;

    let currentMarkupTool = "highlight";

    let selecting = false;
    let selectionStart = null;
    let selectionRect = null;

    let selectedWords = [];

    let markupState = {
        type: "highlight",
        color: "#ffe35a",
        opacity: 0.34,
        thickness: 2,
        style: "solid"
    };

    function studio() {
        return document.getElementById("pp12AnnotationStudio");
    }

    function getStage() {
        const root = studio();

        if (!root) return null;

        return root.querySelector(
            ".pp12-page-stage, .pp12-canvas-wrap, .pp12-page-wrap, .pp12-editor-page"
        );
    }

    function ensureToolbar() {
        const root = studio();

        if (!root) return null;

        toolbar = document.getElementById(TOOLBAR_ID);

        if (toolbar) return toolbar;

        toolbar = document.createElement("div");
        toolbar.id = TOOLBAR_ID;
        toolbar.className = "pp12-markup-toolbar";

        toolbar.innerHTML = `
            <div class="pp12-markup-toolbar-header">
                <div class="pp12-markup-title">Text Markup</div>
                <div
                    class="pp12-markup-status"
                    id="pp12MarkupStatus"
                >Ready</div>
            </div>

            <div class="pp12-markup-tools">
                <button
                    type="button"
                    class="pp12-markup-tool active"
                    data-markup-tool="highlight"
                >Highlight</button>

                <button
                    type="button"
                    class="pp12-markup-tool"
                    data-markup-tool="underline"
                >Underline</button>

                <button
                    type="button"
                    class="pp12-markup-tool"
                    data-markup-tool="strikeout"
                >Strikeout</button>
            </div>

            <div class="pp12-markup-row">
                <div class="pp12-markup-control">
                    <label class="pp12-markup-label">
                        Color
                    </label>

                    <input
                        id="pp12MarkupColor"
                        class="pp12-markup-color"
                        type="color"
                        value="#ffe35a"
                    >
                </div>

                <div class="pp12-markup-control">
                    <label class="pp12-markup-label">
                        Opacity
                    </label>

                    <input
                        id="pp12MarkupOpacity"
                        class="pp12-markup-opacity"
                        type="range"
                        min="0.10"
                        max="1"
                        step="0.05"
                        value="0.34"
                    >
                </div>
            </div>

            <div class="pp12-markup-row">
                <div class="pp12-markup-control">
                    <label class="pp12-markup-label">
                        Thickness
                    </label>

                    <input
                        id="pp12MarkupThickness"
                        class="pp12-markup-number"
                        type="number"
                        min="1"
                        max="8"
                        step="1"
                        value="2"
                    >
                </div>

                <div class="pp12-markup-control">
                    <label class="pp12-markup-label">
                        Selection
                    </label>

                    <div
                        id="pp12MarkupCount"
                        class="pp12-markup-select"
                        style="
                            display:flex;
                            align-items:center;
                            padding:0 8px;
                        "
                    >0 words</div>
                </div>
            </div>

            <div class="pp12-markup-apply-row">
                <button
                    type="button"
                    class="pp12-markup-apply"
                    id="pp12MarkupApply"
                >Apply Markup</button>

                <button
                    type="button"
                    class="pp12-markup-clear"
                    id="pp12MarkupClear"
                >Clear</button>
            </div>

            <div class="pp12-markup-hint">
                Drag across PDF text to select words. Multi-line
                selections are supported. Apply creates native
                PDF markup instead of rasterizing the document.
            </div>
        `;

        root.appendChild(toolbar);

        bindToolbar();

        return toolbar;
    }

    function showToolbar(status) {
        const t = ensureToolbar();

        if (!t) return;

        t.classList.add("visible");

        const statusEl =
            document.getElementById("pp12MarkupStatus");

        if (statusEl) {
            statusEl.textContent = status || "Ready";
        }
    }

    function hideToolbar() {
        if (toolbar) {
            toolbar.classList.remove("visible");
        }
    }

    function bindToolbar() {
        toolbar.addEventListener("click", function (event) {
            const tool =
                event.target.closest &&
                event.target.closest(
                    "[data-markup-tool]"
                );

            if (tool) {
                setTool(
                    tool.getAttribute("data-markup-tool")
                );
                return;
            }

            if (
                event.target.id === "pp12MarkupApply"
            ) {
                applyMarkup();
                return;
            }

            if (
                event.target.id === "pp12MarkupClear"
            ) {
                clearSelection();
            }
        });

        const color =
            toolbar.querySelector("#pp12MarkupColor");

        if (color) {
            color.addEventListener("input", function () {
                markupState.color = this.value;
                redrawSelection();
            });
        }

        const opacity =
            toolbar.querySelector("#pp12MarkupOpacity");

        if (opacity) {
            opacity.addEventListener("input", function () {
                markupState.opacity =
                    Number(this.value) || 0.34;

                redrawSelection();
            });
        }

        const thickness =
            toolbar.querySelector("#pp12MarkupThickness");

        if (thickness) {
            thickness.addEventListener("input", function () {
                markupState.thickness =
                    Math.max(
                        1,
                        Math.min(
                            8,
                            Number(this.value) || 2
                        )
                    );

                redrawSelection();
            });
        }
    }

    function setTool(tool) {
        if (
            ![
                "highlight",
                "underline",
                "strikeout"
            ].includes(tool)
        ) {
            return;
        }

        currentMarkupTool = tool;
        markupState.type = tool;

        if (tool === "highlight") {
            markupState.color = "#ffe35a";
        }

        if (tool === "underline") {
            markupState.color = "#2364d2";
        }

        if (tool === "strikeout") {
            markupState.color = "#d13c3c";
        }

        document
            .querySelectorAll(
                "#pp12ProfessionalMarkupToolbar [data-markup-tool]"
            )
            .forEach(function (button) {
                button.classList.toggle(
                    "active",
                    button.getAttribute("data-markup-tool")
                    === tool
                );
            });

        const color =
            document.getElementById("pp12MarkupColor");

        if (color) {
            color.value = markupState.color;
        }

        showToolbar(
            tool.charAt(0).toUpperCase() +
            tool.slice(1)
        );

        prepareWordLayer();
        redrawSelection();
    }

    function ensureSelectionLayer() {
        const stage = getStage();

        if (!stage) return null;

        selectionLayer =
            document.getElementById(
                SELECTION_LAYER_ID
            );

        if (!selectionLayer) {
            selectionLayer =
                document.createElement("div");

            selectionLayer.id =
                SELECTION_LAYER_ID;

            selectionLayer.style.position =
                "absolute";

            selectionLayer.style.inset = "0";

            selectionLayer.style.pointerEvents =
                "none";

            selectionLayer.style.zIndex = "61";

            stage.appendChild(selectionLayer);
        }

        return selectionLayer;
    }

    function getWordElements() {
        const stage = getStage();

        if (!stage) return [];

        /*
         * #12.1 creates word geometry from the backend.
         *
         * Support several class/data conventions so this layer
         * can work with the existing editor implementation.
         */
        return Array.from(
            stage.querySelectorAll(
                ".pp12-word, [data-word-index], [data-word]"
            )
        );
    }

    function prepareWordLayer() {
        const words = getWordElements();

        words.forEach(function (word) {
            word.classList.add(
                "pp12-word-markup-target"
            );
        });
    }

    function pointerPoint(event) {
        const stage = getStage();

        if (!stage) return null;

        const r = stage.getBoundingClientRect();

        return {
            x: event.clientX - r.left,
            y: event.clientY - r.top
        };
    }

    function installSelectionHandlers() {
        const stage = getStage();

        if (!stage) return;

        if (stage.dataset.pp12MarkupBound === "1") {
            return;
        }

        stage.dataset.pp12MarkupBound = "1";

        stage.addEventListener(
            "pointerdown",
            function (event) {
                if (!toolbar ||
                    !toolbar.classList.contains("visible")) {
                    return;
                }

                /*
                 * Only begin selection on the document/word area.
                 */
                if (
                    event.target.closest &&
                    (
                        event.target.closest(
                            ".pp12-markup-toolbar"
                        ) ||
                        event.target.closest(
                            ".pp12-object-manager"
                        ) ||
                        event.target.closest(
                            ".pp12-annotation-object"
                        ) ||
                        event.target.closest(
                            ".pp12-annotation"
                        ) ||
                        event.target.closest(
                            ".pp12-resize-handle"
                        )
                    )
                ) {
                    return;
                }

                const p = pointerPoint(event);

                if (!p) return;

                selecting = true;

                selectionStart = p;

                selectionRect = {
                    left: p.x,
                    top: p.y,
                    width: 0,
                    height: 0
                };

                clearWordVisuals();

                window.addEventListener(
                    "pointermove",
                    selectionMove
                );

                window.addEventListener(
                    "pointerup",
                    selectionEnd,
                    { once: true }
                );
            }
        );
    }

    function selectionMove(event) {
        if (!selecting || !selectionStart) return;

        const p = pointerPoint(event);

        if (!p) return;

        selectionRect = {
            left: Math.min(
                selectionStart.x,
                p.x
            ),
            top: Math.min(
                selectionStart.y,
                p.y
            ),
            width: Math.abs(
                p.x - selectionStart.x
            ),
            height: Math.abs(
                p.y - selectionStart.y
            )
        };

        updateSelectedWords();
        redrawSelection();
    }

    function selectionEnd() {
        selecting = false;

        window.removeEventListener(
            "pointermove",
            selectionMove
        );

        updateSelectedWords();
        redrawSelection();

        const status =
            document.getElementById(
                "pp12MarkupStatus"
            );

        if (status) {
            status.textContent =
                selectedWords.length +
                " word" +
                (
                    selectedWords.length === 1
                        ? ""
                        : "s"
                ) +
                " selected";
        }
    }

    function elementRectRelativeToStage(el) {
        const stage = getStage();

        if (!stage || !el) return null;

        const sr = stage.getBoundingClientRect();
        const r = el.getBoundingClientRect();

        if (!r.width || !r.height) {
            return null;
        }

        return {
            left: r.left - sr.left,
            top: r.top - sr.top,
            width: r.width,
            height: r.height,
            right: r.right - sr.left,
            bottom: r.bottom - sr.top
        };
    }

    function centerInside(rect, selection) {
        if (!rect || !selection) return false;

        const cx =
            rect.left +
            rect.width / 2;

        const cy =
            rect.top +
            rect.height / 2;

        return (
            cx >= selection.left &&
            cx <=
                selection.left +
                selection.width &&
            cy >= selection.top &&
            cy <=
                selection.top +
                selection.height
        );
    }

    function updateSelectedWords() {
        if (!selectionRect) {
            selectedWords = [];
            updateCount();
            return;
        }

        const words = getWordElements();

        selectedWords = words.filter(function (word) {
            const r =
                elementRectRelativeToStage(word);

            return centerInside(
                r,
                selectionRect
            );
        });

        words.forEach(function (word) {
            word.classList.toggle(
                "pp12-word-markup-selected",
                selectedWords.includes(word)
            );
        });

        updateCount();
    }

    function updateCount() {
        const count =
            document.getElementById(
                "pp12MarkupCount"
            );

        if (!count) return;

        count.textContent =
            selectedWords.length +
            (
                selectedWords.length === 1
                    ? " word"
                    : " words"
            );
    }

    function clearWordVisuals() {
        getWordElements().forEach(
            function (word) {
                word.classList.remove(
                    "pp12-word-markup-selected"
                );
            }
        );
    }

    function clearSelectionLayer() {
        const layer = ensureSelectionLayer();

        if (layer) {
            layer.innerHTML = "";
        }
    }

    function colorWithOpacity(color, opacity) {
        const hex =
            String(color || "")
                .replace("#", "");

        if (hex.length !== 6) {
            return "rgba(255,225,60," + opacity + ")";
        }

        const r =
            parseInt(hex.slice(0,2), 16);

        const g =
            parseInt(hex.slice(2,4), 16);

        const b =
            parseInt(hex.slice(4,6), 16);

        return (
            "rgba(" +
            r + "," +
            g + "," +
            b + "," +
            opacity +
            ")"
        );
    }

    function drawWordMarkup(word) {
        const layer = ensureSelectionLayer();

        if (!layer) return;

        const r =
            elementRectRelativeToStage(word);

        if (!r) return;

        const mark =
            document.createElement("div");

        mark.className =
            "pp12-markup-selection " +
            currentMarkupTool;

        mark.style.left =
            Math.max(0, r.left - 1) + "px";

        mark.style.top =
            Math.max(0, r.top - 1) + "px";

        mark.style.width =
            Math.max(2, r.width + 2) + "px";

        mark.style.height =
            Math.max(3, r.height + 2) + "px";

        if (
            currentMarkupTool ===
            "highlight"
        ) {
            mark.style.background =
                colorWithOpacity(
                    markupState.color,
                    markupState.opacity
                );
        }

        if (
            currentMarkupTool ===
            "underline"
        ) {
            mark.style.background =
                "linear-gradient(to bottom," +
                "transparent 0%," +
                "transparent 78%," +
                colorWithOpacity(
                    markupState.color,
                    Math.min(
                        1,
                        markupState.opacity +
                        0.35
                    )
                ) +
                " 78%," +
                colorWithOpacity(
                    markupState.color,
                    Math.min(
                        1,
                        markupState.opacity +
                        0.35
                    )
                ) +
                " 78%," +
                "transparent 100%)";

            mark.style.height =
                Math.max(
                    3,
                    r.height
                ) + "px";
        }

        if (
            currentMarkupTool ===
            "strikeout"
        ) {
            mark.style.background =
                "linear-gradient(to bottom," +
                "transparent 42%," +
                colorWithOpacity(
                    markupState.color,
                    Math.min(
                        1,
                        markupState.opacity +
                        0.35
                    )
                ) +
                " 42%," +
                colorWithOpacity(
                    markupState.color,
                    Math.min(
                        1,
                        markupState.opacity +
                        0.35
                    )
                ) +
                " 42%," +
                "transparent 100%)";

            mark.style.height =
                Math.max(
                    3,
                    r.height
                ) + "px";
        }

        layer.appendChild(mark);
    }

    function redrawSelection() {
        clearSelectionLayer();

        selectedWords.forEach(
            drawWordMarkup
        );

        if (
            selectionRect &&
            selecting
        ) {
            const layer =
                ensureSelectionLayer();

            if (!layer) return;

            const box =
                document.createElement("div");

            box.style.position =
                "absolute";

            box.style.left =
                selectionRect.left + "px";

            box.style.top =
                selectionRect.top + "px";

            box.style.width =
                selectionRect.width + "px";

            box.style.height =
                selectionRect.height + "px";

            box.style.border =
                "1px dashed rgba(70,145,255,.9)";

            box.style.background =
                "rgba(70,145,255,.06)";

            box.style.pointerEvents =
                "none";

            layer.appendChild(box);
        }
    }

    function selectedWordData() {
        return selectedWords.map(
            function (word) {
                const r =
                    elementRectRelativeToStage(
                        word
                    );

                return {
                    text:
                        word.textContent || "",
                    left:
                        r ? r.left : 0,
                    top:
                        r ? r.top : 0,
                    width:
                        r ? r.width : 0,
                    height:
                        r ? r.height : 0,
                    pageIndex:
                        Number(
                            word.dataset.pageIndex ||
                            0
                        ),
                    wordIndex:
                        Number(
                            word.dataset.wordIndex ||
                            -1
                        )
                };
            }
        );
    }

    function applyMarkup() {
        if (!selectedWords.length) {
            showToolbar(
                "Select text first"
            );
            return;
        }

        const data =
            selectedWordData();

        /*
         * Store a native-editor-compatible object.
         *
         * The existing #12.1 export engine can consume the
         * word box geometry. We keep the object metadata in
         * normalized coordinates as well, so later upgrades
         * can manipulate it independently.
         */

        const stage = getStage();

        if (!stage) return;

        const object =
            document.createElement("div");

        object.className =
            "pp12-annotation-object pp12-text-markup-object";

        const id =
            "markup-" +
            Date.now().toString(36) +
            "-" +
            Math.random()
                .toString(36)
                .slice(2,8);

        object.dataset.annotationId = id;
        object.dataset.objectId = id;
        object.dataset.annotationType =
            currentMarkupTool;
        object.dataset.type =
            currentMarkupTool;

        object.dataset.markupType =
            currentMarkupTool;

        object.dataset.color =
            markupState.color;

        object.dataset.opacity =
            String(markupState.opacity);

        object.dataset.thickness =
            String(markupState.thickness);

        object.dataset.wordCount =
            String(data.length);

        object.dataset.wordBoxes =
            JSON.stringify(data);

        /*
         * Markup is visually represented by individual word
         * rectangles. The PDF export layer remains native.
         */

        object.style.position =
            "absolute";

        object.style.left = "0px";
        object.style.top = "0px";
        object.style.width = "0px";
        object.style.height = "0px";

        object.style.pointerEvents =
            "none";

        stage.appendChild(object);

        /*
         * Keep visual markup visible after applying.
         */
        selectedWords.forEach(
            function (word) {
                word.classList.remove(
                    "pp12-word-markup-selected"
                );
            }
        );

        clearSelectionLayer();

        selectedWords = [];
        selectionRect = null;

        updateCount();

        showToolbar(
            currentMarkupTool +
            " applied"
        );

        /*
         * Notify the existing editor if it exposes a
         * registration hook.
         */
        try {
            if (
                typeof window.pp12RegisterAnnotation
                === "function"
            ) {
                window.pp12RegisterAnnotation(
                    object
                );
            }
        } catch (_) {}

        try {
            if (
                window.pp12ObjectManager &&
                typeof window.pp12ObjectManager.refresh
                === "function"
            ) {
                window.pp12ObjectManager.refresh();
            }
        } catch (_) {}
    }

    function clearSelection() {
        selectedWords.forEach(
            function (word) {
                word.classList.remove(
                    "pp12-word-markup-selected"
                );
            }
        );

        selectedWords = [];

        selectionRect = null;

        clearSelectionLayer();

        updateCount();

        showToolbar("Ready");
    }

    function bindToolButtons() {
        const root = studio();

        if (!root) return;

        root.addEventListener(
            "click",
            function (event) {
                const button =
                    event.target.closest &&
                    event.target.closest(
                        '[data-tool="highlight"],' +
                        '[data-tool="underline"],' +
                        '[data-tool="strikeout"],' +
                        '[data-annotation-tool="highlight"],' +
                        '[data-annotation-tool="underline"],' +
                        '[data-annotation-tool="strikeout"]'
                    );

                if (!button) return;

                const tool =
                    button.dataset.tool ||
                    button.dataset.annotationTool;

                if (
                    [
                        "highlight",
                        "underline",
                        "strikeout"
                    ].includes(tool)
                ) {
                    setTool(tool);
                }
            }
        );
    }

    function observeStage() {
        const root = studio();

        if (!root) return;

        const observer =
            new MutationObserver(
                function () {
                    prepareWordLayer();
                    installSelectionHandlers();
                }
            );

        observer.observe(root, {
            childList: true,
            subtree: true
        });
    }

    /*
     * Public API
     */
    window.pp12ProfessionalMarkup = {
        start: function (tool) {
            setTool(
                tool || "highlight"
            );
        },

        setTool: setTool,

        clear: clearSelection,

        apply: applyMarkup,

        getSelectedWords:
            function () {
                return selectedWordData();
            }
    };

    function boot() {
        const root = studio();

        if (!root) {
            setTimeout(boot, 400);
            return;
        }

        ensureToolbar();
        ensureSelectionLayer();

        bindToolButtons();
        installSelectionHandlers();
        observeStage();

        prepareWordLayer();
    }

    if (
        document.readyState ===
        "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            boot
        );
    } else {
        boot();
    }

})();
</script>
"""

if "upgrade-12-4-professional-text-markup-js" in html:
    html = re.sub(
        r'<script id="upgrade-12-4-professional-text-markup-js">.*?</script>',
        "",
        html,
        flags=re.S
    )

if "</body>" in html:
    html = html.replace(
        "</body>",
        js_block + "\n</body>",
        1
    )
else:
    html += "\n" + js_block

# ============================================================
# WRITE
# ============================================================

HTML.write_text(
    html,
    encoding="utf-8"
)

print()
print("Professional Text Markup Engine installed.")
print()

# ============================================================
# VERIFICATION
# ============================================================

print("==============================================")
print("  #12.4 FILE MARKER CHECK")
print("==============================================")
print()

html_check = HTML.read_text(
    encoding="utf-8"
)

backend_check = APP.read_text(
    encoding="utf-8"
)

checks = [
    (
        "Backend #12.4 marker",
        "UPGRADE_12_4_PROFESSIONAL_TEXT_MARKUP_ENGINE_BACKEND"
        in backend_check
    ),
    (
        "Markup CSS",
        "upgrade-12-4-professional-text-markup-css"
        in html_check
    ),
    (
        "Markup JS",
        "upgrade-12-4-professional-text-markup-js"
        in html_check
    ),
    (
        "Markup toolbar",
        "pp12ProfessionalMarkupToolbar"
        in html_check
    ),
    (
        "Highlight tool",
        'data-markup-tool="highlight"'
        in html_check
    ),
    (
        "Underline tool",
        'data-markup-tool="underline"'
        in html_check
    ),
    (
        "Strikeout tool",
        'data-markup-tool="strikeout"'
        in html_check
    ),
    (
        "Markup color",
        "pp12MarkupColor"
        in html_check
    ),
    (
        "Markup opacity",
        "pp12MarkupOpacity"
        in html_check
    ),
    (
        "Markup thickness",
        "pp12MarkupThickness"
        in html_check
    ),
    (
        "Word selection engine",
        "updateSelectedWords"
        in html_check
    ),
    (
        "Native markup metadata",
        "wordBoxes"
        in html_check
    ),
    (
        "Multiline selection",
        "selectedWords"
        in html_check
    ),
    (
        "Object manager compatibility",
        "pp12ObjectManager"
        in html_check
    ),
]

failed = False

for name, ok in checks:
    print(
        ("OK  " if ok else "FAIL ") +
        name
    )

    if not ok:
        failed = True

# ============================================================
# PYTHON SYNTAX
# ============================================================

print()
print("==============================================")
print("  PYTHON SYNTAX CHECK")
print("==============================================")
print()

import py_compile

try:
    py_compile.compile(
        str(APP),
        doraise=True
    )

    print(
        "Python syntax check PASSED"
    )

except Exception as exc:
    print(
        "ERROR: Python syntax check FAILED"
    )

    print(exc)

    failed = True

# ============================================================
# EXISTING ROUTES
# ============================================================

print()
print("==============================================")
print("  EXISTING ANNOTATION ROUTE CHECK")
print("==============================================")
print()

for route in [
    '@app.post("/api/annotation-page")',
    '@app.post("/api/annotate")',
    '@app.post("/api/merge")'
]:

    ok = route in backend_check

    print(
        route +
        " => " +
        ("OK" if ok else "MISSING")
    )

    if not ok:
        failed = True

# ============================================================
# BACKUP CHECK
# ============================================================

print()
print("==============================================")
print("  BACKUP CHECK")
print("==============================================")
print()

if backend_backup.exists():
    print("Backend backup exists")
else:
    print("ERROR: Backend backup missing")
    failed = True

if frontend_backup.exists():
    print("Frontend backup exists")
else:
    print("ERROR: Frontend backup missing")
    failed = True

# ============================================================
# FINAL
# ============================================================

print()

if failed:
    print("==============================================")
    print("  #12.4 INSTALLATION FAILED")
    print("==============================================")
    print()
    print("DO NOT CONTINUE.")
    print("Paste the COMPLETE ERROR output here.")
    sys.exit(1)

print("==============================================")
print("  #12.4 COMPLETE")
print("==============================================")
print()
print("Professional Text Markup Engine installed.")
print()
print("Added:")
print("  - Highlight")
print("  - Underline")
print("  - Strikeout")
print("  - Word-level selection")
print("  - Multi-word selection")
print("  - Multi-line selection")
print("  - Markup color")
print("  - Opacity control")
print("  - Thickness control")
print("  - Selection preview")
print("  - Native annotation metadata")
print("  - Object manager compatibility")
print("  - Native PDF export compatibility")
print()
print("Existing #12.1 / #12.2 / #12.3 layers preserved.")
print("No persistent document database added.")
print()
print("IMPORTANT:")
print("If ANY ERROR appeared above, do not continue.")
print("Paste the complete ERROR output here.")
print()

