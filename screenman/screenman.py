"""Main module."""

import binascii
import re
import subprocess as sb
from dataclasses import dataclass, field
from typing import ClassVar, Optional

# for some reason, some monitors don't include the serial number in the EDID
# for those, define some fallback option to which the edid is matched.
# This will not be a unique identifier, so it will not work if you have multiple monitors of the same model
FALLBACK_UID = {"frametux": {"Manufacturer": "BOE", "Model": "3018"}}

# Define layouts
# Mapping of the layout name to the EDID serials of the screens, to the settings
LAYOUTS = {
    "office": {
        "internal": {
            "enabled": True,
            "primary": True,
            "mode": (2256, 1504),
            "position": (0, 0),
            "rotation": "normal",
        },
        "office_external": {
            "enabled": True,
            "primary": False,
            "mode": (3440, 1440),
            "position": (2256, 0),
            "rotation": "normal",
        },
    },
    "single_frametux": {
        "frametux": {
            "enabled": True,
            "primary": True,
            "mode": (2256, 1504),
            "position": (0, 0),
            "rotation": "normal",
        },
    },
    "single_baetylus": {
        "DL51145435704": {
            "enabled": True,
            "primary": True,
            "mode": (1920, 1080),
            "position": (0, 0),
            "rotation": "normal",
        },
    },
}


@dataclass
class Mode:
    width: int
    height: int
    freq: float
    current: bool
    preferred: bool

    def resolution(self):
        return self.width, self.height

    def __str__(self):
        return f"<{self.width}x{self.height}, {self.freq}, curr: {self.current}, pref: {self.preferred}>"

    def cmd_str(self):
        return f"{self.width}x{self.height}"


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


@dataclass
class Edid:
    serial: Optional[str] = None
    name: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    fallback_uid: Optional[str] = None

    SERIAL_REGEX: ClassVar[re.Pattern] = re.compile(r"Serial Number: (.+)")
    NAME_REGEX: ClassVar[re.Pattern] = re.compile(r"Monitor name: (.+)")
    MANUFACTURER_REGEX: ClassVar[re.Pattern] = re.compile(r"Manufacturer: (.+)")
    MODEL_NUMBER_REGEX: ClassVar[re.Pattern] = re.compile(r"Model: (.+)")

    @classmethod
    def from_edid_hex(cls, edid_hex: str) -> "Edid":
        edid_bytes = binascii.unhexlify(edid_hex)
        if len(edid_bytes) < 128:
            return Edid()

        # Call edid-decode utility to parse the EDID bytes
        try:
            proc = sb.run(
                ["edid-decode"],
                input=edid_hex,
                capture_output=True,
                text=True,
                check=True,
            )
            edid_output = proc.stdout
        except FileNotFoundError:
            print("Error: edid-decode utility is not installed.")
            return Edid()
        except sb.CalledProcessError as e:
            print(f"Error: Failed to run edid-decode: {e}")
            return Edid()

        edid = Edid()
        # Extract useful information from the edid-decode output
        for line in edid_output.splitlines():
            if serial_match := edid.SERIAL_REGEX.search(line):
                edid.serial = serial_match.group(1).strip()
            if name_match := edid.NAME_REGEX.search(line):
                edid.name = name_match.group(1).strip()
            if manufacturer_match := edid.MANUFACTURER_REGEX.search(line):
                edid.manufacturer = manufacturer_match.group(1).strip()
            if model_number_match := edid.MODEL_NUMBER_REGEX.search(line):
                edid.model_number = model_number_match.group(1).strip()

        if not edid.serial:
            edid.fallback_uid = edid.get_fallback_uid()
        return edid

    def get_fallback_uid(self) -> Optional[str]:
        for uid, fallback in FALLBACK_UID.items():
            if (
                fallback["Manufacturer"] == self.manufacturer
                and fallback["Model"] == self.model_number
            ):
                return uid
        return None


