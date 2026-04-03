"""Main GUI application for the directory tree viewer."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk
from typing import Optional

from .tree_scanner import (
    BackgroundScanner,
    FileEntry,
    scan_single_level,
    DEFAULT_EXCLUDED_DIRS,
)
from .search import SearchResult, search_entries
from .utils import (
    format_file_size,
    format_timestamp,
    open_in_explorer,
    copy_to_clipboard,
    shorten_path,
)

DUMMY_SUFFIX = "__dummy__"


class Application:
    """Top-level application controller using composition over tk.Tk."""

    def __init__(self, root_path: str) -> None:
        self._root_path = os.path.normpath(root_path)
        self._all_entries: list[FileEntry] = []
        self._scanner: Optional[BackgroundScanner] = None
        self._search_after_id: Optional[str] = None
        self._path_map: dict[str, str] = {}  # treeview iid -> absolute path
        self._is_dir_map: dict[str, bool] = {}  # treeview iid -> is_directory
        self._file_count = 0
        self._dir_count = 0

        # Build UI
        self._root = tk.Tk()
        self._setup_window()
        self._setup_styles()

        # Layout
        self._build_toolbar(self._root)
        self._build_search_bar(self._root)
        self._tree = self._build_treeview(self._root)
        self._build_button_bar(self._root)
        self._build_status_bar(self._root)

        self._bind_shortcuts()
        self._root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Initial population
        self._populate_root()
        self._start_background_scan()

    def _setup_window(self) -> None:
        self._root.title("Directory Tree Viewer")
        self._root.geometry("900x650")
        self._root.minsize(600, 400)
        try:
            self._root.state("zoomed")
        except tk.TclError:
            pass

    def _setup_styles(self) -> None:
        style = ttk.Style(self._root)
        try:
            style.theme_use("vista")
        except tk.TclError:
            style.theme_use("clam")

        style.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=24,
            background="#ffffff",
            foreground="#1a1a1a",
            fieldbackground="#ffffff",
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI Semibold", 10),
            padding=(6, 3),
        )
        style.map(
            "Treeview",
            background=[("selected", "#0078D4")],
            foreground=[("selected", "#ffffff")],
        )
        style.configure(
            "Action.TButton",
            font=("Segoe UI", 9),
            padding=(10, 4),
        )
        style.configure(
            "Status.TLabel",
            font=("Segoe UI", 9),
            padding=(6, 3),
            background="#f0f0f0",
        )

    # -- Widget construction ------------------------------------------------

    def _build_toolbar(self, parent: tk.Widget) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=8, pady=(8, 0))

        ttk.Label(
            frame, text="Root:", font=("Segoe UI Semibold", 10),
        ).pack(side=tk.LEFT)

        self._root_label = ttk.Label(
            frame,
            text=shorten_path(self._root_path, 80),
            font=("Segoe UI", 10),
        )
        self._root_label.pack(side=tk.LEFT, padx=(4, 0), fill=tk.X, expand=True)

        ttk.Button(
            frame, text="Refresh", style="Action.TButton",
            command=self._on_refresh,
        ).pack(side=tk.RIGHT)

    def _build_search_bar(self, parent: tk.Widget) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=8, pady=6)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_changed)

        ttk.Label(frame, text="Search:", font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self._search_entry = ttk.Entry(
            frame, textvariable=self._search_var, font=("Segoe UI", 10),
        )
        self._search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 6))

        self._match_label = ttk.Label(
            frame, text="", font=("Segoe UI", 9), foreground="#666666",
        )
        self._match_label.pack(side=tk.LEFT, padx=(0, 6))

        self._clear_btn = ttk.Button(
            frame, text="X", width=3, command=self._clear_search,
        )
        self._clear_btn.pack(side=tk.LEFT)

    def _build_treeview(self, parent: tk.Widget) -> ttk.Treeview:
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))

        tree = ttk.Treeview(
            container,
            columns=("size", "modified"),
            selectmode="browse",
            show="tree headings",
        )

        tree.heading("#0", text="Name", anchor=tk.W)
        tree.heading("size", text="Size", anchor=tk.E)
        tree.heading("modified", text="Modified", anchor=tk.W)

        tree.column("#0", width=450, minwidth=200, stretch=True)
        tree.column("size", width=100, minwidth=70, stretch=False, anchor=tk.E)
        tree.column("modified", width=150, minwidth=100, stretch=False)

        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)
        hsb = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        tree.bind("<<TreeviewOpen>>", self._on_tree_open)
        tree.bind("<Double-1>", lambda e: self._on_open_in_explorer())

        tree.tag_configure("folder", foreground="#1a1a1a")
        tree.tag_configure("file", foreground="#444444")

        return tree

    def _build_button_bar(self, parent: tk.Widget) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=8, pady=(0, 4))

        ttk.Button(
            frame, text="Open in Explorer", style="Action.TButton",
            command=self._on_open_in_explorer,
        ).pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(
            frame, text="Copy Path", style="Action.TButton",
            command=self._on_copy_path,
        ).pack(side=tk.LEFT)

    def _build_status_bar(self, parent: tk.Widget) -> None:
        frame = ttk.Frame(parent, relief=tk.SUNKEN)
        frame.pack(fill=tk.X, side=tk.BOTTOM)

        self._status_var = tk.StringVar(value="Loading...")
        ttk.Label(
            frame, textvariable=self._status_var, style="Status.TLabel",
        ).pack(fill=tk.X)

    # -- Treeview population ------------------------------------------------

    def _populate_root(self) -> None:
        self._tree.delete(*self._tree.get_children())
        self._path_map.clear()
        self._is_dir_map.clear()
        self._file_count = 0
        self._dir_count = 0

        entries = scan_single_level(self._root_path, depth=0)
        self._insert_children("", entries)
        self._update_counts(entries)
        self._refresh_status()

    def _insert_children(self, parent_iid: str, entries: list[FileEntry]) -> None:
        for entry in entries:
            prefix = "\U0001f4c1 " if entry.is_directory else "\U0001f4c4 "
            tag = "folder" if entry.is_directory else "file"

            iid = self._tree.insert(
                parent_iid, tk.END,
                text=f"{prefix}{entry.name}",
                values=(
                    format_file_size(entry.size),
                    format_timestamp(entry.modified),
                ),
                open=False,
                tags=(tag,),
            )
            self._path_map[iid] = entry.path
            self._is_dir_map[iid] = entry.is_directory

            if entry.is_directory:
                self._tree.insert(iid, tk.END, iid=f"{iid}{DUMMY_SUFFIX}", text="")

    def _on_tree_open(self, event: tk.Event) -> None:
        iid = self._tree.focus()
        children = self._tree.get_children(iid)
        if len(children) == 1 and str(children[0]).endswith(DUMMY_SUFFIX):
            self._tree.delete(children[0])
            path = self._path_map.get(iid, "")
            if path:
                entries = scan_single_level(path, depth=0)
                self._insert_children(iid, entries)
                self._update_counts(entries)
                self._refresh_status()

    def _update_counts(self, entries: list[FileEntry]) -> None:
        for e in entries:
            if e.is_directory:
                self._dir_count += 1
            else:
                self._file_count += 1

    def _refresh_status(self) -> None:
        self._status_var.set(
            f"Files: {self._file_count:,} | Folders: {self._dir_count:,} "
            f"| Root: {shorten_path(self._root_path, 70)}"
        )

    # -- Search ------------------------------------------------------------

    def _on_search_changed(self, *_args: object) -> None:
        if self._search_after_id is not None:
            self._root.after_cancel(self._search_after_id)
        self._search_after_id = self._root.after(200, self._execute_search)

    def _execute_search(self) -> None:
        self._search_after_id = None
        query = self._search_var.get().strip()

        if not query:
            self._match_label.config(text="")
            self._populate_root()
            return

        if not self._all_entries:
            self._match_label.config(text="Scanning...")
            self._start_background_scan()
            return

        result = search_entries(query, self._all_entries, root_path=self._root_path)
        self._match_label.config(text=f"{result.match_count} matches")
        self._show_search_results(result.matches, result.ancestor_paths)

    def _show_search_results(
        self, matches: list[FileEntry], ancestor_paths: set[str],
    ) -> None:
        self._tree.delete(*self._tree.get_children())
        self._path_map.clear()
        self._is_dir_map.clear()

        # Build a set of all paths that should be visible
        visible_paths: set[str] = ancestor_paths.copy()
        for m in matches:
            visible_paths.add(os.path.normpath(m.path))

        # Build entries grouped by parent for tree reconstruction
        by_parent: dict[str, list[FileEntry]] = {}
        root_norm = os.path.normpath(self._root_path)

        # Add ancestor directories as entries
        for ap in sorted(ancestor_paths, key=lambda p: p.count(os.sep)):
            parent_dir = os.path.dirname(ap)
            if ap == root_norm:
                continue
            name = os.path.basename(ap)
            by_parent.setdefault(parent_dir, []).append(FileEntry(
                name=name, path=ap, is_directory=True,
                size=0, modified=0.0, depth=0, parent_path=parent_dir,
            ))

        # Add matched entries
        for m in matches:
            parent_norm = os.path.normpath(m.parent_path)
            by_parent.setdefault(parent_norm, []).append(m)

        # Deduplicate entries per parent
        for parent in by_parent:
            seen: set[str] = set()
            unique: list[FileEntry] = []
            for entry in by_parent[parent]:
                norm = os.path.normpath(entry.path)
                if norm not in seen:
                    seen.add(norm)
                    unique.append(entry)
            unique.sort(key=lambda e: (not e.is_directory, e.name.lower()))
            by_parent[parent] = unique

        # Recursive insert starting from root
        iid_map: dict[str, str] = {}  # normalized path -> treeview iid

        def insert_entries(parent_path: str, parent_iid: str) -> None:
            for entry in by_parent.get(parent_path, []):
                prefix = "\U0001f4c1 " if entry.is_directory else "\U0001f4c4 "
                tag = "folder" if entry.is_directory else "file"
                iid = self._tree.insert(
                    parent_iid, tk.END,
                    text=f"{prefix}{entry.name}",
                    values=(
                        format_file_size(entry.size),
                        format_timestamp(entry.modified),
                    ),
                    open=True,
                    tags=(tag,),
                )
                norm = os.path.normpath(entry.path)
                self._path_map[iid] = entry.path
                self._is_dir_map[iid] = entry.is_directory
                iid_map[norm] = iid

                if entry.is_directory and norm in ancestor_paths:
                    insert_entries(norm, iid)

        insert_entries(root_norm, "")

    def _clear_search(self) -> None:
        self._search_var.set("")
        self._match_label.config(text="")
        self._search_entry.focus_set()

    # -- Background scanning -----------------------------------------------

    def _start_background_scan(self) -> None:
        if self._scanner and self._scanner.is_running:
            return
        self._scanner = BackgroundScanner(
            self._root_path,
            on_done=self._on_scan_complete,
            on_progress=self._on_scan_progress,
        )
        self._scanner.start()

    def _on_scan_progress(self, count: int) -> None:
        self._root.after(0, lambda: self._status_var.set(
            f"Scanning... {count:,} items found"
        ))

    def _on_scan_complete(self, entries: list[FileEntry]) -> None:
        def _update() -> None:
            self._all_entries = entries
            dirs = sum(1 for e in entries if e.is_directory)
            files = len(entries) - dirs
            self._file_count = files
            self._dir_count = dirs
            self._refresh_status()

            # If there's a pending search query, execute it now
            query = self._search_var.get().strip()
            if query:
                self._execute_search()

        self._root.after(0, _update)

    # -- Button / action handlers ------------------------------------------

    def _on_open_in_explorer(self) -> None:
        selected = self._tree.selection()
        if not selected:
            return
        path = self._path_map.get(selected[0], "")
        if path and os.path.exists(path):
            open_in_explorer(path)

    def _on_copy_path(self) -> None:
        selected = self._tree.selection()
        if not selected:
            return
        path = self._path_map.get(selected[0], "")
        if path:
            copy_to_clipboard(self._root, path)
            old = self._status_var.get()
            self._status_var.set("Path copied to clipboard!")
            self._root.after(2000, lambda: self._status_var.set(old))

    def _on_refresh(self) -> None:
        if self._scanner and self._scanner.is_running:
            self._scanner.cancel()
        self._all_entries.clear()
        self._search_var.set("")
        self._match_label.config(text="")
        self._populate_root()
        self._start_background_scan()

    # -- Keyboard shortcuts ------------------------------------------------

    def _bind_shortcuts(self) -> None:
        self._root.bind("<Control-f>", lambda e: self._search_entry.focus_set())
        self._root.bind("<F5>", lambda e: self._on_refresh())
        self._root.bind("<Escape>", lambda e: self._clear_search())
        self._root.bind("<Return>", lambda e: self._on_open_in_explorer())

    # -- Status bar --------------------------------------------------------

    def _update_status(self, text: str) -> None:
        self._status_var.set(text)

    # -- Application lifecycle ---------------------------------------------

    def run(self) -> None:
        self._root.mainloop()

    def _on_closing(self) -> None:
        if self._scanner and self._scanner.is_running:
            self._scanner.cancel()
        self._root.destroy()
