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
from typing import Dict, Any

import qtstylish
from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow
from utils.shared_vars import create_shared_vars
from utils.settings_manager import SettingsManager
from backend_manager import BackendManager

def main() -> None:
    """Start the Qt based control GUI."""
    logging.basicConfig(level=logging.INFO)
    multiprocessing.set_start_method("spawn")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(qtstylish.dark())

    settings_manager = SettingsManager()
    shared_vars: Dict[str, Any] = create_shared_vars()
    backend_manager = BackendManager(shared_vars, settings_manager)

    window = MainWindow(settings_manager, backend_manager, shared_vars)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
