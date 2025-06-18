# gui.py
# Entry point used when launching the GUI directly.
import sys

import qtstylish
from PyQt5.QtWidgets import QApplication
from utils.settings_manager import SettingsManager

# Import from the current package so this module works whether executed as part
# of the package or as a script. Absolute imports would fail when invoked via
# ``control/python_pc/main.py`` as they would not resolve correctly.
from .main_window import MainWindow


def run_gui():
    """Create the QApplication and show the main window."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(qtstylish.dark())
    settings = SettingsManager()
    window = MainWindow(settings)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    # Allow ``python gui.py`` for quick testing
    run_gui()
