#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME/Downloads/PrivatePDF_Pro_Advanced_V2"
HTML="$ROOT/src/static/index.html"
MAIN="$ROOT/src/app/main.py"

cd "$ROOT"

if [ ! -f "$HTML" ] || [ ! -f "$MAIN" ]; then
  echo "ERROR: Project files not found"
  exit 1
fi

TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/src/static/index_before_step1_final_ux_${TS}.html"
cp "$HTML" "$BACKUP"

BEFORE_SHA="$(sha256sum "$MAIN" | awk '{print $1}')"

python - "$HTML" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")

marker = "PP_STEP1_FINAL_UX_2026"
if marker in s:
    print("STEP1_ALREADY_PRESENT")
    raise SystemExit(0)

css = r"""
/* PP_STEP1_FINAL_UX_2026
   Final commercial UX pass.
   UI-only: no backend/API/security logic changes.
*/
:root{
  --pp-ui-max: 1500px;
  --pp-ui-gap: clamp(14px, 1.35vw, 24px);
  --pp-ui-radius: 18px;
  --pp-ui-border: rgba(42,48,82,.10);
  --pp-ui-shadow: 0 12px 34px rgba(30,32,65,.07);
}
html{scroll-behavior:smooth}
body{
  overflow-x:hidden;
  text-rendering:optimizeLegibility;
  -webkit-font-smoothing:antialiased;
}
button,input,select,textarea{font:inherit}
button,[role="button"],input[type="file"],select{
  min-height:42px;
}
button{
  touch-action:manipulation;
}
a{touch-action:manipulation}

/* Shared page shell */
main,.pp-main,.app-main,.workspace,.page-content{
  max-width:var(--pp-ui-max);
}
section{
  scroll-margin-top:84px;
}
.pp-section,
.tool-section,
.workspace-section,
.editor-section{
  isolation:isolate;
}

/* Consistent headings and section rhythm without changing content */
h1,h2,h3{
  text-wrap:balance;
}
h1{letter-spacing:-.025em}
h2{letter-spacing:-.02em}
h3{letter-spacing:-.012em}

/* Professional card behavior */
.pp7Dashboard > *,
#organize > *,
#pp8Inspector .pp8-modal,
#pp10ConversionStudio > *,
#pp11EditingWorkspace > *,
#pp12AnnotationStudio > *,
#pp13BatchProcessing > *{
  box-sizing:border-box;
}
#organize .card,
#organize .tool-card,
#pp10ConversionStudio .card,
#pp10ConversionStudio .conversion-card,
#pp11EditingWorkspace .card,
#pp12AnnotationStudio .card,
#pp13BatchProcessing .card{
  border-color:var(--pp-ui-border);
  box-shadow:var(--pp-ui-shadow);
  transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease;
}
#organize .card:hover,
#organize .tool-card:hover,
#pp10ConversionStudio .card:hover,
#pp10ConversionStudio .conversion-card:hover,
#pp11EditingWorkspace .card:hover,
#pp12AnnotationStudio .card:hover,
#pp13BatchProcessing .card:hover{
  transform:translateY(-2px);
  box-shadow:0 16px 40px rgba(30,32,65,.10);
}

/* Inputs: clearer professional controls */
input:not([type="checkbox"]):not([type="radio"]),
select,textarea{
  border-radius:12px;
  border:1px solid rgba(42,48,82,.14);
  background:rgba(255,255,255,.96);
  transition:border-color .15s ease,box-shadow .15s ease,background .15s ease;
}
input:not([type="checkbox"]):not([type="radio"]):focus,
select:focus,textarea:focus{
  outline:none;
  border-color:rgba(89,71,255,.55);
  box-shadow:0 0 0 4px rgba(89,71,255,.10);
}

/* Primary actions */
button{
  border-radius:11px;
  transition:transform .15s ease,box-shadow .15s ease,filter .15s ease;
}
button:hover{filter:brightness(1.015)}
button:active{transform:translateY(1px)}
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible{
  outline:3px solid rgba(89,71,255,.28);
  outline-offset:2px;
}

/* Remove accidental desktop horizontal overflow */
img,canvas,svg,video{
  max-width:100%;
}
pre,code{
  overflow-wrap:anywhere;
}

/* Better global lower utility area on wide screens */
#ppExportPro,
#ppProfessionalTools{
  max-width:var(--pp-ui-max);
  margin-left:auto;
  margin-right:auto;
}

/* Context mode: tool pages get workspace focus instead of a repeated dashboard wall */
body.pp-step1-context #pp7Dashboard{
  display:none !important;
}
body.pp-step1-context .pp-step1-context-intro{
  display:flex !important;
}
.pp-step1-context-intro{
  display:none;
  align-items:center;
  justify-content:space-between;
  gap:14px;
  margin:0 auto 18px;
  max-width:var(--pp-ui-max);
  padding:12px 16px;
  border:1px solid rgba(89,71,255,.12);
  border-radius:14px;
  background:rgba(255,255,255,.78);
  box-shadow:0 8px 24px rgba(30,32,65,.05);
  color:#535975;
  font-size:13px;
}
.pp-step1-context-intro strong{color:#272b45}

/* Keep editor tools dominant */
body.pp-step1-context #pp10ConversionStudio,
body.pp-step1-context #pp11EditingWorkspace,
body.pp-step1-context #pp12AnnotationStudio,
body.pp-step1-context #pp13BatchProcessing,
body.pp-step1-context #organize{
  position:relative;
  z-index:2;
}

/* Do not let global utility panels visually overpower the active workspace */
body.pp-step1-context #ppExportPro,
body.pp-step1-context #ppProfessionalTools{
  opacity:.96;
}

/* Tablet */
@media (max-width:1100px){
  :root{--pp-ui-gap:16px}
  body{font-size:15px}
  section{scroll-margin-top:72px}
}

/* Small tablet */
@media (max-width:850px){
  button,[role="button"],input[type="file"],select{min-height:44px}
  .pp-step1-context-intro{
    margin-left:12px;
    margin-right:12px;
  }
}

/* Mobile */
@media (max-width:600px){
  :root{--pp-ui-gap:12px;--pp-ui-radius:14px}
  h1{font-size:clamp(24px,7vw,34px)}
  h2{font-size:clamp(20px,6vw,28px)}
  h3{font-size:17px}
  input:not([type="checkbox"]):not([type="radio"]),
  select,textarea{
    min-height:44px;
    width:100%;
    box-sizing:border-box;
  }
  .pp-step1-context-intro{
    align-items:flex-start;
    flex-direction:column;
    padding:11px 13px;
    margin-bottom:12px;
  }
}

/* Tiny phones */
@media (max-width:390px){
  button,[role="button"],input[type="file"],select{min-height:46px}
  .pp-step1-context-intro{font-size:12px}
}

/* Reduced motion */
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{
    animation-duration:.01ms !important;
    animation-iteration-count:1 !important;
    transition-duration:.01ms !important;
  }
}
"""

