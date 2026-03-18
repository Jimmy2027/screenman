from dataclasses import dataclass, field
import subprocess as sb
from typing import Optional


class RotateDirection:
    Normal, Left, Inverted, Right = range(1, 5)
    valtoname = {Normal: "normal", Left: "left", Inverted: "inverted", Right: "right"}
    nametoval = {v: k for k, v in valtoname.items()}


def rot_to_str(rot):
    return RotateDirection.valtoname.get(rot, None)


def str_to_rot(s):
    return RotateDirection.nametoval.get(s, RotateDirection.Normal)


def exec_cmd(cmd):
    s = sb.check_output(cmd, stderr=sb.STDOUT)
    return s.decode().split("\n")


def rescan_pci():
    """
    Rescan PCI bus to detect dock/display hardware.

    Returns:
        bool: True if rescan succeeded, False otherwise.
    """
    try:
        sb.run(
            ["sudo", "tee", "/sys/bus/pci/rescan"],
            input=b"1",
            check=True,
            stdout=sb.DEVNULL,
            stderr=sb.DEVNULL,
            timeout=5,
        )
        return True
    except (sb.CalledProcessError, PermissionError, FileNotFoundError, sb.TimeoutExpired):
        return False


@dataclass
class ScreenSettings:
    resolution: tuple[int, int] = (0, 0)
    is_primary: bool = False
    is_enabled: bool = True
    rotation: Optional[int] = None
    position: Optional[tuple[str, str]] = None
    is_connected: bool = True
    scale: Optional[tuple[float, float]] = None
    same_as: Optional[str] = None
    change_table: dict[str, bool] = field(
        default_factory=lambda: {
            "resolution": False,
            "is_primary": False,
            "is_enabled": False,
            "rotation": False,
            "position": False,
            "scale": False,
            "same_as": False,
        }
    )