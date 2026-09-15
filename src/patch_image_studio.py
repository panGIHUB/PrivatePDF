from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

if "/api/image-resize" in s:
    print("Image Studio backend already exists — no changes made.")
    raise SystemExit(0)

marker = '@app.get("/", response_class=HTMLResponse)'

if marker not in s:
    raise SystemExit("ERROR: Could not find insertion point in app/main.py")

endpoint = r'''

@app.post("/api/image-resize")
async def image_resize(
    files: list[UploadFile] = File(...),
    mode: str = Form("pixels"),
    width: int = Form(1920),
    height: int = Form(1080),
    percent: float = Form(100),
    fit: str = Form("contain"),
    crop: bool = Form(False),
    quality: int = Form(90),
    output_format: str = Form("original"),
    dpi: int = Form(96),
    background: str = Form("#ffffff"),
    no_enlarge: bool = Form(False),
    target_kb: int = Form(0),
):
    from PIL import Image, ImageOps
    from pathlib import Path
    from zipfile import ZipFile, ZIP_DEFLATED
    from fastapi import BackgroundTasks
    import tempfile
    import uuid

    if not files:
        raise HTTPException(status_code=400, detail="No images selected.")

    mode = mode.lower().strip()
    fit = fit.lower().strip()
    output_format = output_format.lower().strip()

    if mode not in {"pixels", "percent"}:
        raise HTTPException(status_code=400, detail="Invalid resize mode.")

    if fit not in {"contain", "cover", "stretch"}:
        raise HTTPException(status_code=400, detail="Invalid fit mode.")

    if output_format not in {"original", "jpg", "png", "webp"}:
        raise HTTPException(status_code=400, detail="Invalid output format.")

    width = max(1, min(int(width), 12000))
    height = max(1, min(int(height), 12000))
    percent = max(1, min(float(percent), 1000))
    quality = max(10, min(int(quality), 100))
    dpi = max(1, min(int(dpi), 1200))
    target_kb = max(0, min(int(target_kb), 50000))

    job = new_job()
    output_dir = Path(job)
    generated = []

    def parse_bg(value):
        value = (value or "#ffffff").strip().lstrip("#")
        if len(value) != 6:
            return (255, 255, 255, 255)
        try:
            return (
                int(value[0:2], 16),
                int(value[2:4], 16),
                int(value[4:6], 16),
                255,
            )
        except ValueError:
            return (255, 255, 255, 255)

    bg = parse_bg(background)

    def fit_image(img, target_w, target_h):
        img = img.convert("RGBA")

        if fit == "stretch":
            return img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        if fit == "cover":
            ratio = max(target_w / img.width, target_h / img.height)
            nw = max(1, round(img.width * ratio))
            nh = max(1, round(img.height * ratio))
            resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
            left = max(0, (nw - target_w) // 2)
            top = max(0, (nh - target_h) // 2)
            return resized.crop((left, top, left + target_w, top + target_h))

        ratio = min(target_w / img.width, target_h / img.height)
        nw = max(1, round(img.width * ratio))
        nh = max(1, round(img.height * ratio))
        resized = img.resize((nw, nh), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (target_w, target_h), bg)
        canvas.alpha_composite(
            resized,
            ((target_w - nw) // 2, (target_h - nh) // 2)
        )
        return canvas

    def extension_for(fmt, original):
        if fmt == "jpg":
            return ".jpg"
        if fmt == "png":
            return ".png"
        if fmt == "webp":
            return ".webp"

        ext = Path(original).suffix.lower()
        if ext in {".jpeg", ".jpg"}:
            return ".jpg"
        if ext == ".png":
            return ".png"
        if ext == ".webp":
            return ".webp"
        return ".png"

    try:
        for index, upload in enumerate(files, start=1):
            raw = await upload.read()

            if not raw:
                continue

            if len(raw) > MAX_FILE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"{upload.filename}: file is too large."
                )

            try:
                src = Image.open(io.BytesIO(raw))
                src.load()
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail=f"{upload.filename}: unsupported or invalid image."
                )

            original_w, original_h = src.size

            if mode == "percent":
                factor = percent / 100.0
                target_w = max(1, round(original_w * factor))
                target_h = max(1, round(original_h * factor))
            else:
                target_w = width
                target_h = height

                if fit == "contain":
                    ratio = min(
                        target_w / original_w,
                        target_h / original_h
                    )
                    if no_enlarge:
                        ratio = min(ratio, 1.0)
                    target_w = max(1, round(original_w * ratio))
                    target_h = max(1, round(original_h * ratio))
                elif fit == "cover":
                    if no_enlarge:
                        ratio = min(
                            target_w / original_w,
                            target_h / original_h,
                            1.0
                        )
                        target_w = max(1, round(original_w * ratio))
                        target_h = max(1, round(original_h * ratio))
                else:
                    if no_enlarge:
                        target_w = min(target_w, original_w)
                        target_h = min(target_h, original_h)

            if no_enlarge and mode == "percent":
                target_w = min(target_w, original_w)
                target_h = min(target_h, original_h)

            if crop and mode == "pixels":
                fit_mode_backup = fit
                fit = "cover"
                result = fit_image(src, target_w, target_h)
                fit = fit_mode_backup
            else:
                result = fit_image(src, target_w, target_h)

            if output_format == "original":
                out_ext = extension_for("original", upload.filename or "")
            else:
                out_ext = extension_for(output_format, upload.filename or "")

            stem = Path(upload.filename or f"image_{index}").stem
            stem = safe_name(stem) or f"image_{index}"
            out_path = output_dir / f"{stem}_resized{out_ext}"

            save_format = {
                ".jpg": "JPEG",
                ".png": "PNG",
                ".webp": "WEBP",
            }[out_ext]

            if save_format == "JPEG":
                result = result.convert("RGB")
                result.save(
                    out_path,
                    format="JPEG",
                    quality=quality,
                    optimize=True,
                    dpi=(dpi, dpi),
                )
            elif save_format == "WEBP":
                result.save(
                    out_path,
                    format="WEBP",
                    quality=quality,
                    method=6,
                )
            else:
                result.save(
                    out_path,
                    format="PNG",
                    optimize=True,
                    dpi=(dpi, dpi),
                )

            # Best-effort target-size compression for lossy formats.
            if target_kb > 0 and save_format in {"JPEG", "WEBP"}:
                target_bytes = target_kb * 1024
                current = out_path.stat().st_size

                if current > target_bytes:
                    low, high = 10, quality
                    best = None

                    while low <= high:
                        q = (low + high) // 2
                        if save_format == "JPEG":
                            result.convert("RGB").save(
                                out_path,
                                format="JPEG",
                                quality=q,
                                optimize=True,
                                dpi=(dpi, dpi),
                            )
                        else:
                            result.save(
                                out_path,
                                format="WEBP",
                                quality=q,
                                method=6,
                            )

                        size = out_path.stat().st_size

                        if size <= target_bytes:
                            best = out_path.read_bytes()
                            low = q + 1
                        else:
                            high = q - 1

                    if best is not None:
                        out_path.write_bytes(best)

            generated.append(out_path)

        if not generated:
            raise HTTPException(status_code=400, detail="No valid images processed.")

        background_tasks = BackgroundTasks()

        if len(generated) == 1:
            background_tasks.add_task(cleanup, job)
            return FileResponse(
                generated[0],
                filename=generated[0].name,
                background=background_tasks,
            )

        zip_path = output_dir / "Resized_Images.zip"
        with ZipFile(zip_path, "w", ZIP_DEFLATED) as z:
            for item in generated:
                z.write(item, arcname=item.name)

        background_tasks.add_task(cleanup, job)

        return FileResponse(
            zip_path,
            filename="Resized_Images.zip",
            media_type="application/zip",
            background=background_tasks,
        )

'''

s = s.replace(marker, endpoint + "\n" + marker, 1)
p.write_text(s, encoding="utf-8")
print("Image Studio backend patched successfully.")
