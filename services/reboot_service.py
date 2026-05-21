"""
Handles system reboot via the Windows API.
"""

import subprocess
import logging

logger = logging.getLogger(__name__)


class RebootService:
    """Provides controlled system reboot."""

    @staticmethod
    def reboot(delay_seconds: int = 10, force: bool = False):
        """
        Schedule a Windows reboot.

        Parameters
        ----------
        delay_seconds : int
            Seconds before the reboot occurs (gives user time to cancel).
        force : bool
            If True, forces running applications to close.
        """
        cmd = ["shutdown", "/r", f"/t", str(delay_seconds)]
        if force:
            cmd.append("/f")
        cmd += ["/c", "Rebooting for Windows Updates (scheduled by Update Checker)"]

        logger.info("Scheduling reboot in %d seconds: %s", delay_seconds, cmd)
        subprocess.Popen(cmd, shell=True)

    @staticmethod
    def cancel_reboot():
        """Cancel a previously scheduled reboot."""
        logger.info("Cancelling scheduled reboot.")
        subprocess.Popen(["shutdown", "/a"], shell=True)