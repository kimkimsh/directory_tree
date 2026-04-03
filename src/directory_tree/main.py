"""Entry point for the Directory Tree Viewer application."""

from __future__ import annotations

from .utils import get_root_path
from .app import Application


def main() -> None:
    root_path = get_root_path()
    app = Application(root_path)
    app.run()


if __name__ == "__main__":
    main()
