"""
main.py

Entry point for the desktop application. This simply delegates to the GUI
launcher defined in ``gui.gui``. The extra ``multiprocessing`` start method
setup is required when running on Windows/macOS.

This project is maintained on GitHub: https://github.com/t-bieber/Modular-Inverted-Pendulum

Author: Tom Bieber
"""

import logging
import multiprocessing

# ``run_gui`` lives in the ``gui`` module within the ``gui`` package. Importing
# it explicitly from ``gui.gui`` avoids relying on package ``__init__`` exports.
from gui.gui import run_gui


def main() -> None:
    """Start the Qt based control GUI."""
    logging.basicConfig(level=logging.INFO)
    # ``spawn`` ensures compatibility on Windows/macOS where ``fork`` is not
    # the default start method. The GUI itself will run in the main process.
    multiprocessing.set_start_method("spawn")
    # Launch the Qt event loop defined in ``gui.gui``
    run_gui()


if __name__ == "__main__":
    # When executed directly ``main()`` launches the application.
    main()