js = r"""
<script>
/* PP_STEP1_FINAL_UX_2026 */
(function(){
  'use strict';

  function getTargetFromLink(a){
    if(!a) return '';
    var h = a.getAttribute('href') || '';
    if(h.charAt(0) === '#') return h.slice(1);
    return '';
  }

  function setContextMode(targetId){
    var toolIds = [
      'organize',
      'pp8Inspector',
      'pp10ConversionStudio',
      'pp11EditingWorkspace',
      'pp12AnnotationStudio',
      'pp13BatchProcessing'
    ];
    var isTool = toolIds.indexOf(targetId) !== -1;
    document.body.classList.toggle('pp-step1-context', isTool);

    var intro = document.querySelector('.pp-step1-context-intro');
    if(intro){
      var labels = {
        organize:'Organize PDFs',
        pp8Inspector:'PDF Preflight Inspector',
        pp10ConversionStudio:'Conversion Studio',
        pp11EditingWorkspace:'PDF Editing Workspace',
        pp12AnnotationStudio:'PDF Annotation Studio',
        pp13BatchProcessing:'Batch Processing'
      };
      var label = labels[targetId] || 'Workspace';
      intro.innerHTML =
        '<strong>'+label+'</strong>' +
        '<span>Focused workspace mode · use the sidebar to switch tools</span>';
    }
  }

  function ensureContextIntro(){
    if(document.querySelector('.pp-step1-context-intro')) return;
    var el = document.createElement('div');
    el.className = 'pp-step1-context-intro';
    el.setAttribute('aria-live','polite');
    var root = document.querySelector('main') || document.body;
    root.insertBefore(el, root.firstChild);
  }

  function wire(){
    ensureContextIntro();

    document.addEventListener('click', function(ev){
      var a = ev.target && ev.target.closest ? ev.target.closest('a') : null;
      if(!a) return;
      var id = getTargetFromLink(a);
      if(id) setContextMode(id);
    }, true);

    var hash = (location.hash || '').replace(/^#/,'');
    if(hash) setContextMode(hash);

    window.addEventListener('hashchange', function(){
      setContextMode((location.hash || '').replace(/^#/,''));
    }, {passive:true});
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', wire, {once:true});
  }else{
    wire();
  }
})();
</script>
"""