class Screen:
    def __init__(self, name, primary, rot, modes, edid_hex):
        self.__name = name
        self.__set = ScreenSettings()
        self.uid = None

        if edid_hex:
            edid = Edid.from_edid_hex(edid_hex)
            self.uid = edid.serial or edid.fallback_uid

        self.curr_mode = (
            next((item for item in modes if item.current), None) if modes else None
        )
        self.supported_modes = modes
        self._initialize_settings(primary, rot)

    def _initialize_settings(self, primary, rot):
        self.__set.rotation = rot
        self.__set.is_primary = primary
        self.__set.is_enabled = bool(
            [mode for mode in self.supported_modes if mode.current]
        )
        self.__set.is_connected = bool(self.supported_modes)
        if self.curr_mode:
            self.__set.resolution = self.curr_mode.resolution()

    @property
    def name(self):
        return self.__name

    @property
    def is_connected(self):
        return self.__set.is_connected

    @property
    def is_enabled(self):
        return self.__set.is_enabled

    @is_enabled.setter
    def is_enabled(self, enable):
        if enable != self.__set.is_enabled:
            self.__set.is_enabled = enable
            self.__set.change_table["is_enabled"] = True

    @property
    def is_primary(self):
        return self.__set.is_primary

    @is_primary.setter
    def is_primary(self, is_primary):
        if is_primary != self.__set.is_primary:
            self.__set.is_primary = is_primary
            self.__set.change_table["is_primary"] = True

    @property
    def resolution(self):
        return self.__set.resolution

    @resolution.setter
    def resolution(self, newres):
        if not self.is_enabled and not self.__set.change_table["is_enabled"]:
            raise ValueError("The Screen is off")
        if newres != self.__set.resolution:
            self.check_resolution(newres)
            self.__set.resolution = newres
            self.__set.change_table["resolution"] = True

    @property
    def rotation(self):
        return self.__set.rotation

    @rotation.setter
    def rotation(self, direction):
        if direction != self.__set.rotation:
            self.__set.rotation = direction
            self.__set.change_table["rotation"] = True

    @property
    def position(self):
        return self.__set.position

    @position.setter
    def position(self, args):
        if args != self.__set.position:
            self.__set.position = args
            self.__set.change_table["position"] = True

    def available_resolutions(self):
        return [(r.width, r.height) for r in self.supported_modes]

    def check_resolution(self, newres):
        if newres not in self.available_resolutions():
            raise ValueError("Requested resolution is not supported", newres)

    def build_cmd(self):
        if any(self.__set.change_table.values()):
            if not self.name:
                raise ValueError("Cannot apply settings without screen name", self.name)
            cmd = ["xrandr", "--output", self.name]

            if self.is_enabled:
                cmd.append("--auto")
                self._add_resolution(cmd)
                self._add_primary(cmd)
                self._add_rotation(cmd)
                self._add_position(cmd)
            else:
                cmd.append("--off")

            return cmd
        return None

    def _add_resolution(self, cmd):
        if self.__set.change_table["resolution"]:
            cmd.extend(
                ["--mode", f"{self.__set.resolution[0]}x{self.__set.resolution[1]}"]
            )

    def _add_primary(self, cmd):
        if self.__set.change_table["is_primary"]:
            cmd.append("--primary")

    def _add_rotation(self, cmd):
        if self.__set.change_table["rotation"]:
            rot = rot_to_str(self.__set.rotation)
            if not rot:
                raise ValueError("Invalid rotation value", rot, self.__set.rotation)
            cmd.extend(["--rotate", rot])

    def _add_position(self, cmd):
        if self.__set.change_table["position"]:
            rel, pos = self.__set.position
            cmd.extend([rel, pos])

    def apply_settings(self):
        cmd = self.build_cmd()
        if cmd:
            exec_cmd(cmd)
            self.__set.change_table = {key: False for key in self.__set.change_table}

    def __str__(self):
        return (
            f"<{self.name}, UID: {self.uid}, primary: {self.is_primary}, modes: {len(self.supported_modes)},"
            f"conn: {self.is_connected}, rot: {rot_to_str(self.rotation)}, enabled: {self.is_enabled}>"
        )

    __repr__ = __str__


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


def create_screen(name_str, modes, edid):
    sc_name = name_str.split()[0]
    rot = str_to_rot(name_str.split()[3]) if len(name_str.split()) > 2 else None
    return Screen(sc_name, "primary" in name_str, rot, modes, edid)


def parse_xrandr(lines):
    rx_mode = re.compile(r"^\s+(\d+)x(\d+)\s+((?:\d+\.)?\d+)([* ]?)([+ ]?)")
    rx_conn = re.compile(r"\bconnected\b")
    rx_disconn = re.compile(r"\bdisconnected\b")
    rx_edid_start = re.compile(r"\s+EDID:")
    rx_edid_data = re.compile(r"\s+([0-9a-fA-F]{32})")

    sc_name_line = None
    edid = ""
    parsing_edid = False
    screens = []
    modes = []

    for line in lines:
        if re.search(rx_conn, line) or re.search(rx_disconn, line):
            if sc_name_line:
                newscreen = create_screen(sc_name_line, modes, edid)
                screens.append(newscreen)
                modes = []
                edid = ""
                parsing_edid = False
            sc_name_line = line
        elif re.search(rx_edid_start, line):
            parsing_edid = True
        elif parsing_edid:
            match = re.match(rx_edid_data, line)
            if match:
                edid += match.group(1)
            else:
                parsing_edid = False
        else:
            match = re.search(rx_mode, line)
            if match:
                width, height = int(match.group(1)), int(match.group(2))
                freq = float(match.group(3))
                current = match.group(4).strip() == "*"
                preferred = match.group(5).strip() == "+"
                modes.append(Mode(width, height, freq, current, preferred))

    if sc_name_line:
        newscreen = create_screen(sc_name_line, modes, edid)
        screens.append(newscreen)

    return screens


def connected_screens():
    return [s for s in parse_xrandr(exec_cmd(["xrandr", "--props"])) if s.is_connected]


def determine_layout(screens):
    for layout_name, layout in LAYOUTS.items():
        if all(screen.uid in layout for screen in screens):
            return layout_name
    return None


def apply_layout(screens, layout_name):
    layout = LAYOUTS.get(layout_name, {})
    for screen in screens:
        settings = layout.get(screen.uid)
        if settings:
            screen.is_enabled = settings.get("enabled", False)
            screen.is_primary = settings.get("primary", False)
            if "mode" in settings:
                screen.resolution = settings["mode"]
            if "position" in settings:
                screen.position = (
                    "--pos",
                    f"{settings['position'][0]}x{settings['position'][1]}",
                )
            if "rotation" in settings:
                screen.rotation = str_to_rot(settings["rotation"])
        else:
            screen.is_enabled = False
        screen.apply_settings()


if __name__ == "__main__":
    screens = connected_screens()
    for s in screens:
        print(s)
    layout_name = determine_layout(screens)
    if layout_name:
        print(f"Applying layout: {layout_name}")
        apply_layout(screens, layout_name)
    else:
        print("No matching layout found.")
