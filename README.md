# instax-printing

Arrange **three instax-mini photos** onto a single **4R (15×10 cm) print sheet**,
ready to send to a photo lab and cut apart.

## What it does

1. Load three images.
2. For each, position an **instax-mini-shaped crop frame** — drag to move,
   mouse-wheel to zoom, and rotate (⟲/⟳ 90° buttons or the Angle slider). The
   frame is locked to the instax mini image ratio (46×62 mm) and always stays
   inside the photo, so the crop never has blank edges.
3. When all three crops are ready, **Generate 4R sheet**. The three photos are
   placed side by side across the width of the 4R at ~instax size, centred, with
   small **cut-mark crosses** at every corner so you know where to trim.
4. **Save** the sheet as a 300-DPI JP/PNG/TIFF (physical size embedded) or
   **Print** it directly.

## Dimensions

| | mm | px @ 300 DPI |
|---|---|---|
| 4R sheet (landscape) | 152.4 × 101.6 | 1800 × 1200 |
| instax mini image | 46 × 62 | 543 × 732 |

Three instax photos across the 4R width come out a hair under full instax size
(so they fit with a small margin and gaps). All layout numbers live in
[`instax_config.py`](instax_config.py) and are easy to tweak.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Layout of the code

- `instax_config.py` — physical sizes → pixels, and the 3-up layout.
- `imaging.py` — image I/O (unicode-safe, DPI-aware save) and the crop-transform maths.
- `crop_canvas.py` — the interactive move/zoom/rotate instax crop widget.
- `composite.py` — assembles the 4R sheet and draws the cut crosses.
- `main_window.py` — the three crop slots, generate flow, and preview/save/print dialog.
- `main.py` — entry point.
