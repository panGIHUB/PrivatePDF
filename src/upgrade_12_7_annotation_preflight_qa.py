from pathlib import Path
import shutil
import re
import sys

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app"
STATIC = ROOT / "static"

MAIN = APP / "main.py"
INDEX = STATIC / "index.html"

BACK_MAIN = APP / "main.py.before_annotation_preflight_upgrade"
BACK_INDEX = STATIC / "index.html.before_annotation_preflight_upgrade"

BACKEND_MARKER = "# === UPGRADE_12_7_ANNOTATION_PREFLIGHT_QA_BACKEND ==="
CSS_MARKER = "upgrade-12-7-annotation-preflight-css"
JS_MARKER = "upgrade-12-7-annotation-preflight-js"
UI_MARKER = "upgrade-12-7-annotation-preflight-ui"


def fail(message):
    print("\nERROR:", message)
    sys.exit(1)


print("""
==============================================
  PRIVATE PDF PRO — UPGRADE #12.7
  ANNOTATION PREFLIGHT + EXPORT QA ENGINE
==============================================
""")

if not MAIN.exists():
    fail(f"Backend not found: {MAIN}")

if not INDEX.exists():
    fail(f"Frontend not found: {INDEX}")

print("Project root:", ROOT)
print("Backend:", MAIN)
print("Frontend:", INDEX)

# ============================================================
# BACKUPS
# ============================================================

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

# ============================================================
# BACKEND COMPATIBILITY MARKER
# ============================================================

backend_block = f'''

{BACKEND_MARKER}

# #12.7 Annotation Preflight / Export QA
#
# Final validation remains stateless.
# The backend does not introduce persistent annotation/document
# storage. Existing native PDF annotation/export routes remain
# the source of truth for final PDF generation.
#
# Frontend preflight performs UX-level validation before export.

'''

if BACKEND_MARKER not in main_text:
    route_match = re.search(r'(?m)^@app\.', main_text)

    if route_match:
        pos = route_match.start()
        main_text = (
            main_text[:pos]
            + backend_block
            + main_text[pos:]
        )
    else:
        main_text += backend_block

    MAIN.write_text(main_text, encoding="utf-8")
    print("Preflight backend compatibility layer installed.")
else:
    print("Preflight backend compatibility layer already present.")

# ============================================================
# UI
# ============================================================

ui_block = r'''
<!-- === UPGRADE_12_7_ANNOTATION_PREFLIGHT_QA_UI === -->

<div
  id="pp12PreflightToolbar"
  class="pp12-preflight-toolbar"
  aria-label="Annotation export preflight">

  <div class="pp12-preflight-main">

    <span
      id="pp12PreflightIndicator"
      class="pp12-preflight-indicator pp12-preflight-neutral">
      ● Ready
    </span>

    <span
      id="pp12PreflightSummary"
      class="pp12-preflight-summary">
      No validation performed
    </span>

  </div>

  <div class="pp12-preflight-actions">

    <button
      type="button"
      id="pp12RunPreflight"
      class="pp12-preflight-button"
      title="Validate annotations before export">
      Check export
    </button>

    <button
      type="button"
      id="pp12ShowPreflight"
      class="pp12-preflight-button pp12-preflight-secondary"
      title="Show validation details">
      Details
    </button>

  </div>

</div>

<div
  id="pp12PreflightPanel"
  class="pp12-preflight-panel"
  hidden>

  <div class="pp12-preflight-panel-header">

    <strong>
      Export preflight
    </strong>

    <button
      type="button"
      id="pp12ClosePreflight"
      aria-label="Close">
      ×
    </button>

  </div>

  <div
    id="pp12PreflightResults"
    class="pp12-preflight-results">
  </div>

</div>

<!-- === /UPGRADE_12_7_ANNOTATION_PREFLIGHT_QA_UI === -->
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

    print("Preflight UI installed.")
else:
    print("Preflight UI already present.")

# ============================================================
# CSS
# ============================================================

css_block = r'''
<style id="upgrade-12-7-annotation-preflight-css">

/* ============================================================
   PRIVATE PDF PRO — #12.7 PREFLIGHT / EXPORT QA
   ============================================================ */

#pp12PreflightToolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;

  padding: 8px 10px;
  margin: 8px 0 10px;

  border: 1px solid rgba(148,163,184,.25);
  border-radius: 10px;

  background: rgba(15,23,42,.035);

  position: relative;
  z-index: 102;
}

