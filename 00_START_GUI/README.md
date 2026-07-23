# 🚀 START GUI Application

This folder contains quick-start scripts for launching the **Medical Data Collector** desktop application.

## Quick Start

### Windows
Double-click `start_gui.bat` or run in command prompt:
```cmd
start_gui.bat
```

### Linux / macOS
Run in terminal:
```bash
./start_gui.sh
chmod +x start_gui.sh  # First time only
```

### Any Platform (Python)
Run using Python directly:
```bash
python start_gui.py
```

## What This Does

- ✅ Launches the PyQt6 desktop GUI application
- ✅ Checks for Python installation
- ✅ Loads your configuration from `config/settings.yaml`
- ✅ Connects to your configured medical portals (Diagnostyka.pl, Badaj.to)

## First Time Setup

Before running for the first time, install dependencies:

```bash
cd ..  # Go to project root
pip install -r requirements.txt
python -m playwright install chromium
```

## Features

Once the application starts, you can:

1. **Login** 🔐 — Log into your medical portal (manual login in browser)
2. **Scan** 🔍 — Load your list of medical documents
3. **Filter** 📋 — Filter by date, test type, or search text
4. **Select** ☑️ — Choose which documents to download
5. **Download** ⬇️ — Download selected files with progress tracking

## Troubleshooting

### "Python not found"
- **Windows**: Install Python from https://www.python.org/ (add to PATH during installation)
- **Linux**: `sudo apt install python3`
- **macOS**: `brew install python3`

### "Module not found" errors
Install missing dependencies:
```bash
pip install -r requirements.txt
```

### GUI doesn't start
Check the logs:
```bash
tail -f logs/$(date +%Y-%m-%d)_run.log
```

### Browser automation issues
Install Playwright browsers:
```bash
python -m playwright install chromium
```

## More Information

- See `CLAUDE.md` in project root for architecture documentation
- See `config/settings.yaml` to configure portals and download folders
- Check `logs/` folder for application logs

---

**Medical Data Collector v1.0** — Your personal medical document manager
