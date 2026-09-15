from pathlib import Path
from datetime import datetime
import shutil
import re
import sys

HTML = Path("static/index.html")

if not HTML.exists():
    print("ERROR: static/index.html not found")
    sys.exit(1)

src = HTML.read_text(encoding="utf-8")

MARK = "PP12_ANNOTATION_DEDICATED_TAB_V1"

if MARK in src:
    print("Annotation dedicated tab is already installed.")
    sys.exit(0)

# ------------------------------------------------------------
# Backup
# ------------------------------------------------------------

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = HTML.with_name(
    f"index.html.before_annotation_tab_{stamp}.bak"
)

shutil.copy2(HTML, backup)

# ------------------------------------------------------------
# Verify existing annotation studio
# ------------------------------------------------------------

studio_pattern = (
    r'<section[^>]*id=["\']pp12AnnotationStudio["\'][^>]*>'
)

studio_match = re.search(studio_pattern, src, re.I)

if not studio_match:
    print("ERROR: pp12AnnotationStudio section not found.")
    print("Restoring backup...")
    shutil.copy2(backup, HTML)
    sys.exit(2)

# ------------------------------------------------------------
# CSS
# ------------------------------------------------------------

css = r'''
<style id="pp12DedicatedAnnotationTabCSS">

/* ============================================================
   PP12_ANNOTATION_DEDICATED_TAB_V1
   Professional Annotation Studio dedicated workspace
   ============================================================ */

/* Normal application/dashboard:
   Annotation Studio must NEVER occupy dashboard flow. */
body:not(.pp12-annotation-tab-active)
#pp12AnnotationStudio {
    display: none !important;
}

/* Dedicated Annotation Studio mode */
body.pp12-annotation-tab-active
#pp12AnnotationStudio {
    display: block !important;
    position: relative !important;
    inset: auto !important;
    width: 100% !important;
    max-width: none !important;
    min-height: calc(100vh - 24px) !important;
    margin: 0 !important;
    z-index: 100 !important;
    overflow: visible !important;
}

/* Make the annotation workspace feel like a real application tab */
body.pp12-annotation-tab-active {
    overflow-x: hidden !important;
}

body.pp12-annotation-tab-active
#pp12AnnotationStudio
.pp12-annotation-tab-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin: 0 0 14px 0;
    padding: 12px 14px;
    border: 1px solid rgba(120,120,180,.18);
    border-radius: 14px;
    background: rgba(255,255,255,.92);
    box-shadow: 0 8px 28px rgba(30,30,80,.08);
}

.pp12-annotation-tab-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
    font-size: 14px;
}

.pp12-annotation-tab-title-icon {
    width: 32px;
    height: 32px;
    display: grid;
    place-items: center;
    border-radius: 9px;
    background: #f0edff;
}

.pp12-annotation-back-btn {
    appearance: none;
    border: 1px solid rgba(80,80,160,.18);
    border-radius: 9px;
    padding: 8px 13px;
    background: white;
    cursor: pointer;
    font-weight: 650;
    font-size: 12px;
    transition: .18s ease;
}

.pp12-annotation-back-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 5px 15px rgba(40,40,100,.12);
}

.pp12-annotation-back-btn:active {
    transform: translateY(0);
}

/* Dedicated mode hides the normal dashboard/tool sections.
   Nested sections INSIDE Annotation Studio are preserved. */
body.pp12-annotation-tab-active
.pp12-dedicated-hidden {
    display: none !important;
}

/* Keep the sidebar usable */
body.pp12-annotation-tab-active
.sidebar {
    position: sticky;
    top: 0;
}

/* Mobile */
@media (max-width: 800px) {
    body.pp12-annotation-tab-active
    #pp12AnnotationStudio {
        min-height: 100vh !important;
    }

    body.pp12-annotation-tab-active
    #pp12AnnotationStudio
    .pp12-annotation-tab-header {
        flex-direction: column;
        align-items: stretch;
    }

    .pp12-annotation-back-btn {
        width: 100%;
    }
}

</style>
'''