.pp12-preflight-main {
  display: flex;
  align-items: center;
  gap: 8px;

  min-width: 0;
}

.pp12-preflight-indicator {
  display: inline-flex;
  align-items: center;

  padding: 4px 8px;

  border-radius: 999px;

  font-size: 11px;
  font-weight: 700;

  white-space: nowrap;
}

.pp12-preflight-neutral {
  background: rgba(100,116,139,.10);
  color: rgba(51,65,85,.90);
}

.pp12-preflight-good {
  background: rgba(34,197,94,.10);
  color: rgba(21,128,61,.95);
}

.pp12-preflight-warning {
  background: rgba(234,179,8,.12);
  color: rgba(133,77,14,.95);
}

.pp12-preflight-error {
  background: rgba(239,68,68,.10);
  color: rgba(185,28,28,.95);
}

.pp12-preflight-summary {
  font-size: 12px;
  color: rgba(51,65,85,.78);

  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pp12-preflight-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pp12-preflight-button {
  min-height: 31px;

  padding: 5px 10px;

  border-radius: 8px;
  border: 1px solid rgba(100,116,139,.30);

  background: white;

  cursor: pointer;

  font-size: 12px;
  font-weight: 600;
}

.pp12-preflight-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(15,23,42,.10);
}

.pp12-preflight-secondary {
  font-weight: 500;
}

.pp12-preflight-panel {
  position: relative;

  margin: 0 0 12px;

  border: 1px solid rgba(148,163,184,.28);
  border-radius: 10px;

  background: white;

  overflow: hidden;

  z-index: 103;

  box-shadow:
    0 10px 30px rgba(15,23,42,.08);
}

.pp12-preflight-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  padding: 10px 12px;

  border-bottom: 1px solid rgba(148,163,184,.20);
}

.pp12-preflight-panel-header button {
  width: 28px;
  height: 28px;

  border: 0;
  border-radius: 6px;

  background: transparent;

  cursor: pointer;

  font-size: 20px;
  line-height: 1;
}

.pp12-preflight-results {
  padding: 10px 12px;

  display: grid;
  gap: 7px;
}

.pp12-preflight-result {
  display: flex;
  align-items: flex-start;
  gap: 8px;

  padding: 8px 9px;

  border-radius: 8px;

  background: rgba(15,23,42,.035);

  font-size: 12px;
}

.pp12-preflight-result-icon {
  flex: 0 0 auto;
  font-weight: 800;
}

.pp12-preflight-result-text {
  min-width: 0;
}

.pp12-preflight-result-title {
  font-weight: 700;
}

.pp12-preflight-result-detail {
  margin-top: 2px;
  opacity: .72;
}

.pp12-preflight-result-good {
  border-left: 3px solid rgba(34,197,94,.70);
}

.pp12-preflight-result-warning {
  border-left: 3px solid rgba(234,179,8,.75);
}

.pp12-preflight-result-error {
  border-left: 3px solid rgba(239,68,68,.75);
}

.pp12-preflight-result-info {
  border-left: 3px solid rgba(59,130,246,.65);
}

