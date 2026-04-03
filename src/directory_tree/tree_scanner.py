"""Directory scanning with lazy loading and background recursive scan."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Callable, Optional


DEFAULT_EXCLUDED_DIRS: frozenset[str] = frozenset({
    "node_modules", ".git", "__pycache__", ".venv", "venv", ".env",
    ".idea", ".vs", ".vscode", ".mypy_cache", ".pytest_cache", ".tox",
    "dist", "build", "__pypackages__",
})


@dataclass(frozen=True, slots=True)
class FileEntry:
    name: str
    path: str
    is_directory: bool
    size: int = 0
    modified: float = 0.0
    depth: int = 0
    parent_path: str = ""


def scan_single_level(
    directory: str,
    *,
    excluded_dirs: frozenset[str] = DEFAULT_EXCLUDED_DIRS,
    depth: int = 0,
) -> list[FileEntry]:
    """Scan one level of a directory for lazy tree expansion."""
    entries: list[FileEntry] = []
    try:
        with os.scandir(directory) as it:
            for entry in it:
                if entry.name in excluded_dirs:
                    continue
                try:
                    stat = entry.stat(follow_symlinks=False)
                    is_dir = entry.is_dir(follow_symlinks=False)
                    entries.append(FileEntry(
                        name=entry.name,
                        path=entry.path,
                        is_directory=is_dir,
                        size=0 if is_dir else stat.st_size,
                        modified=stat.st_mtime,
                        depth=depth,
                        parent_path=directory,
                    ))
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass

    entries.sort(key=lambda e: (not e.is_directory, e.name.lower()))
    return entries


def scan_recursive(
    root: str,
    *,
    excluded_dirs: frozenset[str] = DEFAULT_EXCLUDED_DIRS,
    on_progress: Optional[Callable[[int], None]] = None,
    cancel_event: Optional[threading.Event] = None,
) -> list[FileEntry]:
    """Full recursive scan for building the search index."""
    all_entries: list[FileEntry] = []
    root = os.path.normpath(root)

    for dirpath, dirnames, filenames in os.walk(root):
        if cancel_event and cancel_event.is_set():
            break

        dirnames[:] = sorted(
            [d for d in dirnames if d not in excluded_dirs],
            key=str.lower,
        )

        depth = dirpath[len(root):].count(os.sep)
        parent = os.path.dirname(dirpath)

        for d in dirnames:
            full = os.path.join(dirpath, d)
            try:
                stat = os.stat(full)
                all_entries.append(FileEntry(
                    name=d, path=full, is_directory=True,
                    size=0, modified=stat.st_mtime,
                    depth=depth + 1, parent_path=dirpath,
                ))
            except (OSError, PermissionError):
                continue

        for f in sorted(filenames, key=str.lower):
            full = os.path.join(dirpath, f)
            try:
                stat = os.stat(full)
                all_entries.append(FileEntry(
                    name=f, path=full, is_directory=False,
                    size=stat.st_size, modified=stat.st_mtime,
                    depth=depth + 1, parent_path=dirpath,
                ))
            except (OSError, PermissionError):
                continue

        if on_progress:
            on_progress(len(all_entries))

    return all_entries


class BackgroundScanner:
    """Cancellable full-tree scan in a daemon thread."""

    def __init__(
        self,
        root: str,
        *,
        excluded_dirs: frozenset[str] = DEFAULT_EXCLUDED_DIRS,
        on_done: Optional[Callable[[list[FileEntry]], None]] = None,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> None:
        self._root = root
        self._excluded_dirs = excluded_dirs
        self._on_done = on_done
        self._on_progress = on_progress
        self._cancel_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._entries: list[FileEntry] = []

    @property
    def entries(self) -> list[FileEntry]:
        return self._entries

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return
        self._cancel_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        self._cancel_event.set()

    def _run(self) -> None:
        self._entries = scan_recursive(
            self._root,
            excluded_dirs=self._excluded_dirs,
            on_progress=self._on_progress,
            cancel_event=self._cancel_event,
        )
        if self._on_done and not self._cancel_event.is_set():
            self._on_done(self._entries)
