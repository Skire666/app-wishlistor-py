"""Small OS-interaction helpers (file explorer, default browser)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import os
import platform
import subprocess
import webbrowser
from enum import Enum
from pathlib import Path

from wishlistor.shared.exceptions.unsupported_operating_system_error import UnsupportedOperatingSystemError


class OperatingSystemEnum(Enum):
    """Enumerates the operating systems detected at runtime."""

    E_UNSET = "UNSET"
    E_WINDOWS = "WINDOWS"
    E_LINUX = "LINUX"
    E_MACOS = "MACOS"
    E_UNKNOWN = "UNKNOWN"


def detect_os() -> OperatingSystemEnum:
    """Identify the current host operating system from platform.system().

    Returns:
        The matching OperatingSystemEnum variant, or E_UNKNOWN when unrecognised.
    """
    # Detect at runtime, not at import time, to avoid caching a stale platform string.
    os_name = platform.system()
    if not os_name:
        return OperatingSystemEnum.E_UNSET
    if os_name == "Windows":
        return OperatingSystemEnum.E_WINDOWS
    if os_name == "Linux":
        return OperatingSystemEnum.E_LINUX
    if os_name == "Darwin":
        return OperatingSystemEnum.E_MACOS
    return OperatingSystemEnum.E_UNKNOWN


def open_folder(path: str | Path) -> None:
    """Open *path* (or its parent when it is a file) in the OS file explorer.

    Args:
        path: Directory or file path to reveal.

    Raises:
        UnsupportedOperatingSystemError: When the host OS is not supported.
    """
    target = Path(path)
    if not target.is_dir():
        target = target.parent

    enum_os = detect_os()
    if enum_os == OperatingSystemEnum.E_WINDOWS:
        os.startfile(target)
    elif enum_os == OperatingSystemEnum.E_MACOS:
        subprocess.Popen(["open", str(target)])
    elif enum_os == OperatingSystemEnum.E_LINUX:
        subprocess.Popen(["xdg-open", str(target)])
    else:
        raise UnsupportedOperatingSystemError(enum_os.value)


def open_url_in_browser(url: str) -> None:
    """Open *url* in the default web browser.

    Args:
        url: The URL to open.
    """
    webbrowser.open(url)


# EOF
