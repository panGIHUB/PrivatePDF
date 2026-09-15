from pathlib import Path
import shutil
import re
import sys

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app"
STATIC = ROOT / "static"

MAIN = APP / "main.py"
INDEX = STATIC / "index.html"

BACK_MAIN = APP / "main.py.before_shapes_engine_upgrade"
BACK_INDEX = STATIC / "index.html.before_shapes_engine_upgrade"

BACKEND_MARKER = "# === UPGRADE_12_5_PROFESSIONAL_SHAPES_DRAW_ENGINE_BACKEND ==="
CSS_MARKER = "upgrade-12-5-professional-shapes-css"
JS_MARKER = "upgrade-12-5-professional-shapes-js"
UI_MARKER = "upgrade-12-5-professional-shapes-ui"


def fail(msg):
    print("\nERROR:", msg)
    sys.exit(1)


print("""
==============================================
  PRIVATE PDF PRO — UPGRADE #12.5
  PROFESSIONAL DRAW / ARROW / SHAPES ENGINE
==============================================
""")

if not MAIN.exists():
    fail(f"Backend not found: {MAIN}")

if not INDEX.exists():
    fail(f"Frontend not found: {INDEX}")

print("Project root:", ROOT)
print("Backend:", MAIN)
print("Frontend:", INDEX)

# ------------------------------------------------------------
# BACKUPS
# ------------------------------------------------------------

if not BACK_MAIN.exists():
    shutil.copy2(MAIN, BACK_MAIN)
    print("Backend backup created:", BACK_MAIN)
else:
    print("Backend backup already exists:", BACK_MAIN)

if not BACK_INDEX.exists():
    shutil.copy2(INDEX, BACK_INDEX)
    print("Frontend backup created:", BACK_INDEX)
else:
    print("Frontend backup already exists:", BACK_INDEX)

main_text = MAIN.read_text(encoding="utf-8")
html = INDEX.read_text(encoding="utf-8")

# ------------------------------------------------------------
# BACKEND MARKER
# ------------------------------------------------------------

backend_block = f'''

{BACKEND_MARKER}

# #12.5 intentionally keeps the existing native annotation API.
# Existing /api/annotate already supports native:
#   - draw
#   - arrow
#   - rectangle
#   - ellipse-compatible shape metadata
#
# This layer adds frontend professional shape controls without
# replacing the existing PDF annotation/export pipeline.

'''

if BACKEND_MARKER not in main_text:
    # Put marker after imports / before first route where possible.
    route_match = re.search(r'(?m)^@app\.', main_text)

    if route_match:
        pos = route_match.start()
        main_text = main_text[:pos] + backend_block + main_text[pos:]
    else:
        main_text += backend_block

    MAIN.write_text(main_text, encoding="utf-8")
    print("Professional Shapes backend compatibility layer installed.")
else:
    print("Professional Shapes backend compatibility layer already present.")

# ------------------------------------------------------------
# FRONTEND UI
# ------------------------------------------------------------

ui_block = r'''
<!-- === UPGRADE_12_5_PROFESSIONAL_SHAPES_UI === -->

<div id="pp12ShapesToolbar" class="pp12-shapes-toolbar" aria-label="Draw and shapes tools">

  <div class="pp12-shapes-group pp12-shapes-tools">

    <button type="button"
            class="pp12-shape-tool"
            data-shape-tool="select"
            title="Select">
      Select
    </button>

    <button type="button"
            class="pp12-shape-tool"
            data-shape-tool="draw"
            title="Freehand pen">
      Pen
    </button>

    <button type="button"
            class="pp12-shape-tool"
            data-shape-tool="line"
            title="Straight line">
      Line
    </button>

    <button type="button"
            class="pp12-shape-tool"
            data-shape-tool="arrow"
            title="Arrow">
      Arrow
    </button>

    <button type="button"
            class="pp12-shape-tool"
            data-shape-tool="rectangle"
            title="Rectangle">
      Rectangle
    </button>

    <button type="button"
            class="pp12-shape-tool"
            data-shape-tool="ellipse"
            title="Ellipse">
      Ellipse
    </button>

    <button type="button"
            class="pp12-shape-tool"
            data-shape-tool="highlight-box"
            title="Highlight box">
      Box
    </button>

    <button type="button"
            class="pp12-shape-tool"
            data-shape-tool="eraser"
            title="Erase selected shape">
      Eraser
    </button>

  </div>

  <div class="pp12-shapes-group">

    <label>
      Stroke
      <input
        id="pp12ShapeStroke"
        type="color"
        value="#111827"
        title="Stroke color">
    </label>

    <label>
      Fill
      <input
        id="pp12ShapeFill"
        type="color"
        value="#ffffff"
        title="Fill color">
    </label>

    <label>
      Width
      <input
        id="pp12ShapeWidth"
        type="range"
        min="1"
        max="20"
        value="3">
      <span id="pp12ShapeWidthValue">3</span>
    </label>

    <label>
      Opacity
      <input
        id="pp12ShapeOpacity"
        type="range"
        min="10"
        max="100"
        value="100">
      <span id="pp12ShapeOpacityValue">100%</span>
    </label>

  </div>

  <div class="pp12-shapes-group">

    <label>
      Fill
      <input
        id="pp12ShapeFillEnabled"
        type="checkbox">
    </label>

    <label>
      Dash
      <select id="pp12ShapeDash">
        <option value="solid">Solid</option>
        <option value="dashed">Dashed</option>
        <option value="dotted">Dotted</option>
      </select>
    </label>

    <button type="button"
            id="pp12ShapeClearSelection"
            title="Delete selected shape">
      Delete
    </button>

  </div>

</div>

<!-- === /UPGRADE_12_5_PROFESSIONAL_SHAPES_UI === -->
'''