# Insert CSS before </head>
if "</head>" in src.lower():
    pos = re.search(r"</head>", src, re.I).start()
    src = src[:pos] + css + "\n" + src[pos:]
else:
    src = css + "\n" + src

# ------------------------------------------------------------
# Header / Back button
# ------------------------------------------------------------

header = r'''
<div class="pp12-annotation-tab-header">
    <div class="pp12-annotation-tab-title">
        <span class="pp12-annotation-tab-title-icon">🖊️</span>
        <span>Professional PDF Annotation Studio</span>
    </div>

    <button
        type="button"
        class="pp12-annotation-back-btn"
        onclick="window.pp12CloseAnnotationStudio()"
        aria-label="Back to dashboard"
    >
        ← Back to Dashboard
    </button>
</div>
'''

# Insert only once, immediately after annotation section opening tag
studio_match = re.search(studio_pattern, src, re.I)

if not studio_match:
    print("ERROR: Annotation Studio disappeared during patch.")
    shutil.copy2(backup, HTML)
    sys.exit(3)

insert_at = studio_match.end()

src = (
    src[:insert_at]
    + "\n"
    + header
    + "\n"
    + src[insert_at:]
)

# ------------------------------------------------------------
# JavaScript controller
# ------------------------------------------------------------

js = r'''
<script id="pp12DedicatedAnnotationTabJS">
/* ============================================================
   PP12_ANNOTATION_DEDICATED_TAB_V1
   Dedicated Annotation Studio controller
   ============================================================ */

(function () {

    if (window.__PP12_ANNOTATION_TAB_V1__) {
        return;
    }

    window.__PP12_ANNOTATION_TAB_V1__ = true;

    const STUDIO_ID = "pp12AnnotationStudio";
    const HIDDEN_ATTR = "data-pp12-annotation-hidden";

    function studio() {
        return document.getElementById(STUDIO_ID);
    }

    function topLevelSection(section) {
        /*
         * Return true only for sections that are not nested
         * inside another section.
         */
        return !section.parentElement?.closest("section");
    }

    function hideNormalSections() {

        document.querySelectorAll("section").forEach(function (section) {

            const s = studio();

            if (!s) return;

            /*
             * Keep the Annotation Studio and anything nested
             * inside it completely untouched.
             */
            if (
                section === s ||
                s.contains(section)
            ) {
                return;
            }

            if (!topLevelSection(section)) {
                return;
            }

            if (!section.hasAttribute(HIDDEN_ATTR)) {
                section.setAttribute(HIDDEN_ATTR, "1");
                section.dataset.pp12OriginalDisplay =
                    section.style.display || "";
            }

            section.style.display = "none";
        });
    }

    function restoreNormalSections() {

        document.querySelectorAll(
            "section[" + HIDDEN_ATTR + "]"
        ).forEach(function (section) {

            const original =
                section.dataset.pp12OriginalDisplay || "";

            section.style.display = original;

            section.removeAttribute(HIDDEN_ATTR);
            delete section.dataset.pp12OriginalDisplay;
        });
    }

    window.pp12OpenAnnotationStudio = function () {

        const s = studio();

        if (!s) {
            console.warn(
                "PrivatePDF Pro: Annotation Studio not found."
            );
            return;
        }

        hideNormalSections();

        document.body.classList.add(
            "pp12-annotation-tab-active"
        );

        /*
         * Do not call the old scrollIntoView dashboard logic.
         * This is now a dedicated workspace.
         */
        window.scrollTo({
            top: 0,
            behavior: "instant"
        });

        /*
         * Give the studio a short activation event so any
         * existing annotation initialization can detect it.
         */
        try {
            window.dispatchEvent(
                new CustomEvent(
                    "pp12:annotation-studio-open"
                )
            );
        } catch (_) {}
    };

    window.pp12CloseAnnotationStudio = function () {

        restoreNormalSections();

        document.body.classList.remove(
            "pp12-annotation-tab-active"
        );

        window.scrollTo({
            top: 0,
            behavior: "instant"
        });

        try {
            window.dispatchEvent(
                new CustomEvent(
                    "pp12:annotation-studio-close"
                )
            );
        } catch (_) {}

        /*
         * Return to the dashboard through the existing
         * navigation system when available.
         */
        try {
            if (typeof window.show === "function") {
                window.show("dashboard", null);
            }
        } catch (_) {}
    };

    /*
     * Intercept any existing "Annotation Studio" navigation
     * button/link. This avoids changing existing sidebar HTML
     * and prevents the old scroll-to-section behavior.
     */
    document.addEventListener(
        "click",
        function (event) {

            const target =
                event.target.closest(
                    "button, a, [role='button']"
                );

            if (!target) return;

            const text =
                (target.textContent || "")
                .replace(/\s+/g, " ")
                .trim();

            if (!/annotation\s+studio/i.test(text)) {
                return;
            }

            /*
             * Don't intercept the Back button we inserted.
             */
            if (
                target.classList.contains(
                    "pp12-annotation-back-btn"
                )
            ) {
                return;
            }

            event.preventDefault();
            event.stopPropagation();

            window.pp12OpenAnnotationStudio();
        },
        true
    );

    /*
     * Escape = return to dashboard while studio is open.
     */
    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape" &&
                document.body.classList.contains(
                    "pp12-annotation-tab-active"
                )
            ) {
                window.pp12CloseAnnotationStudio();
            }
        }
    );

})();
</script>
'''

