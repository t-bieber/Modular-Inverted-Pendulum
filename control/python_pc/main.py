"""
main.py

Entry point for the desktop application. Starts the Qt GUI and sets up multiprocessing
for cross-platform compatibility.

Project: https://github.com/t-bieber/Modular-Inverted-Pendulum
Author: Tom Bieber
"""

import logging
import multiprocessing
import sys

import qtstylish
from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow
from utils.settings_manager import SettingsManager


def main() -> None:
    """Start the Qt based control GUI."""
    logging.basicConfig(level=logging.INFO)
    multiprocessing.set_start_method("spawn")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(qtstylish.dark())

    settings = SettingsManager()
    window = MainWindow(settings)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
