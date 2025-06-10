import json
import os

class SettingsManager:
    DEFAULT_SETTINGS = {
        "sim_variables": {
            "mass": 0.2,
            "length": 0.5,
            "damping": 0.01,
            "friction": 0.01
        },
        "visible_plots": ["Cart Position", "Pendulum Angle"],
        "plot_order": ["Cart Position", "Pendulum Angle"],
        "last_controller": "pid_controller",
        "controller_params": {}
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

    def get_all_settings(self):
        return self.settings

    def get_sim_variables(self):
        return self.settings.get("sim_variables", self.DEFAULT_SETTINGS["sim_variables"])

    def set_sim_variable(self, key, value):
        self.settings.setdefault("sim_variables", {})[key] = value

    def get_visible_plots(self):
        return self.settings.get("visible_plots", self.DEFAULT_SETTINGS["visible_plots"])

    def set_visible_plots(self, plot_list):
        self.settings["visible_plots"] = plot_list

    def get_plot_order(self):
        return self.settings.get("plot_order", self.DEFAULT_SETTINGS["plot_order"])

    def set_plot_order(self, order_list):
        self.settings["plot_order"] = order_list

    def get_last_controller(self):
        return self.settings.get("last_controller", self.DEFAULT_SETTINGS["last_controller"])

    def set_last_controller(self, name):
        self.settings["last_controller"] = name

    def get_controller_params(self, controller_name):
        return self.settings.get("controller_params", {}).get(controller_name, {})

    def set_controller_params(self, controller_name, params):
        self.settings.setdefault("controller_params", {})[controller_name] = params
