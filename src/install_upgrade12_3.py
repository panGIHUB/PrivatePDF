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
    "main.py.before_advanced_text_annotation_upgrade"
)

frontend_backup = HTML.with_name(
    "index.html.before_advanced_text_annotation_upgrade"
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
# Text export remains native through /api/annotate.
# No new API is required for the editor-side text engine.
# ============================================================

backend_marker = """
# === UPGRADE_12_3_ADVANCED_TEXT_ANNOTATION_ENGINE_BACKEND ===
# Advanced text annotation editor layer.
# Native PDF export remains handled by /api/annotate.
# No persistent document database is introduced.
"""

if "UPGRADE_12_3_ADVANCED_TEXT_ANNOTATION_ENGINE_BACKEND" not in backend:

    anchor = "# === UPGRADE_12_2_ANNOTATION_OBJECT_MANAGER_BACKEND ==="

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

css_marker = "upgrade-12-3-advanced-text-annotation-css"

css_block = r"""
<style id="upgrade-12-3-advanced-text-annotation-css">

/* ============================================================
   PRIVATE PDF PRO
   UPGRADE #12.3
   ADVANCED TEXT ANNOTATION ENGINE
   ============================================================ */

.pp12-text-toolbar {
    position: absolute;
    left: 18px;
    top: 72px;
    width: 330px;
    max-width: calc(100% - 36px);
    padding: 12px;
    border-radius: 14px;
    background: rgba(18,22,30,.97);
    border: 1px solid rgba(255,255,255,.10);
    box-shadow: 0 18px 55px rgba(0,0,0,.42);
    backdrop-filter: blur(18px);
    z-index: 82;
    display: none;
}

.pp12-text-toolbar.visible {
    display: block;
}

.pp12-text-toolbar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}

.pp12-text-toolbar-title {
    font-size: 13px;
    font-weight: 700;
}

.pp12-text-toolbar-status {
    font-size: 10px;
    color: rgba(255,255,255,.45);
}

.pp12-text-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
    margin-bottom: 7px;
}

.pp12-text-row.three {
    grid-template-columns: 1fr 1fr 1fr;
}

.pp12-text-field {
    width: 100%;
    min-width: 0;
    height: 34px;
    padding: 0 9px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,.09);
    background: rgba(255,255,255,.055);
    color: rgba(255,255,255,.90);
    outline: none;
    font-size: 11px;
}

.pp12-text-field:focus {
    border-color: rgba(100,160,255,.65);
    box-shadow: 0 0 0 2px rgba(70,130,255,.12);
}

.pp12-text-label {
    display: block;
    margin: 0 0 4px;
    font-size: 9px;
    color: rgba(255,255,255,.42);
    text-transform: uppercase;
    letter-spacing: .05em;
}

.pp12-text-control {
    min-width: 0;
}

.pp12-text-buttons {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
}

.pp12-text-format-btn {
    width: 34px;
    height: 32px;
    border: 0;
    border-radius: 7px;
    background: rgba(255,255,255,.07);
    color: rgba(255,255,255,.82);
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
}

.pp12-text-format-btn:hover {
    background: rgba(255,255,255,.13);
}

.pp12-text-format-btn.active {
    background: rgba(75,135,235,.35);
    outline: 1px solid rgba(110,165,255,.55);
}

.pp12-text-color {
    width: 100%;
    height: 34px;
    padding: 3px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,.09);
    background: rgba(255,255,255,.055);
    cursor: pointer;
}

.pp12-text-actions {
    display: flex;
    gap: 7px;
    margin-top: 10px;
}

.pp12-text-action {
    flex: 1;
    height: 34px;
    border: 0;
    border-radius: 8px;
    cursor: pointer;
    background: rgba(255,255,255,.08);
    color: rgba(255,255,255,.86);
    font-size: 11px;
    font-weight: 600;
}

.pp12-text-action.primary {
    background: rgba(55,125,235,.82);
    color: white;
}

.pp12-text-action:hover {
    filter: brightness(1.10);
}

.pp12-live-text {
    position: absolute;
    min-width: 35px;
    min-height: 22px;
    padding: 2px 3px;
    border: 1px dashed rgba(80,150,255,.85);
    background: rgba(80,150,255,.08);
    white-space: pre-wrap;
    word-break: break-word;
    pointer-events: none;
    z-index: 65;
    overflow: hidden;
}

.pp12-live-text.empty::before {
    content: "Type text...";
    color: rgba(255,255,255,.40);
}

.pp12-text-editable {
    cursor: text !important;
    pointer-events: auto !important;
    white-space: pre-wrap;
    word-break: break-word;
    overflow-wrap: anywhere;
    outline: none;
}

.pp12-text-editable:focus {
    outline: 1px solid rgba(80,150,255,.65);
    outline-offset: 2px;
}

.pp12-text-resize-frame {
    pointer-events: none;
}

.pp12-text-size-badge {
    position: absolute;
    top: -23px;
    right: 0;
    padding: 3px 6px;
    border-radius: 5px;
    background: rgba(25,70,135,.94);
    color: white;
    font-size: 9px;
    pointer-events: none;
}

.pp12-text-empty {
    padding: 7px 0;
    font-size: 10px;
    color: rgba(255,255,255,.38);
    line-height: 1.4;
}

@media (max-width: 700px) {
    .pp12-text-toolbar {
        left: 10px;
        top: 60px;
        width: 300px;
    }
}

</style>
"""

if css_marker in html:
    html = re.sub(
        r'<style id="upgrade-12-3-advanced-text-annotation-css">.*?</style>',
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
# TEXT TOOL UI + ENGINE
# ============================================================

js_marker = "upgrade-12-3-advanced-text-annotation-js"

js_block = r"""
<script id="upgrade-12-3-advanced-text-annotation-js">
(function () {
    "use strict";

    /*
     * =========================================================
     * PRIVATE PDF PRO
     * UPGRADE #12.3
     *
     * Advanced Text Annotation Engine
     *
     * Responsibilities:
     *   - text creation
     *   - text editing
     *   - formatting
     *   - multiline text
     *   - text box sizing
     *   - live preview
     *   - integration with #12.2 object manager
     * =========================================================
     */

    const TOOLBAR_ID = "pp12AdvancedTextToolbar";
    const LIVE_ID = "pp12AdvancedLiveText";

    let toolbar = null;
    let liveText = null;

    let activeTextObject = null;
    let textCreating = false;
    let textStart = null;

    let textState = {
        fontFamily: "Arial",
        fontSize: 16,
        color: "#111111",
        bold: false,
        italic: false,
        underline: false,
        align: "left",
        text: ""
    };

    function studio() {
        return document.getElementById("pp12AnnotationStudio");
    }

    function ensureToolbar() {
        const root = studio();

        if (!root) return null;

        toolbar = document.getElementById(TOOLBAR_ID);

        if (toolbar) return toolbar;

        toolbar = document.createElement("div");
        toolbar.id = TOOLBAR_ID;
        toolbar.className = "pp12-text-toolbar";

        toolbar.innerHTML = `
            <div class="pp12-text-toolbar-header">
                <div class="pp12-text-toolbar-title">Text</div>
                <div class="pp12-text-toolbar-status" id="pp12TextStatus">
                    Ready
                </div>
            </div>

            <div class="pp12-text-row">
                <div class="pp12-text-control">
                    <label class="pp12-text-label">Font</label>
                    <select id="pp12TextFont" class="pp12-text-field">
                        <option value="Arial">Arial</option>
                        <option value="Helvetica">Helvetica</option>
                        <option value="Times New Roman">Times New Roman</option>
                        <option value="Courier New">Courier New</option>
                        <option value="Georgia">Georgia</option>
                        <option value="Verdana">Verdana</option>
                    </select>
                </div>

                <div class="pp12-text-control">
                    <label class="pp12-text-label">Size</label>
                    <input
                        id="pp12TextSize"
                        class="pp12-text-field"
                        type="number"
                        min="6"
                        max="96"
                        step="1"
                        value="16"
                    >
                </div>
            </div>

            <div class="pp12-text-row">
                <div class="pp12-text-control">
                    <label class="pp12-text-label">Color</label>
                    <input
                        id="pp12TextColor"
                        class="pp12-text-color"
                        type="color"
                        value="#111111"
                    >
                </div>

                <div class="pp12-text-control">
                    <label class="pp12-text-label">Alignment</label>
                    <select id="pp12TextAlign" class="pp12-text-field">
                        <option value="left">Left</option>
                        <option value="center">Center</option>
                        <option value="right">Right</option>
                    </select>
                </div>
            </div>

            <div class="pp12-text-buttons">
                <button
                    type="button"
                    class="pp12-text-format-btn"
                    id="pp12TextBold"
                    title="Bold"
                >B</button>

                <button
                    type="button"
                    class="pp12-text-format-btn"
                    id="pp12TextItalic"
                    title="Italic"
                ><i>I</i></button>

                <button
                    type="button"
                    class="pp12-text-format-btn"
                    id="pp12TextUnderline"
                    title="Underline"
                ><u>U</u></button>
            </div>

            <div class="pp12-text-actions">
                <button
                    type="button"
                    class="pp12-text-action"
                    id="pp12TextCancel"
                >Cancel</button>

                <button
                    type="button"
                    class="pp12-text-action primary"
                    id="pp12TextApply"
                >Apply</button>
            </div>

            <div class="pp12-text-empty">
                Choose the Text tool, drag a text box, then type.
                Double-click an existing text object to edit it.
            </div>
        `;

        root.appendChild(toolbar);

        bindToolbar();

        return toolbar;
    }

    function bindToolbar() {
        const font = document.getElementById("pp12TextFont");
        const size = document.getElementById("pp12TextSize");
        const color = document.getElementById("pp12TextColor");
        const align = document.getElementById("pp12TextAlign");

        if (font) {
            font.addEventListener("change", function () {
                textState.fontFamily = this.value;
                updateActivePreview();
            });
        }

        if (size) {
            size.addEventListener("input", function () {
                const value = Math.max(
                    6,
                    Math.min(96, Number(this.value) || 16)
                );

                textState.fontSize = value;
                this.value = value;
                updateActivePreview();
            });
        }

        if (color) {
            color.addEventListener("input", function () {
                textState.color = this.value;
                updateActivePreview();
            });
        }

        if (align) {
            align.addEventListener("change", function () {
                textState.align = this.value;
                updateActivePreview();
            });
        }

        const bold = document.getElementById("pp12TextBold");
        const italic = document.getElementById("pp12TextItalic");
        const underline = document.getElementById("pp12TextUnderline");

        if (bold) {
            bold.addEventListener("click", function () {
                textState.bold = !textState.bold;
                this.classList.toggle("active", textState.bold);
                updateActivePreview();
            });
        }

        if (italic) {
            italic.addEventListener("click", function () {
                textState.italic = !textState.italic;
                this.classList.toggle("active", textState.italic);
                updateActivePreview();
            });
        }

        if (underline) {
            underline.addEventListener("click", function () {
                textState.underline = !textState.underline;
                this.classList.toggle("active", textState.underline);
                updateActivePreview();
            });
        }

        const cancel = document.getElementById("pp12TextCancel");

        if (cancel) {
            cancel.addEventListener("click", cancelText);
        }

        const apply = document.getElementById("pp12TextApply");

        if (apply) {
            apply.addEventListener("click", applyText);
        }
    }

    function showToolbar(status) {
        const t = ensureToolbar();

        if (!t) return;

        t.classList.add("visible");

        const s = document.getElementById("pp12TextStatus");

        if (s) {
            s.textContent = status || "Ready";
        }
    }

    function hideToolbar() {
        if (toolbar) {
            toolbar.classList.remove("visible");
        }
    }

    function resetToolbar() {
        textState = {
            fontFamily: "Arial",
            fontSize: 16,
            color: "#111111",
            bold: false,
            italic: false,
            underline: false,
            align: "left",
            text: ""
        };

        const font = document.getElementById("pp12TextFont");
        const size = document.getElementById("pp12TextSize");
        const color = document.getElementById("pp12TextColor");
        const align = document.getElementById("pp12TextAlign");

        if (font) font.value = "Arial";
        if (size) size.value = "16";
        if (color) color.value = "#111111";
        if (align) align.value = "left";

        ["pp12TextBold","pp12TextItalic","pp12TextUnderline"]
            .forEach(function (id) {
                const el = document.getElementById(id);
                if (el) el.classList.remove("active");
            });
    }

    function getPageStage() {
        const root = studio();

        if (!root) return null;

        return root.querySelector(
            ".pp12-page-stage, .pp12-canvas-wrap, .pp12-page-wrap, .pp12-editor-page"
        );
    }

    function pointerPoint(event) {
        const stage = getPageStage();

        if (!stage) return null;

        const r = stage.getBoundingClientRect();

        return {
            x: event.clientX - r.left,
            y: event.clientY - r.top,
            width: r.width,
            height: r.height
        };
    }

    function ensureLiveText() {
        const stage = getPageStage();

        if (!stage) return null;

        liveText = document.getElementById(LIVE_ID);

        if (!liveText) {
            liveText = document.createElement("div");
            liveText.id = LIVE_ID;
            liveText.className = "pp12-live-text empty";
            stage.appendChild(liveText);
        }

        return liveText;
    }

    function applyTextStyle(el) {
        if (!el) return;

        el.style.fontFamily = textState.fontFamily;

        el.style.fontSize = textState.fontSize + "px";

        el.style.color = textState.color;

        el.style.fontWeight =
            textState.bold ? "700" : "400";

        el.style.fontStyle =
            textState.italic ? "italic" : "normal";

        el.style.textDecoration =
            textState.underline ? "underline" : "none";

        el.style.textAlign = textState.align;

        el.style.lineHeight = "1.2";

        el.style.whiteSpace = "pre-wrap";

        el.style.wordBreak = "break-word";

        el.style.overflowWrap = "anywhere";
    }

    function updateActivePreview() {
        if (liveText) {
            applyTextStyle(liveText);

            liveText.textContent = textState.text || "";

            liveText.classList.toggle(
                "empty",
                !textState.text
            );
        }

        if (activeTextObject) {
            applyTextStyle(activeTextObject);

            syncTextObjectData(activeTextObject);
        }
    }

    function beginTextBox(event) {
        const stage = getPageStage();

        if (!stage) return;

        const p = pointerPoint(event);

        if (!p) return;

        textCreating = true;

        textStart = {
            x: Math.max(0, p.x),
            y: Math.max(0, p.y)
        };

        const preview = ensureLiveText();

        if (!preview) return;

        preview.style.left = textStart.x + "px";
        preview.style.top = textStart.y + "px";
        preview.style.width = "160px";
        preview.style.height = "55px";

        preview.textContent = "";

        applyTextStyle(preview);

        showToolbar("New text");

        window.addEventListener(
            "pointermove",
            resizeTextPreview
        );

        window.addEventListener(
            "pointerup",
            finishTextBox,
            { once: true }
        );
    }

    function resizeTextPreview(event) {
        if (!textCreating || !textStart) return;

        const p = pointerPoint(event);

        if (!p || !liveText) return;

        const x = Math.max(0, p.x);
        const y = Math.max(0, p.y);

        const left = Math.min(textStart.x, x);
        const top = Math.min(textStart.y, y);

        const width = Math.max(
            80,
            Math.abs(x - textStart.x)
        );

        const height = Math.max(
            35,
            Math.abs(y - textStart.y)
        );

        liveText.style.left = left + "px";
        liveText.style.top = top + "px";
        liveText.style.width = width + "px";
        liveText.style.height = height + "px";
    }

    function finishTextBox() {
        window.removeEventListener(
            "pointermove",
            resizeTextPreview
        );

        textCreating = false;

        if (!liveText) return;

        /*
         * The user now types directly into the preview.
         */
        liveText.contentEditable = "true";
        liveText.classList.remove("empty");

        liveText.focus();

        showToolbar("Editing");

        /*
         * Move cursor to the beginning.
         */
        try {
            const range = document.createRange();
            range.selectNodeContents(liveText);
            range.collapse(false);

            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
        } catch (_) {}
    }

    function textFromElement(el) {
        if (!el) return "";

        return (
            el.dataset.text ||
            el.textContent ||
            ""
        ).replace(/\r/g, "");
    }

    function syncTextObjectData(el) {
        if (!el) return;

        el.dataset.text = textFromElement(el);

        el.dataset.fontFamily = textState.fontFamily;
        el.dataset.fontSize = String(textState.fontSize);
        el.dataset.color = textState.color;
        el.dataset.bold = textState.bold ? "1" : "0";
        el.dataset.italic = textState.italic ? "1" : "0";
        el.dataset.underline = textState.underline ? "1" : "0";
        el.dataset.align = textState.align;
    }

    function createTextObject() {
        const stage = getPageStage();

        if (!stage || !liveText) return null;

        const value = textFromElement(liveText);

        if (!value.trim()) {
            return null;
        }

        const object = document.createElement("div");

        object.className =
            "pp12-annotation-object pp12-text-editable";

        object.dataset.annotationId =
            "text-" +
            Date.now().toString(36) +
            "-" +
            Math.random().toString(36).slice(2, 8);

        object.dataset.objectId =
            object.dataset.annotationId;

        object.dataset.type = "text";
        object.dataset.annotationType = "text";

        object.style.position = "absolute";
        object.style.left = liveText.style.left;
        object.style.top = liveText.style.top;
        object.style.width = liveText.style.width;
        object.style.height = liveText.style.height;

        object.textContent = value;

        applyTextStyle(object);
        syncTextObjectData(object);

        /*
         * Text objects are editor objects. They are not rendered
         * as a screenshot and therefore remain vector/text data
         * until native PDF export.
         */
        stage.appendChild(object);

        makeEditable(object);

        return object;
    }

    function makeEditable(object) {
        if (!object || object.dataset.pp12TextBound === "1") {
            return;
        }

        object.dataset.pp12TextBound = "1";

        object.addEventListener("dblclick", function (event) {
            event.preventDefault();
            event.stopPropagation();

            editTextObject(object);
        });

        object.addEventListener("input", function () {
            object.dataset.text = object.textContent || "";
        });
    }

    function editTextObject(object) {
        if (!object) return;

        activeTextObject = object;

        textState.fontFamily =
            object.dataset.fontFamily ||
            getComputedStyle(object).fontFamily ||
            "Arial";

        textState.fontSize =
            Number(object.dataset.fontSize) ||
            parseFloat(getComputedStyle(object).fontSize) ||
            16;

        textState.color =
            object.dataset.color ||
            rgbToHex(getComputedStyle(object).color) ||
            "#111111";

        textState.bold =
            object.dataset.bold === "1" ||
            getComputedStyle(object).fontWeight === "700";

        textState.italic =
            object.dataset.italic === "1" ||
            getComputedStyle(object).fontStyle === "italic";

        textState.underline =
            object.dataset.underline === "1" ||
            getComputedStyle(object).textDecoration.includes("underline");

        textState.align =
            object.dataset.align ||
            getComputedStyle(object).textAlign ||
            "left";

        syncToolbar();

        object.contentEditable = "true";
        object.focus();

        showToolbar("Editing");

        try {
            const range = document.createRange();
            range.selectNodeContents(object);
            range.collapse(false);

            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
        } catch (_) {}
    }

    function syncToolbar() {
        const font = document.getElementById("pp12TextFont");
        const size = document.getElementById("pp12TextSize");
        const color = document.getElementById("pp12TextColor");
        const align = document.getElementById("pp12TextAlign");

        if (font) {
            font.value = textState.fontFamily;
        }

        if (size) {
            size.value = textState.fontSize;
        }

        if (color) {
            color.value = normalizeColor(textState.color);
        }

        if (align) {
            align.value = textState.align;
        }

        const bold = document.getElementById("pp12TextBold");
        const italic = document.getElementById("pp12TextItalic");
        const underline = document.getElementById("pp12TextUnderline");

        if (bold) {
            bold.classList.toggle("active", textState.bold);
        }

        if (italic) {
            italic.classList.toggle("active", textState.italic);
        }

        if (underline) {
            underline.classList.toggle(
                "active",
                textState.underline
            );
        }
    }

    function normalizeColor(color) {
        if (!color) return "#111111";

        if (color.startsWith("#")) {
            return color;
        }

        return rgbToHex(color) || "#111111";
    }

    function rgbToHex(rgb) {
        const match = String(rgb).match(
            /rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)/
        );

        if (!match) return null;

        const r = Number(match[1]);
        const g = Number(match[2]);
        const b = Number(match[3]);

        return "#" +
            [r,g,b]
                .map(function (v) {
                    return v.toString(16).padStart(2, "0");
                })
                .join("");
    }

    function applyText() {
        /*
         * Existing object editing.
         */
        if (activeTextObject) {
            activeTextObject.contentEditable = "false";

            applyTextStyle(activeTextObject);

            syncTextObjectData(activeTextObject);

            try {
                if (
                    typeof window.pp12CommitAnnotationTransform ===
                    "function"
                ) {
                    window.pp12CommitAnnotationTransform(
                        activeTextObject
                    );
                }
            } catch (_) {}

            try {
                if (
                    window.pp12ObjectManager &&
                    typeof window.pp12ObjectManager.refresh ===
                    "function"
                ) {
                    window.pp12ObjectManager.refresh();
                }
            } catch (_) {}

            activeTextObject = null;

            hideToolbar();

            return;
        }

        /*
         * New object.
         */
        if (!liveText) return;

        const value = textFromElement(liveText);

        if (!value.trim()) {
            cancelText();
            return;
        }

        const object = createTextObject();

        if (!object) {
            return;
        }

        liveText.remove();
        liveText = null;

        object.contentEditable = "false";

        activeTextObject = object;

        try {
            if (
                window.pp12ObjectManager &&
                typeof window.pp12ObjectManager.select ===
                "function"
            ) {
                window.pp12ObjectManager.select(object);
            }
        } catch (_) {}

        activeTextObject = null;

        resetToolbar();
        hideToolbar();
    }

    function cancelText() {
        textCreating = false;
        textStart = null;

        if (liveText) {
            liveText.remove();
            liveText = null;
        }

        if (activeTextObject) {
            activeTextObject.contentEditable = "false";
            activeTextObject = null;
        }

        hideToolbar();
    }

    function detectTextTool() {
        /*
         * #12.1 editor stores its current tool in a state
         * object that is not guaranteed to be globally exposed.
         *
         * Therefore we watch toolbar/button activity and also
         * expose a public method for the existing tool layer.
         */
    }

    function bindTextToolButtons() {
        const root = studio();

        if (!root) return;

        root.addEventListener("click", function (event) {
            const button = event.target.closest &&
                event.target.closest(
                    '[data-tool="text"], [data-annotation-tool="text"], [data-tool-name="text"]'
                );

            if (!button) return;

            resetToolbar();
            showToolbar("New text");
        });
    }

    function bindStage() {
        const root = studio();

        if (!root) return;

        root.addEventListener("pointerdown", function (event) {
            /*
             * Do not interfere with resize handles, object manager,
             * existing annotation objects, or UI controls.
             */
            if (
                event.target.closest &&
                (
                    event.target.closest(".pp12-text-toolbar") ||
                    event.target.closest(".pp12-object-manager") ||
                    event.target.closest(".pp12-resize-handle") ||
                    event.target.closest(".pp12-annotation-object") ||
                    event.target.closest(".pp12-annotation")
                )
            ) {
                return;
            }

            const button = root.querySelector(
                '[data-tool="text"].active, [data-annotation-tool="text"].active, [data-tool-name="text"].active'
            );

            if (!button) return;

            beginTextBox(event);
        });
    }

    function scanExistingTextObjects() {
        const root = studio();

        if (!root) return;

        root.querySelectorAll(
            '.pp12-annotation-object[data-type="text"],' +
            '.pp12-annotation-object[data-annotation-type="text"]'
        ).forEach(function (object) {
            makeEditable(object);
        });
    }

    function observeEditor() {
        const root = studio();

        if (!root) return;

        const observer = new MutationObserver(function () {
            scanExistingTextObjects();
        });

        observer.observe(root, {
            childList: true,
            subtree: true
        });
    }

    /*
     * Public API
     */
    window.pp12AdvancedText = {
        start: function () {
            resetToolbar();
            showToolbar("New text");
        },

        edit: function (object) {
            editTextObject(object);
        },

        cancel: cancelText,

        apply: applyText,

        state: textState
    };

    function boot() {
        const root = studio();

        if (!root) {
            setTimeout(boot, 400);
            return;
        }

        ensureToolbar();
        bindTextToolButtons();
        bindStage();
        observeEditor();
        scanExistingTextObjects();

        /*
         * Keyboard shortcut:
         * T activates the advanced text layer only when the user
         * is not typing in a field.
         */
        window.addEventListener("keydown", function (event) {
            const tag = (
                event.target &&
                event.target.tagName ||
                ""
            ).toLowerCase();

            if (
                tag === "input" ||
                tag === "textarea" ||
                tag === "select" ||
                event.target.isContentEditable
            ) {
                return;
            }

            if (
                event.key.toLowerCase() === "t" &&
                !event.ctrlKey &&
                !event.altKey &&
                !event.metaKey
            ) {
                try {
                    window.pp12AdvancedText.start();
                } catch (_) {}
            }
        });
    }

    if (document.readyState === "loading") {
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

if js_marker in html:
    html = re.sub(
        r'<script id="upgrade-12-3-advanced-text-annotation-js">.*?</script>',
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
# WRITE FRONTEND
# ============================================================

HTML.write_text(html, encoding="utf-8")

print()
print("Advanced Text Annotation Engine installed.")
print()

# ============================================================
# VERIFICATION
# ============================================================

print("==============================================")
print("  #12.3 FILE MARKER CHECK")
print("==============================================")
print()

html_check = HTML.read_text(encoding="utf-8")
backend_check = APP.read_text(encoding="utf-8")

checks = [
    (
        "Backend #12.3 marker",
        "UPGRADE_12_3_ADVANCED_TEXT_ANNOTATION_ENGINE_BACKEND"
        in backend_check
    ),
    (
        "Advanced Text CSS",
        "upgrade-12-3-advanced-text-annotation-css"
        in html_check
    ),
    (
        "Advanced Text JS",
        "upgrade-12-3-advanced-text-annotation-js"
        in html_check
    ),
    (
        "Text toolbar",
        "pp12AdvancedTextToolbar"
        in html_check
    ),
    (
        "Text live preview",
        "pp12AdvancedLiveText"
        in html_check
    ),
    (
        "Font family control",
        "pp12TextFont"
        in html_check
    ),
    (
        "Font size control",
        "pp12TextSize"
        in html_check
    ),
    (
        "Text color control",
        "pp12TextColor"
        in html_check
    ),
    (
        "Bold control",
        "pp12TextBold"
        in html_check
    ),
    (
        "Italic control",
        "pp12TextItalic"
        in html_check
    ),
    (
        "Underline control",
        "pp12TextUnderline"
        in html_check
    ),
    (
        "Alignment control",
        "pp12TextAlign"
        in html_check
    ),
    (
        "Double-click editing",
        "dblclick"
        in html_check
    ),
    (
        "Multiline text",
        "pre-wrap"
        in html_check
    ),
    (
        "Text object class",
        "pp12-text-editable"
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
    print("Python syntax check PASSED")
except Exception as exc:
    print("ERROR: Python syntax check FAILED")
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
    print("  #12.3 INSTALLATION FAILED")
    print("==============================================")
    print()
    print("DO NOT CONTINUE.")
    print("Paste the COMPLETE ERROR output here.")
    sys.exit(1)

print("==============================================")
print("  #12.3 COMPLETE")
print("==============================================")
print()
print("Advanced Text Annotation Engine installed.")
print()
print("Added:")
print("  - Professional text toolbar")
print("  - Font family")
print("  - Font size")
print("  - Text color")
print("  - Bold")
print("  - Italic")
print("  - Underline")
print("  - Left / Center / Right alignment")
print("  - Multiline text")
print("  - Text box creation")
print("  - Live text preview")
print("  - Double-click text editing")
print("  - Text object metadata")
print("  - Native PDF export compatibility")
print()
print("Existing #12.1 and #12.2 layers preserved.")
print("No persistent document database added.")
print()
print("IMPORTANT:")
print("If ANY ERROR appeared above, do not continue.")
print("Paste the complete ERROR output here.")
print()

