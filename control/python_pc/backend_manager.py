import multiprocessing
import logging
import time

from backends.serial_backend import hardwareUpdateLoop
from backends.linear_sim_backend import simulated_physics_loop
from backends.nonlinear_sim_backend import nonlinear_physics_loop
from utils.shared_vars import create_shared_vars

logger = logging.getLogger(__name__)

class BackendManager:
    def __init__(self):
        self.shared_vars = create_shared_vars()
        self.hardware_process = None
        self.sim_process = None

    def start_hardware(self):
        if self.hardware_process is not None and self.hardware_process.is_alive():
            logger.warning("Hardware already running.")
            return
        self.hardware_process = multiprocessing.Process(
            target=hardwareUpdateLoop, args=(self.shared_vars["position"], self.shared_vars["angle"],
                                                  self.shared_vars["control_signal"])
        )
        self.hardware_process.start()
        logger.info("Hardware backend started.")
        return self.shared_vars

    def stop_hardware(self):
        if self.hardware_process:
            self.hardware_process.terminate()
            self.hardware_process.join()
            self.hardware_process = None
            logger.info("Hardware backend stopped.")

    def start_linear_sim(self, sim_vars: dict):
        if self.sim_process is not None and self.sim_process.is_alive():
            logger.warning("Simulation already running.")
            return
        self.sim_process = multiprocessing.Process(
            target=nonlinear_physics_loop, args=(self.shared_vars["position"], self.shared_vars["angle"],
                                                  self.shared_vars["control_signal"], sim_vars)
        )
        self.sim_process.start()
        logger.info("Linear simulation started.")

    def stop_linear_sim(self):
        if self.sim_process:
            self.sim_process.terminate()
            self.sim_process.join()
            self.sim_process = None
            logger.info("Linear simulation stopped.")

    def start_nonlinear_sim(self, sim_vars: dict):
        if self.sim_process is not None and self.sim_process.is_alive():
            logger.warning("Simulation already running.")
            return
        self.sim_process = multiprocessing.Process(
            target=simulated_physics_loop, args=(self.shared_vars["position"], self.shared_vars["angle"],
                                                  self.shared_vars["control_signal"], sim_vars)
        )
        self.sim_process.start()
        logger.info("Linear simulation started.")

    def stop_nonlinear_sim(self):
        if self.sim_process:
            self.sim_process.terminate()
            self.sim_process.join()
            self.sim_process = None
            logger.info("Linear simulation stopped.")