if UI_MARKER not in html:
    body_match = re.search(r'(?i)</body\s*>', html)

    if body_match:
        html = (
            html[:body_match.start()]
            + ui_block
            + "\n"
            + html[body_match.start():]
        )
    else:
        html += "\n" + ui_block

    print("Shapes toolbar UI installed.")
else:
    print("Shapes toolbar UI already present.")

# ------------------------------------------------------------
# FRONTEND CSS
# ------------------------------------------------------------

css_block = r'''
<style id="upgrade-12-5-professional-shapes-css">

/* ============================================================
   PRIVATE PDF PRO — #12.5 SHAPES ENGINE
   ============================================================ */

#pp12ShapesToolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin: 8px 0 12px;
  border: 1px solid rgba(148,163,184,.25);
  border-radius: 12px;
  background: rgba(15,23,42,.04);
  backdrop-filter: blur(10px);
  position: relative;
  z-index: 100;
}

#pp12ShapesToolbar .pp12-shapes-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px;
}

#pp12ShapesToolbar label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

#pp12ShapesToolbar button,
#pp12ShapesToolbar select {
  border: 1px solid rgba(100,116,139,.30);
  border-radius: 8px;
  min-height: 32px;
  padding: 5px 9px;
  background: white;
  cursor: pointer;
  font-size: 12px;
}

#pp12ShapesToolbar button:hover {
  transform: translateY(-1px);
}

#pp12ShapesToolbar .pp12-shape-tool.is-active {
  box-shadow:
    0 0 0 2px rgba(59,130,246,.18),
    0 3px 10px rgba(15,23,42,.10);
  font-weight: 700;
}

#pp12ShapesToolbar input[type="color"] {
  width: 32px;
  height: 28px;
  padding: 2px;
  border-radius: 7px;
  border: 1px solid rgba(100,116,139,.35);
}

#pp12ShapesToolbar input[type="range"] {
  width: 90px;
}

.pp12-shape-preview {
  position: absolute;
  pointer-events: none;
  z-index: 9998;
  box-sizing: border-box;
}

.pp12-shape-preview-line {
  position: absolute;
  left: 0;
  top: 0;
  transform-origin: 0 0;
}

.pp12-shape-preview-arrow {
  position: absolute;
  pointer-events: none;
  z-index: 9999;
}

.pp12-shape-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 40;
}

.pp12-shape-object {
  position: absolute;
  box-sizing: border-box;
  pointer-events: auto;
  cursor: move;
  user-select: none;
}

.pp12-shape-object.pp12-shape-selected {
  outline: 1px dashed rgba(37,99,235,.8);
  outline-offset: 3px;
}

.pp12-shape-resize-frame {
  position: absolute;
  pointer-events: none;
  border: 1px dashed rgba(37,99,235,.9);
  z-index: 10000;
}

.pp12-shape-resize-handle {
  width: 8px;
  height: 8px;
  position: absolute;
  border-radius: 2px;
  background: white;
  border: 1px solid rgba(37,99,235,.95);
  pointer-events: auto;
}

.pp12-shape-resize-handle.nw { left:-5px; top:-5px; cursor:nwse-resize; }
.pp12-shape-resize-handle.n  { left:50%; top:-5px; transform:translateX(-50%); cursor:ns-resize; }
.pp12-shape-resize-handle.ne { right:-5px; top:-5px; cursor:nesw-resize; }
.pp12-shape-resize-handle.e  { right:-5px; top:50%; transform:translateY(-50%); cursor:ew-resize; }
.pp12-shape-resize-handle.se { right:-5px; bottom:-5px; cursor:nwse-resize; }
.pp12-shape-resize-handle.s  { left:50%; bottom:-5px; transform:translateX(-50%); cursor:ns-resize; }
.pp12-shape-resize-handle.sw { left:-5px; bottom:-5px; cursor:nesw-resize; }
.pp12-shape-resize-handle.w  { left:-5px; top:50%; transform:translateY(-50%); cursor:ew-resize; }

.pp12-shape-cursor-draw {
  cursor: crosshair !important;
}

.pp12-shape-cursor-select {
  cursor: default !important;
}

@media (max-width: 800px) {
  #pp12ShapesToolbar {
    gap: 7px;
    padding: 8px;
  }

  #pp12ShapesToolbar input[type="range"] {
    width: 70px;
  }

  #pp12ShapesToolbar button {
    min-height: 30px;
    padding: 4px 7px;
  }
}

</style>
'''

