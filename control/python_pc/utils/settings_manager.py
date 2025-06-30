import json
import os


class SettingsManager: #TODO: decide whether to use @property on all getters
    DEFAULT_SETTINGS = {
        "sim_variables": {
            "mass": 0.2,
            "length": 0.5,
            "damping": 0.01,
            "friction": 0.01,
        },
        "hardware_constants": {
            "serial_port": "COM5",
            "serial_baudrate": 115200,
            "max_angle_deg": 15,
            "max_xpos_mm": 220,
        },
        "visible_plots": ["Cart Position", "Pendulum Angle"],
        "plot_order": ["Cart Position", "Pendulum Angle"],
        "last_controller": "pid_controller",
        "controller_params": {},
    }

    def __init__(self, filename="settings.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(base_dir, filename)
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARNING] Failed to load settings: {e}")
        return self.DEFAULT_SETTINGS.copy()

    def save_settings(self):
        try:
            with open(self.path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"[ERROR] Failed to save settings: {e}")

    # --- Simulation Variables ---
    def get_sim_variables(self):
        return self.settings.get(
            "sim_variables", self.DEFAULT_SETTINGS["sim_variables"]
        )

    def set_sim_variable(self, key, value):
        if key not in self.DEFAULT_SETTINGS["sim_variables"]:
            print(f"[WARNING] Unknown simulation variable: {key}")
            return
        expected_type = type(self.DEFAULT_SETTINGS["sim_variables"][key])
        try:
            self.settings.setdefault("sim_variables", {})[key] = expected_type(value)
        except ValueError:
            print(f"[ERROR] Invalid value for {key}: expected {expected_type.__name__}")

    def update_sim_variables(self, new_values):
        for key, value in new_values.items():
            self.set_sim_variable(key, value)

    # --- Hardware Constants ---
    def get_hardware_constant(self, key):
        return self.settings.get("hardware_constants", {}).get(
            key, self.DEFAULT_SETTINGS["hardware_constants"].get(key)
        )

    def set_hardware_constant(self, key, value):
        if key not in self.DEFAULT_SETTINGS["hardware_constants"]:
            print(f"[WARNING] Unknown hardware constant: {key}")
            return
        expected_type = type(self.DEFAULT_SETTINGS["hardware_constants"][key])
        try:
            self.settings.setdefault("hardware_constants", {})[key] = expected_type(value)
        except ValueError:
            print(f"[ERROR] Invalid value for {key}: expected {expected_type.__name__}")

    # --- Direct accessors for old config.py variables ---
    
    def get_serial_port(self) -> str:
        return self.get_hardware_constant("serial_port")

    def get_serial_baudrate(self) -> int:
        return self.get_hardware_constant("serial_baudrate")

    def get_max_angle_deg(self) -> int:
        return self.get_hardware_constant("max_angle_deg")

    def get_max_xpos_mm(self) -> int:
        return self.get_hardware_constant("max_xpos_mm")

    # --- Plot Settings ---
    def get_visible_plots(self):
        return self.settings.get(
            "visible_plots", self.DEFAULT_SETTINGS["visible_plots"]
        )

    def set_visible_plots(self, plot_list):
        self.settings["visible_plots"] = plot_list

    def get_plot_order(self):
        return self.settings.get("plot_order", self.DEFAULT_SETTINGS["plot_order"])

    def set_plot_order(self, order_list):
        self.settings["plot_order"] = order_list

    # --- Controller Management ---
    def get_last_controller(self):
        return self.settings.get(
            "last_controller", self.DEFAULT_SETTINGS["last_controller"]
        )

    def set_last_controller(self, name):
        self.settings["last_controller"] = name

    def get_controller_params(self, controller_name):
        return self.settings.get("controller_params", {}).get(controller_name, {})

    def set_controller_params(self, controller_name, params):
        self.settings.setdefault("controller_params", {})[controller_name] = params

    def get_all_settings(self):
        return self.settings


__all__ = ["SettingsManager"]
