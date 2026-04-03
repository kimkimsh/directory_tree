# Directory Tree Viewer

A lightweight Windows GUI application for browsing directory structures with real-time search, lazy-loading tree expansion, and Windows Explorer integration.

<!-- screenshot -->

---

## Features

- **Hierarchical tree display** -- visualize folder and file structures with expand/collapse navigation
- **Lazy loading** -- subdirectories are scanned on demand when expanded, keeping startup fast
- **Background full-tree scan** -- a daemon thread indexes the entire directory tree for instant search
- **Real-time search with debounce** -- filter files and folders by name with 200ms input debounce; matching entries and their ancestor folders are displayed automatically
- **Match count indicator** -- live "N matches" counter next to the search bar
- **File metadata columns** -- file size (human-readable) and last-modified date displayed alongside each entry
- **Open in Explorer** -- open the selected file or folder in Windows Explorer with the item pre-selected (`/select,` mode)
- **Copy Path** -- copy the absolute path of the selected item to the clipboard
- **Refresh** -- re-scan the current root directory and rebuild the tree
- **Smart exclusions** -- common noise directories (`node_modules`, `.git`, `__pycache__`, `.venv`, `dist`, `build`, etc.) are excluded by default
- **Status bar** -- displays running file/folder counts and the current root path
- **Keyboard navigation** -- arrow keys, Enter, Ctrl+F, F5, and Escape shortcuts

---

## Quick Start

```bat
make.bat setup     :: one-time: create environment + install dependencies
make.bat run       :: launch the application
make.bat build     :: produce dist\DirectoryTree.exe
```

> **PowerShell users:** PowerShell does not run `.bat` files from the current directory without an explicit path prefix. Use `.\make.bat` instead of `make.bat`:
> ```powershell
> .\make.bat setup
> .\make.bat run
> .\make.bat build
> ```
> This is not required in CMD, where `make.bat` works directly.

The application opens in the current working directory by default. You can also pass a directory path as an argument:

```bat
make.bat run C:\path\to\directory
```

Or run the built executable directly:

```bat
dist\DirectoryTree.exe C:\path\to\directory
```

---

## Prerequisites

One of the following must be installed:

| Option | Details |
|--------|---------|
| **Python 3.12** | Download from [python.org](https://www.python.org/downloads/). Ensure "Add to PATH" and "py launcher" are checked during installation. |
| **Anaconda / Miniconda** | Download from [anaconda.com](https://www.anaconda.com/download) or [miniconda](https://docs.conda.io/en/latest/miniconda.html). |

No additional runtime dependencies are required -- the application uses only Python's built-in `tkinter` library.

---

## How `make.bat` Auto-Detection Works

`make.bat` automatically detects your Python environment using the following resolution order:

1. **Python 3.12 via `py` launcher** -- if `py -3.12 --version` succeeds, the script uses the standard `venv` module to create a `.venv/` virtual environment.
2. **Conda** -- if `py -3.12` is not available, the script checks for `conda` on PATH, then probes common installation paths (`%USERPROFILE%\anaconda3`, `%USERPROFILE%\miniconda3`, `%ProgramData%\anaconda3`, `%ProgramData%\miniconda3`). If found, it creates a conda environment named `directory_tree` with Python 3.12.
3. **Neither found** -- the script prints an error with installation links and exits.

All subsequent commands (`run`, `build`, `freeze`, etc.) invoke the correct Python executable for the detected mode, so you never need to manually activate the environment.

---

## Project Structure

```
directory_tree/
├── src/
│   └── directory_tree/
│       ├── __init__.py          # Package metadata and version
│       ├── main.py              # Entry point
│       ├── app.py               # Main Application class (GUI, event handling)
│       ├── tree_scanner.py      # Directory scanning (lazy + recursive + background)
│       ├── search.py            # Search and filter logic
│       └── utils.py             # Formatting, path helpers, OS integration
├── assets/
│   └── app.ico                  # Application icon
├── docs/
│   └── plan/
│       └── project-plan.md      # Project plan document
├── make.bat                     # Build system (setup / run / build / clean)
├── requirements.txt             # Runtime dependencies
├── requirements-dev.txt         # Development dependencies (includes PyInstaller)
├── DirectoryTree.spec           # PyInstaller spec (generated on first build)
└── README.md
```

---

## `make.bat` Commands

| Command | Description |
|---------|-------------|
| `setup` | Create virtual environment (venv or conda) and install all dependencies |
| `run` | Launch the application |
| `build` | Build a single `.exe` with PyInstaller (`--onefile --windowed`) |
| `rebuild` | Clean build artifacts, then build |
| `clean` | Remove `build/`, `dist/`, and all `__pycache__/` directories |
| `nuke` | Remove the environment entirely (`.venv` or conda env) |
| `freeze` | Export current pip packages to `requirements.txt` |
| `info` | Display detected environment mode, Python path, and version |
| `help` | Show usage information |

---

## Build and Distribution

The project uses **PyInstaller 6.x** to produce a standalone Windows executable.

### Build options applied

| Option | Purpose |
|--------|---------|
| `--onefile` | Bundle everything into a single `.exe` |
| `--windowed` | Suppress the console window (GUI application) |
| `--icon=assets/app.ico` | Embed the application icon (applied automatically if the file exists) |
| `--name DirectoryTree` | Set the output filename to `DirectoryTree.exe` |

### Expected EXE size

| Configuration | Approximate Size |
|---------------|-----------------|
| tkinter only | 10 -- 15 MB |
| tkinter + Pillow | 15 -- 20 MB |

### Notes

- If a `DirectoryTree.spec` file exists, PyInstaller uses it instead of generating a new configuration.
- `--onefile` executables extract to a temp directory on each launch, adding 2--5 seconds of cold-start time. For frequent personal use, consider `--onedir` mode instead.
- Unsigned PyInstaller executables may trigger Windows SmartScreen or antivirus warnings.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+F` | Focus the search bar |
| `F5` | Refresh the directory tree |
| `Escape` | Clear the current search query |
| `Enter` | Open the selected item in Windows Explorer |
| `Double-click` | Open the selected item in Windows Explorer |
| Arrow keys | Navigate the tree |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| GUI framework | tkinter / ttk (built-in) |
| Styling | ttk `vista` theme with custom Segoe UI fonts |
| Directory scanning | `os.scandir` / `os.walk` with background `threading.Thread` |
| Search | Case-insensitive substring matching with ancestor-path reconstruction |
| Explorer integration | `subprocess.Popen` with `/select,` flag |
| Build tool | PyInstaller >= 6.0 |
| Build system | `make.bat` (Windows batch) |

---

## Default Excluded Directories

The following directories are excluded from scanning to reduce noise and improve performance:

```
node_modules  .git  __pycache__  .venv  venv  .env
.idea  .vs  .vscode  .mypy_cache  .pytest_cache  .tox
dist  build  __pypackages__
```

---

## License

This project is licensed under the [MIT License](LICENSE).
