# screenman

A Python tool to manage and configure multi-monitor setups using EDID information, allowing users to apply predefined screen layouts with ease.

## Setup

```terminal
$ screenman --help
Usage: screenman [OPTIONS]

  Console script for screenman.

Options:
  --log-level TEXT  Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR,
                    CRITICAL)
  --log-file TEXT   Set the log file path.
  --print-info      Print the connected screens and the corresponding
                    layout.If no layout is defined, the default layout 'auto'
                    is used.
  --help            Show this message and exit.

```

When wanting to setup a new screen layout, you can use the `--print-info` flag to get the connected screens information. This information can be used to create a new screen layout.

```terminal
$ screenman --print-info
<HDMI-2, UID: DL51145435704, primary: True, modes: 13, conn: True, rot: normal, enabled: True, res: (1920, 1080)>
Layout: auto
```

From that we can create our toml configuration file with the following content:

```toml
# the hierarchy of the configuration file is as follows:
# layouts.<layout_name>.<screen_uid>
[layouts.single_baetylus.DL51145435704]
primary = true
mode = [1920, 1080]
position = [0, 0]
rotation = "normal"
```

A more advanced screenman.toml configuration file can be found in the [examples](examples) directory.

## Usage
I have `screenman --log-file ~/.local/logs/screenman.log --log-level DEBUG` mapped to a keybinding.

If you can't install `screenman` with your package manager, you can also run it with `uv`:
    
```bash
uv tool run screenman --help
```

## Installation

### Dependencies
Install [edid-decode](https://git.linuxtv.org/edid-decode.git/).

### pip release version

```bash
pip install screenman
```

### pip live version

```bash
pip install git+https://github.com/Jimmy2027/screenman.git
```

### portage

`screenman` is available via [Jimmy's overlay](https://github.com/Jimmy2027/overlay/blob/main/dev-python/screenman/screenman-9999.ebuild).
Either enable the repo or copy the ebuild to your local overlay.

Then run:

```bash
emerge -av screenman
```