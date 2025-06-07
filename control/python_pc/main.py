"""
main.py

Run this file to start the application. This will run the GUI, which contains the rest of the application logic.
This project is maintained on GitHub: https://github.com/t-bieber/Modular-Inverted-Pendulum

Author: Tom Bieber
"""

import multiprocessing
from gui.main_window import run_gui

def main():
    multiprocessing.set_start_method("spawn")  # Required on Windows/macOS

    # Launch GUI and pass shared_vars
    run_gui()

if __name__ == "__main__":
    main()