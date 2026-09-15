import io
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

import fitz
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pypdf import PdfReader, PdfWriter, Transformation

BASE = Path(__file__).resolve().parent.parent
STATIC = BASE / "static"
JOBS = Path(tempfile.gettempdir()) / "privatepdf_pro_jobs"
JOBS.mkdir(exist_ok=True)

app = FastAPI(title="PrivatePDF Pro", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

MAX_FILE_MB = 250


def new_job():
    p = JOBS / uuid.uuid4().hex
    p.mkdir()
    return p


def cleanup(path: Path):
    shutil.rmtree(path, ignore_errors=True)


def safe_name(name: str) -> str:
    return Path(name or "document").name.replace("\x00", "")


async def save_upload(upload: UploadFile, folder: Path, max_mb=MAX_FILE_MB) -> Path:
    name = safe_name(upload.filename)
    target = folder / name
    total = 0
    with target.open("wb") as f:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_mb * 1024 * 1024:
                raise ValueError(f"File exceeds {max_mb} MB limit.")
            f.write(chunk)
    return target


def output_file(job: Path, path: Path, filename: str, media_type: str):
    # FastAPI FileResponse streams the temporary result. A production deployment
    # should use a post-response cleanup worker/container TTL rather than deleting
    # the file before the response is consumed.
    return FileResponse(path, filename=filename, media_type=media_type)


def parse_pages(spec: str, total: int):
    out = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        if re.fullmatch(r"\d+", token):
            n = int(token)
            if 1 <= n <= total:
                out.append(n)
        elif re.fullmatch(r"\d+\s*-\s*\d+", token):
            a, b = map(int, re.split(r"\s*-\s*", token))
            if a > b:
                a, b = b, a
            out.extend(n for n in range(a, b + 1) if 1 <= n <= total)
    return out


@app.get("/", response_class=HTMLResponse)
def home():
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health():
    return {"ok": True, "version": "1.0.0", "storage": "temporary-only"}


@app.post("/api/merge")
async def merge(files: List[UploadFile] = File(...)):
    job = new_job()
    try:
        writer = PdfWriter()
        for u in files:
            p = await save_upload(u, job)
            writer.append(str(p))
        out = job / "merged.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Merged.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/pages")
async def page_operation(
    file: UploadFile = File(...),
    action: str = Form(...),
    pages: str = Form(...)
):
    job = new_job()
    try:
        src = await save_upload(file, job)
        reader = PdfReader(str(src))
        selected = parse_pages(pages, len(reader.pages))
        if not selected:
            raise ValueError("No valid pages selected.")

        writer = PdfWriter()
        if action == "extract":
            for n in selected:
                writer.add_page(reader.pages[n - 1])
        elif action == "delete":
            s = set(selected)
            for n, page in enumerate(reader.pages, 1):
                if n not in s:
                    writer.add_page(page)
        elif action == "reorder":
            for n in selected:
                writer.add_page(reader.pages[n - 1])
        else:
            raise ValueError("Unsupported page action.")

        out = job / "result.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Pages_Result.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/rotate")
