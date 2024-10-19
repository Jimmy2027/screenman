"""Console script for screenman."""

import sys

import click

from screenman.screenman import apply_layout, connected_screens, determine_layout


@click.command()
def main(args=None):
    """Console script for screenman."""
    screens = connected_screens()
    for s in screens:
        print(s)
    layout_name = determine_layout(screens)
    if layout_name:
        print(f"Applying layout: {layout_name}")
        apply_layout(screens, layout_name)
    else:
        print("No matching layout found.")


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
