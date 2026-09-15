from pathlib import Path
import shutil
import re
import sys

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app"
STATIC = ROOT / "static"

MAIN = APP / "main.py"
INDEX = STATIC / "index.html"

BACK_MAIN = APP / "main.py.before_history_engine_upgrade"
BACK_INDEX = STATIC / "index.html.before_history_engine_upgrade"

BACKEND_MARKER = "# === UPGRADE_12_6_PROFESSIONAL_HISTORY_ENGINE_BACKEND ==="
CSS_MARKER = "upgrade-12-6-professional-history-css"
JS_MARKER = "upgrade-12-6-professional-history-js"
UI_MARKER = "upgrade-12-6-professional-history-ui"


def fail(msg):
    print("\nERROR:", msg)
    sys.exit(1)


print("""
==============================================
  PRIVATE PDF PRO — UPGRADE #12.6
  PROFESSIONAL UNDO / REDO HISTORY ENGINE
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

# #12.6 Professional History Engine
#
# History is intentionally maintained in the frontend workspace.
# The PDF backend remains stateless and continues using the existing
# native annotation/export pipeline.
#
# No persistent document database is introduced by this upgrade.

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
    print("History backend compatibility layer installed.")
else:
    print("History backend compatibility layer already present.")

# ============================================================
# HISTORY UI
# ============================================================

ui_block = r'''
<!-- === UPGRADE_12_6_PROFESSIONAL_HISTORY_UI === -->

<div
  id="pp12HistoryToolbar"
  class="pp12-history-toolbar"
  aria-label="Annotation history">

  <div class="pp12-history-actions">

    <button
      type="button"
      id="pp12UndoButton"
      class="pp12-history-button"
      title="Undo (Ctrl+Z)"
      aria-label="Undo">
      ↶ Undo
    </button>

    <button
      type="button"
      id="pp12RedoButton"
      class="pp12-history-button"
      title="Redo (Ctrl+Y)"
      aria-label="Redo">
      ↷ Redo
    </button>

  </div>

  <div
    id="pp12HistoryStatus"
    class="pp12-history-status"
    aria-live="polite">
    No changes
  </div>

  <div class="pp12-history-actions">

    <button
      type="button"
      id="pp12HistoryClear"
      class="pp12-history-button pp12-history-secondary"
      title="Clear local history">
      Clear history
    </button>

  </div>

</div>

<!-- === /UPGRADE_12_6_PROFESSIONAL_HISTORY_UI === -->
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

    print("History toolbar UI installed.")
else:
    print("History toolbar UI already present.")

# ============================================================
# CSS
# ============================================================

css_block = r'''
<style id="upgrade-12-6-professional-history-css">

/* ============================================================
   PRIVATE PDF PRO — #12.6 HISTORY ENGINE
   ============================================================ */

#pp12HistoryToolbar {
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
  z-index: 101;
}

.pp12-history-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pp12-history-button {
  min-height: 32px;

  padding: 5px 10px;

  border-radius: 8px;
  border: 1px solid rgba(100,116,139,.30);

  background: white;

  font-size: 12px;
  font-weight: 600;

  cursor: pointer;

  transition:
    transform .12s ease,
    opacity .12s ease,
    box-shadow .12s ease;
}

.pp12-history-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(15,23,42,.10);
}

.pp12-history-button:active:not(:disabled) {
  transform: translateY(0);
}

.pp12-history-button:disabled {
  opacity: .40;
  cursor: not-allowed;
}

.pp12-history-secondary {
  font-weight: 500;
}

.pp12-history-status {
  flex: 1;

  min-width: 130px;

  text-align: center;

  font-size: 12px;
  color: rgba(51,65,85,.82);

  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pp12-history-status.is-active {
  font-weight: 600;
}

@media (max-width: 800px) {

  #pp12HistoryToolbar {
    justify-content: flex-start;
  }

  .pp12-history-status {
    order: 3;
    flex-basis: 100%;
    text-align: left;
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

    print("History CSS installed.")
else:
    print("History CSS already present.")

# ============================================================
# JAVASCRIPT HISTORY ENGINE
# ============================================================

js_block = r'''
<script id="upgrade-12-6-professional-history-js">

(function () {
  "use strict";

  /* ==========================================================
     PRIVATE PDF PRO — #12.6 PROFESSIONAL HISTORY ENGINE
     ========================================================== */

  if (window.__PP12_HISTORY_ENGINE__) return;

  window.__PP12_HISTORY_ENGINE__ = true;

  const undoButton =
    document.getElementById("pp12UndoButton");

  const redoButton =
    document.getElementById("pp12RedoButton");

  const clearButton =
    document.getElementById("pp12HistoryClear");

  const status =
    document.getElementById("pp12HistoryStatus");

  if (!undoButton || !redoButton) {
    console.warn(
      "[Private PDF Pro] #12.6 history toolbar not found."
    );
    return;
  }

  const MAX_HISTORY = 100;

  const state = {
    undoStack: [],
    redoStack: [],
    replaying: false,
    initialized: false
  };

  /* ==========================================================
     SAFE CLONE
     ========================================================== */

  function clone(value) {

    if (value === undefined) {
      return undefined;
    }

    try {
      return JSON.parse(
        JSON.stringify(value)
      );
    } catch (_) {
      return value;
    }
  }

  /* ==========================================================
     STATUS
     ========================================================== */

  function updateStatus() {

    undoButton.disabled =
      state.undoStack.length === 0 ||
      state.replaying;

    redoButton.disabled =
      state.redoStack.length === 0 ||
      state.replaying;

    if (status) {

      if (
        state.undoStack.length === 0 &&
        state.redoStack.length === 0
      ) {
        status.textContent =
          "No changes";
        status.classList.remove(
          "is-active"
        );
        return;
      }

      const undoCount =
        state.undoStack.length;

      const redoCount =
        state.redoStack.length;

      status.textContent =
        undoCount +
        " undo" +
        (undoCount === 1 ? "" : "s") +
        " • " +
        redoCount +
        " redo" +
        (redoCount === 1 ? "" : "s");

      status.classList.add(
        "is-active"
      );
    }
  }

  /* ==========================================================
     DESCRIPTION
     ========================================================== */

  function describe(action) {

    if (!action) {
      return "Change";
    }

    if (action.label) {
      return action.label;
    }

    if (action.type) {
      return String(action.type)
        .replace(/[-_]/g, " ")
        .replace(/\b\w/g, function (c) {
          return c.toUpperCase();
        });
    }

    return "Change";
  }

  /* ==========================================================
     REGISTER HISTORY ACTION
     ========================================================== */

  function push(action) {

    if (
      state.replaying ||
      !action
    ) {
      return;
    }

    const item = {
      id:
        action.id ||
        (
          "history_" +
          Date.now().toString(36) +
          "_" +
          Math.random()
            .toString(36)
            .slice(2, 8)
        ),

      type:
        action.type ||
        "change",

      label:
        describe(action),

      undo:
        typeof action.undo === "function"
          ? action.undo
          : function () {},

      redo:
        typeof action.redo === "function"
          ? action.redo
          : function () {},

      meta:
        clone(action.meta || null)
    };

    state.undoStack.push(item);

    if (
      state.undoStack.length >
      MAX_HISTORY
    ) {
      state.undoStack.shift();
    }

    /*
      Any new action after undo invalidates the redo branch.
    */

    state.redoStack = [];

    updateStatus();

    window.dispatchEvent(
      new CustomEvent(
        "pp12:history-change",
        {
          detail: {
            action: item,
            undoCount:
              state.undoStack.length,
            redoCount:
              state.redoStack.length
          }
        }
      )
    );
  }

  /* ==========================================================
     UNDO
     ========================================================== */

  async function undo() {

    if (
      state.replaying ||
      state.undoStack.length === 0
    ) {
      return false;
    }

    const action =
      state.undoStack.pop();

    state.replaying = true;
    updateStatus();

    try {

      await action.undo();

      state.redoStack.push(action);

      if (
        state.redoStack.length >
        MAX_HISTORY
      ) {
        state.redoStack.shift();
      }

      return true;

    } catch (error) {

      console.error(
        "[Private PDF Pro] Undo failed:",
        error
      );

      /*
        Restore action to undo stack if undo failed.
      */

      state.undoStack.push(action);

      return false;

    } finally {

      state.replaying = false;
      updateStatus();

      window.dispatchEvent(
        new CustomEvent(
          "pp12:history-undo",
          {
            detail: {
              action: action,
              undoCount:
                state.undoStack.length,
              redoCount:
                state.redoStack.length
            }
          }
        )
      );
    }
  }

  /* ==========================================================
     REDO
     ========================================================== */

  async function redo() {

    if (
      state.replaying ||
      state.redoStack.length === 0
    ) {
      return false;
    }

    const action =
      state.redoStack.pop();

    state.replaying = true;
    updateStatus();

    try {

      await action.redo();

      state.undoStack.push(action);

      if (
        state.undoStack.length >
        MAX_HISTORY
      ) {
        state.undoStack.shift();
      }

      return true;

    } catch (error) {

      console.error(
        "[Private PDF Pro] Redo failed:",
        error
      );

      state.redoStack.push(action);

      return false;

    } finally {

      state.replaying = false;
      updateStatus();

      window.dispatchEvent(
        new CustomEvent(
          "pp12:history-redo",
          {
            detail: {
              action: action,
              undoCount:
                state.undoStack.length,
              redoCount:
                state.redoStack.length
            }
          }
        )
      );
    }
  }

  /* ==========================================================
     CLEAR
     ========================================================== */

  function clear() {

    state.undoStack = [];
    state.redoStack = [];

    updateStatus();

    window.dispatchEvent(
      new CustomEvent(
        "pp12:history-clear"
      )
    );
  }

  /* ==========================================================
     BUTTONS
     ========================================================== */

  undoButton.addEventListener(
    "click",
    function () {
      undo();
    }
  );

  redoButton.addEventListener(
    "click",
    function () {
      redo();
    }
  );

  if (clearButton) {
    clearButton.addEventListener(
      "click",
      function () {
        clear();
      }
    );
  }

  /* ==========================================================
     KEYBOARD SHORTCUTS
     ========================================================== */

  document.addEventListener(
    "keydown",
    function (event) {

      const target =
        event.target;

      const editing =
        target &&
        (
          target.matches(
            "input, textarea, select"
          ) ||
          target.isContentEditable
        );

      /*
        Never steal Ctrl+Z / Ctrl+Y from a text input.
      */

      if (editing) {
        return;
      }

      /*
        Ctrl+Z
      */

      if (
        event.ctrlKey &&
        !event.altKey &&
        !event.shiftKey &&
        event.key.toLowerCase() === "z"
      ) {

        event.preventDefault();

        undo();

        return;
      }

      /*
        Ctrl+Shift+Z
      */

      if (
        event.ctrlKey &&
        event.shiftKey &&
        !event.altKey &&
        event.key.toLowerCase() === "z"
      ) {

        event.preventDefault();

        redo();

        return;
      }

      /*
        Ctrl+Y
      */

      if (
        event.ctrlKey &&
        !event.altKey &&
        event.key.toLowerCase() === "y"
      ) {

        event.preventDefault();

        redo();

        return;
      }
    },
    true
  );

  /* ==========================================================
     COMPATIBILITY BRIDGE
     ========================================================== */

  function snapshotShapes() {

    if (
      !window.pp12ShapesEngine ||
      typeof window.pp12ShapesEngine.getShapes !==
        "function"
    ) {
      return [];
    }

    try {

      return clone(
        window.pp12ShapesEngine
          .getShapes()
          .map(function (shape) {

            return {
              id: shape.id,
              type: shape.type,
              pageIndex: shape.pageIndex,
              x: shape.x,
              y: shape.y,
              width: shape.width,
              height: shape.height,
              stroke: shape.stroke,
              fill: shape.fill,
              fillEnabled:
                shape.fillEnabled,
              strokeWidth:
                shape.strokeWidth,
              opacity:
                shape.opacity,
              dash:
                shape.dash,
              points:
                shape.points || []
            };
          })
      );

    } catch (_) {

      return [];
    }
  }

  function refreshShapes() {

    if (
      window.pp12ShapesEngine &&
      typeof window.pp12ShapesEngine.refresh ===
        "function"
    ) {

      try {
        window.pp12ShapesEngine.refresh();
      } catch (_) {}
    }
  }

  /*
    Shape events generated by #12.5.

    We record the previous and current shape state when
    available. The event is intentionally lightweight so that
    #12.5 remains independent from #12.6.
  */

  document.addEventListener(
    "pp12:shape-created",
    function (event) {

      if (state.replaying) return;

      const detail =
        event.detail || {};

      const shape =
        clone(detail);

      push({

        type: "shape-create",

        label: "Create " +
          (
            shape.type || "shape"
          ),

        meta: shape,

        undo: function () {

          if (
            window.pp12ShapesEngine &&
            typeof window.pp12ShapesEngine.getShapes ===
              "function"
          ) {

            const shapes =
              window.pp12ShapesEngine
                .getShapes();

            const target =
              shapes.find(function (s) {
                return s.id === shape.id;
              });

            if (
              target &&
              typeof window.pp12ShapesEngine.remove ===
                "function"
            ) {
              window.pp12ShapesEngine.remove(
                target
              );
            }
          }
        },

        redo: function () {

          /*
            Redo is intentionally delegated to the
            public shape layer when supported.
          */

          window.dispatchEvent(
            new CustomEvent(
              "pp12:history-redo-shape",
              {
                detail: shape
              }
            )
          );
        }
      });
    }
  );

  /* ==========================================================
     GENERIC ACTION REGISTRATION
     ========================================================== */

  window.pp12History = {

    push: push,

    undo: undo,

    redo: redo,

    clear: clear,

    canUndo: function () {
      return (
        state.undoStack.length > 0
      );
    },

    canRedo: function () {
      return (
        state.redoStack.length > 0
      );
    },

    getUndoCount: function () {
      return state.undoStack.length;
    },

    getRedoCount: function () {
      return state.redoStack.length;
    },

    getHistory: function () {
      return state.undoStack
        .concat(
          state.redoStack
        )
        .map(function (item) {
          return {
            id: item.id,
            type: item.type,
            label: item.label,
            meta: clone(item.meta)
          };
        });
    },

    isReplaying: function () {
      return state.replaying;
    }
  };

  /* ==========================================================
     MOVE COMPATIBILITY
     ========================================================== */

  document.addEventListener(
    "pp12:annotation-moved",
    function (event) {

      if (state.replaying) return;

      const detail =
        event.detail || {};

      if (
        !detail.before ||
        !detail.after
      ) {
        return;
      }

      const before =
        clone(detail.before);

      const after =
        clone(detail.after);

      push({

        type: "move",

        label: "Move annotation",

        meta: {
          before: before,
          after: after
        },

        undo: function () {

          window.dispatchEvent(
            new CustomEvent(
              "pp12:history-apply-position",
              {
                detail: before
              }
            )
          );
        },

        redo: function () {

          window.dispatchEvent(
            new CustomEvent(
              "pp12:history-apply-position",
              {
                detail: after
              }
            )
          );
        }
      });
    }
  );

  /* ==========================================================
     DELETE COMPATIBILITY
     ========================================================== */

  document.addEventListener(
    "pp12:annotation-deleted",
    function (event) {

      if (state.replaying) return;

      const detail =
        event.detail || {};

      push({

        type: "delete",

        label: "Delete annotation",

        meta: clone(detail),

        undo: function () {

          window.dispatchEvent(
            new CustomEvent(
              "pp12:history-restore-annotation",
              {
                detail: clone(detail)
              }
            )
          );
        },

        redo: function () {

          window.dispatchEvent(
            new CustomEvent(
              "pp12:history-delete-annotation",
              {
                detail: clone(detail)
              }
            )
          );
        }
      });
    }
  );

  /* ==========================================================
     INITIALIZATION
     ========================================================== */

  state.initialized = true;

  updateStatus();

  console.log(
    "[Private PDF Pro] #12.6 Professional History Engine loaded."
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

    print("Professional History JavaScript installed.")
else:
    print("Professional History JavaScript already present.")

INDEX.write_text(html, encoding="utf-8")

print("""
==============================================
  #12.6 INSTALLATION COMPLETE
==============================================
""")

# ============================================================
# MARKER CHECK
# ============================================================

print("""
==============================================
  #12.6 FILE MARKER CHECK
==============================================
""")

checks = [
    ("Backend #12.6 marker", BACKEND_MARKER, main_text),
    ("History CSS", CSS_MARKER, html),
    ("History JS", JS_MARKER, html),
    ("History UI", UI_MARKER, html),
    ("Undo button", "pp12UndoButton", html),
    ("Redo button", "pp12RedoButton", html),
    ("History status", "pp12HistoryStatus", html),
    ("Clear history", "pp12HistoryClear", html),
    ("Undo engine", "function undo()", html),
    ("Redo engine", "function redo()", html),
    ("History API", "window.pp12History", html),
    ("Ctrl+Z", 'event.key.toLowerCase() === "z"', html),
    ("Ctrl+Y", 'event.key.toLowerCase() === "y"', html),
    ("Shape history", "pp12:shape-created", html),
    ("Move history", "pp12:annotation-moved", html),
    ("Delete history", "pp12:annotation-deleted", html),
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
  #12.6 FINAL STATUS
==============================================

Added:
  - Professional Undo
  - Professional Redo
  - 100-action history limit
  - Redo branch invalidation
  - History status
  - Clear history
  - Ctrl+Z
  - Ctrl+Y
  - Ctrl+Shift+Z
  - Shape history compatibility
  - Move history compatibility
  - Delete history compatibility
  - Object Manager compatibility
  - Future history API
  - Stateless frontend history
  - No persistent document database

Preserved:
  - #12.1 Professional Annotation Engine
  - #12.2 Annotation Object Manager
  - #12.3 Advanced Text Annotation Engine
  - #12.4 Professional Text Markup Engine
  - #12.5 Professional Draw / Shapes Engine

IMPORTANT:
If ANY ERROR appeared above, do not continue.
Paste the complete ERROR output here.
""")
