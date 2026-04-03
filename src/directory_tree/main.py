"""Entry point for the Directory Tree Viewer application."""

from __future__ import annotations

import os
import sys

# Support both direct execution (python main.py) and package execution (python -m ...)
if __name__ == "__main__" and __package__ is None:
    # Add src/ to sys.path so absolute imports work
    _src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _src not in sys.path:
        sys.path.insert(0, _src)
    __package__ = "directory_tree"

from .utils import get_root_path
from .app import Application


def main() -> None:
    root_path = get_root_path()
    app = Application(root_path)
    app.run()


if __name__ == "__main__":
    main()
