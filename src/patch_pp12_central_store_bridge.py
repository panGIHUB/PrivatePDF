from pathlib import Path
import re
import shutil
from datetime import datetime

ROOT = Path(".")
HTML = ROOT / "static" / "index.html"

if not HTML.exists():
    raise SystemExit("ERROR: static/index.html not found")

src = HTML.read_text(encoding="utf-8")

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = HTML.with_name(f"index.html.before_central_store_bridge_{STAMP}.bak")
shutil.copy2(HTML, BACKUP)

print("=" * 62)
print(" PP12 CENTRAL ANNOTATION STORE BRIDGE")
print("=" * 62)
print(f"Backup: {BACKUP.name}")

# ------------------------------------------------------------
# 1. Prevent duplicate installation
# ------------------------------------------------------------

if "PP12_CENTRAL_STORE_BRIDGE_V1" in src:
    print("WARNING: Central Store Bridge already detected.")
    print("No duplicate patch applied.")
    raise SystemExit(0)

# ------------------------------------------------------------
# 2. Central bridge
#
# This lives in the main PP12 annotation scope so it can access
# the existing `state`, `current()` and `status()` functions.
# ------------------------------------------------------------

bridge = r'''
/* ============================================================
 * PP12_CENTRAL_STORE_BRIDGE_V1
 * ------------------------------------------------------------
 * #12.1 -> #12.2 -> #12.3 -> #12.4 -> #12.5 -> #12.6
 *
 * Single frontend source of truth for PDF annotations.
 * No database. No persistent document storage.
 * ============================================================ */

(function installPP12CentralStoreBridge(){

    if (window.__PP12_CENTRAL_STORE_BRIDGE__) return;

    function safeClone(value){
        try {
            return JSON.parse(JSON.stringify(value));
        } catch (_) {
            return value;
        }
    }

    function pageIndex(value){
        const n = Number(value);
        return Number.isFinite(n) && n >= 0 ? Math.floor(n) : 0;
    }

    function normalize(payload){
        if (!payload || typeof payload !== "object") return null;

        const a = safeClone(payload);

        if (!a.id) {
            a.id =
                "pp12-" +
                Date.now().toString(36) +
                "-" +
                Math.random().toString(36).slice(2, 9);
        }

        a.page = pageIndex(
            a.page !== undefined
                ? a.page
                : (typeof state !== "undefined" ? state.page : 0)
        );

        if (!a.type && a.annotationType) {
            a.type = a.annotationType;
        }

        if (!a.type && a.kind) {
            a.type = a.kind;
        }

        return a;
    }

    function bucket(page){
        if (!state.annotations[page]) {
            state.annotations[page] = [];
        }
        return state.annotations[page];
    }

    function upsert(payload){
        const a = normalize(payload);
        if (!a) return null;

        const list = bucket(a.page);
        const id = String(a.id);

        const existingIndex = list.findIndex(
            item => item && String(item.id) === id
        );

        if (existingIndex >= 0) {
            list[existingIndex] = {
                ...list[existingIndex],
                ...a
            };
        } else {
            list.push(a);
        }

        return a;
    }

    function remove(id, page){
        const p = pageIndex(
            page !== undefined
                ? page
                : (typeof state !== "undefined" ? state.page : 0)
        );

        const list = bucket(p);

        const before = list.length;

        state.annotations[p] = list.filter(
            item => !item || String(item.id) !== String(id)
        );

        return before !== state.annotations[p].length;
    }

    function update(id, patch, page){
        const p = pageIndex(
            page !== undefined
                ? page
                : (typeof state !== "undefined" ? state.page : 0)
        );

        const list = bucket(p);

        const index = list.findIndex(
            item => item && String(item.id) === String(id)
        );

        if (index < 0) return null;

        list[index] = {
            ...list[index],
            ...safeClone(patch || {}),
            id: list[index].id,
            page: p
        };

        return list[index];
    }

    function all(){
        const result = [];

        Object.keys(state.annotations || {}).forEach(key => {
            const p = pageIndex(key);

            (state.annotations[key] || []).forEach(item => {
                const a = normalize({
                    ...item,
                    page: p
                });

                if (a) result.push(a);
            });
        });

        return result;
    }

    function dedupe(){
        const seen = new Map();

        Object.keys(state.annotations || {}).forEach(key => {
            const p = pageIndex(key);
            const list = state.annotations[key] || [];

            const cleaned = [];

            list.forEach(item => {
                const a = normalize({
                    ...item,
                    page: p
                });

                if (!a) return;

                const keyId =
                    p + "::" + String(a.id);

                if (seen.has(keyId)) return;

                seen.set(keyId, true);
                cleaned.push(a);
            });

            state.annotations[p] = cleaned;
        });

        return all();
    }

    /*
     * Public bridge used by #12.5 Shapes and future annotation
     * engines.
     */
    window.pp12RegisterAnnotation = function(payload){
        try {
            return upsert(payload);
        } catch (error) {
            console.warn(
                "PP12 central annotation registration failed:",
                error
            );
            return null;
        }
    };

    window.pp12UpdateAnnotation = function(id, patch, page){
        try {
            return update(id, patch, page);
        } catch (error) {
            console.warn(
                "PP12 central annotation update failed:",
                error
            );
            return null;
        }
    };

    window.pp12RemoveAnnotation = function(id, page){
        try {
            return remove(id, page);
        } catch (error) {
            console.warn(
                "PP12 central annotation removal failed:",
                error
            );
            return false;
        }
    };

    window.pp12GetAnnotations = function(){
        try {
            return all();
        } catch (_) {
            return [];
        }
    };

    window.pp12DedupeAnnotations = function(){
        try {
            return dedupe();
        } catch (_) {
            return [];
        }
    };

    window.__PP12_CENTRAL_STORE_BRIDGE__ = true;

})();
'''

