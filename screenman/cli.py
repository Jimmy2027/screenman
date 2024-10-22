"""Console script for screenman."""

import sys

import click
from loguru import logger

from screenman.screen import apply_layout, connected_screens, determine_layout


def configure_logger(log_level="INFO", log_file=None):
    logger.remove()  # Remove default logger
    logger.add(sys.stderr, level=log_level)  # Add stderr logging with chosen level

    if log_file:
        logger.add(log_file, rotation="1 MB", retention="10 days", level=log_level)


@click.command()
@click.option(
    "--log-level",
    default="INFO",
    help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option("--log-file", default=None, help="Set the log file path")
@click.option("--print-info", is_flag=True, help="Print the connected screens and exit")
def main(log_level, log_file, print_info):
    """Console script for screenman."""
    configure_logger(log_level, log_file)

    screens = connected_screens()
    layout_name = determine_layout(screens)
    if print_info:
        for s in screens:
            print(s)
        print(f"Layout: {layout_name}")
        return

    if layout_name:
        logger.info(f"Applying layout: {layout_name}")
        apply_layout(screens, layout_name)
    else:
        logger.info("No matching layout found.")


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
