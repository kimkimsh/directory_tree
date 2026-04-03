"""Utility functions for formatting, path handling, and OS integration."""

from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime


def format_file_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes} {unit}" if unit == "B" else f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def format_timestamp(timestamp: float, fmt: str = "%Y-%m-%d %H:%M") -> str:
    if timestamp == 0:
        return ""
    try:
        return datetime.fromtimestamp(timestamp).strftime(fmt)
    except (OSError, ValueError):
        return ""


def shorten_path(path: str, max_length: int = 60) -> str:
    if len(path) <= max_length:
        return path
    parts = path.replace("\\", "/").split("/")
    if len(parts) <= 3:
        return path[:max_length - 3] + "..."
    head = "/".join(parts[:2])
    tail = "/".join(parts[-2:])
    return f"{head}/.../{tail}"


def normalize_path(path: str) -> str:
    return os.path.normpath(os.path.abspath(path))


def open_in_explorer(path: str) -> None:
    path = os.path.normpath(path)
    if os.path.isdir(path):
        subprocess.Popen(["explorer", path])
    else:
        subprocess.Popen(["explorer", "/select,", path])


def copy_to_clipboard(root: tk.Tk | tk.Misc, text: str) -> None:
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()


def get_root_path() -> str:
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        return normalize_path(sys.argv[1])
    if getattr(sys, "frozen", False):
        return normalize_path(os.path.dirname(sys.executable))
    return normalize_path(os.getcwd())
