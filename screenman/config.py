from screenman.utils import ScreenSettings


from platformdirs import site_config_dir, user_config_dir


import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from screenman.utils import str_to_rot


@dataclass
class Config:
    # for some reason, some monitors don't include the serial number in the EDID
    # for those, define some fallback option to which the edid is matched.
    # This will not be a unique identifier, so it will not work if you have multiple monitors of the same model
    fallback_uid: Dict[str, Dict[str, str]] = field(default_factory=dict)
    layouts: Dict[str, Dict[str, ScreenSettings]] = field(default_factory=dict)

    @classmethod
    def load_from_toml(cls) -> "Config":
        config_paths = [
            Path.cwd(),
            Path.home(),
            Path(user_config_dir(roaming=True)),
            Path(user_config_dir("synthara_sdk", roaming=False)),
            Path(site_config_dir()),
        ]
        for path in config_paths:
            path = path / "screenman.toml"
            if path and path.exists():
                try:
                    with open(path, "rb") as f:
                        config_data = tomllib.load(f)
                    fallback_uid = config_data.get("fallback_uid", {})
                    layouts = {
                        layout_name: {
                            screen_name: ScreenSettings(
                                resolution=tuple(screen_data.get("mode", (0, 0))),
                                is_primary=screen_data.get("primary", False),
                                is_enabled=screen_data.get("enabled", True),
                                rotation=str_to_rot(
                                    screen_data.get("rotation", "normal")
                                ),
                                position=(
                                    "--pos",
                                    f"{screen_data['position'][0]}x{screen_data['position'][1]}",
                                )
                                if "position" in screen_data
                                else None,
                            )
                            for screen_name, screen_data in layout_screens.items()
                        }
                        for layout_name, layout_screens in config_data.get(
                            "layouts", {}
                        ).items()
                    }
                    return cls(fallback_uid=fallback_uid, layouts=layouts)
                except Exception as e:
                    print(f"Failed to load configuration file '{path}': {e}")
        # Default configuration if no config file is found
        return cls()