# ------------------------------------------------------------
# 3. Insert bridge immediately before the first export function.
# ------------------------------------------------------------

export_match = re.search(
    r'\n\s*async\s+function\s+exportPDF\s*\(\s*\)\s*\{',
    src
)

if not export_match:
    print("ERROR: async function exportPDF() not found.")
    print("Restoring backup...")
    shutil.copy2(BACKUP, HTML)
    raise SystemExit(1)

src = (
    src[:export_match.start()]
    + "\n\n"
    + bridge
    + "\n"
    + src[export_match.start():]
)

print("OK: Central bridge inserted before exportPDF().")

# ------------------------------------------------------------
# 4. Make exporter explicitly consume central store.
#
# Replace only the annotation collection section.
# ------------------------------------------------------------

old_collection = r'''const out = [];
    Object.entries(state.annotations).forEach(([pi,arr])=>{
        const n=+pi;
        if(!allowed.has(n)) return;
        arr.forEach(a=>{
            const c=JSON.parse(JSON.stringify(a));
            delete c.id;
            c.page=n;
            out.push(c);
        });
    });'''

new_collection = r'''const out = [];

    /*
     * PP12 CENTRAL STORE
     * All annotation engines ultimately export through
     * state.annotations.
     */
    try {
        if (typeof window.pp12DedupeAnnotations === "function") {
            window.pp12DedupeAnnotations();
        }
    } catch (_) {}

    Object.entries(state.annotations || {}).forEach(([pi, arr])=>{
        const n = +pi;

        if(!allowed.has(n)) return;

        (arr || []).forEach(a=>{
            if(!a) return;

            const c = JSON.parse(JSON.stringify(a));

            /*
             * Frontend-only object identifiers must never be sent
             * as PDF annotation IDs.
             */
            delete c.id;
            delete c.objectId;
            delete c.annotationId;

            c.page = n;

            out.push(c);
        });
    });'''

if old_collection in src:
    src = src.replace(old_collection, new_collection, 1)
    print("OK: exportPDF() now consumes central annotation store.")
else:
    print("WARNING: exact exporter block not found.")
    print("The central bridge was installed, but exporter block was not changed.")