@media (max-width: 800px) {

  #pp12PreflightToolbar {
    justify-content: flex-start;
  }

  .pp12-preflight-main {
    width: 100%;
  }

  .pp12-preflight-summary {
    max-width: 65vw;
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

    print("Preflight CSS installed.")
else:
    print("Preflight CSS already present.")

# ============================================================
# JAVASCRIPT
# ============================================================

js_block = r'''
<script id="upgrade-12-7-annotation-preflight-js">

(function () {
  "use strict";

  /* ==========================================================
     PRIVATE PDF PRO — #12.7 PREFLIGHT / EXPORT QA ENGINE
     ========================================================== */

  if (window.__PP12_PREFLIGHT_ENGINE__) return;

  window.__PP12_PREFLIGHT_ENGINE__ = true;

  const toolbar =
    document.getElementById(
      "pp12PreflightToolbar"
    );

  const indicator =
    document.getElementById(
      "pp12PreflightIndicator"
    );

  const summary =
    document.getElementById(
      "pp12PreflightSummary"
    );

  const runButton =
    document.getElementById(
      "pp12RunPreflight"
    );

  const detailsButton =
    document.getElementById(
      "pp12ShowPreflight"
    );

  const panel =
    document.getElementById(
      "pp12PreflightPanel"
    );

  const results =
    document.getElementById(
      "pp12PreflightResults"
    );

  const closeButton =
    document.getElementById(
      "pp12ClosePreflight"
    );

  if (!toolbar ||
      !indicator ||
      !summary ||
      !runButton) {

    console.warn(
      "[Private PDF Pro] #12.7 preflight UI not found."
    );

    return;
  }

  const state = {
    lastReport: null,
    dirty: false,
    running: false,
    exportReady: false,
    annotationCount: 0
  };

  /* ==========================================================
     HELPERS
     ========================================================== */

  function safeNumber(value, fallback) {

    const n = Number(value);

    return Number.isFinite(n)
      ? n
      : fallback;
  }

  function getAllAnnotationElements() {

    const selectors = [
      ".pp12-shape-object",
      ".pp12-text-object",
      ".pp12-annotation-object",
      ".pp12-annotation",
      "[data-annotation-id]",
      "[data-pp12-annotation-id]"
    ];

    const set = new Set();

    selectors.forEach(function (selector) {

      document
        .querySelectorAll(selector)
        .forEach(function (element) {
          set.add(element);
        });

    });

    return Array.from(set);
  }

  function getPageHosts() {

    const selectors = [
      ".pp12-page-canvas",
      ".pp12-page-stage",
      "[data-annotation-page]",
      ".pp12-annotation-page",
      ".page-stage",
      ".page-container"
    ];

    const set = new Set();

    selectors.forEach(function (selector) {

      document
        .querySelectorAll(selector)
        .forEach(function (element) {
          set.add(element);
        });

    });

    return Array.from(set);
  }

  function getShapeObjects() {

    if (
      window.pp12ShapesEngine &&
      typeof window.pp12ShapesEngine.getShapes ===
        "function"
    ) {

      try {
        return window.pp12ShapesEngine.getShapes();
      } catch (_) {}
    }

    return [];
  }

  function getObjectManagerState() {

    if (
      window.pp12ObjectManager
    ) {

      try {

        if (
          typeof window.pp12ObjectManager.getState ===
            "function"
        ) {
          return window.pp12ObjectManager.getState();
        }

      } catch (_) {}
    }

    return null;
  }

  /* ==========================================================
     INDICATOR
     ========================================================== */

  function setIndicator(
    type,
    text
  ) {

    indicator.className =
      "pp12-preflight-indicator " +
      "pp12-preflight-" +
      type;

    indicator.textContent =
      "● " + text;
  }

  /* ==========================================================
     REPORT RENDERING
     ========================================================== */

  function renderReport(report) {

    if (!results) return;

    results.innerHTML = "";

    report.checks.forEach(function (check) {

      const row =
        document.createElement("div");

      row.className =
        "pp12-preflight-result " +
        "pp12-preflight-result-" +
        check.level;

      const icon =
        document.createElement("div");

      icon.className =
        "pp12-preflight-result-icon";

      icon.textContent =
        check.level === "good"
          ? "✓"
          : check.level === "warning"
            ? "!"
            : check.level === "error"
              ? "×"
              : "i";

      const text =
        document.createElement("div");

      text.className =
        "pp12-preflight-result-text";

      const title =
        document.createElement("div");

      title.className =
        "pp12-preflight-result-title";

      title.textContent =
        check.title;

      text.appendChild(title);

      if (check.detail) {

        const detail =
          document.createElement("div");

        detail.className =
          "pp12-preflight-result-detail";

        detail.textContent =
          check.detail;

        text.appendChild(detail);
      }

      row.appendChild(icon);
      row.appendChild(text);

      results.appendChild(row);
    });

    if (report.errors > 0) {

      setIndicator(
        "error",
        "Export blocked"
      );

    } else if (report.warnings > 0) {

      setIndicator(
        "warning",
        "Review warnings"
      );

    } else {

      setIndicator(
        "good",
        "Export ready"
      );
    }

    summary.textContent =
      report.total +
      " checks • " +
      report.errors +
      " errors • " +
      report.warnings +
      " warnings";

    state.exportReady =
      report.errors === 0;

    state.lastReport =
      report;
  }

  /* ==========================================================
     VALIDATE
     ========================================================== */

  function validate() {

    const checks = [];

    let errors = 0;
    let warnings = 0;

    function add(
      level,
      title,
      detail
    ) {

      checks.push({
        level: level,
        title: title,
        detail: detail || ""
      });

      if (level === "error") {
        errors++;
      }

      if (level === "warning") {
        warnings++;
      }
    }

    /* --------------------------------------------------------
       Workspace existence
       -------------------------------------------------------- */

    const pages =
      getPageHosts();

    if (pages.length > 0) {

      add(
        "good",
        "Annotation workspace detected",
        pages.length +
          " page workspace(s) available."
      );

    } else {

      add(
        "warning",
        "No page workspace detected",
        "Open a PDF in Annotation Studio before exporting."
      );
    }

    /* --------------------------------------------------------
       Annotation inventory
       -------------------------------------------------------- */

    const elements =
      getAllAnnotationElements();

    const shapes =
      getShapeObjects();

    const annotationCount =
      Math.max(
        elements.length,
        shapes.length
      );

    state.annotationCount =
      annotationCount;

    if (annotationCount > 0) {

      add(
        "good",
        "Annotations detected",
        annotationCount +
          " visible annotation object(s) detected."
      );

    } else {

      add(
        "info",
        "No annotations detected",
        "The original PDF can still be exported without new annotations."
      );
    }

    /* --------------------------------------------------------
       Shape validation
       -------------------------------------------------------- */

    let invalidShapes = 0;

    shapes.forEach(function (shape) {

      const x =
        safeNumber(shape.x, NaN);

      const y =
        safeNumber(shape.y, NaN);

      const width =
        safeNumber(shape.width, NaN);

      const height =
        safeNumber(shape.height, NaN);

      if (
        !Number.isFinite(x) ||
        !Number.isFinite(y) ||
        !Number.isFinite(width) ||
        !Number.isFinite(height)
      ) {

        invalidShapes++;

        return;
      }

      if (
        width <= 0 ||
        height <= 0
      ) {
        invalidShapes++;
      }
    });

    if (invalidShapes === 0) {

      add(
        "good",
        "Shape geometry valid",
        "No invalid shape dimensions detected."
      );

    } else {

      add(
        "error",
        "Invalid shape geometry",
        invalidShapes +
          " shape(s) have invalid position or size."
      );
    }

    /* --------------------------------------------------------
       Page boundary validation
       -------------------------------------------------------- */

    let offPage = 0;

    shapes.forEach(function (shape) {

      if (!shape.host) return;

      const width =
        safeNumber(
          shape.host.clientWidth,
          0
        );

      const height =
        safeNumber(
          shape.host.clientHeight,
          0
        );

      const right =
        safeNumber(shape.x, 0) +
        safeNumber(shape.width, 0);

      const bottom =
        safeNumber(shape.y, 0) +
        safeNumber(shape.height, 0);

      if (
        right < -1 ||
        bottom < -1 ||
        safeNumber(shape.x, 0) > width + 1 ||
        safeNumber(shape.y, 0) > height + 1
      ) {
        offPage++;
      }
    });

    if (offPage === 0) {

      add(
        "good",
        "Page placement valid",
        "No completely off-page shape objects detected."
      );

    } else {

      add(
        "warning",
        "Off-page annotation detected",
        offPage +
          " annotation object(s) may be outside the visible page."
      );
    }

    /* --------------------------------------------------------
       Zero-size DOM elements
       -------------------------------------------------------- */

    let zeroSize = 0;

    elements.forEach(function (element) {

      const rect =
        element.getBoundingClientRect();

      if (
        rect.width < 1 ||
        rect.height < 1
      ) {
        zeroSize++;
      }
    });

    if (zeroSize === 0) {

      add(
        "good",
        "Visible annotation dimensions valid",
        "No zero-size annotation elements detected."
      );

    } else {

      add(
        "warning",
        "Zero-size annotation detected",
        zeroSize +
          " annotation element(s) have nearly zero visible size."
      );
    }

    /* --------------------------------------------------------
       Object manager
       -------------------------------------------------------- */

    const manager =
      getObjectManagerState();

    if (manager !== null) {

      add(
        "good",
        "Object Manager available",
        "Annotation object management layer is active."
      );

    } else {

      add(
        "info",
        "Object Manager status",
        "No public object-manager state API was detected."
      );
    }

    /* --------------------------------------------------------
       History
       -------------------------------------------------------- */

    if (window.pp12History) {

      const undoCount =
        typeof window.pp12History.getUndoCount ===
          "function"
          ? window.pp12History.getUndoCount()
          : 0;

      const redoCount =
        typeof window.pp12History.getRedoCount ===
          "function"
          ? window.pp12History.getRedoCount()
          : 0;

      add(
        "good",
        "History engine available",
        undoCount +
          " undo action(s), " +
          redoCount +
          " redo action(s)."
      );

    } else {

      add(
        "warning",
        "History engine unavailable",
        "Undo/redo state could not be inspected."
      );
    }

    /* --------------------------------------------------------
       Shapes engine
       -------------------------------------------------------- */

    if (window.pp12ShapesEngine) {

      add(
        "good",
        "Shapes engine available",
        "Draw, line, arrow and shape layer is active."
      );

    } else {

      add(
        "info",
        "Shapes engine not active",
        "No shape objects are currently available."
      );
    }

    /* --------------------------------------------------------
       Native annotation API
       -------------------------------------------------------- */

    const nativeAPI =
      document.body &&
      document.body.innerHTML.indexOf(
        "/api/annotate"
      ) >= 0;

    if (nativeAPI) {

      add(
        "good",
        "Native annotation export detected",
        "Existing annotation API compatibility marker is present."
      );

    } else {

      add(
        "info",
        "Native export API",
        "Frontend route marker was not found in the current DOM."
      );
    }

    /* --------------------------------------------------------
       Duplicate script protection
       -------------------------------------------------------- */

    const scriptIds =
      Array.from(
        document.scripts
      )
      .map(function (script) {
        return script.id;
      })
      .filter(Boolean);

    const duplicateIds =
      scriptIds.filter(function (
        id,
        index
      ) {
        return (
          scriptIds.indexOf(id) !== index
        );
      });

    if (duplicateIds.length === 0) {

      add(
        "good",
        "Script duplication check passed",
        "No duplicate script IDs detected."
      );

    } else {

      add(
        "warning",
        "Duplicate script IDs detected",
        duplicateIds.join(", ")
      );
    }

    /* --------------------------------------------------------
       Performance sanity
       -------------------------------------------------------- */

    if (elements.length < 500) {

      add(
        "good",
        "Annotation count within normal range",
        elements.length +
          " visible annotation DOM object(s)."
      );

    } else {

      add(
        "warning",
        "Large annotation count",
        elements.length +
          " visible objects may affect editor performance."
      );
    }

    /* --------------------------------------------------------
       Final report
       -------------------------------------------------------- */

    const report = {
      checks: checks,
      total: checks.length,
      errors: errors,
      warnings: warnings,
      timestamp: Date.now()
    };

    renderReport(report);

    window.dispatchEvent(
      new CustomEvent(
        "pp12:preflight-complete",
        {
          detail: report
        }
      )
    );

    return report;
  }

  /* ==========================================================
     RUN BUTTON
     ========================================================== */

  runButton.addEventListener(
    "click",
    function () {

      if (state.running) return;

      state.running = true;

      setIndicator(
        "neutral",
        "Checking"
      );

      summary.textContent =
        "Running export preflight...";

      /*
        Small async boundary prevents the UI from appearing frozen
        during larger annotation workspaces.
      */

      window.setTimeout(
        function () {

          try {
            validate();

          } catch (error) {

            console.error(
              "[Private PDF Pro] Preflight failed:",
              error
            );

            setIndicator(
              "error",
              "Preflight failed"
            );

            summary.textContent =
              "Validation could not be completed.";

          } finally {

            state.running = false;
          }

        },
        0
      );
    }
  );

  /* ==========================================================
     DETAILS
     ========================================================== */

  if (detailsButton) {

    detailsButton.addEventListener(
      "click",
      function () {

        if (!state.lastReport) {
          validate();
        }

        if (panel) {
          panel.hidden =
            !panel.hidden;
        }
      }
    );
  }

  if (closeButton) {

    closeButton.addEventListener(
      "click",
      function () {

        if (panel) {
          panel.hidden = true;
        }
      }
    );
  }

  /* ==========================================================
     DIRTY STATE
     ========================================================== */

  function markDirty() {

    state.dirty = true;

    /*
      Existing history engine is the source of truth when available.
    */

    if (
      window.pp12History &&
      typeof window.pp12History.canUndo ===
        "function"
    ) {

      if (
        window.pp12History.canUndo()
      ) {
        setIndicator(
          "warning",
          "Changes pending"
        );
      }
    }
  }

  [
    "pp12:shape-created",
    "pp12:annotation-moved",
    "pp12:annotation-deleted",
    "pp12:history-change",
    "pp12:history-undo",
    "pp12:history-redo"
  ].forEach(function (eventName) {

    window.addEventListener(
      eventName,
      markDirty
    );
  });

  /* ==========================================================
     PUBLIC API
     ========================================================== */

  window.pp12Preflight = {

    run: validate,

    getReport: function () {
      return state.lastReport;
    },

    isExportReady: function () {
      return state.exportReady;
    },

    isDirty: function () {
      return state.dirty;
    },

    getAnnotationCount: function () {
      return state.annotationCount;
    },

    clearDirty: function () {
      state.dirty = false;
    }
  };

  /*
    Run a lightweight initial validation.
  */

  window.setTimeout(
    function () {

      try {
        validate();
      } catch (_) {}

    },
    100
  );

  console.log(
    "[Private PDF Pro] #12.7 Annotation Preflight QA loaded."
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

    print("Preflight JavaScript installed.")
else:
    print("Preflight JavaScript already present.")

INDEX.write_text(html, encoding="utf-8")

print("""
==============================================
  #12.7 INSTALLATION COMPLETE
==============================================
""")

# ============================================================
# MARKER CHECK
# ============================================================

print("""
==============================================
  #12.7 FILE MARKER CHECK
==============================================
""")

checks = [
    ("Backend #12.7 marker", BACKEND_MARKER, main_text),
    ("Preflight CSS", CSS_MARKER, html),
    ("Preflight JS", JS_MARKER, html),
    ("Preflight UI", UI_MARKER, html),
    ("Preflight toolbar", "pp12PreflightToolbar", html),
    ("Preflight indicator", "pp12PreflightIndicator", html),
    ("Preflight summary", "pp12PreflightSummary", html),
    ("Run preflight", "pp12RunPreflight", html),
    ("Preflight details", "pp12ShowPreflight", html),
    ("Preflight panel", "pp12PreflightPanel", html),
    ("Preflight engine", "window.pp12Preflight", html),
    ("Export readiness", "isExportReady", html),
    ("Annotation count", "getAnnotationCount", html),
    ("Geometry validation", "Invalid shape geometry", html),
    ("Page validation", "Page placement valid", html),
    ("History validation", "History engine available", html),
    ("Duplicate script check", "Duplicate script IDs detected", html),
]

for name, needle, text in checks:
    if needle in text:
        print("OK ", name)
    else:
        print("FAIL", name)

# ============================================================
# PREVIOUS LAYERS
# ============================================================

print("""
==============================================
  PREVIOUS LAYER PRESERVATION CHECK
==============================================
""")

previous = [
    ("#12.1 annotation-page",
     '@app.post("/api/annotation-page")'),

    ("#12.1 annotate",
     '@app.post("/api/annotate")'),

    ("#12.2 object manager",
     "pp12AnnotationObjectManager"),

    ("#12.2 transform frame",
     "pp12AnnotationTransformFrame"),

    ("#12.3 advanced text",
     "pp12AdvancedTextToolbar"),

    ("#12.4 markup",
     "pp12ProfessionalMarkupToolbar"),

    ("#12.5 shapes",
     "pp12ShapesEngine"),

    ("#12.6 history",
     "window.pp12History"),
]

for name, needle in previous:

    if (
        needle in main_text or
        needle in html
    ):
        print("OK ", name)
    else:
        print("WARNING:", name, "marker not found")

# ============================================================
# ROUTES
# ============================================================

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

# ============================================================
# BACKUPS
# ============================================================

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
  #12.7 FINAL STATUS
==============================================

Added:
  - Annotation preflight validation
  - Export readiness state
  - Geometry validation
  - Page placement validation
  - Zero-size annotation detection
  - Annotation inventory
  - Object Manager validation
  - History engine validation
  - Shapes engine validation
  - Native export compatibility check
  - Duplicate script detection
  - Performance sanity check
  - Dirty/unsaved annotation state
  - Preflight details panel
  - Stateless QA layer

Preserved:
  - #12.1 Professional Annotation Engine
  - #12.2 Annotation Object Manager
  - #12.3 Advanced Text Annotation Engine
  - #12.4 Professional Text Markup Engine
  - #12.5 Professional Draw / Shapes Engine
  - #12.6 Professional Undo / Redo History Engine

No persistent document database added.

IMPORTANT:
If ANY ERROR appeared above, do not continue.
Paste the complete ERROR output here.
""")
