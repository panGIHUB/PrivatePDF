from pathlib import Path
import shutil
from datetime import datetime

HTML = Path("static/index.html")

if not HTML.exists():
    raise SystemExit("ERROR: static/index.html not found")

src = HTML.read_text(encoding="utf-8")

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = HTML.with_name(
    f"index.html.before_exporter_connection_{STAMP}.bak"
)

shutil.copy2(HTML, BACKUP)

print("=" * 64)
print(" PP12 EXPORTER -> CENTRAL STORE CONNECTION")
print("=" * 64)
print("Backup:", BACKUP.name)

# ------------------------------------------------------------
# Locate exportPDF
# ------------------------------------------------------------

export_pos = src.find("async function exportPDF()")

if export_pos < 0:
    raise SystemExit("ERROR: exportPDF() not found")

# ------------------------------------------------------------
# Locate exact collection block by structural anchors
# ------------------------------------------------------------

start_marker = "const out = [];"

start = src.find(start_marker, export_pos)

if start < 0:
    raise SystemExit(
        "ERROR: exporter annotation collection start not found"
    )

end_marker = "if(!out.length){"

end = src.find(end_marker, start)

if end < 0:
    raise SystemExit(
        "ERROR: exporter annotation collection end not found"
    )

old = src[start:end]

print()
print("Existing exporter collection found:")
print("  start:", start)
print("  end  :", end)
print("  bytes:", len(old))

# ------------------------------------------------------------
# New central-store collection
# ------------------------------------------------------------

new = r'''const out = [];

    /*
     * ========================================================
     * PP12 CENTRAL ANNOTATION STORE
     * ========================================================
     *
     * #12.1 owns state.annotations.
     *
     * #12.2 Object Manager
     * #12.3 Advanced Text
     * #12.4 Text Markup
     * #12.5 Shapes
     * #12.6 History
     *
     * must ultimately feed this store.
     */

    try {
        if (
            typeof window.pp12DedupeAnnotations === "function"
        ) {
            window.pp12DedupeAnnotations();
        }
    } catch (error) {
        console.warn(
            "PP12 central-store dedupe failed:",
            error
        );
    }

    /*
     * Collect ONLY the pages selected by Apply Mode.
     */
    Object.entries(
        state.annotations || {}
    ).forEach(
        ([pi, arr]) => {

            const n = Number(pi);

            if (!allowed.has(n)) {
                return;
            }

            (arr || []).forEach(
                annotation => {

                    if (
                        !annotation ||
                        typeof annotation !== "object"
                    ) {
                        return;
                    }

                    const c =
                        JSON.parse(
                            JSON.stringify(annotation)
                        );

                    /*
                     * These IDs are frontend object-management
                     * identifiers and must not be forwarded as
                     * native PDF annotation IDs.
                     */
                    delete c.id;
                    delete c.objectId;
                    delete c.annotationId;

                    c.page = n;

                    out.push(c);
                }
            );
        }
    );

    /*
     * Central-store diagnostic information.
     * This is intentionally console-only.
     */
    try {
        console.info(
            "[PP12 EXPORT]",
            "central annotations:",
            out.length
        );
    } catch (_) {}

    '''

src = src[:start] + new + src[end:]

HTML.write_text(src, encoding="utf-8")

print()
print("OK: exporter collection block replaced.")
print("OK: exporter now performs central-store dedupe.")
print("OK: exporter reads state.annotations after bridge sync.")
print()

# ------------------------------------------------------------
# Verify exact connection
# ------------------------------------------------------------

fresh = HTML.read_text(encoding="utf-8")

checks = {
    "Central bridge":
        "PP12_CENTRAL_STORE_BRIDGE_V1" in fresh,

    "Register":
        "window.pp12RegisterAnnotation" in fresh,

    "Update":
        "window.pp12UpdateAnnotation" in fresh,

    "Remove":
        "window.pp12RemoveAnnotation" in fresh,

    "Dedupe":
        "window.pp12DedupeAnnotations" in fresh,

    "Export function":
        "async function exportPDF()" in fresh,

    "Central export comment":
        "PP12 CENTRAL ANNOTATION STORE" in fresh,

    "Export console":
        "[PP12 EXPORT]" in fresh,

    "Advanced Text":
        "createTextObject" in fresh,

    "Shapes":
        "registerNativeShape" in fresh,

    "Markup":
        "pp12-word-markup-target" in fresh,

    "History":
        "pp12HistoryToolbar" in fresh,
}

failed = []

for name, result in checks.items():
    print(
        ("OK  " if result else "FAIL"),
        name
    )

    if not result:
        failed.append(name)

# ------------------------------------------------------------
# Check duplicate bridge
# ------------------------------------------------------------

print()
print(
    "Central bridge marker count:",
    fresh.count("PP12_CENTRAL_STORE_BRIDGE_V1")
)

# ------------------------------------------------------------
# Script balance
# ------------------------------------------------------------

opens = fresh.lower().count("<script")
closes = fresh.lower().count("</script>")

print("Script tags:", opens, "/", closes)

if opens != closes:
    failed.append("script-tag-balance")

# ------------------------------------------------------------
# Final
# ------------------------------------------------------------

print()

if failed:
    print("=" * 64)
    print(" PATCH FAILED VERIFICATION")
    print("=" * 64)
    print("Failed:", ", ".join(failed))
    print()
    print("Restoring backup...")
    shutil.copy2(BACKUP, HTML)
    print("RESTORED:", HTML)
    raise SystemExit(2)

print("=" * 64)
print(" EXPORTER CONNECTION COMPLETE")
print("=" * 64)
print()
print("Flow is now:")
print()
print("  Text / Markup / Shapes")
print("          ↓")
print("  pp12RegisterAnnotation()")
print("          ↓")
print("  state.annotations")
print("          ↓")
print("  pp12DedupeAnnotations()")
print("          ↓")
print("  exportPDF()")
print("          ↓")
print("  /api/annotate")
print("          ↓")
print("  Annotated_PDF.pdf")
print()
print("No backend changes.")
print("No database.")
print("No rasterization.")
print("No #12.1-#12.6 engine removal.")
