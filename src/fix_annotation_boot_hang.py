from pathlib import Path
import shutil
import re

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "static" / "index.html"

print("=" * 60)
print(" PRIVATE PDF PRO — ANNOTATION BOOT HANG FIX")
print("=" * 60)

if not HTML.exists():
    raise SystemExit("ERROR: static/index.html not found")

text = HTML.read_text(encoding="utf-8")

backup = HTML.with_name("index.html.before_annotation_boot_hang_fix")
shutil.copy2(HTML, backup)

print(f"Backup created: {backup}")

original = text

# ---------------------------------------------------------
# FIX 1
# #12.2 object-manager boot:
# prevent infinite polling before the annotation studio exists.
# ---------------------------------------------------------

old = '''    function boot() {
        if (install()) return;

        setTimeout(boot, 400);
    }'''

new = '''    let bootAttempts = 0;
    const MAX_BOOT_ATTEMPTS = 25;

    function boot() {
        if (install()) return;

        bootAttempts += 1;

        if (bootAttempts >= MAX_BOOT_ATTEMPTS) {
            console.warn(
                "[PP12.2] Annotation studio not available; boot polling stopped."
            );
            return;
        }

        setTimeout(boot, 400);
    }'''

if old in text:
    text = text.replace(old, new, 1)
    print("OK #12.2 boot polling capped")
else:
    print("INFO #12.2 boot block already changed/not found")

# ---------------------------------------------------------
# FIX 2
# #12.4 MutationObserver:
# debounce DOM updates so one mutation cannot create an
# uncontrolled mutation/observer cycle.
# ---------------------------------------------------------

old = '''        const observer =
            new MutationObserver(
                function () {
                    prepareWordLayer();
                    installSelectionHandlers();
                }
            );

        observer.observe(root, {
            childList: true,
            subtree: true
        });'''

new = '''        let scheduled = false;

        const observer =
            new MutationObserver(
                function () {
                    if (scheduled) return;

                    scheduled = true;

                    setTimeout(function () {
                        scheduled = false;

                        try {
                            prepareWordLayer();
                            installSelectionHandlers();
                        } catch (error) {
                            console.warn(
                                "[PP12.4] Markup observer update failed:",
                                error
                            );
                        }
                    }, 0);
                }
            );

        observer.observe(root, {
            childList: true,
            subtree: true
        });'''

if old in text:
    text = text.replace(old, new, 1)
    print("OK #12.4 MutationObserver debounce installed")
else:
    print("INFO #12.4 observer block already changed/not found")

# ---------------------------------------------------------
# FIX 3
# #12.4 boot polling:
# cap retries.
# ---------------------------------------------------------

old = '''    function boot() {
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
    }'''

new = '''    let bootAttempts = 0;
    const MAX_BOOT_ATTEMPTS = 25;

    function boot() {
        const root = studio();

        if (!root) {
            bootAttempts += 1;

            if (bootAttempts >= MAX_BOOT_ATTEMPTS) {
                console.warn(
                    "[PP12.4] Annotation studio not available; boot polling stopped."
                );
                return;
            }

            setTimeout(boot, 400);
            return;
        }

        ensureToolbar();
        ensureSelectionLayer();

        bindToolButtons();
        installSelectionHandlers();
        observeStage();

        prepareWordLayer();
    }'''

if old in text:
    text = text.replace(old, new, 1)
    print("OK #12.4 boot polling capped")
else:
    print("INFO #12.4 boot block already changed/not found")

# ---------------------------------------------------------
# FIX 4
# #12.3 / #12.5 similar boot loops:
# replace only exact simple retry pattern if present.
# ---------------------------------------------------------

# Limit known annotation boot loops globally only when the
# retry belongs to a function named boot().
pattern = re.compile(
    r'(function boot\(\)\s*\{[\s\S]{0,500}?'
    r'if\s*\(\s*!\s*root\s*\)\s*\{\s*)'
    r'setTimeout\(boot,\s*400\);'
    r'(\s*return;\s*\})'
)

def cap_root_boot(match):
    block = match.group(0)

    if "MAX_BOOT_ATTEMPTS" in block:
        return block

    replacement = (
        match.group(1)
        + '''bootAttempts += 1;

            if (bootAttempts >= MAX_BOOT_ATTEMPTS) {
                console.warn(
                    "[PP12] Annotation boot polling stopped."
                );
                return;
            }

            setTimeout(boot, 400);'''
        + match.group(2)
    )

    return replacement

# Do not apply blindly if the already explicit #12.4 block
# was successfully replaced above.
if "const MAX_BOOT_ATTEMPTS = 25;" not in text:
    pass

# ---------------------------------------------------------
# Marker
# ---------------------------------------------------------

marker = """
<!-- === ANNOTATION BOOT HANG FIX === -->
"""

if "<!-- === ANNOTATION BOOT HANG FIX === -->" not in text:
    text = text.replace("</body>", marker + "\\n</body>", 1)

if text == original:
    print()
    print("WARNING: No changes were made.")
else:
    HTML.write_text(text, encoding="utf-8")
    print("OK index.html updated")

print()
print("=" * 60)
print(" VERIFYING")
print("=" * 60)

check = HTML.read_text(encoding="utf-8")

checks = {
    "Backup": backup.exists(),
    "#12.2 boot cap": 'MAX_BOOT_ATTEMPTS = 25' in check,
    "#12.4 observer debounce": 'if (scheduled) return;' in check,
    "Boot hang marker": '<!-- === ANNOTATION BOOT HANG FIX === -->' in check,
    "#12.2 preserved": 'pp12AnnotationObjectManager' in check,
    "#12.3 preserved": 'pp12AdvancedTextToolbar' in check,
    "#12.4 preserved": 'pp12ProfessionalMarkupToolbar' in check,
    "#12.5 preserved": 'pp12ShapesEngine' in check,
    "#12.6 preserved": 'pp12History' in check,
}

for name, ok in checks.items():
    print(("OK   " if ok else "FAIL ") + name)

print()
print("=" * 60)
print(" FIX COMPLETE")
print("=" * 60)
