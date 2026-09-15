from pathlib import Path
from datetime import datetime
import re
import shutil
import sys

ROOT = Path.cwd()
HTML = ROOT / "static" / "index.html"

if not HTML.exists():
    print("ERROR: static/index.html not found")
    sys.exit(1)

text = HTML.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = HTML.with_name(f"index.html.before_existing_highlight_fix_{stamp}.bak")
shutil.copy2(HTML, backup)

MARK = "PP12_EXISTING_PDF_HIGHLIGHT_FIX_V1"

if MARK in text:
    print("Already installed. Nothing duplicated.")
else:
    patch = r'''
<!-- PP12_EXISTING_PDF_HIGHLIGHT_FIX_V1 -->
<style id="pp12-existing-pdf-highlight-fix-css">
/*
 * Existing native PDF annotations are rendered inside the page image.
 * The transparent word-selection layer must always stay interactive.
 */
.pp12-word-layer,
.pp12-word-layer *,
.pp12-markup-word-layer,
.pp12-markup-word-layer * {
    pointer-events: auto !important;
}

.pp12-word-markup-target {
    pointer-events: auto !important;
    user-select: none !important;
    -webkit-user-select: none !important;
    cursor: crosshair !important;
}

.pp12-page-image {
    pointer-events: none !important;
}

.pp12-word-markup-target.pp12-word-selected {
    outline: none !important;
}
</style>

<script id="pp12-existing-pdf-highlight-fix-js">
(function () {
    "use strict";

    /*
     * Existing native annotations must NEVER block the text-selection
     * surface. We deliberately keep the PDF image passive and let the
     * transparent extracted-word layer receive pointer events.
     */

    function fixWordLayer(root) {
        if (!root) return;

        var selectors = [
            ".pp12-word-layer",
            ".pp12-markup-word-layer",
            ".pp12-word-layer-container",
            ".pp12-markup-layer"
        ];

        selectors.forEach(function (selector) {
            root.querySelectorAll(selector).forEach(function (layer) {
                layer.style.pointerEvents = "auto";
                layer.style.zIndex = "20";

                layer.querySelectorAll(
                    ".pp12-word-markup-target," +
                    "[data-word-index]," +
                    "[data-word]"
                ).forEach(function (word) {
                    word.style.pointerEvents = "auto";
                    word.style.userSelect = "none";
                    word.style.webkitUserSelect = "none";
                });
            });
        });

        root.querySelectorAll(
            ".pp12-page-image," +
            ".pp12-rendered-page," +
            ".pp12-page-preview"
        ).forEach(function (img) {
            /*
             * Never let the rendered PDF bitmap swallow pointer events.
             */
            if (
                img.tagName === "IMG" ||
                img.classList.contains("pp12-page-image")
            ) {
                img.style.pointerEvents = "none";
            }
        });
    }

    function getStudio() {
        return document.querySelector(
            "#pp12AnnotationStudio," +
            "#pp12Studio," +
            ".pp12-overlay"
        );
    }

    function install() {
        var root = getStudio();
        if (!root) return false;

        fixWordLayer(root);

        /*
         * Re-apply after page navigation/rendering, but do NOT create a
         * recursive observer. A small debounced observer is sufficient.
         */
        if (!root.__pp12ExistingHighlightObserver) {
            var timer = null;

            var observer = new MutationObserver(function () {
                if (timer) return;

                timer = setTimeout(function () {
                    timer = null;
                    fixWordLayer(root);
                }, 50);
            });

            observer.observe(root, {
                childList: true,
                subtree: true
            });

            root.__pp12ExistingHighlightObserver = observer;
        }

        return true;
    }

    function boot() {
        if (install()) return;
        setTimeout(boot, 500);
    }

    /*
     * Public helper for the existing markup engine.
     * It can safely call this after prepareWordLayer().
     */
    window.pp12FixExistingHighlightLayer = install;

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot, { once: true });
    } else {
        boot();
    }

})();
</script>
<!-- /PP12_EXISTING_PDF_HIGHLIGHT_FIX_V1 -->
'''

    # Insert before </body>, avoiding interference with existing scripts.
    pos = text.lower().rfind("</body>")
    if pos >= 0:
        text = text[:pos] + "\n" + patch + "\n" + text[pos:]
    else:
        text += "\n" + patch + "\n"

    HTML.write_text(text, encoding="utf-8")

print("=" * 70)
print(" EXISTING PDF HIGHLIGHT FIX")
print("=" * 70)
print("Backup:", backup.name)
print("Marker:", MARK in text)
print("HTML size:", len(text), "bytes")

# Structural checks
checks = {
    "CSS layer pointer-events": ".pp12-word-layer" in text,
    "Word target pointer-events": ".pp12-word-markup-target" in text,
    "PDF image passive": ".pp12-page-image" in text,
    "Fix function": "pp12FixExistingHighlightLayer" in text,
    "Mutation observer": "pp12ExistingHighlightObserver" in text,
}

for name, ok in checks.items():
    print(("OK   " if ok else "FAIL ") + name)

# Script balance
opens = len(re.findall(r"<script\b", text, flags=re.I))
closes = len(re.findall(r"</script>", text, flags=re.I))
print("Script tags:", opens, "/", closes)

if opens != closes:
    print("ERROR: script tag mismatch — restoring backup")
    shutil.copy2(backup, HTML)
    sys.exit(2)

print()
print("FIX INSTALLED SUCCESSFULLY")
print()
print("IMPORTANT:")
print("1. Restart Uvicorn.")
print("2. Browser: Ctrl+Shift+R")
print("3. Load the SAME Annotated_PDF.")
print("4. Go to page 6.")
print("5. Select Highlight.")
print("6. Drag across text that is already highlighted.")
print("7. Also test NEW unhighlighted text.")
print()
print("Backup remains available:", backup.name)
