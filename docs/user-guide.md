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

## Three Tools (the menu)

The app has three tools, chosen from the **Tools** menu in the menu bar:

- **4R Print Sheet (3 instax mini)** — the default; the sheet workflow described
  below. Three instax-mini cards on one 15×10 cm lab print.
- **Instax Collage** — combine several photos into **one** instax-sized image
  (Mini, Square, or Wide) and export it to print on an **instax printer**, with
  or without the white border. See [Instax Collage](#instax-collage) below.
- **A4 Instax Sheet** — pack the most instax cards that fit on a landscape A4
  (10 Mini / 8 Square / 4 Wide), true-size with cut lines, for **home printing**.
  See [A4 Instax Sheet](#a4-instax-sheet) below.

**File → Quit** (Ctrl+Q) closes the app.

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
│  2 / 3 images loaded …          [ New sheet ] [ Generate 4R sheet ]│
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

When all three photos are framed, click **Generate 4R sheet**. A preview window
opens showing the finished sheet at **15×10 cm**, where you choose the **border**
style (the preview updates as you switch):

### Border: Instax border (default)

Each crop is placed inside a full **instax-mini card** (white border, thin
top/sides, thick bottom) and the three cards are packed **edge-to-edge and flush
to the top** of the 4R:

- Three **54×86 mm instax cards** across the width, white borders and all.
- **Cut marks** only where you need to cut — two **full-height vertical lines**
  between the cards and one **horizontal trim line** across the card bottoms; the
  left/right/top edges are the sheet's own trim edges.

Because three 54 mm cards (162 mm) are slightly wider than the 4R (152 mm), the
cards print a touch under full instax size — a couple of millimetres, not
noticeable once cut. Each cut-out looks like a real instax mini.

### Border: Thin border only

Each photo gets just a **thin uniform white border** (no instax frame), so the
images print **bigger**. The three photos are centred across the 4R, each outlined
with a **cut line** — trim along the lines for near-borderless prints. Pick this
when you want more photo and less white.

---

## Saving and Printing

The preview dialog has three buttons:

### Save…

Opens a save dialog. Choose **JPEG**, **PNG**, or **TIFF**. The file is written at
**300 DPI with the physical size embedded**, so a photo lab (or your own printer)
reproduces it at exactly 15×10 cm without you having to set the size manually.

The dialog opens in the **folder you saved to last** (during the session) and
suggests the next free name — `instax_4r.jpg`, then `instax_4r_1.jpg`,
`instax_4r_2.jpg`, and so on — so **saving another sheet never overwrites an
earlier one**. You can of course rename it to whatever you like.

### Print…

Opens the system print dialog and sends the sheet straight to a printer at 300
DPI, scaled to fit the page while keeping its aspect ratio and centred.

### High resolution (600 DPI)

Tick **High resolution (2× · 600 DPI)** to save or print at **double** the pixels
and DPI. The output is **re-rendered from your source photos**, so the extra
resolution is real detail (not upscaling) — useful for sharper prints or larger
reproductions. The file is bigger; leave the box unticked for the usual 300-DPI
output. This option is in **every** tool's preview (4R sheet, collage, and A4).

### Close

Dismisses the preview and returns to the crop stations — your three crops are
kept, so you can tweak one and regenerate.

---

## Starting a New Sheet

Two ways to start over:

- **Reset one photo** — the **Reset** button on a crop station returns just that
  frame to centred, full-size, and level (the photo stays loaded).
- **New sheet** — the **New sheet** button in the bottom bar clears **all three**
  photos at once so you can build a fresh sheet. It asks for confirmation first
  (as long as at least one photo is loaded) so you don't wipe your work by
  accident.

---

## Cutting the Print

1. Make the **two vertical cuts** between the cards (full height of the sheet).
   Each cut splits the shared white gutter into an even ~3.7 mm border on both
   neighbours.
2. Make the **one horizontal cut** along the bottom trim line to remove the strip
   under the cards.

That's it — three cuts total, and you have three instax-mini-style prints.

---

## Instax Collage

Switch to **Tools → Instax Collage** to combine several photos into a single
instax-sized image — the kind you send to an **instax printer** (Mini Link,
SP-2/3, Link Wide, etc.).

### 1 — Pick a format and layout

At the top of the tool:

- **Format** — the instax size you'll print on:
  - **Instax Mini** — 46×62 mm image (portrait)
  - **Instax Square** — 62×62 mm image
  - **Instax Wide** — 99×62 mm image (landscape)
- **Layout** — a preset arrangement that fills the frame (15 to choose from):
  **1 photo**; **2** side-by-side or stacked; **3** columns, rows, or one big
  photo plus two small (*1 top + 2*, *1 bottom + 2*, *1 left + 2*, *1 right + 2*);
  **4** as a 2×2 grid, columns, or rows; **5** as *1 top + 4*; **6** as 3×2; **9**
  as 3×3. The big cell is always **#1**.
(The gutter between photos and the border are set later, in the export preview.)

Changing either one rebuilds the cells below — and the grid of cells **mirrors the
layout** (the big cell is big, the row of small ones sits in a row), so you always
know which photo goes where.

### 2 — Fill each cell

Each cell is a crop station exactly like the sheet tool: **Load** a photo, then
**drag / wheel-zoom / rotate** to frame it. The frame is locked to that cell's
shape, and each cell shows its own effective-DPI readout (red below 180). Photos
fill the frame **edge-to-edge** — only the chosen gutter separates them.

### 3 — Export: set the gutter and border in the preview

Click **Export collage…** once every cell is filled. The preview shows the
finished collage and updates live as you adjust two things:

- **Gutter** — the thin white line *between* photos: **None**, **Thin** (default),
  or **Medium**. (There's no outer border around the whole collage — on an instax
  printer the **film supplies that**.)
- **Add white instax border** — leave it **off** for an instax printer (image only
  at the printer's native resolution — 600×800 Mini, 800×800 Square, 1260×840
  Wide). Turn it **on** only for a *normal* printer to wrap the collage in a full
  instax card (thin top/sides, thick bottom); an instax printer would double it.

Change either and watch the preview, so you can see exactly what you'll get before
you print.

**Save…** writes a JPEG/PNG/TIFF with the instax print DPI embedded (using the
last-used folder and the same incremental naming as the sheet tool), and
**Print…** sends it to a printer. Tick **High resolution (2× · 600 DPI)** for a
double-resolution file re-rendered from the source photos. **New collage** clears
every cell to start over.

> Changing the Format, Layout, or Gutter **keeps your loaded photos** — only cells
> that a smaller layout removes are dropped — so you can tweak freely without
> starting over.

---

## A4 Instax Sheet

Switch to **Tools → A4 Instax Sheet** to print the **most instax cards that fit on
a landscape A4** at home, then cut them out.

### 1 — Pick a format

- **Format** — Mini, Square, or Wide. The label shows how many fit per A4:
  - **Instax Mini** — **10** (5×2)
  - **Instax Square** — **8** (4×2)
  - **Instax Wide** — **4** (2×2)

The grid below shows one crop station per card.

### 2 — Fill the cards you want

Load a photo into as many cards as you like — **you don't have to fill them all**.
Each cell is the usual crop station (Load / ⟲ / ⟳ / Reset, Zoom + Angle, DPI
readout). Switching format keeps the photos you've already loaded (up to the new
capacity).

### 3 — Generate, save, print, cut

Click **Generate A4 sheet** (enabled once at least one card is loaded). The preview
shows a print-ready **A4 landscape** page:

- Each card is a **true-size** instax (300 DPI) with the **full white border**
  (thin top/sides, thick bottom) — nothing is shrunk.
- A **light-grey cut line** outlines every card; cards sit edge-to-edge, so one
  straight cut separates two.
- The block is **centred with a margin**, so it prints centred on A4 without the
  printer clipping the edges.

**Save…** writes a 300-DPI A4 image (print it at **100% / actual size** for exact
instax dimensions, or fit-to-page), **Print…** sends it to a printer, and **New
sheet** clears everything. Tick **High resolution (2× · 600 DPI)** for a
double-resolution A4 re-rendered from the source photos.

> **Tip:** to print several copies of the *same* photo, load it into each card.

---

## Tips

- **Batch a shoot:** load all three from the same folder (the dialog remembers
  it), frame quickly, generate, then load the next three over the top.
- **Rotate before zooming** if a subject is tilted — the frame stays inside the
  photo at any angle, so you won't fight blank corners.
- **Keep an eye on the DPI colour** — green everywhere means a sharp print.
- **Regenerate freely** — closing the preview keeps your crops, so it's cheap to
  nudge one frame and make a new sheet.