async def rotate(file: UploadFile = File(...), degrees: int = Form(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        d = degrees % 360
        if d % 90:
            raise ValueError("Rotation must be 0, 90, 180 or 270 degrees.")
        reader = PdfReader(str(src))
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate(d)
            writer.add_page(page)
        out = job / "rotated.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Rotated.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/compress")
async def compress(file: UploadFile = File(...), dpi: int = Form(110), quality: int = Form(70)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        dpi = max(60, min(dpi, 220))
        quality = max(25, min(quality, 95))
        # Rebuild pages and downsample embedded raster images.
        for page in doc:
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.width > 1400 or pix.height > 1400:
                        scale = min(1.0, (dpi / 72.0) * 0.75)
                        nw = max(1, int(pix.width * scale))
                        nh = max(1, int(pix.height * scale))
                        small = fitz.Pixmap(pix, 0) if pix.alpha else pix
                        if small.width != nw or small.height != nh:
                            resized = fitz.Pixmap(small, fitz.Matrix(nw / small.width, nh / small.height))
                            doc.update_stream(xref, resized.tobytes("jpeg", jpg_quality=quality))
                except Exception:
                    pass
        out = job / "compressed.pdf"
        doc.save(str(out), garbage=4, deflate=True, clean=True)
        doc.close()
        return output_file(job, out, "Compressed.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, f"Compression failed: {e}")


@app.post("/api/resize")
async def resize_pdf(file: UploadFile = File(...), size: str = Form("A4"), orientation: str = Form("portrait")):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        sizes = {
            "A4": (595.276, 841.89),
            "A3": (841.89, 1190.55),
            "Letter": (612, 792),
            "Legal": (612, 1008),
        }
        w, h = sizes.get(size, sizes["A4"])
        if orientation == "landscape":
            w, h = h, w
        outdoc = fitz.open()
        for page in doc:
            newp = outdoc.new_page(width=w, height=h)
            src_rect = page.rect
            scale = min(w / src_rect.width, h / src_rect.height)
            nw, nh = src_rect.width * scale, src_rect.height * scale
            x, y = (w - nw) / 2, (h - nh) / 2
            newp.show_pdf_page(fitz.Rect(x, y, x + nw, y + nh), doc, page.number)
        out = job / "resized.pdf"
        outdoc.save(str(out))
        outdoc.close()
        doc.close()
        return output_file(job, out, "Resized.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, f"Resize failed: {e}")


@app.post("/api/crop")
async def crop_pdf(file: UploadFile = File(...), margin: float = Form(20)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        m = max(0, min(float(margin), 300))
        for page in doc:
            r = page.rect
            page.set_cropbox(fitz.Rect(r.x0 + m, r.y0 + m, r.x1 - m, r.y1 - m))
        out = job / "cropped.pdf"
        doc.save(str(out))
        doc.close()
        return output_file(job, out, "Cropped.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, f"Crop failed: {e}")


@app.post("/api/numbers")
async def numbers(file: UploadFile = File(...), start: int = Form(1)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        for i, page in enumerate(doc, start):
            r = page.rect
            text = str(i)
            page.insert_text((r.width / 2 - 5, r.height - 24), text, fontsize=9)
        out = job / "numbered.pdf"
        doc.save(str(out))
        doc.close()
        return output_file(job, out, "Numbered.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, f"Numbering failed: {e}")


@app.post("/api/watermark")
async def watermark(
    file: UploadFile = File(...),
    text: str = Form(...),
    opacity: float = Form(0.25),
    size: int = Form(30),
):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        # PyMuPDF's text rotation is restricted to right angles. Use a
        # transparent semi-opaque textbox without illegal arbitrary rotation.
        opacity = max(0.05, min(float(opacity), 1.0))
        size = max(8, min(int(size), 96))
        for page in doc:
            r = page.rect
            box = fitz.Rect(r.width * .12, r.height * .42, r.width * .88, r.height * .58)
            page.insert_textbox(
                box, text, fontsize=size, align=1,
                color=(0.55, 0.55, 0.55), fill_opacity=opacity, overlay=True
            )
        out = job / "watermarked.pdf"
        doc.save(str(out))
        doc.close()
        return output_file(job, out, "Watermarked.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, f"Watermark failed: {e}")


@app.post("/api/protect")
async def protect(file: UploadFile = File(...), password: str = Form(...)):
    job = new_job()
    try:
        if not password:
            raise ValueError("Password required.")
        src = await save_upload(file, job)
        reader = PdfReader(str(src))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        out = job / "protected.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Protected.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/unlock")
async def unlock(file: UploadFile = File(...), password: str = Form(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        reader = PdfReader(str(src))
        if reader.is_encrypted and not reader.decrypt(password):
            raise ValueError("Incorrect password or unsupported encryption.")
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        out = job / "unlocked.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Unlocked.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/metadata")
async def metadata(file: UploadFile = File(...), mode: str = Form("remove")):
    job = new_job()
    try:
        src = await save_upload(file, job)
        reader = PdfReader(str(src))
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)
        if mode == "remove":
            writer.add_metadata({})
        elif mode == "set":
            writer.add_metadata({
                "/Title": "PrivatePDF Document",
                "/Author": "PrivatePDF Pro",
                "/Creator": "PrivatePDF Pro",
            })
        out = job / "metadata.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return output_file(job, out, "Metadata_Result.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/grayscale")
async def grayscale(file: UploadFile = File(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2), colorspace=fitz.csGRAY, alpha=False)
            page.clean_contents()
            page.show_pdf_page(page.rect, doc, page.number)
            # Raster replacement is intentionally conservative; use render overlay.
            page.insert_image(page.rect, stream=pix.tobytes("png"), overlay=True)
        out = job / "grayscale.pdf"
        doc.save(str(out), garbage=4, deflate=True)
        doc.close()
        return output_file(job, out, "Grayscale.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, f"Grayscale conversion failed: {e}")


@app.post("/api/text")
async def pdf_text(file: UploadFile = File(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        text = "\n\n".join(page.get_text() for page in doc)
        out = job / "extracted.txt"
        out.write_text(text, encoding="utf-8")
        doc.close()
        return output_file(job, out, "Extracted_Text.txt", "text/plain")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/markdown")
async def pdf_markdown(file: UploadFile = File(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        chunks = []
        for i, page in enumerate(doc, 1):
            text = page.get_text("text").strip()
            chunks.append(f"## Page {i}\n\n{text}" if text else f"## Page {i}\n\n")
        out = job / "document.md"
        out.write_text("\n\n".join(chunks), encoding="utf-8")
        doc.close()
        return output_file(job, out, "Document.md", "text/markdown")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/pdf-to-jpg")
async def pdf_to_jpg(file: UploadFile = File(...), fmt: str = Form("jpg")):
    job = new_job()
    try:
        src = await save_upload(file, job)
        doc = fitz.open(str(src))
        outdir = job / "images"
        outdir.mkdir()
        for i, page in enumerate(doc, 1):
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            pix.save(str(outdir / f"page-{i}.{fmt}"))
        doc.close()
        archive = shutil.make_archive(str(job / "PDF_Images"), "zip", outdir)
        return output_file(job, Path(archive), "PDF_Images.zip", "application/zip")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/images-to-pdf")
async def images_to_pdf(files: List[UploadFile] = File(...)):
    job = new_job()
    try:
        outdoc = fitz.open()
        for u in files:
            p = await save_upload(u, job)
            img = Image.open(p).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            page = outdoc.new_page(width=img.width, height=img.height)
            page.insert_image(page.rect, stream=buf.getvalue())
        out = job / "images.pdf"
        outdoc.save(str(out))
        outdoc.close()
        return output_file(job, out, "Images_to_PDF.pdf", "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


def libreoffice_path():
    candidates = [
        "libreoffice", "soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for c in candidates:
        if os.path.isabs(c) and Path(c).exists():
            return c
        if shutil.which(c):
            return c
    return None


@app.post("/api/office-to-pdf")
async def office_to_pdf(file: UploadFile = File(...)):
    job = new_job()
    try:
        src = await save_upload(file, job)
        lo = libreoffice_path()
        if not lo:
            raise ValueError("LibreOffice is not installed. Install LibreOffice to enable Word/Excel/PPT → PDF.")
        subprocess.run([lo, "--headless", "--convert-to", "pdf", "--outdir", str(job), str(src)],
                       check=True, capture_output=True, timeout=120)
        out = job / (src.stem + ".pdf")
        if not out.exists():
            raise ValueError("LibreOffice conversion did not create a PDF.")
        return output_file(job, out, out.name, "application/pdf")
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


@app.post("/api/pdf-to-office")
async def pdf_to_office(file: UploadFile = File(...), kind: str = Form("docx")):
    job = new_job()
    try:
        src = await save_upload(file, job)
        lo = libreoffice_path()
        if not lo:
            raise ValueError("LibreOffice is not installed. Install LibreOffice for office conversion.")
        # LibreOffice PDF import support varies. This endpoint is intentionally
        # labelled beta; quality depends on the source PDF and installed filters.
        target = {"docx": "docx", "xlsx": "xlsx", "pptx": "pptx"}.get(kind)
        if not target:
            raise ValueError("Unsupported office format.")
        subprocess.run([lo, "--headless", "--convert-to", target, "--outdir", str(job), str(src)],
                       check=True, capture_output=True, timeout=120)
        out = job / (src.stem + "." + target)
        if not out.exists():
            raise ValueError("Conversion is not supported by this LibreOffice build for this PDF.")
        media = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }[target]
        return output_file(job, out, out.name, media)
    except Exception as e:
        cleanup(job)
        raise HTTPException(400, str(e))


# Cleanup old temporary jobs on startup. Production should also use a scheduled
# TTL worker/container cleanup.
@app.on_event("startup")
def cleanup_old_jobs():
    for p in JOBS.iterdir():
        if p.is_dir():
            try:
                cleanup(p)
            except Exception:
                pass
