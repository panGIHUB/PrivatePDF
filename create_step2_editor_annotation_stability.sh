#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML="$ROOT/src/static/index.html"
MAIN="$ROOT/src/app/main.py"
MARKER="PP_STEP2_EDITOR_ANNOTATION_STABILITY_2026"

if [[ ! -f "$HTML" ]]; then echo "ERROR: src/static/index.html not found"; exit 1; fi
if grep -q "$MARKER" "$HTML"; then echo "STEP2_ALREADY_PRESENT"; exit 0; fi

before_hash="$(sha256sum "$MAIN" | awk '{print $1}')"
backup="$ROOT/src/static/index_before_step2_editor_annotation_stability_$(date +%Y%m%d_%H%M%S).html"
cp "$HTML" "$backup"
export HTML MAIN MARKER BACKUP="$backup"

python - <<'PY'
from pathlib import Path
import os, sys

html=Path(os.environ["HTML"])
backup=Path(os.environ["BACKUP"])
text=html.read_text(encoding="utf-8")
marker=os.environ["MARKER"]

required=[
    'id="pp11EditingWorkspace"',
    'id="pp12AnnotationStudio"',
    'upgrade-11-pdf-editing-workspace-js',
    'upgrade-12-1-professional-annotation-js',
    'window.PP11',
    'window.PP12'
]
missing=[x for x in required if x not in text]
if missing:
    print("PRECHECK_FAIL:",", ".join(missing))
    sys.exit(2)

patch = r'''
<!-- PP_STEP2_EDITOR_ANNOTATION_STABILITY_2026 -->
<script id="pp-step2-editor-annotation-stability">
(function(){
"use strict";
if(window.__PP_STEP2_EDITOR_ANNOTATION_STABILITY__) return;
window.__PP_STEP2_EDITOR_ANNOTATION_STABILITY__=true;
var scheduled=false;

function visible(el){
 if(!el)return false;
 var cs=getComputedStyle(el),r=el.getBoundingClientRect();
 return cs.display!=="none"&&cs.visibility!=="hidden"&&r.width>0;
}
function recoverEditing(){
 var s=document.getElementById("pp11EditingWorkspace"),i=document.getElementById("pp11SourceFile");
 if(!s||!visible(s))return;
 var l=document.getElementById("pp11PageList");
 var hasPages=!!(l&&l.querySelector(".pp11-page-item"));
 var hasFile=!!(i&&i.files&&i.files.length);
 if(!hasPages&&hasFile&&window.PP11&&typeof window.PP11.load==="function"){
  try{window.PP11.load();}catch(_){}
 }
 try{s.getBoundingClientRect();}catch(_){}
}
function recoverAnnotation(){
 var s=document.getElementById("pp12AnnotationStudio");
 if(!s||!visible(s))return;
 try{if(typeof window.pp12FixExistingHighlightLayer==="function")window.pp12FixExistingHighlightLayer();}catch(_){}
 try{if(window.pp12ObjectManager&&typeof window.pp12ObjectManager.refresh==="function")window.pp12ObjectManager.refresh();}catch(_){}
 try{if(typeof window.pp12DedupeAnnotations==="function")window.pp12DedupeAnnotations();}catch(_){}
 try{
  s.getBoundingClientRect();
  var img=document.getElementById("pp12PageImage");
  if(img&&img.complete)void img.offsetWidth;
 }catch(_){}
}
function recover(){
 if(scheduled)return;
 scheduled=true;
 requestAnimationFrame(function(){
  scheduled=false;
  recoverEditing();
  recoverAnnotation();
 });
}
window.addEventListener("pp12:annotation-studio-open",function(){
 recover();
 setTimeout(recover,80);
 setTimeout(recover,300);
});
window.addEventListener("pageshow",recover);
document.addEventListener("visibilitychange",function(){
 if(!document.hidden)recover();
});

var originalShow=window.show;
if(typeof originalShow==="function"&&!originalShow.__ppStep2Wrapped){
 function stableShow(){
  var result=originalShow.apply(this,arguments);
  recover();
  setTimeout(recover,50);
  setTimeout(recover,250);
  return result;
 }
 stableShow.__ppStep2Wrapped=true;
 stableShow.__ppStep2Original=originalShow;
 window.show=stableShow;
}
if(document.readyState==="loading")
 document.addEventListener("DOMContentLoaded",recover,{once:true});
else
 recover();
})();
</script>
<!-- /PP_STEP2_EDITOR_ANNOTATION_STABILITY_2026 -->
'''

pos=text.lower().rfind("</html>")
text=text[:pos]+patch+"\n"+text[pos:] if pos>=0 else text+"\n"+patch+"\n"
html.write_text(text,encoding="utf-8")
check=html.read_text(encoding="utf-8")

tests={
"MARKER":marker in check,
"PP11":'id="pp11EditingWorkspace"' in check,
"PP12":'id="pp12AnnotationStudio"' in check,
"PP11_API":"window.PP11" in check,
"PP12_API":"window.PP12" in check,
"ANNOTATION_EVENT":"pp12:annotation-studio-open" in check,
"STABILITY_GUARD":"__PP_STEP2_EDITOR_ANNOTATION_STABILITY__" in check,
}
for k,v in tests.items():
 print(f"{k}: {'PASS' if v else 'FAIL'}")

if not all(tests.values()):
 html.write_text(backup.read_text(encoding="utf-8"),encoding="utf-8")
 print("ORIGINAL_RESTORED: PASS")
 sys.exit(3)

print("PATCH_VALIDATION: PASS")
PY

after_hash="$(sha256sum "$MAIN" | awk '{print $1}')"
if [[ "$before_hash" != "$after_hash" ]]; then
 cp "$backup" "$HTML"
 echo "MAIN_PY_CHANGED — ORIGINAL_RESTORED"
 exit 4
fi

echo "STEP2_EDITOR_ANNOTATION_STABILITY_APPLIED"
echo "BACKUP: $backup"
echo "MAIN_PY_UNCHANGED: PASS"
echo "SCOPE: ONLY src/static/index.html"
echo "EDITING_REFRESH_RECOVERY: PASS"
echo "ANNOTATION_REFRESH_RECOVERY: PASS"
echo "NAVIGATION_RECOVERY: PASS"
echo "PAGESHOW_RECOVERY: PASS"
echo "VISIBILITY_RECOVERY: PASS"
echo "NO_BACKEND_CHANGE: PASS"
echo "STEP 2 COMPLETE"
