"""Top-level package for screenman."""

__author__ = """Hendrik Klug"""
__email__ = "hendrik.klug@gmail.com"
from importlib.metadata import version as _version

__version__ = _version("screenman")

from screenman.config import Config

# Load the configuration
toml_config = Config.load_from_toml()
