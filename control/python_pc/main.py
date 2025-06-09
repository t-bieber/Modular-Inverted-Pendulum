"""
main.py

Run this file to start the application. This will run the GUI, which contains the rest of the application logic.
This project is maintained on GitHub: https://github.com/t-bieber/Modular-Inverted-Pendulum

Author: Tom Bieber
"""

if __name__ == "__main__":
    
    run_gui()

import multiprocessing
import sys
from PyQt5.QtWidgets import QApplication
from gui import run_gui

def main():
    multiprocessing.set_start_method("spawn")  # Good practice on Windows/macOS
    app = QApplication(sys.argv)
    window = run_gui()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()