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

backend_backup = APP.with_name("main.py.before_annotation_object_manager_upgrade")
frontend_backup = HTML.with_name("index.html.before_annotation_object_manager_upgrade")

shutil.copy2(APP, backend_backup)
shutil.copy2(HTML, frontend_backup)

print("Backend backup created:", backend_backup)
print("Frontend backup created:", frontend_backup)

# ============================================================
# READ FILES
# ============================================================

backend = APP.read_text(encoding="utf-8")
html = HTML.read_text(encoding="utf-8")

# ============================================================
# 12.2 BACKEND
#
# No new API endpoint is required.
# 12.1 already provides native annotation export.
#
# Add a small health marker so the installer can verify that
# the backend belongs to the upgraded annotation engine.
# ============================================================

backend_marker = """
# === UPGRADE_12_2_ANNOTATION_OBJECT_MANAGER_BACKEND ===
# Annotation Object Manager is a frontend/editor-layer upgrade.
# Native PDF annotation export remains handled by /api/annotate.
# No persistent document database is introduced.
"""

if "UPGRADE_12_2_ANNOTATION_OBJECT_MANAGER_BACKEND" not in backend:
    anchor = "# === UPGRADE_12_1_PROFESSIONAL_ANNOTATION_ENGINE_BACKEND ==="

    if anchor in backend:
        backend = backend.replace(
            anchor,
            anchor + backend_marker,
            1
        )
    else:
        # Safe fallback: add marker before first FastAPI route.
        pos = backend.find('@app.')
        if pos == -1:
            backend += "\n" + backend_marker + "\n"
        else:
            backend = backend[:pos] + backend_marker + "\n" + backend[pos:]

    APP.write_text(backend, encoding="utf-8")
else:
    print("Backend #12.2 marker already exists; skipping backend insertion.")

# ============================================================
# FRONTEND CSS
# ============================================================

css_marker = "upgrade-12-2-annotation-object-manager-css"

