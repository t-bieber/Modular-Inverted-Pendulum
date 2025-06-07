import sys
import time
import multiprocessing
from backends.sim_backend import start_simulation_backend
from gui.main_window import run_gui

def main():
    multiprocessing.set_start_method("spawn")  # Required on Windows/macOS

    # Launch GUI and pass shared_vars
    run_gui()

if __name__ == "__main__":
    main()