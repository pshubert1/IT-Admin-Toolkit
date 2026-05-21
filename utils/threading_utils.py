"""
Utility for running long-running tasks off the main/GUI thread.
Uses a Queue so the main thread can safely pick up results.
"""

import threading
from typing import Callable, Optional

def run_in_background(
    target: Callable,
    args: tuple = (),
    on_complete: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
    daemon: bool = True,
):
    """
    Run *target* in a background thread.

    Parameters
    ----------
    target : callable       – function to execute
    args : tuple            – positional args for *target*
    on_complete : callable  – called with the return value on success
    on_error : callable     – called with the exception on failure
    daemon : bool           – thread dies with the main thread
    """

    def _wrapper():
        try:
            result = target(*args)
            if on_complete:
                on_complete(result)
        except Exception as exc:
            if on_error:
                on_error(exc)

    thread = threading.Thread(target=_wrapper, daemon=daemon)
    thread.start()
    return thread