# gui.py
import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
from utils.settings_manager import SettingsManager

def run_gui():
    app = QApplication(sys.argv)
    settings = SettingsManager()
    window = MainWindow(settings)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_gui()