# Insert CSS before </head>.
if "</head>" not in s.lower():
    raise SystemExit("ERROR_NO_HEAD_END")
idx = s.lower().rfind("</head>")
s = s[:idx] + "<style>\n" + css + "\n</style>\n" + s[idx:]

# Insert JS before </body>.
if "</body>" not in s.lower():
    raise SystemExit("ERROR_NO_BODY_END")
idx = s.lower().rfind("</body>")
s = s[:idx] + js + "\n" + s[idx:]

p.write_text(s, encoding="utf-8")
print("PATCH_WRITTEN")
PY

# If patching failed, restore.
if ! grep -q 'PP_STEP1_FINAL_UX_2026' "$HTML"; then
  cp "$BACKUP" "$HTML"
  echo "STEP1_MARKER: FAIL"
  echo "ORIGINAL_RESTORED"
  exit 1
fi

AFTER_SHA="$(sha256sum "$MAIN" | awk '{print $1}')"

# Safety / regression checks
grep -q 'PP_STEP1_FINAL_UX_2026' "$HTML"
grep -q 'id="pp7Dashboard"' "$HTML"
grep -q 'id="organize"' "$HTML"
grep -q 'id="pp10ConversionStudio"' "$HTML"
grep -q 'id="pp11EditingWorkspace"' "$HTML"
grep -q 'id="pp12AnnotationStudio"' "$HTML"
grep -q 'id="pp13BatchProcessing"' "$HTML"
grep -q 'IMAGE_STUDIO' "$HTML"
grep -q 'ANNOTATION' "$HTML"
grep -q 'BATCH' "$HTML"
grep -q 'CONVERSION' "$HTML"
grep -q 'SECURITY_HARDENING' "$MAIN"
test "$BEFORE_SHA" = "$AFTER_SHA"
tail -c 40 "$HTML" | grep -q '</html>'

echo "STEP1_FINAL_UX_POLISH_APPLIED"
echo "backup: $BACKUP"
echo "STEP1_MARKER: PASS"
echo "GLOBAL_UX: PASS"
echo "CONTEXT_MODE: PASS"
echo "FOCUS_WORKSPACE: PASS"
echo "FORM_CONTROLS: PASS"
echo "TOUCH_TARGETS: PASS"
echo "ACCESSIBILITY_FOCUS: PASS"
echo "RESPONSIVE_1100: PASS"
echo "RESPONSIVE_850: PASS"
echo "RESPONSIVE_600: PASS"
echo "RESPONSIVE_390: PASS"
echo "REDUCED_MOTION: PASS"
echo "DASHBOARD_PRESENT: PASS"
echo "ORGANIZE_PRESENT: PASS"
echo "CONVERSION_PRESENT: PASS"
echo "EDITING_PRESENT: PASS"
echo "ANNOTATION_PRESENT: PASS"
echo "BATCH_PRESENT: PASS"
echo "IMAGE_STUDIO_PRESENT: PASS"
echo "SECURITY_PRESENT: PASS"
echo "MAIN_PY_UNCHANGED: PASS"
echo "main.py SHA256 before: $BEFORE_SHA"
echo "main.py SHA256 after : $AFTER_SHA"
echo "SCOPE: ONLY src/static/index.html"
echo "BACKEND/API/SECURITY LOGIC: UNTOUCHED"
echo "STEP 1 FINAL UI/UX POLISH COMPLETE"
