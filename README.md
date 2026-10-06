# instax-printing

Three tools for instax prints, chosen from the **Tools** menu:

1. **4R Print Sheet** — arrange photos onto a single **4R (15×10 cm) print sheet**,
   ready to send to a photo lab and cut apart. Pick a **Layout** from the dropdown:
   3 instax minis (with or **without** the white frame), or a **2×2 / 3×2 / 2×3**
   grid of photos separated by white gutters with cut lines.
2. **Instax Collage** — combine several photos into **one** instax-sized image
   (Mini, Square, or Wide) and export it — as a plain image for an **instax
   printer**, or with the white instax border drawn on.
3. **A4 Instax Sheet** — pack the **maximum instax cards onto a landscape A4**
   (10 Mini / 8 Square / 4 Wide), true-size with white borders and cut lines,
   centred for **home printing** — print it and cut them out.

## What it does (4R Print Sheet)

1. Pick a **Layout** from the dropdown at the top:
   - **3 × Instax mini — white frame** — each photo inside a full **instax-mini
     card** (white border, thin top/sides, thick bottom — the classic instax look).
   - **4 × Instax mini — no frame (portrait)** — the sheet turns **portrait** so
     **four** full-size upright minis fit as a 2×2 (only three fit on a landscape 4R).
   - **2 × 2 grid — 4 photos**, **3 × 2 grid — 6 photos**, **2 × 3 grid — 6 photos**
     — a plain grid of photos separated by white gutters with **cut lines** down
     the middle; print, then cut, into bordered prints.
   The crop stations below rebuild to match (the right number of photos, each
   cropped to the right shape, arranged like the printed grid).
2. Load each image and position its **crop frame** — drag to move, mouse-wheel to
   zoom, and rotate (⟲/⟳ 90° buttons or the Angle slider). The frame is locked to
   the cell's aspect ratio and always stays inside the photo, so the crop never has
   blank edges. A live **DPI** readout warns if a photo is too low-res.
3. When all the photos are ready, **Generate 4R sheet** to preview it.
4. **Save** the sheet as a 300-DPI JPG/PNG/TIFF (physical size embedded) or
   **Print** it directly. Tick **High resolution** in any tool's preview to save
   at **2× · 600 DPI** — re-rendered from the source photos, so it's real detail.

Print it and cut along the lines — with the instax border, each piece looks like a
real instax mini.

## Dimensions

| | mm | px @ 300 DPI |
|---|---|---|
| 4R sheet (landscape) | 152.4 × 101.6 | 1800 × 1200 |
| instax mini card | 54 × 86 | 638 × 1016 |
| instax mini image area | 46 × 62 | 543 × 732 |

The image area sits inside the card with 4 mm side borders, an 8 mm top border,
and a 16 mm bottom border (the image is offset toward the top — the classic
instax look). Three 54 mm cards are wider than the 4R (152 mm), so they print a
little under full size. All layout numbers live in
[`instax_config.py`](instax_config.py) and are easy to tweak.

## Instax Collage

**Tools → Instax Collage** combines several photos into a single instax-sized
image. Pick a **format** (Mini 46×62 mm, Square 62×62 mm, or Wide 99×62 mm), a
**layout** (13 presets — grids plus asymmetric ones like *1 big + 4*), and the
**gutter** between photos (None / Thin / Medium), frame each cell, then export:

- **Image only** (default) — photos fill the image area edge-to-edge at the
  printer's native resolution (600×800 Mini, 800×800 Square, 1260×840 Wide), with
  **no outer border**. Send it to an instax printer, which adds the physical white
  border itself. (The collage deliberately adds none — otherwise you'd get a
  *double* border on an instax print.)
- **With border** (optional) — the collage inside a full white instax card, for a
  **normal** printer only. Leave it off for an instax printer.

Instax formats, layouts, and gutter sizes all live in
[`instax_config.py`](instax_config.py).

## A4 Instax Sheet

**Tools → A4 Instax Sheet** packs the most instax cards that fit on a **landscape
A4** for home printing — **10** Mini (5×2), **8** Square (4×2), or **4** Wide
(2×2). Load a photo into as many cards as you like (you don't have to fill them
all), then **Generate A4 sheet**:

- **True-size** instax cards at 300 DPI with the **full white border** (not
  reduced), each outlined with a **light-grey cut line**.
- The card block is **centred and kept a few mm inside the A4**, so it prints
  centred without the printer clipping the edges.

Save a 300-DPI A4 image (print it at 100% / fit-to-page) or Print directly, then
cut along the lines. Page geometry lives in [`a4_sheet.py`](a4_sheet.py).

## Run

```bash
./run.sh
```

First run creates a local `.venv` and installs dependencies; after that it just
launches the app. To do it by hand instead:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Layout of the code

- `instax_config.py` — physical sizes → pixels, the 3-up sheet layout, and the instax formats + collage layouts.
- `imaging.py` — image I/O (unicode-safe, DPI-aware save), incremental naming, and the crop-transform maths.
- `composite.py` — assembles the 4R sheet and draws the cut marks.
- `collage.py` — assembles an instax-format collage (image-only or bordered).
- `a4_sheet.py` — packs the max instax cards onto a landscape A4 with cut lines.
- `crop_canvas.py` — the interactive move/zoom/rotate crop widget (any output size).
- `crop_station.py` — a crop station (canvas + load/rotate/reset + sliders + DPI hint), shared by both tools.
- `ui_common.py` — shared button styles and save/print helpers.
- `collage_page.py` — the Instax Collage tool UI and its export preview.
- `a4_page.py` — the A4 Instax Sheet tool UI.
- `main_window.py` — the sheet tool, the menu, and the three-tool page stack.
- `main.py` — entry point.

## Documentation

A landing page and full docs live alongside the code:

- **[index.html](index.html)** — project landing page (open it in a browser).
- **[docs/installation.md](docs/installation.md)** — install on Linux / macOS / Windows.
- **[docs/user-guide.md](docs/user-guide.md)** — the complete workflow, crop, DPI, and cutting guide.
- **[docs/architecture.md](docs/architecture.md)** — module map, the size model, and the crop maths.

## Support

instax-printing is a free, open-source side project. If it saves you money and
hassle printing your instax photos, you can support development via:

- **GitHub Sponsors** — https://github.com/sponsors/mnavas
- **PayPal** — https://paypal.me/warionv
- **De Una · Banco Pichincha** — scan [`assets/deuna-qr.png`](assets/deuna-qr.png) with your banking app (Ecuador)

The support options are also on the [landing page](index.html). ¡Gracias!