css_block = r"""
<style id="upgrade-12-2-annotation-object-manager-css">

/* ============================================================
   PRIVATE PDF PRO
   UPGRADE #12.2
   ANNOTATION OBJECT MANAGER
   ============================================================ */

.pp12-object-manager {
    position: absolute;
    top: 72px;
    right: 18px;
    width: 270px;
    max-height: calc(100% - 100px);
    display: flex;
    flex-direction: column;
    background: rgba(18, 22, 30, .96);
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 14px;
    box-shadow: 0 18px 55px rgba(0,0,0,.40);
    backdrop-filter: blur(18px);
    overflow: hidden;
    z-index: 80;
}

.pp12-object-manager.is-hidden {
    display: none;
}

.pp12-object-manager-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    border-bottom: 1px solid rgba(255,255,255,.08);
}

.pp12-object-manager-title {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: .02em;
}

.pp12-object-manager-count {
    min-width: 22px;
    height: 22px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    background: rgba(255,255,255,.08);
    color: rgba(255,255,255,.75);
    font-size: 11px;
}

.pp12-object-manager-list {
    overflow: auto;
    padding: 7px;
    min-height: 45px;
}

.pp12-object-row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 38px;
    padding: 7px 8px;
    margin-bottom: 3px;
    border-radius: 9px;
    cursor: pointer;
    user-select: none;
    transition: background .12s ease, transform .12s ease;
}

.pp12-object-row:hover {
    background: rgba(255,255,255,.07);
}

.pp12-object-row.selected {
    background: rgba(90,150,255,.17);
    outline: 1px solid rgba(100,160,255,.35);
}

.pp12-object-icon {
    width: 25px;
    height: 25px;
    flex: 0 0 25px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 7px;
    background: rgba(255,255,255,.07);
    font-size: 12px;
}

.pp12-object-name {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    font-size: 12px;
    color: rgba(255,255,255,.88);
}

.pp12-object-page {
    font-size: 10px;
    color: rgba(255,255,255,.42);
}

.pp12-object-empty {
    padding: 18px 10px;
    text-align: center;
    color: rgba(255,255,255,.40);
    font-size: 11px;
}

.pp12-object-manager-actions {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 5px;
    padding: 8px;
    border-top: 1px solid rgba(255,255,255,.08);
}

.pp12-object-action {
    height: 30px;
    border: 0;
    border-radius: 7px;
    background: rgba(255,255,255,.07);
    color: rgba(255,255,255,.82);
    cursor: pointer;
    font-size: 11px;
}

.pp12-object-action:hover {
    background: rgba(255,255,255,.13);
}

.pp12-object-action:disabled {
    opacity: .30;
    cursor: default;
}

.pp12-object-manager-hint {
    padding: 0 10px 10px;
    color: rgba(255,255,255,.34);
    font-size: 10px;
    line-height: 1.45;
}

/* ============================================================
   RESIZE FRAME
   ============================================================ */

.pp12-transform-frame {
    position: absolute;
    pointer-events: none;
    border: 1px solid rgba(85,155,255,.95);
    box-shadow:
        0 0 0 1px rgba(85,155,255,.18),
        0 0 18px rgba(50,120,255,.12);
    z-index: 70;
}

.pp12-transform-frame .pp12-resize-handle {
    position: absolute;
    width: 9px;
    height: 9px;
    border-radius: 2px;
    background: #fff;
    border: 1px solid rgba(30,80,160,.9);
    box-shadow: 0 1px 5px rgba(0,0,0,.35);
    pointer-events: auto;
}

.pp12-transform-frame .nw { left: -5px; top: -5px; cursor: nwse-resize; }
.pp12-transform-frame .n  { left: calc(50% - 4px); top: -5px; cursor: ns-resize; }
.pp12-transform-frame .ne { right: -5px; top: -5px; cursor: nesw-resize; }
.pp12-transform-frame .e  { right: -5px; top: calc(50% - 4px); cursor: ew-resize; }
.pp12-transform-frame .se { right: -5px; bottom: -5px; cursor: nwse-resize; }
.pp12-transform-frame .s  { left: calc(50% - 4px); bottom: -5px; cursor: ns-resize; }
.pp12-transform-frame .sw { left: -5px; bottom: -5px; cursor: nesw-resize; }
.pp12-transform-frame .w  { left: -5px; top: calc(50% - 4px); cursor: ew-resize; }

.pp12-selection-badge {
    position: absolute;
    top: -25px;
    left: 0;
    padding: 4px 7px;
    border-radius: 6px 6px 0 0;
    background: rgba(35,90,170,.95);
    color: #fff;
    font-size: 10px;
    white-space: nowrap;
    pointer-events: none;
}

.pp12-annotation-object.pp12-object-selected {
    outline: 1px solid rgba(80,150,255,.9) !important;
    outline-offset: 1px;
}

@media (max-width: 900px) {
    .pp12-object-manager {
        right: 8px;
        width: 235px;
    }
}

@media (max-width: 700px) {
    .pp12-object-manager {
        top: auto;
        bottom: 12px;
        right: 12px;
        max-height: 42%;
    }
}

</style>
"""

# Remove previous copy if present, then insert one copy.
if css_marker in html:
    html = re.sub(
        r'<style id="upgrade-12-2-annotation-object-manager-css">.*?</style>',
        "",
        html,
        flags=re.S
    )

css_anchor = "</head>"
if css_anchor in html:
    html = html.replace(css_anchor, css_block + "\n" + css_anchor, 1)
else:
    html = css_block + "\n" + html

# ============================================================
# OBJECT MANAGER HTML + JS
# ============================================================

js_marker = "upgrade-12-2-annotation-object-manager-js"

