"""
Downloads and installs selected Windows updates via the WUA COM API.
Must be run as Administrator.

Uses explicit COM object cleanup to prevent slow CoUninitialize.
"""

import gc
import logging
import pythoncom
import win32com.client
from typing import List, Callable, Optional

logger = logging.getLogger(__name__)

_RESULT_CODES = {
    0: "Not Started",
    1: "In Progress",
    2: "Succeeded",
    3: "Succeeded With Errors",
    4: "Failed",
    5: "Aborted",
}


class InstallService:
    """Downloads and installs Windows updates by title."""

    @staticmethod
    def download_and_install(
        selected_titles: List[str],
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ) -> dict:
        """
        Search for, download, and install updates matching *selected_titles*.

        Returns
        -------
        dict   {"installed": int, "failed": int, "reboot_required": bool, "details": list}
        """

        def _report(msg: str, level: str = "step"):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg, level)

        _report("Initializing COM interface for install...", "info")
        pythoncom.CoInitialize()

        session = None
        searcher = None
        search_result = None
        downloader = None
        installer = None
        updates_to_install = None
        download_result = None
        install_result = None

        try:
            # ----------------------------------------------------------
            #  1. Re-search (COM objects can't cross threads)
            # ----------------------------------------------------------
            _report("Creating Windows Update session...")
            session = win32com.client.Dispatch("Microsoft.Update.Session")
            searcher = session.CreateUpdateSearcher()

            _report("Re-searching for available updates...")
            search_result = searcher.Search("IsInstalled=0 AND IsHidden=0")

            total_available = search_result.Updates.Count
            _report(f"Found {total_available} available update(s). Matching your selection...")

            # ----------------------------------------------------------
            #  2. Build collection of selected updates
            # ----------------------------------------------------------
            title_set = set(selected_titles)
            updates_to_install = win32com.client.Dispatch("Microsoft.Update.UpdateColl")
            matched_titles = []

            for i in range(total_available):
                update = search_result.Updates.Item(i)
                if update.Title in title_set:
                    if not update.EulaAccepted:
                        update.AcceptEula()
                        _report(f"  Accepted EULA for: {update.Title}")
                    updates_to_install.Add(update)
                    matched_titles.append(update.Title)
                    _report(f"  Queued: {update.Title}")
                update = None  # release COM ref immediately

            match_count = updates_to_install.Count
            if match_count == 0:
                _report("⚠️ No matching updates found to install.", "warning")
                return {"installed": 0, "failed": 0, "reboot_required": False, "details": []}

            _report(f"Matched {match_count} update(s) for install.", "success")

            # Release search objects — no longer needed
            search_result = None
            searcher = None
            gc.collect()

            # ----------------------------------------------------------
            #  3. Download
            # ----------------------------------------------------------
            _report("=" * 50, "info")
            _report("📥 DOWNLOADING updates...", "info")
            _report("=" * 50, "info")

            downloader = session.CreateUpdateDownloader()
            downloader.Updates = updates_to_install

            for i in range(match_count):
                _report(f"  Downloading {i+1}/{match_count}: {matched_titles[i]}...")

            download_result = downloader.Download()
            dl_code = download_result.ResultCode
            _report(
                f"Download result: {_RESULT_CODES.get(dl_code, 'Unknown')} (code {dl_code})",
                "success" if dl_code == 2 else "warning",
            )

            for i in range(match_count):
                item_result = download_result.GetUpdateResult(i).ResultCode
                status = _RESULT_CODES.get(item_result, "Unknown")
                lvl = "success" if item_result == 2 else "error"
                _report(f"  {matched_titles[i]}: {status}", lvl)

            # Release downloader
            download_result = None
            downloader = None
            gc.collect()

            if dl_code not in (2, 3):
                _report("❌ Download failed — aborting install.", "error")
                return {"installed": 0, "failed": match_count, "reboot_required": False, "details": []}

            # ----------------------------------------------------------
            #  4. Install
            # ----------------------------------------------------------
            _report("=" * 50, "info")
            _report("⚙️ INSTALLING updates...", "info")
            _report("=" * 50, "info")

            installer = session.CreateUpdateInstaller()
            installer.Updates = updates_to_install

            for i in range(match_count):
                _report(f"  Installing {i+1}/{match_count}: {matched_titles[i]}...")

            install_result = installer.Install()
            inst_code = install_result.ResultCode
            _report(
                f"Install result: {_RESULT_CODES.get(inst_code, 'Unknown')} (code {inst_code})",
                "success" if inst_code == 2 else "warning",
            )

            # ----------------------------------------------------------
            #  5. Collect per-update results
            # ----------------------------------------------------------
            installed = 0
            failed = 0
            details = []

            for i in range(match_count):
                item_code = install_result.GetUpdateResult(i).ResultCode
                status = _RESULT_CODES.get(item_code, "Unknown")
                success = item_code in (2, 3)

                if success:
                    installed += 1
                    lvl = "success"
                else:
                    failed += 1
                    lvl = "error"

                _report(f"  {matched_titles[i]}: {status}", lvl)
                details.append({
                    "title": matched_titles[i],
                    "result_code": item_code,
                    "status": status,
                    "success": success,
                })

            reboot_required = bool(install_result.RebootRequired)
            if reboot_required:
                _report("🔄 A system reboot is required to complete the install.", "warning")

            _report(
                f"✅ Install complete — {installed} succeeded, {failed} failed.",
                "success" if failed == 0 else "warning",
            )

            result = {
                "installed": installed,
                "failed": failed,
                "reboot_required": reboot_required,
                "details": details,
            }

            # ----------------------------------------------------------
            #  6. Explicit COM cleanup BEFORE CoUninitialize
            # ----------------------------------------------------------
            _report("Cleaning up COM objects...", "info")
            install_result = None
            installer = None
            updates_to_install = None
            session = None
            gc.collect()

            _report("Releasing COM interface.", "info")
            pythoncom.CoUninitialize()

            return result

        except Exception as exc:
            _report(f"❌ Install error: {exc}", "error")
            logger.exception("Install failed")

            # Cleanup on error
            install_result = None
            download_result = None
            installer = None
            downloader = None
            updates_to_install = None
            search_result = None
            searcher = None
            session = None
            gc.collect()

            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

            raise