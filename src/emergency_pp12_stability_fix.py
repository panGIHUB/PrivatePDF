from pathlib import Path
import shutil

p = Path("static/index.html")

if not p.exists():
    raise SystemExit("ERROR: static/index.html not found")

backup = p.with_name("index.html.before_emergency_pp12_stability_fix")
shutil.copy2(p, backup)

text = p.read_text(encoding="utf-8")

print("Backup:", backup)

# ============================================================
# 1. KILL #12.2 MUTATION OBSERVER EXACTLY
# ============================================================

start_marker = "    function installObserver() {"
start = text.find(start_marker, text.find("function objectId"))

if start == -1:
    raise SystemExit("ERROR: #12.2 installObserver start not found")

end_marker = "    function install() {"
end = text.find(end_marker, start)

if end == -1:
    raise SystemExit("ERROR: #12.2 install() boundary not found")

new_function = r'''    function installObserver() {
        /*
         * #12.2 STABILITY FIX
         *
         * MutationObserver intentionally disabled.
         *
         * The previous observer watched the entire annotation
         * workspace including style/data attributes while its
         * callback called refreshManager() and positionFrame().
         * Those functions mutate the same DOM being observed.
         *
         * This created a recursive DOM mutation loop and could
         * freeze/refresh the browser.
         *
         * Object Manager uses explicit refresh calls instead.
         */
        if (observer) {
            try {
                observer.disconnect();
            } catch (_) {}
        }

        observer = null;
    }

'''

text = text[:start] + new_function + text[end:]

print("OK: #12.2 observer function replaced")


# ============================================================
# 2. DISABLE #12.4 OBSERVER SAFELY
#
# It is not currently the primary confirmed loop, but for the
# first stability test we remove all PP12 MutationObservers.
# Explicit selection still works.
# ============================================================

start_marker_24 = "    function observeEditor() {"
start24 = text.find(start_marker_24)

if start24 != -1:
    # Find next public API boundary
    end_marker_24 = "    /*\n     * Public API"
    end24 = text.find(end_marker_24, start24)

    if end24 != -1:
        replacement24 = r'''    function observeEditor() {
        /*
         * #12.4 STABILITY MODE
         *
         * Automatic MutationObserver scanning is disabled.
         * Text objects are processed by explicit editor actions.
         */
        return;
    }

'''
        text = text[:start24] + replacement24 + text[end24:]
        print("OK: #12.4 observer disabled")
    else:
        print("WARNING: #12.4 boundary not found")
else:
    print("INFO: #12.4 observeEditor() not found")


# ============================================================
# 3. DISABLE #12.4 observeStage()
# ============================================================

start_marker_stage = "    function observeStage() {"
start_stage = text.find(start_marker_stage)

if start_stage != -1:
    end_marker_stage = "    /*\n     * Public API"
    end_stage = text.find(end_marker_stage, start_stage)

    if end_stage != -1:
        replacement_stage = r'''    function observeStage() {
        /*
         * #12.4 STABILITY MODE
         *
         * Stage MutationObserver disabled to prevent automatic
         * DOM rescans during initial workspace construction.
         */
        return;
    }

'''
        text = text[:start_stage] + replacement_stage + text[end_stage:]
        print("OK: #12.4 stage observer disabled")
    else:
        print("WARNING: #12.4 observeStage boundary not found")
else:
    print("INFO: #12.4 observeStage() not found")


# ============================================================
# 4. REMOVE ANY REMAINING DIRECT BODY INSTALL OBSERVER
# ============================================================

danger = """new MutationObserver(
    install
).observe(
    document.body,
    {
        childList:true,
        subtree:true
    }
);"""

if danger in text:
    text = text.replace(
        danger,
        """/* #12.7 recursive body observer permanently disabled */"""
    )
    print("OK: recursive body observer removed")
else:
    print("OK: no recursive body observer found")


# ============================================================
# 5. WRITE FILE
# ============================================================

p.write_text(text, encoding="utf-8")

print()
print("==============================================")
print(" EMERGENCY PP12 STABILITY FIX INSTALLED")
print("==============================================")