js_block = r"""
<script id="upgrade-12-2-annotation-object-manager-js">
(function () {
    "use strict";

    /*
     * =========================================================
     * PRIVATE PDF PRO
     * UPGRADE #12.2
     *
     * Professional annotation object management layer.
     *
     * This layer deliberately sits above the #12.1 editor
     * instead of replacing its native PDF export engine.
     * =========================================================
     */

    const MANAGER_ID = "pp12AnnotationObjectManager";
    const FRAME_ID = "pp12AnnotationTransformFrame";

    let manager = null;
    let frame = null;
    let activeObject = null;
    let resizeState = null;
    let observer = null;

    const HANDLE_NAMES = ["nw","n","ne","e","se","s","sw","w"];

    function studio() {
        return document.getElementById("pp12AnnotationStudio");
    }

    function getCanvas() {
        const root = studio();
        if (!root) return null;

        return root.querySelector(
            ".pp12-page-stage, .pp12-canvas-wrap, .pp12-page-wrap, .pp12-editor-page"
        ) || root;
    }

    function findAnnotationObjects() {
        const root = studio();
        if (!root) return [];

        /*
         * #12.1 annotation elements use pp12 naming.
         * We intentionally accept several likely class names so
         * the manager remains compatible with the current editor.
         */
        const selectors = [
            ".pp12-annotation-object",
            ".pp12-annotation",
            "[data-annotation-id]",
            "[data-annotation-index]"
        ];

        const found = [];

        selectors.forEach(function (selector) {
            root.querySelectorAll(selector).forEach(function (el) {
                if (!found.includes(el)) found.push(el);
            });
        });

        return found.filter(function (el) {
            return !el.classList.contains("pp12-transform-frame") &&
                   el.id !== FRAME_ID;
        });
    }

    function objectId(el, index) {
        if (!el) return "annotation-" + index;

        return (
            el.dataset.annotationId ||
            el.dataset.objectId ||
            el.dataset.id ||
            el.getAttribute("data-annotation-id") ||
            el.id ||
            ("annotation-" + index)
        );
    }

    function objectType(el) {
        if (!el) return "Annotation";

        const raw = (
            el.dataset.type ||
            el.dataset.annotationType ||
            el.getAttribute("data-type") ||
            ""
        ).toLowerCase();

        if (raw.includes("highlight")) return "Highlight";
        if (raw.includes("underline")) return "Underline";
        if (raw.includes("strike")) return "Strikeout";
        if (raw.includes("text")) return "Text";
        if (raw.includes("draw")) return "Draw";
        if (raw.includes("arrow")) return "Arrow";
        if (raw.includes("box") || raw.includes("rect")) return "Box";

        return "Annotation";
    }

    function objectIcon(type) {
        switch (type) {
            case "Highlight": return "H";
            case "Underline": return "U";
            case "Strikeout": return "S";
            case "Text": return "T";
            case "Draw": return "✎";
            case "Arrow": return "➜";
            case "Box": return "□";
            default: return "•";
        }
    }

    function ensureManager() {
        const root = studio();
        if (!root) return null;

        if (document.getElementById(MANAGER_ID)) {
            manager = document.getElementById(MANAGER_ID);
            return manager;
        }

        manager = document.createElement("aside");
        manager.id = MANAGER_ID;
        manager.className = "pp12-object-manager";

        manager.innerHTML = `
            <div class="pp12-object-manager-header">
                <div class="pp12-object-manager-title">Objects</div>
                <div class="pp12-object-manager-count" id="pp12ObjectCount">0</div>
            </div>

            <div class="pp12-object-manager-list" id="pp12ObjectList">
                <div class="pp12-object-empty">
                    No annotations on this page
                </div>
            </div>

            <div class="pp12-object-manager-actions">
                <button class="pp12-object-action" data-object-action="front" title="Bring forward">↑</button>
                <button class="pp12-object-action" data-object-action="back" title="Send backward">↓</button>
                <button class="pp12-object-action" data-object-action="duplicate" title="Duplicate">⧉</button>
                <button class="pp12-object-action" data-object-action="delete" title="Delete">×</button>
            </div>

            <div class="pp12-object-manager-hint">
                Select an object to move or resize it.<br>
                Arrow keys move • Shift+Arrow moves faster • Delete removes
            </div>
        `;

        root.appendChild(manager);

        manager.addEventListener("click", function (event) {
            const row = event.target.closest("[data-object-id]");
            if (row) {
                const id = row.getAttribute("data-object-id");
                selectById(id);
                return;
            }

            const action = event.target.closest("[data-object-action]");
            if (action) {
                runObjectAction(action.getAttribute("data-object-action"));
            }
        });

        return manager;
    }

    function ensureFrame() {
        if (frame && document.body.contains(frame)) return frame;

        frame = document.createElement("div");
        frame.id = FRAME_ID;
        frame.className = "pp12-transform-frame";
        frame.style.display = "none";

        HANDLE_NAMES.forEach(function (name) {
            const h = document.createElement("div");
            h.className = "pp12-resize-handle " + name;
            h.dataset.handle = name;

            h.addEventListener("pointerdown", beginResize);

            frame.appendChild(h);
        });

        const badge = document.createElement("div");
        badge.className = "pp12-selection-badge";
        badge.id = "pp12SelectionBadge";
        frame.appendChild(badge);

        document.body.appendChild(frame);

        return frame;
    }

    function rect(el) {
        if (!el) return null;
        const r = el.getBoundingClientRect();

        if (!r.width || !r.height) return null;

        return {
            left: r.left,
            top: r.top,
            width: r.width,
            height: r.height
        };
    }

    function positionFrame() {
        if (!activeObject || !document.body.contains(activeObject)) {
            hideFrame();
            return;
        }

        const r = rect(activeObject);
        if (!r) {
            hideFrame();
            return;
        }

        const f = ensureFrame();

        f.style.display = "block";
        f.style.left = r.left + "px";
        f.style.top = r.top + "px";
        f.style.width = r.width + "px";
        f.style.height = r.height + "px";

        const badge = document.getElementById("pp12SelectionBadge");
        if (badge) {
            badge.textContent = objectType(activeObject);
        }
    }

    function hideFrame() {
        if (frame) frame.style.display = "none";
    }

    function clearSelectionVisuals() {
        findAnnotationObjects().forEach(function (el) {
            el.classList.remove("pp12-object-selected");
        });
    }

    function selectObject(el) {
        if (!el) return;

        activeObject = el;

        clearSelectionVisuals();
        el.classList.add("pp12-object-selected");

        positionFrame();
        refreshManager();

        /*
         * If the original #12.1 editor exposes its internal
         * selection hooks, use them without depending on them.
         */
        try {
            if (typeof window.pp12SelectAnnotation === "function") {
                window.pp12SelectAnnotation(el);
            }
        } catch (_) {}
    }

    function selectById(id) {
        const objects = findAnnotationObjects();

        const found = objects.find(function (el, index) {
            return objectId(el, index) === id;
        });

        if (found) {
            selectObject(found);
        }
    }

    function deselect() {
        activeObject = null;
        clearSelectionVisuals();
        hideFrame();
        refreshManager();
    }

    function refreshManager() {
        const m = ensureManager();
        if (!m) return;

        const list = m.querySelector("#pp12ObjectList");
        const count = m.querySelector("#pp12ObjectCount");

        if (!list) return;

        const objects = findAnnotationObjects();

        if (count) count.textContent = String(objects.length);

        list.innerHTML = "";

        if (!objects.length) {
            list.innerHTML = `
                <div class="pp12-object-empty">
                    No annotations on this page
                </div>
            `;
            return;
        }

        objects.forEach(function (el, index) {
            const type = objectType(el);
            const id = objectId(el, index);

            const row = document.createElement("div");
            row.className = "pp12-object-row" +
                (el === activeObject ? " selected" : "");

            row.dataset.objectId = id;

            row.innerHTML = `
                <div class="pp12-object-icon">${objectIcon(type)}</div>
                <div class="pp12-object-name">${type} ${index + 1}</div>
                <div class="pp12-object-page">P</div>
            `;

            list.appendChild(row);
        });
    }

    function beginResize(event) {
        event.preventDefault();
        event.stopPropagation();

        if (!activeObject) return;

        const handle = event.currentTarget.dataset.handle;
        const r = rect(activeObject);

        if (!r) return;

        resizeState = {
            handle: handle,
            startX: event.clientX,
            startY: event.clientY,
            startRect: r,
            originalLeft: parseFloat(activeObject.style.left) || 0,
            originalTop: parseFloat(activeObject.style.top) || 0,
            originalWidth: parseFloat(activeObject.style.width) || 0,
            originalHeight: parseFloat(activeObject.style.height) || 0
        };

        try {
            event.currentTarget.setPointerCapture(event.pointerId);
        } catch (_) {}

        window.addEventListener("pointermove", resizeMove);
        window.addEventListener("pointerup", endResize, { once: true });
    }

    function resizeMove(event) {
        if (!resizeState || !activeObject) return;

        const s = resizeState;

        const dx = event.clientX - s.startX;
        const dy = event.clientY - s.startY;

        let left = s.startRect.left;
        let top = s.startRect.top;
        let width = s.startRect.width;
        let height = s.startRect.height;

        const minSize = 12;

        if (s.handle.includes("e")) {
            width = Math.max(minSize, s.startRect.width + dx);
        }

        if (s.handle.includes("w")) {
            width = Math.max(minSize, s.startRect.width - dx);
            left = s.startRect.left + dx;
        }

        if (s.handle.includes("s")) {
            height = Math.max(minSize, s.startRect.height + dy);
        }

        if (s.handle.includes("n")) {
            height = Math.max(minSize, s.startRect.height - dy);
            top = s.startRect.top + dy;
        }

        /*
         * Resize in screen coordinates first. The existing
         * editor remains responsible for PDF-coordinate export.
         */
        activeObject.style.position = "absolute";

        const parent = activeObject.offsetParent;
        if (parent) {
            const pr = parent.getBoundingClientRect();

            activeObject.style.left = (left - pr.left) + "px";
            activeObject.style.top = (top - pr.top) + "px";
        }

        activeObject.style.width = width + "px";
        activeObject.style.height = height + "px";

        positionFrame();
    }

    function endResize() {
        window.removeEventListener("pointermove", resizeMove);

        if (!resizeState) return;

        resizeState = null;

        /*
         * Give the underlying editor an opportunity to record
         * the transformed object in its undo history.
         */
        try {
            if (typeof window.pp12CommitAnnotationTransform === "function") {
                window.pp12CommitAnnotationTransform(activeObject);
            }
        } catch (_) {}

        positionFrame();
        refreshManager();
    }

    function runObjectAction(action) {
        if (!activeObject) return;

        if (action === "delete") {
            deleteActive();
            return;
        }

        if (action === "duplicate") {
            duplicateActive();
            return;
        }

        if (action === "front") {
            bringForward();
            return;
        }

        if (action === "back") {
            sendBackward();
            return;
        }
    }

    function deleteActive() {
        if (!activeObject) return;

        const target = activeObject;

        /*
         * Prefer existing editor delete implementation if exposed.
         */
        try {
            if (typeof window.pp12DeleteAnnotation === "function") {
                window.pp12DeleteAnnotation(target);
                deselect();
                refreshManager();
                return;
            }
        } catch (_) {}

        target.remove();

        activeObject = null;
        hideFrame();
        refreshManager();
    }

    function duplicateActive() {
        if (!activeObject) return;

        const clone = activeObject.cloneNode(true);

        /*
         * New object id.
         */
        const newId =
            "annotation-" +
            Date.now().toString(36) +
            "-" +
            Math.random().toString(36).slice(2, 8);

        clone.dataset.annotationId = newId;
        clone.dataset.objectId = newId;

        const currentLeft = parseFloat(activeObject.style.left) || 0;
        const currentTop = parseFloat(activeObject.style.top) || 0;

        clone.style.left = (currentLeft + 12) + "px";
        clone.style.top = (currentTop + 12) + "px";

        activeObject.parentNode.insertBefore(
            clone,
            activeObject.nextSibling
        );

        selectObject(clone);
        refreshManager();
    }

    function bringForward() {
        if (!activeObject || !activeObject.parentNode) return;

        const parent = activeObject.parentNode;

        if (activeObject.nextElementSibling) {
            parent.insertBefore(
                activeObject.nextElementSibling,
                activeObject
            );
        } else {
            parent.appendChild(activeObject);
        }

        refreshManager();
        positionFrame();
    }

    function sendBackward() {
        if (!activeObject || !activeObject.parentNode) return;

        const parent = activeObject.parentNode;

        if (activeObject.previousElementSibling) {
            parent.insertBefore(
                activeObject,
                activeObject.previousElementSibling
            );
        }

        refreshManager();
        positionFrame();
    }

    function moveByKeyboard(dx, dy) {
        if (!activeObject) return;

        const left = parseFloat(activeObject.style.left) || 0;
        const top = parseFloat(activeObject.style.top) || 0;

        activeObject.style.left = (left + dx) + "px";
        activeObject.style.top = (top + dy) + "px";

        positionFrame();
    }

    function keyboard(event) {
        if (!activeObject) return;

        /*
         * Do not hijack normal typing.
         */
        const tag = (event.target && event.target.tagName || "").toLowerCase();

        if (
            tag === "input" ||
            tag === "textarea" ||
            tag === "select" ||
            event.target.isContentEditable
        ) {
            return;
        }

        const speed = event.shiftKey ? 10 : 1;

        if (event.key === "Delete" || event.key === "Backspace") {
            event.preventDefault();
            deleteActive();
            return;
        }

        if (event.key === "Escape") {
            event.preventDefault();
            deselect();
            return;
        }

        if (event.key === "ArrowLeft") {
            event.preventDefault();
            moveByKeyboard(-speed, 0);
            return;
        }

        if (event.key === "ArrowRight") {
            event.preventDefault();
            moveByKeyboard(speed, 0);
            return;
        }

        if (event.key === "ArrowUp") {
            event.preventDefault();
            moveByKeyboard(0, -speed);
            return;
        }

        if (event.key === "ArrowDown") {
            event.preventDefault();
            moveByKeyboard(0, speed);
            return;
        }
    }

    function canvasClick(event) {
        const target = event.target.closest &&
            event.target.closest(
                ".pp12-annotation-object, .pp12-annotation, [data-annotation-id], [data-annotation-index]"
            );

        if (!target) {
            return;
        }

        if (target.id === FRAME_ID ||
            target.closest("#" + FRAME_ID)) {
            return;
        }

        selectObject(target);
    }

    function installObserver() {
        const root = studio();

        if (!root) return;

        if (observer) observer.disconnect();

        observer = new MutationObserver(function () {
            refreshManager();

            if (
                activeObject &&
                !document.body.contains(activeObject)
            ) {
                activeObject = null;
                hideFrame();
            } else {
                positionFrame();
            }
        });

        observer.observe(root, {
            subtree: true,
            childList: true,
            attributes: true,
            attributeFilter: [
                "style",
                "data-annotation-id",
                "data-object-id",
                "data-type"
            ]
        });
    }

    function install() {
        const root = studio();

        if (!root) return false;

        ensureManager();
        ensureFrame();

        root.addEventListener("click", canvasClick);

        window.addEventListener("resize", positionFrame);
        window.addEventListener("scroll", positionFrame, true);
        window.addEventListener("keydown", keyboard);

        installObserver();

        refreshManager();

        return true;
    }

    function boot() {
        if (install()) return;

        setTimeout(boot, 400);
    }

    /*
     * Public helpers for compatibility with the existing
     * #12.1 annotation editor.
     */
    window.pp12ObjectManager = {
        refresh: refreshManager,
        select: selectObject,
        deselect: deselect,
        deleteSelected: deleteActive,
        duplicateSelected: duplicateActive,
        bringForward: bringForward,
        sendBackward: sendBackward
    };

    /*
     * Run after the existing #12.1 script.
     */
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }

})();
</script>
"""

