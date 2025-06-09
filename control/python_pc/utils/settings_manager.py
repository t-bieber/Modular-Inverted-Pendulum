import os
import json

class SettingsManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_path = os.path.join(base_dir, "settings.json")

        self.defaults = {
            "sim_variables": {
                "mass": 0.2,
                "length": 0.5,
                "friction": 0.01,
                "start_angle": 0.1,
                "start_velocity": 0.0
            },
            "visible_plots": ["Cart Position", "Pendulum Angle", "Control Output"],
            "plot_order": ["Cart Position", "Pendulum Angle", "Control Output"],
            "last_controller": "pid_controller",
            "controller_params": {}
        }

        self.data = self.load()

    def load(self):
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARNING] Failed to load settings: {e}")
        return self.defaults.copy()

    def save(self):
        try:
            with open(self.settings_path, "w") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"[ERROR] Failed to save settings: {e}")

    # --- Simulation settings ---
    def get_sim_var(self, name):
        return self.data.get("sim_variables", {}).get(name, self.defaults["sim_variables"].get(name))

    def set_sim_var(self, name, value):
        if "sim_variables" not in self.data:
            self.data["sim_variables"] = {}
        self.data["sim_variables"][name] = value

    # --- Plots ---
    def get_visible_plots(self):
        return self.data.get("visible_plots", self.defaults["visible_plots"])

    def set_visible_plots(self, plot_names):
        self.data["visible_plots"] = plot_names

    def get_plot_order(self):
        return self.data.get("plot_order", self.defaults["plot_order"])

    def set_plot_order(self, order):
        self.data["plot_order"] = order

    # --- Controller state ---
    def get_last_controller(self):
        return self.data.get("last_controller", self.defaults["last_controller"])

    def set_last_controller(self, name):
        self.data["last_controller"] = name

    def get_controller_params(self, controller_name):
        return self.data.get("controller_params", {}).get(controller_name, {})

    def set_controller_params(self, controller_name, params):
        if "controller_params" not in self.data:
            self.data["controller_params"] = {}
        self.data["controller_params"][controller_name] = params
