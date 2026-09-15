# PrivatePDF Pro — Advanced V2

This is a separate upgraded build. The previous `PrivatePDF_Pro_Advanced.zip` remains unchanged.

## What's improved without adding a new product category

- Fixed the grayscale conversion bug found by automated testing.
- Switched the backend import to the current `pymupdf` package style.
- Watermark controls upgraded to a Word-like workflow:
  - text
  - font size
  - opacity
  - color
  - arbitrary angle (0–359°)
  - 9-position placement
  - tiled watermark
  - bold
  - outline
  - live browser preview
- Compression UI now exposes JPEG quality instead of hard-coding it.
- Cleaner responsive UI, grouped controls, better labels and inline previews.
- Added a backend smoke-test script covering every currently implemented API feature.

## Automated test

From the project directory:

```bash
python test_all_features.py
```

A successful run ends with:

```text
RESULT: 19/19 passed
```

LibreOffice-dependent conversions are intentionally not included in the smoke test because availability depends on the machine.

## Run

```bash
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`

## Important

This V2 does not add OCR, AI, accounts, billing, API keys, batch queues, etc. Those remain outside this upgrade so the existing feature set can be stabilized and polished first.
