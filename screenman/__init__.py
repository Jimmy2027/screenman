"""Top-level package for screenman."""

__author__ = """Hendrik Klug"""
__email__ = "hendrik.klug@gmail.com"
__version__ = "0.1.0"

from screenman.config import Config

# Load the configuration
toml_config = Config.load_from_toml()