# Remove old #12.2 block if re-running.
if js_marker in html:
    html = re.sub(
        r'<script id="upgrade-12-2-annotation-object-manager-js">.*?</script>',
        "",
        html,
        flags=re.S
    )

# Put JS immediately before </body>.
body_anchor = "</body>"

if body_anchor in html:
    html = html.replace(
        body_anchor,
        js_block + "\n" + body_anchor,
        1
    )
else:
    html += "\n" + js_block

# ============================================================
# FRONTEND WRITE
# ============================================================

HTML.write_text(html, encoding="utf-8")

print()
print("Frontend #12.2 object manager installed.")
print()

# ============================================================
# VERIFICATION
# ============================================================

print("==============================================")
print("  #12.2 FILE MARKER CHECK")
print("==============================================")
print()

html_check = HTML.read_text(encoding="utf-8")
backend_check = APP.read_text(encoding="utf-8")

checks = [
    (
        "Backend #12.2 marker",
        "UPGRADE_12_2_ANNOTATION_OBJECT_MANAGER_BACKEND" in backend_check
    ),
    (
        "Object Manager CSS",
        'upgrade-12-2-annotation-object-manager-css' in html_check
    ),
    (
        "Object Manager JS",
        'upgrade-12-2-annotation-object-manager-js' in html_check
    ),
    (
        "Object Manager UI",
        'pp12AnnotationObjectManager' in html_check
    ),
    (
        "Resize frame",
        'pp12AnnotationTransformFrame' in html_check
    ),
    (
        "Resize handles",
        'pp12-resize-handle' in html_check
    ),
    (
        "Duplicate action",
        'data-object-action="duplicate"' in html_check
    ),
    (
        "Bring forward",
        'data-object-action="front"' in html_check
    ),
    (
        "Send backward",
        'data-object-action="back"' in html_check
    ),
    (
        "Keyboard movement",
        'ArrowLeft' in html_check and 'ArrowRight' in html_check
    ),
]