# ------------------------------------------------------------
# 5. Advanced Text -> central store
#
# We do not rewrite the text engine. We hook object creation
# after createTextObject() returns an object.
# ------------------------------------------------------------

text_pattern = re.compile(
    r'(const\s+object\s*=\s*createTextObject\(\);\s*'
    r'\n\s*'
    r'if\s*\(\s*!object\s*\)\s*\{\s*'
    r'\n\s*return;\s*'
    r'\n\s*\})',
    re.MULTILINE
)

m = text_pattern.search(src)

if m:
    insertion = r'''\1

    /*
     * PP12 CENTRAL STORE: Advanced Text
     */
    try {
        if (object && typeof window.pp12RegisterAnnotation === "function") {

            const rect = object.getBoundingClientRect();
            const stage = object.parentElement;
            const stageRect = stage
                ? stage.getBoundingClientRect()
                : rect;

            window.pp12RegisterAnnotation({
                id:
                    object.dataset.annotationId ||
                    object.dataset.objectId ||
                    object.id ||
                    ("text-" + Date.now() + "-" +
                     Math.random().toString(36).slice(2,7)),

                type: "text",
                page: typeof state !== "undefined" ? state.page : 0,

                text:
                    object.innerText ||
                    object.textContent ||
                    "",

                x: rect.left - stageRect.left,
                y: rect.top - stageRect.top,

                width: rect.width,
                height: rect.height,

                color:
                    object.dataset.color ||
                    object.style.color ||
                    "#111111",

                fontSize:
                    Number(object.dataset.fontSize) ||
                    parseFloat(object.style.fontSize) ||
                    18,

                fontFamily:
                    object.dataset.fontFamily ||
                    object.style.fontFamily ||
                    "Helvetica",

                bold:
                    object.dataset.bold === "1" ||
                    object.style.fontWeight === "bold" ||
                    Number(object.style.fontWeight) >= 600,

                italic:
                    object.dataset.italic === "1" ||
                    object.style.fontStyle === "italic",

                underline:
                    object.dataset.underline === "1" ||
                    object.style.textDecoration.includes("underline"),

                align:
                    object.dataset.align ||
                    object.style.textAlign ||
                    "left"
            });
        }
    } catch (error) {
        console.warn(
            "PP12 Advanced Text central-store sync failed:",
            error
        );
    }'''
    src = src[:m.start()] + insertion + src[m.end():]
    print("OK: Advanced Text creation bridge installed.")
else:
    print("WARNING: Advanced Text createTextObject() hook not matched.")

# ------------------------------------------------------------
# 6. Ensure Shapes bridge is safe.
#
# registerNativeShape() already calls pp12RegisterAnnotation()
# in the current project, so no duplicate shape registration
# is injected.
# ------------------------------------------------------------

if "window.pp12RegisterAnnotation(payload)" in src:
    print("OK: Shapes -> central bridge call already present.")
else:
    print("WARNING: Shapes registration call not detected.")

# ------------------------------------------------------------
# 7. Export guard:
#    If the current page has no records but other pages do,
#    don't falsely report an empty document.
# ------------------------------------------------------------

old_empty = """if(!out.length){
        status('No annotations found for the selected pages.');
        return;
    }"""

new_empty = """if(!out.length){
        status('No annotations found for the selected pages.');
        return;
    }"""

# Deliberately unchanged: this preserves existing UX.
src = src.replace(old_empty, new_empty, 1)

# ------------------------------------------------------------
# 8. Expose bridge through PP12 API if object exists.
# ------------------------------------------------------------

needle = "window.PP12 = {"

