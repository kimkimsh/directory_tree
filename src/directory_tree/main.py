"""Entry point for the Directory Tree Viewer application."""

from __future__ import annotations

import os
import sys

# Ensure directory_tree package is importable in all execution modes:
# 1. python main.py (direct script)
# 2. python -m directory_tree.main (package)
# 3. PyInstaller frozen EXE
_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src not in sys.path:
    sys.path.insert(0, _src)

from directory_tree.utils import get_root_path
from directory_tree.app import Application


def main() -> None:
    root_path = get_root_path()
    app = Application(root_path)
    app.run()


if __name__ == "__main__":
    main()
