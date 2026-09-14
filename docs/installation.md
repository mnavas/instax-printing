# Installation Guide

## Prerequisites

- **Python 3.11 or newer** — [python.org/downloads](https://www.python.org/downloads/)
- **pip** (bundled with Python 3.11+)
- **git** (to clone the repository)

instax-printing is a desktop app built on **PyQt6 + OpenCV + Pillow**. There is no
build step — clone, install the four Python dependencies, and run.

---

## Linux

### 1 — System dependencies

PyQt6 requires a few system libraries that may not be present on a minimal install.

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install python3-dev libxcb-cursor0 libgl1
```

**Fedora / RHEL:**
```bash
sudo dnf install python3-devel xcb-util-cursor mesa-libGL
```

**Arch:**
```bash
sudo pacman -S xcb-util-cursor mesa
```

> If you see `qt.qpa.plugin: could not load the Qt platform plugin "xcb"` on
> launch, the `libxcb-cursor0` package is likely missing.

Direct printing (the **Print…** button in the preview dialog) also needs a
working CUPS setup, which is standard on most desktop distros. Saving to a file
works without it.

### 2 — Clone and run

```bash
git clone https://github.com/mnavas/instax-printing.git
cd instax-printing
./run.sh
```

`run.sh` creates a local `.venv`, installs the dependencies from
`requirements.txt` on first run, and launches the app. Every run after that just
starts the app.

### 3 — Run by hand (optional)

If you'd rather manage the virtual environment yourself:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 4 — Desktop launcher (optional)

Create a `.desktop` entry so the app appears in your application menu:

```bash
cat > ~/.local/share/applications/instax-printing.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=instax-printing
Comment=Arrange three instax-mini photos on a print-ready 4R sheet
Exec=/absolute/path/to/instax-printing/run.sh
Icon=shotwell
Terminal=false
Categories=Graphics;Photography;
StartupNotify=true
EOF
```

Replace `/absolute/path/to/instax-printing` with the actual path where you cloned
the repo, then:

```bash
chmod +x /absolute/path/to/instax-printing/run.sh
update-desktop-database ~/.local/share/applications/
```

---

## macOS

### 1 — Clone and install

```bash
git clone https://github.com/mnavas/instax-printing.git
cd instax-printing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2 — Run

```bash
source .venv/bin/activate
python main.py
```

The `run.sh` launcher works on macOS too (it uses `python3` by default).

---

## Windows

### 1 — Clone and install

Open **PowerShell** or **Command Prompt**:

```powershell
git clone https://github.com/mnavas/instax-printing.git
cd instax-printing
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2 — Run

```powershell
.venv\Scripts\activate
python main.py
```

> `run.sh` is a Bash script — on Windows launch with `python main.py` (or run
> `run.sh` from Git Bash / WSL).

---

## Dependencies

All Python dependencies are pinned in `requirements.txt`:

| Package | Version | Purpose |
|---------|---------|---------|
| `PyQt6` | ≥ 6.6 | UI framework, print dialog |
| `opencv-python` | ≥ 4.9 | Image loading, the crop warp, and 4R compositing |
| `Pillow` | ≥ 10.0 | DPI-aware saving (embeds 300 DPI into the file) |
| `numpy` | ≥ 1.24 | Array maths for the crop transform and canvas |

No account, API key, or internet connection is required — everything runs
locally.

---

## First launch

The window opens with **three empty crop slots**. Click **Load #1**, **#2**, and
**#3** to choose a photo for each, position the instax frame on each one, then
**Generate 4R sheet**. See [user-guide.md](user-guide.md) for the full workflow.

The file dialog remembers the last folder you loaded from, shared across all
three slots, so a folder of photos is quick to work through.
