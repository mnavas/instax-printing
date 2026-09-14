# instax-printing — User Guide

## What is instax-printing?

instax-printing arranges **three photos** onto a single **4R (15×10 cm) print
sheet**, each one composited inside a full instax-mini card — the classic white
border, thin at the top and sides, thick at the bottom. Send the sheet to a photo
lab (or print it at home), cut along the marks, and each piece looks like a real
instax mini.

The whole point is that you never print one tiny instax at a time: three of them
fit on one cheap standard 4R print.

---

## The Workflow at a Glance

1. **Load** three photos — one per crop slot.
2. **Frame** each photo inside the instax-shaped crop — drag, zoom, rotate.
3. **Generate the 4R sheet** once all three are ready.
4. **Save or Print** the sheet.
5. Cut along the light-grey trim lines.

---

## The Main Window

```
┌──────────────────────────────────────────────────────────────┐
│  Load three photos, then drag / zoom / rotate each …          │
├────────────────┬────────────────┬────────────────────────────┤
│                │                │                             │
│   [ crop #1 ]  │   [ crop #2 ]  │   [ crop #3 ]               │
│                │                │                             │
│  Load ⟲ ⟳ Reset│  Load ⟲ ⟳ Reset│  Load ⟲ ⟳ Reset            │
│  Zoom  ────────│  Zoom  ────────│  Zoom  ────────             │
│  Angle ────────│  Angle ────────│  Angle ────────             │
│  ≈ 312 DPI     │  ≈ 289 DPI     │  ≈ 205 DPI                  │
├────────────────┴────────────────┴────────────────────────────┤
│  2 / 3 images loaded …                    [ Generate 4R sheet ]│
└──────────────────────────────────────────────────────────────┘
```

Each of the three columns is an independent **crop station**. The **Generate 4R
sheet** button stays disabled until all three photos are loaded.

---

## Loading Photos

Click **Load #1** (and #2, #3) to pick an image. Supported formats:

`.jpg` / `.jpeg` / `.jpe` / `.jfif` · `.png` · `.tif` / `.tiff` · `.bmp` · `.webp`

- The dialog opens in the last folder you loaded from — that folder is
  **shared across all three slots**, so you can load three photos from one shoot
  without navigating each time.
- File paths with **accents, ñ, or non-Latin characters** load correctly on every
  platform.

> **Empty folder in the file dialog?** The app lists both lower- and upper-case
> extensions (`*.jpg *.JPG`) precisely so photos never get hidden by a
> case-sensitive filter — a common problem with the native Linux dialog.

---

## Framing a Photo

Each crop station shows the **whole photo** with a blue **instax-shaped frame**
over it. Everything outside the frame is dimmed, and a rule-of-thirds grid is
drawn inside it to help you compose. Only what's inside the frame ends up on the
print.

The frame is locked to the **instax-mini image ratio (46×62 mm, portrait)** and
is always kept fully inside the photo, so a crop can **never** contain blank
white edges — even when rotated.

| Action | How | Result |
|--------|-----|--------|
| **Move** | Left-drag on the photo | Slides the frame around the image |
| **Zoom** | Mouse wheel, or the **Zoom** slider | Tightens (in) or loosens (out) the crop, 1.00× – 8.00× |
| **Rotate 90°** | **⟲ 90** / **⟳ 90** buttons | Rotates the frame a quarter-turn left / right |
| **Fine rotate** | **Angle** slider | Any angle from −180° to +180° |
| **Start over** | **Reset** button | Returns the frame to centred, full-size, level |

The **Zoom** and **Angle** sliders and the mouse/wheel gestures stay in sync —
dragging the wheel moves the Zoom slider, and vice-versa.

> **A higher zoom means a tighter, more magnified crop** — the instax frame
> covers a smaller part of the original photo, so fewer source pixels fill the
> print. Watch the DPI readout (below) as you zoom in.

---

## The DPI Readout

Under each crop station is a live **effective print resolution** for that crop,
e.g. `≈ 312 DPI`. It's the number of original photo pixels that will be printed
per inch of instax image at the current zoom.

- **180 DPI or above** — good; the print will look crisp.
- **Below 180 DPI** — the readout turns **red** with a `⚠ low-res` note, and the
  bottom status bar names which photos are soft. The print will still generate,
  but that photo may look a little fuzzy. Zoom out (loosen the crop) or use a
  higher-resolution source to recover sharpness.

The status bar at the bottom summarises the whole sheet:

- `2 / 3 images loaded — load all three to continue.`
- `Ready — note: photo(s) 3 are below 180 DPI and may look soft.` (red)
- `All three ready and at good resolution ✓` (green)

---

## Generating the 4R Sheet

When all three photos are framed, click **Generate 4R sheet**. Each crop is
placed inside a full instax-mini card and the three cards are packed **edge-to-edge
and flush to the top** of the 4R. A preview window opens showing the finished
sheet at **15×10 cm**.

### What the sheet looks like

- Three **54×86 mm instax cards** across the width, white borders and all.
- **Cut marks** only where you actually need to cut:
  - two **full-height vertical lines** between the cards, and
  - one **horizontal trim line** across the bottom of the cards.
- The **left, right, and top edges are the sheet's own trim edges** — nothing to
  cut there.

Because three 54 mm cards (162 mm) are slightly wider than the 4R (152 mm), the
cards print a touch under full instax size — the difference is a couple of
millimetres and not noticeable once cut.

---

## Saving and Printing

The preview dialog has three buttons:

### Save…

Opens a save dialog. Choose **JPEG**, **PNG**, or **TIFF**. The file is written at
**300 DPI with the physical size embedded**, so a photo lab (or your own printer)
reproduces it at exactly 15×10 cm without you having to set the size manually.

### Print…

Opens the system print dialog and sends the sheet straight to a printer at 300
DPI, scaled to fit the page while keeping its aspect ratio and centred.

### Close

Dismisses the preview and returns to the crop stations — your three crops are
kept, so you can tweak one and regenerate.

---

## Cutting the Print

1. Make the **two vertical cuts** between the cards (full height of the sheet).
   Each cut splits the shared white gutter into an even ~3.7 mm border on both
   neighbours.
2. Make the **one horizontal cut** along the bottom trim line to remove the strip
   under the cards.

That's it — three cuts total, and you have three instax-mini-style prints.

---

## Tips

- **Batch a shoot:** load all three from the same folder (the dialog remembers
  it), frame quickly, generate, then load the next three over the top.
- **Rotate before zooming** if a subject is tilted — the frame stays inside the
  photo at any angle, so you won't fight blank corners.
- **Keep an eye on the DPI colour** — green everywhere means a sharp print.
- **Regenerate freely** — closing the preview keeps your crops, so it's cheap to
  nudge one frame and make a new sheet.
