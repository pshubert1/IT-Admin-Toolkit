"""
Handles Windows feature updates (version upgrades) by downloading
and running the official Microsoft Windows Update Assistant.

This is separate from the WUA COM API which only handles quality updates.
"""

import gc
import os
import logging
import platform
import winreg
import urllib.request
import subprocess
import shutil
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Microsoft's official Update Assistant download links (always point to latest)
_ASSISTANT_URLS = {
    "11": "https://go.microsoft.com/fwlink/?linkid=2171764",
    "10": "https://go.microsoft.com/fwlink/?LinkID=799445",
}

_DOWNLOAD_DIR = os.path.join(os.environ.get("TEMP", r"C:\temp"), "WinUpdateAssistant")
_ASSISTANT_EXE_NAME = "Windows_Update_Assistant.exe"


class FeatureUpdateService:
    """Detects the current Windows version and runs the Update Assistant."""

    # =================================================================
    #  Version detection
    # =================================================================

    @staticmethod
    def get_current_version_info() -> dict:
        """
        Read the current Windows version from the registry.

        Returns
        -------
        dict with keys:
            product_name    – e.g. "Windows 11 Pro"
            display_version – e.g. "24H2"
            build_number    – e.g. "26100"
            ubr             – Update Build Revision, e.g. "8246"
            full_build      – e.g. "26100.8246"
            major_version   – "10" or "11"
        """
        info = {}
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
            )

            def _read(name, default="Unknown"):
                try:
                    return str(winreg.QueryValueEx(key, name)[0])
                except FileNotFoundError:
                    return default

            info["product_name"] = _read("ProductName")
            info["display_version"] = _read("DisplayVersion")       # 24H2
            info["build_number"] = _read("CurrentBuildNumber")       # 26100
            info["ubr"] = _read("UBR", "0")                         # 8246
            info["full_build"] = f"{info['build_number']}.{info['ubr']}"
            info["edition_id"] = _read("EditionID")                  # Professional

            # Determine major version (10 or 11)
            build_int = int(info["build_number"])
            if build_int >= 22000:
                info["major_version"] = "11"
            else:
                info["major_version"] = "10"

            winreg.CloseKey(key)

        except Exception as exc:
            logger.exception("Failed to read Windows version from registry")
            info["error"] = str(exc)
            info["major_version"] = "11"  # default fallback

        return info

    # =================================================================
    #  Download the Update Assistant
    # =================================================================

    @staticmethod
    def download_update_assistant(
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ) -> str:
        """
        Download the latest Windows Update Assistant from Microsoft.

        Returns
        -------
        str — full path to the downloaded .exe
        """

        def _report(msg: str, level: str = "step"):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg, level)

        version_info = FeatureUpdateService.get_current_version_info()
        major = version_info.get("major_version", "11")
        url = _ASSISTANT_URLS.get(major, _ASSISTANT_URLS["11"])

        _report(f"Detected Windows {major} ({version_info.get('display_version', '?')})")
        _report(f"Download URL: {url}")

        # Create download directory
        os.makedirs(_DOWNLOAD_DIR, exist_ok=True)
        exe_path = os.path.join(_DOWNLOAD_DIR, _ASSISTANT_EXE_NAME)

        # Remove old copy if it exists
        if os.path.isfile(exe_path):
            os.remove(exe_path)
            _report("Removed previous copy of Update Assistant.")

        _report("📥 Downloading Windows Update Assistant...", "info")
        _report("   This is ~10 MB — please wait...", "info")

        try:
            # Download with progress
            def _reporthook(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    pct = min(100, int(downloaded * 100 / total_size))
                    if pct % 25 == 0 and pct > 0:
                        _report(f"   Downloaded {pct}%...", "step")

            urllib.request.urlretrieve(url, exe_path, reporthook=_reporthook)

        except Exception as exc:
            _report(f"❌ Download failed: {exc}", "error")
            raise

        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        _report(f"✅ Downloaded successfully ({size_mb:.1f} MB)", "success")
        _report(f"   Saved to: {exe_path}", "info")

        return exe_path

    # =================================================================
    #  Run the Update Assistant
    # =================================================================

    @staticmethod
    def run_feature_update(
        progress_callback: Optional[Callable[[str, str], None]] = None,
        quiet: bool = True,
    ) -> dict:
        """
        Download and run the Windows Update Assistant to perform
        a feature update to the latest Windows version.

        Parameters
        ----------
        progress_callback : callable, optional
        quiet : bool
            If True, run with silent/auto-accept flags.

        Returns
        -------
        dict  {"success": bool, "exe_path": str, "version_info": dict, ...}
        """

        def _report(msg: str, level: str = "step"):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg, level)

        _report("=" * 55, "info")
        _report("  WINDOWS FEATURE UPDATE", "warning")
        _report("=" * 55, "info")

        # 1. Get current version
        version_info = FeatureUpdateService.get_current_version_info()
        _report(f"Current version: {version_info.get('product_name', '?')}", "info")
        _report(f"  Release:  {version_info.get('display_version', '?')}", "info")
        _report(f"  Build:    {version_info.get('full_build', '?')}", "info")
        _report(f"  Edition:  {version_info.get('edition_id', '?')}", "info")

        # 2. Download the assistant
        exe_path = FeatureUpdateService.download_update_assistant(progress_callback)

        # 3. Launch the assistant
        _report("", "info")
        _report("🚀 Launching Windows Update Assistant...", "warning")

        cmd = [exe_path]
        if quiet:
            cmd.extend([
                "/quietinstall",
                "/skipeula",
                "/auto",
                "upgrade",
            ])
            _report("   Mode: Quiet install (auto-accept EULA, auto upgrade)", "info")
        else:
            _report("   Mode: Interactive (the assistant window will open)", "info")

        _report(f"   Command: {' '.join(cmd)}", "info")

        try:
            # Use Popen so it runs independently — the assistant manages
            # its own download of the actual Windows image (~4-5 GB),
            # installation, and reboot.
            process = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )

            _report("", "info")
            _report("✅ Update Assistant launched successfully!", "success")
            _report("", "info")
            _report("⚠️  IMPORTANT — What happens next:", "warning")
            _report("   1. The assistant will download the latest Windows version (~4-5 GB)", "info")
            _report("   2. It will prepare the update (this takes 30-60+ minutes)", "info")
            _report("   3. Your PC will reboot AUTOMATICALLY to finish the install", "info")
            _report("   4. The install continues after reboot (may reboot 2-3 times)", "info")
            _report("", "info")
            _report("   ⏳ Do NOT shut down your PC during this process.", "warning")
            _report("   📋 You can monitor progress in Windows Update settings.", "info")

            return {
                "success": True,
                "exe_path": exe_path,
                "pid": process.pid,
                "version_info": version_info,
            }

        except Exception as exc:
            _report(f"❌ Failed to launch Update Assistant: {exc}", "error")
            logger.exception("Feature update launch failed")
            return {
                "success": False,
                "error": str(exc),
                "version_info": version_info,
            }

    # =================================================================
    #  Cleanup
    # =================================================================

    @staticmethod
    def cleanup():
        """Remove the downloaded Update Assistant."""
        if os.path.isdir(_DOWNLOAD_DIR):
            shutil.rmtree(_DOWNLOAD_DIR, ignore_errors=True)
            logger.info("Cleaned up: %s", _DOWNLOAD_DIR)