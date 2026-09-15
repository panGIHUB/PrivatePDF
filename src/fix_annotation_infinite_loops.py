from pathlib import Path
import shutil
import re

HTML = Path("static/index.html")

if not HTML.exists():
    raise SystemExit("ERROR: static/index.html not found")

text = HTML.read_text(encoding="utf-8")

backup = HTML.with_name("index.html.before_annotation_infinite_loop_fix")
shutil.copy2(HTML, backup)

print("Backup created:")
print(backup)

original = text

# ============================================================
# FIX 1 — #12.2 OBJECT MANAGER
#
# The old observer watches:
#   childList + subtree + attributes(style/data...)
#
# Its callback calls refreshManager()/positionFrame(), which
# itself mutates the observed DOM.
#
# Disable this observer completely.
# Object Manager already refreshes explicitly from its own
# selection/move/delete/duplicate/layer operations.
# ============================================================

pattern_122 = re.compile(
    r'''(\s*function installObserver\(\) \{\s*)
        .*?
        (\s*\}\s*
        \n\s*function install\(\) \{)''',
    re.S | re.X
)

replacement_122 = r'''
    function installObserver() {
        /*
         * #12.2 HOTFIX
         *
         * The original MutationObserver watched the entire
         * annotation studio and also observed style/data
         * attributes. Its callback called refreshManager()
         * and positionFrame(), both of which mutate DOM.
         *
         * That created a self-triggering MutationObserver loop
         * and could freeze the browser.
         *
         * Object Manager now relies on explicit refresh calls
         * from selection/object operations instead.
         */
        if (observer) {
            try {
                observer.disconnect();
            } catch (_) {}
        }

        observer = null;
    }

    function install() {'''

m = pattern_122.search(text)

if m:
    text = text[:m.start()] + replacement_122 + text[m.end():]
    print("OK: #12.2 MutationObserver disabled safely")
else:
    print("WARNING: #12.2 installObserver block not matched")


# ============================================================
# FIX 2 — REMOVE LEFTOVER #12.7 BODY MUTATION OBSERVER
#
# Exact dangerous pattern:
#
#   new MutationObserver(install).observe(document.body,...)
#
# This can repeatedly execute install() whenever install()
# changes the body.
# ============================================================

pattern_body_observer = re.compile(
    r'''
    \n\s*new\s+MutationObserver\(\s*
        install
    \s*\)\s*
    \.observe\(\s*
        document\.body\s*,\s*
        \{\s*
            childList\s*:\s*true\s*,\s*
            subtree\s*:\s*true\s*
        \}\s*
    \)\s*;
    ''',
    re.S | re.X
)

text, removed = pattern_body_observer.subn(
    '''
    /*
     * #12.7 REMNANT HOTFIX
     *
     * Removed recursive document.body MutationObserver.
     * Initialization is already performed through
     * DOMContentLoaded / delayed install().
     */
    ''',
    text,
)

if removed:
    print(f"OK: Removed {removed} recursive body MutationObserver")
else:
    print("WARNING: #12.7 body MutationObserver pattern not found")


# ============================================================
# FIX 3 — SAFETY: REMOVE ANY OTHER EXACT install-on-body
# observer if formatting differs slightly.
# ============================================================

dangerous = re.compile(
    r'''
    new\s+MutationObserver\(\s*install\s*\)
    \s*\.\s*observe\(\s*document\.body\s*,\s*
    \{\s*childList\s*:\s*true\s*,\s*subtree\s*:\s*true\s*\}
    \s*\)\s*;
    ''',
    re.S | re.X
)

text, removed2 = dangerous.subn(
    '''
    /* recursive body install observer intentionally disabled */
    ''',
    text,
)

if removed2:
    print(f"OK: Removed {removed2} additional recursive observer(s)")


# ============================================================
# FIX 4 — SAFETY: Do not leave #12.2 observer active
# ============================================================

if "observer.observe(root" in text:
    # Only report. Do not blindly remove other observers because
    # #12.4/#12.5 may legitimately use their own observers.
    print("INFO: Other root observers remain; they are NOT blindly removed.")
else:
    print("INFO: No root observer calls remain.")


# ============================================================
# WRITE
# ============================================================

if text == original:
    print("ERROR: No changes were made.")
    raise SystemExit(2)

HTML.write_text(text, encoding="utf-8")

print()
print("==============================================")
print(" ANNOTATION INFINITE LOOP FIX COMPLETE")
print("==============================================")
print()
print("Backup:")
print(backup)
print()
