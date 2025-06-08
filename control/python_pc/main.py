"""
main.py

Run this file to start the application. This will run the GUI, which contains the rest of the application logic.
This project is maintained on GitHub: https://github.com/t-bieber/Modular-Inverted-Pendulum

Author: Tom Bieber
"""

if __name__ == "__main__":
    import multiprocessing
    from gui.main_window import run_gui
    multiprocessing.set_start_method("spawn")  # Good practice on Windows/macOS
    run_gui()