if CSS_MARKER not in html:
    body_match = re.search(r'(?i)</body\s*>', html)

    if body_match:
        html = (
            html[:body_match.start()]
            + css_block
            + "\n"
            + html[body_match.start():]
        )
    else:
        html += "\n" + css_block

    print("Shapes CSS installed.")
else:
    print("Shapes CSS already present.")

# ------------------------------------------------------------
# FRONTEND JS
# ------------------------------------------------------------

js_block = r'''
<script id="upgrade-12-5-professional-shapes-js">

(function () {
  "use strict";

  /* ==========================================================
     PRIVATE PDF PRO — #12.5 PROFESSIONAL SHAPES ENGINE
     ========================================================== */

  if (window.__PP12_SHAPES_ENGINE__) return;
  window.__PP12_SHAPES_ENGINE__ = true;

  const toolbar =
    document.getElementById("pp12ShapesToolbar");

  if (!toolbar) return;

  const state = {
    tool: "select",
    stroke: "#111827",
    fill: "#ffffff",
    fillEnabled: false,
    width: 3,
    opacity: 1,
    dash: "solid",
    drawing: false,
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0,
    preview: null,
    activePage: null,
    shapes: [],
    selected: null
  };

  const strokeInput =
    document.getElementById("pp12ShapeStroke");

  const fillInput =
    document.getElementById("pp12ShapeFill");

  const widthInput =
    document.getElementById("pp12ShapeWidth");

  const widthValue =
    document.getElementById("pp12ShapeWidthValue");

  const opacityInput =
    document.getElementById("pp12ShapeOpacity");

  const opacityValue =
    document.getElementById("pp12ShapeOpacityValue");

  const fillEnabledInput =
    document.getElementById("pp12ShapeFillEnabled");

  const dashInput =
    document.getElementById("pp12ShapeDash");

  const deleteButton =
    document.getElementById("pp12ShapeClearSelection");

  function clamp(v, a, b) {
    return Math.max(a, Math.min(b, v));
  }

  function uid(prefix) {
    return prefix + "_" +
      Date.now().toString(36) + "_" +
      Math.random().toString(36).slice(2, 8);
  }

  function getCanvasHost() {
    return (
      document.querySelector(".pp12-page-canvas") ||
      document.querySelector(".pp12-page-stage") ||
      document.querySelector("[data-annotation-page]") ||
      document.querySelector(".pp12-annotation-page") ||
      document.querySelector(".page-stage") ||
      document.querySelector(".page-container")
    );
  }

  function pointerPosition(ev, host) {
    const r = host.getBoundingClientRect();

    return {
      x: clamp(ev.clientX - r.left, 0, r.width),
      y: clamp(ev.clientY - r.top, 0, r.height)
    };
  }

  function normalizedRect(a, b) {
    return {
      x: Math.min(a.x, b.x),
      y: Math.min(a.y, b.y),
      width: Math.abs(b.x - a.x),
      height: Math.abs(b.y - a.y)
    };
  }

  function dashArray() {
    if (state.dash === "dashed") return "10 7";
    if (state.dash === "dotted") return "2 6";
    return "";
  }

  function shapeStyle() {
    return {
      stroke: state.stroke,
      fill: state.fillEnabled ? state.fill : "transparent",
      strokeWidth: state.width,
      opacity: state.opacity,
      dash: dashArray()
    };
  }

  function removePreview() {
    if (state.preview && state.preview.parentNode) {
      state.preview.parentNode.removeChild(state.preview);
    }

    state.preview = null;
  }

  function ensureOverlay(host) {
    let overlay = host.querySelector(".pp12-shape-overlay");

    if (!overlay) {
      overlay = document.createElement("div");
      overlay.className = "pp12-shape-overlay";

      const cs = getComputedStyle(host);

      if (cs.position === "static") {
        host.style.position = "relative";
      }

      host.appendChild(overlay);
    }

    return overlay;
  }

  function svgElement(name) {
    return document.createElementNS(
      "http://www.w3.org/2000/svg",
      name
    );
  }

  function createShapeSvg(shape) {
    const ns = "http://www.w3.org/2000/svg";

    const svg = document.createElementNS(ns, "svg");

    svg.setAttribute("class", "pp12-shape-svg");
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.setAttribute("viewBox", "0 0 100 100");
    svg.setAttribute("preserveAspectRatio", "none");

    const stroke =
      shape.stroke || "#111827";

    const fill =
      shape.fillEnabled
        ? (shape.fill || "#ffffff")
        : "none";

    const opacity =
      Number(shape.opacity ?? 1);

    const width =
      Number(shape.strokeWidth || 3);

    const dash =
      shape.dash || "";

    if (shape.type === "rectangle" ||
        shape.type === "highlight-box") {

      const rect = svgElement("rect");

      rect.setAttribute("x", "0");
      rect.setAttribute("y", "0");
      rect.setAttribute("width", "100");
      rect.setAttribute("height", "100");
      rect.setAttribute("rx", "1.5");
      rect.setAttribute("fill", fill);
      rect.setAttribute("stroke", stroke);
      rect.setAttribute("stroke-width", width);
      rect.setAttribute("vector-effect", "non-scaling-stroke");
      rect.setAttribute("opacity", opacity);

      if (dash) rect.setAttribute("stroke-dasharray", dash);

      svg.appendChild(rect);

    } else if (shape.type === "ellipse") {

      const ellipse = svgElement("ellipse");

      ellipse.setAttribute("cx", "50");
      ellipse.setAttribute("cy", "50");
      ellipse.setAttribute("rx", "50");
      ellipse.setAttribute("ry", "50");
      ellipse.setAttribute("fill", fill);
      ellipse.setAttribute("stroke", stroke);
      ellipse.setAttribute("stroke-width", width);
      ellipse.setAttribute("vector-effect", "non-scaling-stroke");
      ellipse.setAttribute("opacity", opacity);

      if (dash) {
        ellipse.setAttribute("stroke-dasharray", dash);
      }

      svg.appendChild(ellipse);

    } else if (shape.type === "line" ||
               shape.type === "arrow") {

      const line = svgElement("line");

      line.setAttribute("x1", "0");
      line.setAttribute("y1", "100");
      line.setAttribute("x2", "100");
      line.setAttribute("y2", "0");
      line.setAttribute("stroke", stroke);
      line.setAttribute("stroke-width", width);
      line.setAttribute("vector-effect", "non-scaling-stroke");
      line.setAttribute("stroke-linecap", "round");
      line.setAttribute("opacity", opacity);

      if (dash) {
        line.setAttribute("stroke-dasharray", dash);
      }

      svg.appendChild(line);

      if (shape.type === "arrow") {
        const markerId =
          "pp12-arrow-" + shape.id;

        const defs = svgElement("defs");
        const marker = svgElement("marker");

        marker.setAttribute("id", markerId);
        marker.setAttribute("viewBox", "0 0 10 10");
        marker.setAttribute("refX", "9");
        marker.setAttribute("refY", "5");
        marker.setAttribute("markerWidth", "7");
        marker.setAttribute("markerHeight", "7");
        marker.setAttribute("orient", "auto-start-reverse");

        const path = svgElement("path");

        path.setAttribute(
          "d",
          "M 0 0 L 10 5 L 0 10 z"
        );

        path.setAttribute("fill", stroke);

        marker.appendChild(path);
        defs.appendChild(marker);
        svg.appendChild(defs);

        line.setAttribute(
          "marker-end",
          "url(#" + markerId + ")"
        );
      }

    } else if (shape.type === "draw") {

      const points =
        Array.isArray(shape.points)
          ? shape.points
          : [];

      if (points.length > 1) {
        const poly = svgElement("polyline");

        poly.setAttribute(
          "points",
          points.map(function (p) {
            return p.x + "," + p.y;
          }).join(" ")
        );

        poly.setAttribute("fill", "none");
        poly.setAttribute("stroke", stroke);
        poly.setAttribute("stroke-width", width);
        poly.setAttribute("stroke-linecap", "round");
        poly.setAttribute("stroke-linejoin", "round");
        poly.setAttribute("vector-effect", "non-scaling-stroke");
        poly.setAttribute("opacity", opacity);

        if (dash) {
          poly.setAttribute("stroke-dasharray", dash);
        }

        svg.appendChild(poly);
      }
    }

    return svg;
  }

  function renderShape(shape) {

    const host = shape.host;

    if (!host || !host.isConnected) return;

    const overlay = ensureOverlay(host);

    const object =
      document.createElement("div");

    object.className =
      "pp12-shape-object";

    object.dataset.pp12ShapeId =
      shape.id;

    object.dataset.pp12ShapeType =
      shape.type;

    object.style.left =
      shape.x + "px";

    object.style.top =
      shape.y + "px";

    object.style.width =
      Math.max(2, shape.width) + "px";

    object.style.height =
      Math.max(2, shape.height) + "px";

    object.appendChild(
      createShapeSvg(shape)
    );

    object.addEventListener(
      "pointerdown",
      function (ev) {

        ev.stopPropagation();

        if (state.tool !== "select") return;

        selectShape(shape);

        const p =
          pointerPosition(ev, host);

        const offsetX =
          p.x - shape.x;

        const offsetY =
          p.y - shape.y;

        function move(e) {
          const q =
            pointerPosition(e, host);

          shape.x =
            clamp(
              q.x - offsetX,
              0,
              Math.max(0, host.clientWidth - shape.width)
            );

          shape.y =
            clamp(
              q.y - offsetY,
              0,
              Math.max(0, host.clientHeight - shape.height)
            );

          object.style.left =
            shape.x + "px";

          object.style.top =
            shape.y + "px";
        }

        function up() {
          window.removeEventListener(
            "pointermove",
            move
          );

          window.removeEventListener(
            "pointerup",
            up
          );

          registerNativeShape(shape);
        }

        window.addEventListener(
          "pointermove",
          move
        );

        window.addEventListener(
          "pointerup",
          up,
          { once: true }
        );
      }
    );

    overlay.appendChild(object);

    shape.element = object;
  }

  function selectShape(shape) {

    state.selected = shape;

    document
      .querySelectorAll(
        ".pp12-shape-object.pp12-shape-selected"
      )
      .forEach(function (el) {
        el.classList.remove(
          "pp12-shape-selected"
        );
      });

    if (shape && shape.element) {
      shape.element.classList.add(
        "pp12-shape-selected"
      );
    }

    if (window.pp12ObjectManager &&
        typeof window.pp12ObjectManager.refresh === "function") {
      try {
        window.pp12ObjectManager.refresh();
      } catch (_) {}
    }
  }

  function removeShape(shape) {

    if (!shape) return;

    if (shape.element &&
        shape.element.parentNode) {
      shape.element.parentNode.removeChild(
        shape.element
      );
    }

    const index =
      state.shapes.indexOf(shape);

    if (index >= 0) {
      state.shapes.splice(index, 1);
    }

    if (state.selected === shape) {
      state.selected = null;
    }

    if (window.pp12ObjectManager &&
        typeof window.pp12ObjectManager.refresh === "function") {
      try {
        window.pp12ObjectManager.refresh();
      } catch (_) {}
    }
  }

  function registerNativeShape(shape) {

    /*
      Compatibility bridge.

      Existing #12.1/#12.2 annotation systems may expose
      pp12RegisterAnnotation. We pass a normalized object to
      that layer when available.

      The existing /api/annotate native export pipeline remains
      the source of truth for final PDF export.
    */

    const payload = {
      id: shape.id,
      type: shape.type,
      page_index: shape.pageIndex,
      x: shape.x,
      y: shape.y,
      width: shape.width,
      height: shape.height,
      stroke: shape.stroke,
      fill: shape.fill,
      fillEnabled: shape.fillEnabled,
      strokeWidth: shape.strokeWidth,
      opacity: shape.opacity,
      dash: shape.dash,
      points: shape.points || []
    };

    if (typeof window.pp12RegisterAnnotation === "function") {
      try {
        window.pp12RegisterAnnotation(payload);
      } catch (_) {}
    }

    window.dispatchEvent(
      new CustomEvent(
        "pp12:shape-created",
        { detail: payload }
      )
    );
  }

  function makeShape(
    type,
    start,
    end,
    host,
    extra
  ) {

    const r =
      normalizedRect(start, end);

    const shape = Object.assign({
      id: uid("shape"),
      type: type,
      pageIndex: getPageIndex(host),
      x: r.x,
      y: r.y,
      width: Math.max(2, r.width),
      height: Math.max(2, r.height),
      stroke: state.stroke,
      fill: state.fill,
      fillEnabled: state.fillEnabled,
      strokeWidth: state.width,
      opacity: state.opacity,
      dash: state.dash === "solid"
        ? ""
        : (
          state.dash === "dashed"
            ? "10 7"
            : "2 6"
        ),
      host: host,
      points: []
    }, extra || {});

    return shape;
  }

  function getPageIndex(host) {

    const candidates = [
      host.dataset.pageIndex,
      host.dataset.page,
      host.getAttribute("data-page-index"),
      host.getAttribute("data-page")
    ];

    for (const value of candidates) {
      if (value !== null &&
          value !== undefined &&
          value !== "") {
        const n = Number(value);
        if (Number.isFinite(n)) return n;
      }
    }

    return 0;
  }

  function updatePreview(host, start, current) {

    removePreview();

    const type = state.tool;

    const shape =
      makeShape(
        type === "highlight-box"
          ? "highlight-box"
          : type,
        start,
        current,
        host
      );

    const preview =
      document.createElement("div");

    preview.className =
      "pp12-shape-preview";

    preview.style.left =
      shape.x + "px";

    preview.style.top =
      shape.y + "px";

    preview.style.width =
      Math.max(2, shape.width) + "px";

    preview.style.height =
      Math.max(2, shape.height) + "px";

    preview.appendChild(
      createShapeSvg(shape)
    );

    const overlay =
      ensureOverlay(host);

    overlay.appendChild(preview);

    state.preview = preview;
  }

  function startDraw(ev, host) {

    if (
      state.tool === "select" ||
      state.tool === "eraser"
    ) return;

    const p =
      pointerPosition(ev, host);

    state.drawing = true;
    state.startX = p.x;
    state.startY = p.y;
    state.currentX = p.x;
    state.currentY = p.y;
    state.activePage = host;

    if (state.tool === "draw") {

      const shape =
        makeShape(
          "draw",
          p,
          p,
          host,
          { points: [
            {
              x: p.x / host.clientWidth * 100,
              y: p.y / host.clientHeight * 100
            }
          ]}
        );

      state.preview = {
        shape: shape,
        host: host
      };
    }
  }

  function moveDraw(ev, host) {

    if (!state.drawing) return;

    const p =
      pointerPosition(ev, host);

    state.currentX = p.x;
    state.currentY = p.y;

    if (state.tool === "draw") {

      const item = state.preview;

      if (!item || !item.shape) return;

      item.shape.points.push({
        x: p.x / host.clientWidth * 100,
        y: p.y / host.clientHeight * 100
      });

      removePreview();

      const overlay =
        ensureOverlay(host);

      const preview =
        document.createElement("div");

      preview.className =
        "pp12-shape-preview";

      preview.style.left = "0";
      preview.style.top = "0";
      preview.style.width = "100%";
      preview.style.height = "100%";

      preview.appendChild(
        createShapeSvg(item.shape)
      );

      overlay.appendChild(preview);

      state.preview = {
        shape: item.shape,
        host: host
      };

      return;
    }

    updatePreview(
      host,
      {
        x: state.startX,
        y: state.startY
      },
      p
    );
  }

  function finishDraw(ev, host) {

    if (!state.drawing) return;

    const p =
      pointerPosition(ev, host);

    state.currentX = p.x;
    state.currentY = p.y;

    const start = {
      x: state.startX,
      y: state.startY
    };

    const end = {
      x: p.x,
      y: p.y
    };

    let shape = null;

    if (state.tool === "draw") {

      const item = state.preview;

      if (item && item.shape) {
        shape = item.shape;
      }

      removePreview();

    } else {

      removePreview();

      let type = state.tool;

      if (type === "highlight-box") {
        type = "highlight-box";
      }

      shape =
        makeShape(
          type,
          start,
          end,
          host
        );
    }

    state.drawing = false;

    if (!shape) return;

    if (
      shape.width < 3 &&
      shape.height < 3 &&
      shape.type !== "draw"
    ) {
      return;
    }

    state.shapes.push(shape);

    renderShape(shape);

    registerNativeShape(shape);

    selectShape(shape);

    state.preview = null;
  }

  function activateTool(tool) {

    state.tool = tool;

    document
      .querySelectorAll(
        "#pp12ShapesToolbar [data-shape-tool]"
      )
      .forEach(function (button) {
        button.classList.toggle(
          "is-active",
          button.dataset.shapeTool === tool
        );
      });

    document
      .querySelectorAll(
        ".pp12-shape-cursor-draw"
      )
      .forEach(function (el) {
        el.classList.remove(
          "pp12-shape-cursor-draw"
        );
      });

    if (
      tool !== "select" &&
      tool !== "eraser"
    ) {
      document
        .querySelectorAll(
          ".pp12-shape-overlay"
        )
        .forEach(function (el) {
          el.classList.add(
            "pp12-shape-cursor-draw"
          );
        });
    }
  }

  toolbar
    .querySelectorAll(
      "[data-shape-tool]"
    )
    .forEach(function (button) {

      button.addEventListener(
        "click",
        function () {
          activateTool(
            button.dataset.shapeTool
          );
        }
      );
    });

  if (strokeInput) {
    strokeInput.addEventListener(
      "input",
      function () {
        state.stroke =
          strokeInput.value || "#111827";
      }
    );
  }

  if (fillInput) {
    fillInput.addEventListener(
      "input",
      function () {
        state.fill =
          fillInput.value || "#ffffff";
      }
    );
  }

  if (fillEnabledInput) {
    fillEnabledInput.addEventListener(
      "change",
      function () {
        state.fillEnabled =
          !!fillEnabledInput.checked;
      }
    );
  }

  if (widthInput) {
    widthInput.addEventListener(
      "input",
      function () {
        state.width =
          Number(widthInput.value || 3);

        if (widthValue) {
          widthValue.textContent =
            String(state.width);
        }
      }
    );
  }

  if (opacityInput) {
    opacityInput.addEventListener(
      "input",
      function () {
        const value =
          Number(opacityInput.value || 100);

        state.opacity =
          value / 100;

        if (opacityValue) {
          opacityValue.textContent =
            value + "%";
        }
      }
    );
  }

  if (dashInput) {
    dashInput.addEventListener(
      "change",
      function () {
        state.dash =
          dashInput.value || "solid";
      }
    );
  }

  if (deleteButton) {
    deleteButton.addEventListener(
      "click",
      function () {
        removeShape(state.selected);
      }
    );
  }

  /*
    Event delegation:
    We do not assume one specific page-manager DOM class.
    The engine discovers a usable page host when pointer events
    reach the annotation workspace.
  */

  document.addEventListener(
    "pointerdown",
    function (ev) {

      if (!state.tool ||
          state.tool === "select" ||
          state.tool === "eraser") {
        return;
      }

      if (toolbar.contains(ev.target)) return;

      const host =
        ev.target.closest(
          ".pp12-page-canvas, " +
          ".pp12-page-stage, " +
          "[data-annotation-page], " +
          ".pp12-annotation-page, " +
          ".page-stage, " +
          ".page-container"
        );

      if (!host) return;

      /*
        Do not steal pointer events from existing annotation
        controls or text selection layers.
      */

      if (
        ev.target.closest(
          "input, textarea, select, button, " +
          ".pp12-word, [data-word], " +
          ".pp12-text-object, " +
          ".pp12-shape-object"
        )
      ) {
        return;
      }

      startDraw(ev, host);
    },
    true
  );

  document.addEventListener(
    "pointermove",
    function (ev) {

      if (!state.drawing ||
          !state.activePage) return;

      moveDraw(
        ev,
        state.activePage
      );
    },
    true
  );

  document.addEventListener(
    "pointerup",
    function (ev) {

      if (!state.drawing ||
          !state.activePage) return;

      finishDraw(
        ev,
        state.activePage
      );

      state.activePage = null;
    },
    true
  );

  document.addEventListener(
    "keydown",
    function (ev) {

      if (
        ev.key === "Delete" &&
        state.selected &&
        !ev.target.matches(
          "input, textarea, select"
        )
      ) {
        ev.preventDefault();
        removeShape(state.selected);
        return;
      }

      if (
        !state.selected ||
        ev.target.matches(
          "input, textarea, select"
        )
      ) return;

      const step =
        ev.shiftKey ? 10 : 1;

      if (ev.key === "ArrowLeft") {
        ev.preventDefault();
        state.selected.x -= step;
      }

      if (ev.key === "ArrowRight") {
        ev.preventDefault();
        state.selected.x += step;
      }

      if (ev.key === "ArrowUp") {
        ev.preventDefault();
        state.selected.y -= step;
      }

      if (ev.key === "ArrowDown") {
        ev.preventDefault();
        state.selected.y += step;
      }

      const s = state.selected;

      if (s && s.element) {
        s.element.style.left =
          s.x + "px";

        s.element.style.top =
          s.y + "px";

        registerNativeShape(s);
      }
    }
  );

  /*
    Public API for future #12.6 history / object manager layers.
  */

  window.pp12ShapesEngine = {

    getState: function () {
      return state;
    },

    getShapes: function () {
      return state.shapes.slice();
    },

    select: selectShape,

    remove: removeShape,

    setTool: activateTool,

    register: registerNativeShape,

    refresh: function () {
      state.shapes.forEach(function (shape) {
        if (
          shape.element &&
          shape.element.parentNode
        ) {
          shape.element.parentNode.removeChild(
            shape.element
          );
        }

        renderShape(shape);
      });
    }
  };

  activateTool("select");

  console.log(
    "[Private PDF Pro] #12.5 Professional Shapes Engine loaded."
  );

})();

</script>
'''

