"""
Data model representing a single Windows update.
Lightweight — only stores what we actually display.
"""

from dataclasses import dataclass, field
from typing import List

@dataclass
class UpdateInfo:
    title: str
    kb_article_ids: List[str] = field(default_factory=list)
    severity: str = "Unspecified"
    is_downloaded: bool = False
    is_mandatory: bool = False
    max_download_size: int = 0  # bytes  (0 = unknown / skipped)

    @property
    def kb_display(self) -> str:
        """Return a formatted KB string like 'KB1234567'."""
        if self.kb_article_ids:
            return ", ".join(f"KB{kb}" for kb in self.kb_article_ids)
        return "N/A"

    @property
    def size_display(self) -> str:
        """Return human-readable file size."""
        size = self.max_download_size
        if size <= 0:
            return "—"
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"