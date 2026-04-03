"""Search and filter logic for the directory tree."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from .tree_scanner import FileEntry


@dataclass(frozen=True, slots=True)
class SearchResult:
    query: str
    matches: list[FileEntry]
    ancestor_paths: set[str]
    total_count: int

    @property
    def match_count(self) -> int:
        return len(self.matches)


def search_entries(
    query: str,
    entries: list[FileEntry],
    *,
    root_path: Optional[str] = None,
) -> SearchResult:
    """Case-insensitive substring search across entry names."""
    query = query.strip()
    if not query:
        return SearchResult(query="", matches=[], ancestor_paths=set(), total_count=len(entries))

    query_lower = query.lower()
    matches: list[FileEntry] = []
    ancestor_paths: set[str] = set()

    for entry in entries:
        if query_lower in entry.name.lower():
            matches.append(entry)
            if root_path:
                ancestor_paths.update(collect_ancestor_paths(entry, root_path))

    return SearchResult(
        query=query,
        matches=matches,
        ancestor_paths=ancestor_paths,
        total_count=len(entries),
    )


def collect_ancestor_paths(entry: FileEntry, root_path: str) -> list[str]:
    """Walk parent directories from entry up to root (inclusive)."""
    ancestors: list[str] = []
    current = os.path.dirname(entry.path)
    root_norm = os.path.normpath(root_path)

    while True:
        current_norm = os.path.normpath(current)
        ancestors.append(current_norm)
        if current_norm == root_norm or current_norm == os.path.dirname(current_norm):
            break
        current = os.path.dirname(current)

    return ancestors