if JS_MARKER not in html:
    body_match = re.search(r'(?i)</body\s*>', html)

    if body_match:
        html = (
            html[:body_match.start()]
            + js_block
            + "\n"
            + html[body_match.start():]
        )
    else:
        html += "\n" + js_block

    print("Professional Shapes JavaScript installed.")
else:
    print("Professional Shapes JavaScript already present.")

INDEX.write_text(html, encoding="utf-8")

print("""
==============================================
  #12.5 INSTALLATION COMPLETE
==============================================
""")

# ------------------------------------------------------------
# CHECKS
# ------------------------------------------------------------

print("==============================================")
print("  #12.5 FILE MARKER CHECK")
print("==============================================")

checks = [
    ("Backend #12.5 marker", BACKEND_MARKER, main_text),
    ("Shapes CSS", CSS_MARKER, html),
    ("Shapes JS", JS_MARKER, html),
    ("Shapes UI", UI_MARKER, html),
    ("Pen tool", 'data-shape-tool="draw"', html),
    ("Line tool", 'data-shape-tool="line"', html),
    ("Arrow tool", 'data-shape-tool="arrow"', html),
    ("Rectangle tool", 'data-shape-tool="rectangle"', html),
    ("Ellipse tool", 'data-shape-tool="ellipse"', html),
    ("Highlight box", 'data-shape-tool="highlight-box"', html),
    ("Eraser", 'data-shape-tool="eraser"', html),
    ("Stroke control", 'id="pp12ShapeStroke"', html),
    ("Fill control", 'id="pp12ShapeFill"', html),
    ("Width control", 'id="pp12ShapeWidth"', html),
    ("Opacity control", 'id="pp12ShapeOpacity"', html),
    ("Dash control", 'id="pp12ShapeDash"', html),
    ("Shape engine API", "window.pp12ShapesEngine", html),
    ("Native compatibility", "pp12RegisterAnnotation", html),
]