# Insert before </body>
if "</body>" in src.lower():
    pos = re.search(r"</body>", src, re.I).start()
    src = src[:pos] + "\n" + js + "\n" + src[pos:]
else:
    src += "\n" + js

# ------------------------------------------------------------
# Final checks
# ------------------------------------------------------------

checks = [
    ("V1 marker", MARK in src),
    ("Annotation Studio exists",
     'id="pp12AnnotationStudio"' in src),
    ("Dedicated CSS",
     "pp12DedicatedAnnotationTabCSS" in src),
    ("Dedicated JS",
     "pp12DedicatedAnnotationTabJS" in src),
    ("Open controller",
     "pp12OpenAnnotationStudio" in src),
    ("Close controller",
     "pp12CloseAnnotationStudio" in src),
    ("Dedicated body class",
     "pp12-annotation-tab-active" in src),
    ("Back button",
     "pp12-annotation-back-btn" in src),
    ("Annotation API untouched",
     "/api/annotate" in src),
]

print("=" * 72)
print(" ANNOTATION STUDIO — DEDICATED TAB INSTALL")
print("=" * 72)
print()
print("Backup:", backup.name)
print()

for name, ok in checks:
    print(("OK   " if ok else "FAIL ") + name)

if not all(ok for _, ok in checks):
    print()
    print("ERROR: Verification failed.")
    print("Restoring backup...")
    shutil.copy2(backup, HTML)
    sys.exit(4)

# ------------------------------------------------------------
# Basic HTML sanity checks
# ------------------------------------------------------------

if src.lower().count("<html") != src.lower().count("</html>"):
    print("WARNING: HTML tag count looks unusual.")

if src.lower().count("<script") < src.lower().count("</script>"):
    print("ERROR: Script tags appear unbalanced.")
    print("Restoring backup...")
    shutil.copy2(backup, HTML)
    sys.exit(5)

HTML.write_text(src, encoding="utf-8")

print()
print("=" * 72)
print(" ANNOTATION TAB INSTALL COMPLETE")
print("=" * 72)
print()
print("Annotation Studio is now:")
print("  ✓ Hidden from dashboard")
print("  ✓ Opened as dedicated workspace")
print("  ✓ Existing sidebar button intercepted")
print("  ✓ Back to Dashboard button added")
print("  ✓ Escape closes the workspace")
print("  ✓ Existing annotation engine preserved")
print("  ✓ Existing annotation export preserved")
print()
print("Hard refresh browser with Ctrl+F5.")
print()
