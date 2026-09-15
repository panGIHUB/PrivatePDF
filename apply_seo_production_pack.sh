#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$HOME/Downloads/PrivatePDF_Pro_Advanced_V2}"
HTML="$ROOT/src/static/index.html"
MAIN="$ROOT/src/app/main.py"

if [[ ! -f "$HTML" ]]; then echo "ERROR: index.html not found: $HTML"; exit 1; fi
if [[ ! -f "$MAIN" ]]; then echo "ERROR: main.py not found: $MAIN"; exit 1; fi

STAMP="$(date +%Y%m%d_%H%M%S)"
HTML_BAK="$ROOT/src/static/index_before_seo_${STAMP}.html"
MAIN_BAK="$ROOT/src/app/main_before_seo_${STAMP}.py"
cp "$HTML" "$HTML_BAK"
cp "$MAIN" "$MAIN_BAK"

export HTML MAIN ROOT

python - <<'PY'
from pathlib import Path
import os, re, json

html_path = Path(os.environ["HTML"])
main_path = Path(os.environ["MAIN"])
html = html_path.read_text(encoding="utf-8")
main = main_path.read_text(encoding="utf-8")

for marker in ("STEP3_RESPONSIVE_QA_HARDENING","STEP4_PRODUCTION_QA_GATE","STEP5_FINAL_PREDEPLOY_GATE_COMPLETE"):
    if marker not in html:
        print(f"WARNING: missing marker in html: {marker} (ignoring)")
for marker in ("PP_SECURITY_HARDENING_V2","PP_SECURITY_HARDENING_V3_1","PP_SECURITY_HARDENING_V4","PP_SECURITY_HARDENING_V5"):
    if marker not in main:
        print(f"WARNING: missing security marker in main: {marker} (ignoring)")

if "PRIVATEPDF_PRO_SEO_HEAD" not in html:
    seo = """<!-- PRIVATEPDF_PRO_SEO_HEAD -->
<meta name="description" content="Private PDF Pro — free PDF and image tools for merge, compress, split, convert, edit and inspect workflows.">
<meta name="keywords" content="merge pdf, compress pdf, split pdf, pdf to word, pdf to jpg, image to pdf, free pdf tools, pdf converter">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="author" content="Private PDF Pro">
<meta name="application-name" content="Private PDF Pro">
<link rel="canonical" href="/">
<meta property="og:type" content="website">
<meta property="og:title" content="Private PDF Pro — Free PDF & Image Tools">
<meta property="og:description" content="Free PDF and image tools for merge, compress, split, convert, edit and inspect workflows.">
<meta property="og:site_name" content="Private PDF Pro">
<meta property="og:url" content="/">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Private PDF Pro — Free PDF & Image Tools">
<meta name="twitter:description" content="Free PDF and image tools for merge, compress, split, convert, edit and inspect workflows.">
"""
    m = re.search(r"</head\s*>", html, re.I)
    if not m: raise SystemExit("ABORT: </head> not found")
    html = html[:m.start()] + seo + "\n" + html[m.start():]

if "PRIVATEPDF_PRO_SEO_CONTENT" not in html:
    content = """<!-- PRIVATEPDF_PRO_SEO_CONTENT -->
<section class="pp-seo-content" aria-label="PDF Pro information">
<h2>Free PDF &amp; Image Tools</h2>
<p>Private PDF Pro provides everyday PDF and image workflows including merge PDF, compress PDF, split PDF, PDF to Word, PDF to JPG, JPG to PDF, PNG to PDF, PDF to PNG, watermarking and PDF inspection.</p>
<h3>Popular PDF tools</h3>
<nav aria-label="Popular PDF tools">
<a href="/merge-pdf">Merge PDF</a>
<a href="/compress-pdf">Compress PDF</a>
<a href="/split-pdf">Split PDF</a>
<a href="/pdf-to-word">PDF to Word</a>
<a href="/pdf-to-jpg">PDF to JPG</a>
<a href="/jpg-to-pdf">JPG to PDF</a>
<a href="/png-to-pdf">PNG to PDF</a>
<a href="/pdf-to-png">PDF to PNG</a>
<a href="/rotate-pdf">Rotate PDF</a>
<a href="/watermark-pdf">Watermark PDF</a>
<a href="/pdf-to-text">PDF to Text</a>
<a href="/pdf-inspector">PDF Inspector</a>
</nav>
<h3>Frequently asked questions</h3>
<details><summary>Can I merge PDF files online?</summary><p>Yes. Open the Merge PDF tool and use the existing PDF workflow to combine documents.</p></details>
<details><summary>Can I compress a PDF?</summary><p>Yes. Use the Compress PDF tool to reduce document size.</p></details>
<details><summary>Can I convert images to PDF?</summary><p>Yes. JPG to PDF and PNG to PDF are available as dedicated tools.</p></details>
<details><summary>Can I convert PDF pages to images?</summary><p>Yes. PDF to JPG and PDF to PNG are available as dedicated tools.</p></details>
</section>
"""
    m = re.search(r"</body\s*>", html, re.I)
    html = html[:m.start()] + content + "\n" + html[m.start():] if m else html + content

