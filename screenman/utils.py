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


@dataclass
class ScreenSettings:
    resolution: tuple[int, int] = (0, 0)
    is_primary: bool = False
    is_enabled: bool = True
    rotation: Optional[int] = None
    position: Optional[tuple[str, str]] = None
    is_connected: bool = True
    change_table: dict[str, bool] = field(
        default_factory=lambda: {
            "resolution": False,
            "is_primary": False,
            "is_enabled": False,
            "rotation": False,
            "position": False,
        }
    )