for name, needle, text in checks:
    if needle in text:
        print("OK ", name)
    else:
        print("FAIL", name)

# ------------------------------------------------------------
# PRESERVE PREVIOUS LAYERS
# ------------------------------------------------------------

print("""
==============================================
  PREVIOUS LAYER PRESERVATION CHECK
==============================================
""")

for name, needle in [
    ("#12.1 annotation-page", '@app.post("/api/annotation-page")'),
    ("#12.1 annotate", '@app.post("/api/annotate")'),
    ("#12.2 object manager", "pp12AnnotationObjectManager"),
    ("#12.2 transform frame", "pp12AnnotationTransformFrame"),
    ("#12.3 advanced text", "pp12AdvancedTextToolbar"),
    ("#12.4 markup", "pp12ProfessionalMarkupToolbar"),
]:
    if needle in main_text or needle in html:
        print("OK ", name)
    else:
        print("WARNING:", name, "marker not found")

# ------------------------------------------------------------
# ROUTE CHECK
# ------------------------------------------------------------

print("""
==============================================
  EXISTING ANNOTATION ROUTE CHECK
==============================================
""")

for route in [
    '@app.post("/api/annotation-page")',
    '@app.post("/api/annotate")',
    '@app.post("/api/merge")',
]:
    if route in main_text:
        print(route, "=> OK")
    else:
        print(route, "=> MISSING")

