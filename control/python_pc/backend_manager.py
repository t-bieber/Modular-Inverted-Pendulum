"""
backend_manager.py

This file implements the backend manager, which starts either the real hardware backend
(for serial communicationw ith the inverted pendulum hardware) or a simulation backend.
It runs the backend in its own thread and passes the shared vars to it.
"""

import logging
import multiprocessing
from typing import Any, Dict

from backends.serial_backend import hardwareUpdateLoop
from backends.linear_sim_backend import linear_physics_loop
from backends.nonlinear_sim_backend import nonlinear_physics_loop
from utils.settings_manager import SettingsManager


logger = logging.getLogger(__name__)


class BackendManager:
    def __init__(self, shared_vars: Dict[str, Any], settings_manager: SettingsManager):
        self.shared_vars: Dict[str, Any] = shared_vars
        self.settings_manager: SettingsManager = settings_manager
        self.hardware_process = None
        self.hardware_stop_event = None
        self.sim_process = None
        self.sim_stop_event = None

    def start_hardware(self) -> None:
        if self.hardware_process is not None and self.hardware_process.is_alive():
            logger.info("Hardware already running.")
            return

        settings_dict = self.settings_manager.export_for_backend()
        self.hardware_stop_event = multiprocessing.Event()

        self.hardware_process = multiprocessing.Process(
            target=hardwareUpdateLoop, args=(
                                            self.shared_vars,
                                            settings_dict,
                                            self.hardware_stop_event
                                            )
        )
        self.hardware_process.start()
        logger.info("Hardware backend started.")

    def stop_hardware(self) -> None:
        if self.hardware_process:
            if self.hardware_stop_event:
                self.hardware_stop_event.set()
            self.hardware_process.join(timeout=2)

            if self.hardware_process.is_alive():
                logger.warning("Graceful shutdown failed. Forcing termination.")
                self.hardware_process.terminate()
                self.hardware_process.join()

            self.hardware_process = None
            self.hardware_stop_event = None
            logger.info("Hardware backend stopped.")

    def start_linear_sim(self, sim_vars: dict) -> None:
        if self.sim_process is not None and self.sim_process.is_alive():
            logger.warning("Simulation already running.")
            return
        
        self.sim_stop_event = multiprocessing.Event()
        self.sim_process = multiprocessing.Process(
            target=linear_physics_loop,
            args=  (self.shared_vars, sim_vars, self.sim_stop_event)
        )
        self.sim_process.start()
        logger.info("Linear simulation started.")

    def stop_linear_sim(self) -> None:
        if self.sim_process:
            if self.sim_stop_event:
                self.sim_stop_event.set()
            self.sim_process.join(timeout=2)

            if self.sim_process.is_alive():
                logger.warning("Simulation did not shut down cleanly. Terminating.")
                self.sim_process.terminate()
                self.sim_process.join()

            self.sim_process = None
            self.sim_stop_event = None
            logger.info("Linear simulation stopped.")

    def start_nonlinear_sim(self, sim_vars: dict) -> None:
        if self.sim_process is not None and self.sim_process.is_alive():
            logger.warning("Simulation already running.")
            return

        self.sim_stop_event = multiprocessing.Event()

        self.sim_process = multiprocessing.Process(
            target=nonlinear_physics_loop,
            args=(self.shared_vars, sim_vars, self.sim_stop_event),
        )
        self.sim_process.start()
        logger.info("Nonlinear simulation started.")

    def stop_nonlinear_sim(self) -> None:
        if self.sim_process:
            if self.sim_stop_event:
                self.sim_stop_event.set()
            self.sim_process.join(timeout=2)

            if self.sim_process.is_alive():
                logger.warning("Simulation did not shut down cleanly. Terminating.")
                self.sim_process.terminate()
                self.sim_process.join()

            self.sim_process = None
            self.sim_stop_event = None
            logger.info("Nonlinear simulation stopped.")