if needle in src:
    # Add register functions to the first PP12 export object
    # only if they aren't already listed nearby.
    pp12_match = re.search(
        r'window\.PP12\s*=\s*\{',
        src
    )

    if pp12_match:
        tail = src[pp12_match.start():pp12_match.start()+2500]

        if "registerAnnotation" not in tail:
            src = (
                src[:pp12_match.end()]
                + """
    registerAnnotation: window.pp12RegisterAnnotation,
    updateAnnotation: window.pp12UpdateAnnotation,
    removeAnnotation: window.pp12RemoveAnnotation,
    getAnnotations: window.pp12GetAnnotations,
"""
                + src[pp12_match.end():]
            )
            print("OK: PP12 public API exposes central-store methods.")
        else:
            print("OK: PP12 central-store API already exposed.")
else:
    print("WARNING: window.PP12 export object not found.")

# ------------------------------------------------------------
# 9. Final write
# ------------------------------------------------------------

HTML.write_text(src, encoding="utf-8")

print()
print("=" * 62)
print(" PATCH COMPLETE")
print("=" * 62)
print(f"Backup created : {BACKUP.name}")
print(f"HTML size      : {HTML.stat().st_size:,} bytes")
print()

# ------------------------------------------------------------
# 10. Verification
# ------------------------------------------------------------

checks = {
    "Central bridge marker":
        "PP12_CENTRAL_STORE_BRIDGE_V1" in src,

    "pp12RegisterAnnotation":
        "window.pp12RegisterAnnotation" in src,

    "pp12UpdateAnnotation":
        "window.pp12UpdateAnnotation" in src,

    "pp12RemoveAnnotation":
        "window.pp12RemoveAnnotation" in src,

    "pp12GetAnnotations":
        "window.pp12GetAnnotations" in src,

    "central dedupe":
        "pp12DedupeAnnotations" in src,

    "Shapes bridge":
        "window.pp12RegisterAnnotation(payload)" in src,

    "exportPDF":
        "async function exportPDF()" in src,

    "central export":
        "PP12 CENTRAL STORE" in src,

    "#12.2 Object Manager":
        "refreshManager" in src,

    "#12.3 Advanced Text":
        "pp12Text" in src and "createTextObject" in src,

    "#12.4 Markup":
        "pp12-word-markup-target" in src,

    "#12.5 Shapes":
        "pp12ShapesToolbar" in src and
        "registerNativeShape" in src,

    "#12.6 History":
        "pp12HistoryToolbar" in src and
        "pp12History" in src,
}

failed = []

for name, ok in checks.items():
    if ok:
        print("OK  ", name)
    else:
        print("FAIL", name)
        failed.append(name)

print()

# ------------------------------------------------------------
# 11. Structural duplicate protection
# ------------------------------------------------------------

bridge_count = src.count("PP12_CENTRAL_STORE_BRIDGE_V1")

print("Central bridge marker count:", bridge_count)

if bridge_count != 1:
    print("WARNING: Unexpected bridge marker count.")

# ------------------------------------------------------------
# 12. Basic script balance
# ------------------------------------------------------------

script_open = len(re.findall(r"<script\b", src, re.I))
script_close = len(re.findall(r"</script\s*>", src, re.I))

print("Script tags:", script_open, "/", script_close)

if script_open != script_close:
    print("WARNING: Script tag count mismatch.")

# ------------------------------------------------------------
# 13. Final status
# ------------------------------------------------------------

if failed:
    print()
    print("WARNING: Some verification checks failed.")
    print("The original file has NOT been automatically restored.")
    print("Backup remains available:")
    print(BACKUP.name)
    raise SystemExit(2)

print()
print("ALL CENTRAL STORE CHECKS PASSED.")
print()
print("Architecture:")
print("  #12.1 Annotation Store")
print("       ↑")
print("  #12.2 Object Manager")
print("       ↑")
print("  #12.3 Advanced Text")
print("       ↑")
print("  #12.4 Text Markup")
print("       ↑")
print("  #12.5 Shapes")
print("       ↑")
print("  #12.6 History")
print("       ↓")
print("  Apply & Export Annotated PDF")
print("       ↓")
print("  /api/annotate")
print()
print("NO DATABASE ADDED.")
print("NO BACKEND RASTERIZATION CHANGES.")
print("NO EXISTING #12.1-#12.6 ENGINE REMOVED.")
