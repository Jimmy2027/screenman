"""Console script for screenman."""

import sys
from importlib.metadata import version

import click
from loguru import logger

from screenman.screen import apply_layout, apply_mirror, connected_screens, determine_layout


def configure_logger(log_level="INFO", log_file=None):
    logger.remove()  # Remove default logger
    logger.add(sys.stderr, level=log_level)  # Add stderr logging with chosen level

    if log_file:
        logger.add(log_file, rotation="1 MB", retention="10 days", level=log_level)


@click.command()
@click.version_option(version=version("screenman"), prog_name="screenman")
@click.option(
    "--log-level",
    default="INFO",
    help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option("--log-file", default=None, help="Set the log file path.")
@click.option(
    "--print-info",
    is_flag=True,
    help="Print the connected screens and the corresponding layout."
    "If no layout is defined, the default layout 'auto' is used.",
)
@click.option(
    "--rescan-pci",
    is_flag=True,
    help="Rescan PCI bus before applying layout. Useful for dock/display detection issues after resume.",
)
@click.option(
    "--mirror",
    is_flag=True,
    help="Mirror the internal (eDP) display to the external display.",
)
@click.option(
    "--mirror-off",
    is_flag=True,
    help="Revert mirroring and apply the normal layout.",
)
def main(log_level, log_file, print_info, rescan_pci, mirror, mirror_off):
    """Console script for screenman."""
    configure_logger(log_level, log_file)

    if mirror and mirror_off:
        raise click.UsageError("Cannot use --mirror and --mirror-off together.")

    screens = connected_screens()

    if mirror:
        apply_mirror(screens)
        return

    if mirror_off:
        logger.info("Reverting mirror mode, applying normal layout.")

    layout_name = determine_layout(screens)
    if print_info:
        for s in screens:
            print(s)
        print(f"Layout: {layout_name}")
        return

    if layout_name:
        logger.info(f"Applying layout: {layout_name}")
        apply_layout(screens, layout_name, do_rescan_pci=rescan_pci)
    else:
        logger.info("No matching layout found.")


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
