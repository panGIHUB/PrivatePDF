from pathlib import Path
from datetime import datetime

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

backup = p.with_name(
    f"main.py.before_export_error_diagnostic_{datetime.now():%Y%m%d_%H%M%S}.bak"
)
backup.write_text(s, encoding="utf-8")

old = '''    except Exception as exc:
        clean()
        raise HTTPException(
            status_code=400,
            detail=f"Annotation export failed: {exc}"
        )
'''

new = '''    except Exception as exc:
        print("\\n" + "=" * 72)
        print("PP12 ANNOTATION EXPORT ERROR")
        print("=" * 72)
        print("Exception type:", type(exc).__name__)
        print("Exception:", repr(exc))
        print("Message:", str(exc))
        import traceback
        traceback.print_exc()
        print("=" * 72 + "\\n")

        clean()
        raise HTTPException(
            status_code=400,
            detail=f"Annotation export failed: {type(exc).__name__}: {exc}"
        )
'''

if old not in s:
    print("ERROR: expected /api/annotate exception block not found.")
    print("NO CHANGES MADE.")
    raise SystemExit(1)

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

compile(p, "app/main.py", "exec")

print("=" * 72)
print("PP12 EXPORT ERROR DIAGNOSTIC INSTALLED")
print("=" * 72)
print("Backup:", backup.name)
print("OK: /api/annotate now prints the real exception")
print("OK: Python syntax")
print()
print("Restart uvicorn and reproduce ONE export.")
print("The terminal will now show the exact failing annotation/type.")
print("=" * 72)
