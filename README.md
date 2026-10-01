# instax-printing

Two tools for instax prints, chosen from the **Tools** menu:

1. **4R Print Sheet** — arrange **three instax-mini photos** onto a single **4R
   (15×10 cm) print sheet**, ready to send to a photo lab and cut apart.
2. **Instax Collage** — combine several photos into **one** instax-sized image
   (Mini, Square, or Wide) and export it — as a plain image for an **instax
   printer**, or with the white instax border drawn on.

## What it does (4R Print Sheet)

1. Load three images.
2. For each, position an **instax-mini-shaped crop frame** — drag to move,
   mouse-wheel to zoom, and rotate (⟲/⟳ 90° buttons or the Angle slider). The
   frame is locked to the instax mini image ratio (46×62 mm) and always stays
   inside the photo, so the crop never has blank edges.
3. When all three crops are ready, **Generate 4R sheet**. Each photo is placed
   inside a full **instax-mini card** — white border, thin at the top, thick at
   the bottom (the classic instax look) — and the three cards are laid across the
   width of the 4R, centred, with **light-grey trim lines and corner crosses** so
   you know exactly where to cut.
4. **Save** the sheet as a 300-DPI JPG/PNG/TIFF (physical size embedded) or
   **Print** it directly.

Print it, cut along the marks, and each piece looks like a real instax mini.

## Dimensions

| | mm | px @ 300 DPI |
|---|---|---|
| 4R sheet (landscape) | 152.4 × 101.6 | 1800 × 1200 |
| instax mini card | 54 × 86 | 638 × 1016 |
| instax mini image area | 46 × 62 | 543 × 732 |

The image area sits inside the card with 4 mm side/top borders and a ~20 mm
bottom border. Three 54 mm cards are wider than the 4R (152 mm), so they print a
little under full size. All layout numbers live in
[`instax_config.py`](instax_config.py) and are easy to tweak.

## Instax Collage

**Tools → Instax Collage** combines several photos into a single instax-sized
image. Pick a **format** (Mini 46×62 mm, Square 62×62 mm, or Wide 99×62 mm) and a
preset **grid layout** (1, 2, 3, or 2×2), frame each cell, then export:

- **Image only** — at the instax printer's native resolution (600×800 Mini,
  800×800 Square, 1260×840 Wide). Send it to an instax printer, which adds the
  physical white border itself.
- **With border** — the collage inside a full white instax card, for a normal
  printer or a true-to-life preview.

Toggle the two in the export preview. Instax formats, layouts, and the gutter all
live in [`instax_config.py`](instax_config.py).

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
- `crop_canvas.py` — the interactive move/zoom/rotate crop widget (any output size).
- `crop_station.py` — a crop station (canvas + load/rotate/reset + sliders + DPI hint), shared by both tools.
- `ui_common.py` — shared button styles and save/print helpers.
- `collage_page.py` — the Instax Collage tool UI and its export preview.
- `main_window.py` — the sheet tool, the menu, and the two-tool page stack.
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