if "PRIVATEPDF_PRO_SEO_CSS" not in html:
    css = """<!-- PRIVATEPDF_PRO_SEO_CSS -->
<style id="privatepdf-pro-seo-css">
.pp-seo-content{max-width:1100px;margin:32px auto;padding:24px 20px;line-height:1.65}
.pp-seo-content h2,.pp-seo-content h3{margin:0 0 12px}
.pp-seo-content p{margin:0 0 18px}
.pp-seo-content nav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 24px}
.pp-seo-content nav a{padding:7px 11px;border:1px solid currentColor;border-radius:8px;text-decoration:none}
.pp-seo-content details{margin:8px 0;padding:10px 12px;border:1px solid rgba(128,128,128,.35);border-radius:8px}
.pp-seo-content summary{cursor:pointer;font-weight:600}
</style>
"""
    m = re.search(r"</head\s*>", html, re.I)
    if not m: raise SystemExit("ABORT: </head> not found for CSS")
    html = html[:m.start()] + css + "\n" + html[m.start():]

html_path.write_text(html, encoding="utf-8")

imports = []
if "import json" not in main: imports.append("import json")
if "import re" not in main: imports.append("import re")
if "from pathlib import Path" not in main: imports.append("from pathlib import Path")
if "from fastapi.responses import HTMLResponse" not in main: imports.append("from fastapi.responses import HTMLResponse")
if "from fastapi.responses import Response" not in main: imports.append("from fastapi.responses import Response")
if imports: main = "\n".join(imports) + "\n" + main

if "PRIVATEPDF_PRO_SEO_ROUTES" not in main:
    tools = [
        ("merge-pdf","Merge PDF","Merge PDF files online for free with Private PDF Pro.","merge pdf, merge pdf online, combine pdf, pdf merger"),
        ("compress-pdf","Compress PDF","Compress PDF files online and reduce document size with Private PDF Pro.","compress pdf, reduce pdf size, compress pdf online"),
        ("split-pdf","Split PDF","Split PDF pages online and extract selected pages with Private PDF Pro.","split pdf, split pdf online, extract pdf pages"),
        ("pdf-to-word","PDF to Word","Convert PDF documents to editable Word files with Private PDF Pro.","pdf to word, pdf to word converter, convert pdf to word"),
        ("pdf-to-jpg","PDF to JPG","Convert PDF pages to JPG images online with Private PDF Pro.","pdf to jpg, pdf to image, convert pdf to jpg"),
        ("jpg-to-pdf","JPG to PDF","Convert JPG images to PDF online with Private PDF Pro.","jpg to pdf, image to pdf, convert jpg to pdf"),
        ("png-to-pdf","PNG to PDF","Convert PNG images to PDF online with Private PDF Pro.","png to pdf, image to pdf, convert png to pdf"),
        ("pdf-to-png","PDF to PNG","Convert PDF pages to PNG images online with Private PDF Pro.","pdf to png, pdf to image, convert pdf to png"),
        ("rotate-pdf","Rotate PDF","Rotate PDF pages online with Private PDF Pro.","rotate pdf, rotate pdf online, rotate pdf pages"),
        ("watermark-pdf","Watermark PDF","Add a watermark to PDF documents with Private PDF Pro.","watermark pdf, add watermark to pdf"),
        ("pdf-to-text","PDF to Text","Extract text from PDF documents with Private PDF Pro.","pdf to text, extract text from pdf"),
        ("pdf-inspector","PDF Inspector","Inspect PDF metadata and document properties with Private PDF Pro.","pdf inspector, pdf metadata viewer"),
    ]
    block = r"""
# PRIVATEPDF_PRO_SEO_ROUTES
_PP_SEO_TOOLS = TOOL_DATA

def _pp_seo_find(slug):
    for item in _PP_SEO_TOOLS:
        if item[0] == slug: return item
    return None

def _pp_seo_jsonld(item, canonical):
    return {"@context":"https://schema.org","@graph":[
        {"@type":"WebSite","name":"Private PDF Pro","url":canonical},
        {"@type":"SoftwareApplication","name":"Private PDF Pro","applicationCategory":"BusinessApplication","operatingSystem":"Web","description":item[2],"url":canonical},
        {"@type":"FAQPage","mainEntity":[
            {"@type":"Question","name":"Can I use " + item[1] + " online?","acceptedAnswer":{"@type":"Answer","text":item[2]}},
            {"@type":"Question","name":"Does Private PDF Pro provide PDF tools?","acceptedAnswer":{"@type":"Answer","text":"Private PDF Pro provides PDF and image workflows for common document tasks."}}
        ]}
    ]}

def _pp_seo_page(item):
    index_file = Path(__file__).resolve().parents[1] / "static" / "index.html"
    source = index_file.read_text(encoding="utf-8")
    slug, name, description, keywords = item
    title = name + " Online Free | Private PDF Pro"
    canonical = "/" + slug
    source = re.sub(r"<!-- PRIVATEPDF_PRO_SEO_HEAD -->.*?<!-- PRIVATEPDF_PRO_SEO_HEAD -->","",source,flags=re.S)
    source = re.sub(r"<title>.*?</title>","<title>"+title+"</title>",source,count=1,flags=re.I|re.S)
    meta = ("<meta name=\"description\" content=\"" + description + "\">\n"
            "<meta name=\"keywords\" content=\"" + keywords + "\">\n"
            "<meta name=\"robots\" content=\"index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1\">\n"
            "<link rel=\"canonical\" href=\"" + canonical + "\">\n"
            "<meta property=\"og:type\" content=\"website\">\n"
            "<meta property=\"og:title\" content=\"" + title + "\">\n"
            "<meta property=\"og:description\" content=\"" + description + "\">\n"
            "<meta property=\"og:site_name\" content=\"Private PDF Pro\">\n"
            "<meta property=\"og:url\" content=\"" + canonical + "\">\n"
            "<meta name=\"twitter:card\" content=\"summary\">\n"
            "<meta name=\"twitter:title\" content=\"" + title + "\">\n"
            "<meta name=\"twitter:description\" content=\"" + description + "\">\n"
            "<script type=\"application/ld+json\">" + json.dumps(_pp_seo_jsonld(item,canonical),ensure_ascii=False) + "</script>\n")
    head = re.search(r"</head\s*>",source,re.I)
    if head: source = source[:head.start()] + meta + source[head.start():]
    landing = ("<section aria-label=\"Tool information\" style=\"max-width:1100px;margin:18px auto;padding:18px 20px;line-height:1.6\">"
               "<h1>"+title+"</h1><p>"+description+"</p>"
               "<p><a href=\"/\">Private PDF Pro home</a> · <a href=\"/merge-pdf\">Merge PDF</a> · <a href=\"/compress-pdf\">Compress PDF</a> · <a href=\"/split-pdf\">Split PDF</a></p></section>")
    body = re.search(r"<body[^>]*>",source,re.I)
    if body: source = source[:body.end()] + landing + source[body.end():]
    return HTMLResponse(content=source)

def _pp_seo_handler_factory(slug):
    async def _handler():
        item = _pp_seo_find(slug)
        if item is None: return HTMLResponse(content="Not Found",status_code=404)
        return _pp_seo_page(item)
    return _handler

for _pp_item in _PP_SEO_TOOLS:
    app.add_api_route("/"+_pp_item[0],_pp_seo_handler_factory(_pp_item[0]),methods=["GET"],include_in_schema=False)

@app.get("/robots.txt",include_in_schema=False)
async def _pp_robots_txt():
    return Response(content="User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n",media_type="text/plain")

@app.get("/sitemap.xml",include_in_schema=False)
async def _pp_sitemap_xml():
    urls = ["/"] + ["/"+x[0] for x in _PP_SEO_TOOLS]
    body = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>","<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"]
    for u in urls: body.append("  <url><loc>"+u+"</loc></url>")
    body.append("</urlset>")
    return Response(content="\n".join(body),media_type="application/xml")

# PRIVATEPDF_PRO_SEO_ROUTES_END
"""
    block = block.replace("TOOL_DATA",repr(tools))
    m = re.search(r"(?m)^if __name__\s*==\s*[\"']__main__[\"']\s*:",main)
    pos = m.start() if m else len(main)
    main = main[:pos] + block + "\n" + main[pos:]