failed = False

for name, ok in checks:
    print(("OK  " if ok else "FAIL") + name)
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
# ROUTE CHECK
# ============================================================

print()
print("==============================================")
print("  ROUTE CHECK")
print("==============================================")
print()

try:
    import ast

    tree = ast.parse(backend_check)

    routes = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                text = ast.unparse(dec)

                if (
                    "app." in text and
                    (
                        "get(" in text or
                        "post(" in text or
                        "put(" in text or
                        "delete(" in text or
                        "patch(" in text
                    )
                ):
                    routes.append(text)

    print("Detected route decorators:", len(routes))

    for required in [
        '/api/annotation-page',
        '/api/annotate',
        '/api/merge'
    ]:
        found = required in backend_check
        print(
            f"{required} => " +
            ("OK" if found else "MISSING")
        )

        if not found:
            failed = True

except Exception as exc:
    print("WARNING: Route AST check failed:")
    print(exc)

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
    print("  #12.2 INSTALLATION FAILED")
    print("==============================================")
    print()
    print("DO NOT CONTINUE.")
    print("Paste the COMPLETE ERROR output here.")
    sys.exit(1)

print("==============================================")
print("  #12.2 COMPLETE")
print("==============================================")
print()
print("Professional Annotation Object Manager installed.")
print()
print("Added:")
print("  - Select")
print("  - Move")
print("  - Resize")
print("  - Delete")
print("  - Object manager")
print("  - Object selection state")
print("  - Bring forward")
print("  - Send backward")
print("  - Duplicate")
print("  - Keyboard movement")
print("  - Delete / Backspace")
print("  - Escape deselect")
print("  - Resize handles")
print()
print("Existing native PDF export preserved.")
print("No persistent document database added.")
print()
print("IMPORTANT:")
print("If ANY ERROR appeared above, do not continue.")
print("Paste the complete ERROR output here.")
print()

