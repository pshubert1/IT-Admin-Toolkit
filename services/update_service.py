"""
Interfaces with the Windows Update Agent (WUA) COM API to
search for missing updates.

Optimised:
  • Only accesses fast COM properties.
  • Explicitly releases COM objects before CoUninitialize to avoid
    slow garbage-collected COM Release() calls.
"""

import gc
import logging
import pythoncom
import win32com.client
from typing import List, Callable, Optional
from models.update_info import UpdateInfo

logger = logging.getLogger(__name__)


class UpdateService:
    """Wraps the Windows Update Agent search functionality."""

    _SEARCH_CRITERIA = "IsInstalled=0 AND IsHidden=0"

    @staticmethod
    def search_missing_updates(
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ) -> List[UpdateInfo]:
        """
        Query Windows Update for all missing (not-installed) updates.

        Parameters
        ----------
        progress_callback : callable, optional
            Called as progress_callback(message, level).

        Returns
        -------
        list[UpdateInfo]
        """

        def _report(msg: str, level: str = "step"):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg, level)

        _report("Initializing COM interface...", "info")
        pythoncom.CoInitialize()

        session = None
        searcher = None
        search_result = None
        item = None

        try:
            _report("Creating Windows Update session...")
            session = win32com.client.Dispatch("Microsoft.Update.Session")

            _report("Creating update searcher...")
            searcher = session.CreateUpdateSearcher()

            _report(f"Searching with criteria: {UpdateService._SEARCH_CRITERIA}")
            _report(
                "⏳ Contacting Windows Update servers — this may take a while...",
                "warning",
            )

            search_result = searcher.Search(UpdateService._SEARCH_CRITERIA)

            total = search_result.Updates.Count
            _report(f"Search complete. Found {total} update(s). Processing...", "success")

            # ---------------------------------------------------------
            #  Extract data into pure-Python objects as fast as possible,
            #  then release every COM reference.
            # ---------------------------------------------------------
            updates: List[UpdateInfo] = []

            for i in range(total):
                item = search_result.Updates.Item(i)

                title = item.Title

                kb_ids = []
                for k in range(item.KBArticleIDs.Count):
                    kb_ids.append(str(item.KBArticleIDs.Item(k)))

                severity = "Unspecified"
                try:
                    if item.MsrcSeverity:
                        severity = item.MsrcSeverity
                except Exception:
                    pass

                size = 0
                try:
                    size = int(item.MaxDownloadSize)
                except Exception:
                    pass

                updates.append(
                    UpdateInfo(
                        title=title,
                        kb_article_ids=kb_ids,
                        severity=severity,
                        is_downloaded=bool(item.IsDownloaded),
                        is_mandatory=bool(item.IsMandatory),
                        max_download_size=size,
                    )
                )

                # Release this item's COM pointer immediately
                item = None

            # Log all titles in one batch
            for idx, upd in enumerate(updates, 1):
                _report(f"  {idx}/{total}: {upd.title}")

            _report(f"✅ Done — {len(updates)} missing update(s) catalogued.", "success")

            # ---------------------------------------------------------
            #  EXPLICIT COM CLEANUP — this is the key fix.
            #  Release every COM reference in reverse order, then force
            #  garbage collection BEFORE CoUninitialize.
            #  Without this, CoUninitialize triggers slow Release()
            #  calls on dangling COM pointers.
            # ---------------------------------------------------------
            _report("Cleaning up COM objects...", "info")

            search_result = None
            searcher = None
            session = None
            gc.collect()

            _report("Releasing COM interface.", "info")
            pythoncom.CoUninitialize()

            return updates

        except Exception as exc:
            _report(f"❌ Error during update search: {exc}", "error")
            logger.exception("Update search failed")

            # Clean up on error path too
            item = None
            search_result = None
            searcher = None
            session = None
            gc.collect()

            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

            raise