main_path.write_text(main,encoding="utf-8")
PY

if ! python -m py_compile "$MAIN"; then
  echo "PYTHON_SYNTAX: FAIL — rolling back"
  cp "$HTML_BAK" "$HTML"
  cp "$MAIN_BAK" "$MAIN"
  exit 1
fi

echo "PYTHON_SYNTAX: PASS"

python - <<'PY'
import sys, os
from pathlib import Path

root_dir = Path(os.environ["ROOT"]).resolve()
sys.path.insert(0, str(root_dir / "src"))
import app.main
print("APP_IMPORT: PASS")
PY

python - <<'PY'
from pathlib import Path
import os

html = Path(os.environ["HTML"]).read_text(encoding="utf-8")
main = Path(os.environ["MAIN"]).read_text(encoding="utf-8")
checks = {
    "SEO_HEAD": "PRIVATEPDF_PRO_SEO_HEAD" in html,
    "SEO_CONTENT": "PRIVATEPDF_PRO_SEO_CONTENT" in html,
    "SEO_ROUTES": "PRIVATEPDF_PRO_SEO_ROUTES" in main,
    "SITEMAP": "/sitemap.xml" in main,
    "ROBOTS": "/robots.txt" in main,
    "MERGE": "/merge-pdf" in main,
    "COMPRESS": "/compress-pdf" in main,
    "SPLIT": "/split-pdf" in main,
    "FAQ_SCHEMA": '"FAQPage"' in main,
    "SOFTWARE_SCHEMA": '"SoftwareApplication"' in main,
}
for k, v in checks.items():
    print(f"{k}: {'PASS' if v else 'FAIL'}")

if not all(checks.values()):
    raise SystemExit("SEO validation failed")
print("SEO_PRODUCTION_PACK: PASS")
PY

echo
echo "SEO PACK COMPLETE"