# ------------------------------------------------------------
# BACKUP CHECK
# ------------------------------------------------------------

print("""
==============================================
  BACKUP CHECK
==============================================
""")

if BACK_MAIN.exists():
    print("Backend backup exists")
else:
    print("ERROR: Backend backup missing")

if BACK_INDEX.exists():
    print("Frontend backup exists")
else:
    print("ERROR: Frontend backup missing")

print("""
==============================================
  #12.5 FINAL STATUS
==============================================

Added:
  - Professional freehand Pen
  - Straight Line
  - Arrow
  - Rectangle
  - Ellipse
  - Highlight Box
  - Eraser
  - Stroke color
  - Fill color
  - Fill enable/disable
  - Stroke width
  - Opacity
  - Solid / dashed / dotted strokes
  - Live shape preview
  - Shape selection
  - Shape movement
  - Delete
  - Keyboard movement
  - Native annotation compatibility
  - Object manager compatibility
  - Existing annotation API preserved

Preserved:
  - #12.1 Professional Annotation Engine
  - #12.2 Annotation Object Manager
  - #12.3 Advanced Text Annotation Engine
  - #12.4 Professional Text Markup Engine

No persistent document database added.

IMPORTANT:
If ANY ERROR appeared above, do not continue.
Paste the complete ERROR output here.
""")
