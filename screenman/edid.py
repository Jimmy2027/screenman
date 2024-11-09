import binascii
import re
import subprocess as sb
from dataclasses import dataclass
from typing import ClassVar, Optional

from loguru import logger

from screenman import toml_config

FALLBACK_UID = toml_config.fallback_uid


@dataclass
class Edid:
    """
    Represents the Extended Display Identification Data (EDID) of a monitor.
    Needs the edid-decode utility to be installed:
    https://git.linuxtv.org/edid-decode.git/

    Attributes:
        serial (Optional[str]): The serial number of the monitor.
        name (Optional[str]): The name of the monitor.
        manufacturer (Optional[str]): The manufacturer of the monitor.
        model_number (Optional[str]): The model number of the monitor.
        fallback_uid (Optional[str]): A fallback unique identifier for the monitor.

    Class Attributes:
        SERIAL_REGEX (ClassVar[re.Pattern]): Regex pattern to extract the serial number from EDID data.
        NAME_REGEX (ClassVar[re.Pattern]): Regex pattern to extract the name from EDID data.
        MANUFACTURER_REGEX (ClassVar[re.Pattern]): Regex pattern to extract the manufacturer from EDID data.
        MODEL_NUMBER_REGEX (ClassVar[re.Pattern]): Regex pattern to extract the model number from EDID data.

    Methods:
        from_edid_hex(cls, edid_hex: str) -> "Edid":
            Parses EDID data from a hexadecimal string and returns an Edid instance.
        get_fallback_uid() -> Optional[str]:
            Returns a fallback unique identifier based on the manufacturer and model number.
    """

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
            logger.error("edid-decode utility is not installed.")
            return Edid()
        except sb.CalledProcessError as e:
            logger.error(f"Failed to run edid-decode: {e}")
            return Edid()

        edid = Edid()
        # Extract useful information from the edid-decode output
        for line in edid_output.splitlines():
            if serial_match := edid.SERIAL_REGEX.search(line):
                edid.serial = serial_match.group(1).strip().replace("'", "")
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
