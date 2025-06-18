"""
main_window.py

This file implements the main GUI window for the Modular Inverted Pendulum project.
It provides controls for starting/stopping the simulation or hardware, selecting controllers, and enabling swing-up mode.
The right side of the window displays real-time plots of system variables and a visualizer for the cart-pendulum system.
The GUI communicates with simulation or hardware backends using shared variables and multiprocessing.
"""
### === external imports ===
import sys
import os
import math
import importlib
import multiprocessing
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QCheckBox, QLabel, QLineEdit, QFormLayout, QGroupBox, QSpinBox, QDoubleSpinBox, QAction,
)
### === internal imports ===
from .collapsible_groupbox import CollapsibleGroupBox
from .visualizer import PendulumVisualizer
from .plot_widgets import PlotContainer, PlotList, DropPlotArea
from .settings_window import SettingsWindow
from backends.linear_sim_backend import start_linear_simulation_backend
from backends.nonlinear_sim_backend import start_nonlinear_simulation_backend
from backends.serial_backend import start_serial_backend
from utils.settings_manager import SettingsManager


class MainWindow(QMainWindow):
    def __init__(self, settings: SettingsManager = None):
        super().__init__()
        self.setWindowTitle("Modular Inverted Pendulum Control")
        self.setMinimumSize(800, 600)
        self.showMaximized()

        self.settings = settings
        self.plot_list = None
        self.plot_area = None
        self.shared_vars = None
        self.sim_proc = None
        self.controller_proc = None
        self.swingup_proc = None
        self.controller_start_func = None
        self.controller_param_values = None
        self.swingup_timer = None

        self.led_style = lambda active: (
            "background-color: #00cc00; border-radius: 7px;" if active else
            "background-color: #003300; border-radius: 7px;"
        )

        # --- Build UI layout ---
        central_widget = QWidget()
        master_layout = QHBoxLayout()
        central_widget.setLayout(master_layout)
        self.setCentralWidget(central_widget)

        # --- Menu bar ---
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("&Settings")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings_window)
        settings_menu.addAction(settings_action)
        about_action = QAction("About", self) # no functionality yet
        settings_menu.addAction(about_action)

        # --- Controls column ---
        controls_layout = QVBoxLayout()

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        self.start_button.clicked.connect(self.start_system)
        self.stop_button.clicked.connect(self.stop_system)
            # SYSTEM SELECTION
        self.system_selector = QComboBox()
        self.system_selector.addItems(["Linearized Simulation", "Nonlinear Simulation", "COM5"])
        self.system_selector.setToolTip("Select the system to control (simulation or hardware).")
        controls_layout.addWidget(QLabel("System:"))
        controls_layout.addWidget(self.system_selector)

            # CONTROLLER SELECTION
        controls_layout.addWidget(QLabel("Controller:"))
        self.controller_param_fields = {} 
        self.controller_dropdown = QComboBox()
        self.controller_dropdown.currentTextChanged.connect(self.display_param_fields)
        controls_layout.addWidget(self.controller_dropdown)
        
        self.controller_group = CollapsibleGroupBox("Controller Tuning")
        self.controller_form_layout = QFormLayout()
        self.controller_group.setContentLayout(self.controller_form_layout)
        controls_layout.addWidget(self.controller_group)

        self.controllers, self.controller_params = self.get_available_controllers()
        self.controller_dropdown.addItems(self.controllers)
        self.display_param_fields(self.controller_dropdown.currentText())

        # --- Simulation Settings Panel ---
        self.sim_settings_group = CollapsibleGroupBox("Simulation Settings")
        sim_layout = QFormLayout()

        self.sim_cmass_field = QDoubleSpinBox()
        self.sim_cmass_field.setRange(0.01, 10.0)
        self.sim_cmass_field.setDecimals(2)
        self.sim_cmass_field.setValue(0.5)
        sim_layout.addRow("Cart mass (kg):", self.sim_cmass_field)

        self.sim_pmass_field = QDoubleSpinBox()
        self.sim_pmass_field.setRange(0.01, 10.0)
        self.sim_pmass_field.setDecimals(2)
        self.sim_pmass_field.setValue(0.2)
        sim_layout.addRow("Pendulum mass (kg):", self.sim_pmass_field)

        self.sim_length_field = QDoubleSpinBox()
        self.sim_length_field.setRange(0.01, 2.0)
        self.sim_length_field.setDecimals(2)
        self.sim_length_field.setValue(0.5)
        sim_layout.addRow("Length (m):", self.sim_length_field)

        self.sim_friction_field = QDoubleSpinBox()
        self.sim_friction_field.setRange(0.0, 1.0)
        self.sim_friction_field.setDecimals(2)
        self.sim_friction_field.setValue(0.01)
        sim_layout.addRow("Cart Friction:", self.sim_friction_field)

        self.sim_damping_field = QDoubleSpinBox()
        self.sim_damping_field.setRange(0.0, 1.0)
        self.sim_damping_field.setDecimals(2)
        self.sim_damping_field.setValue(0.01)
        sim_layout.addRow("Pendulum Friction:", self.sim_damping_field)

        self.sim_initial_angle_field = QDoubleSpinBox()
        self.sim_initial_angle_field.setRange(0.0, 359.99)
        self.sim_initial_angle_field.setDecimals(2)
        self.sim_initial_angle_field.setValue(180.00)
        sim_layout.addRow("Initial angle (deg):", self.sim_initial_angle_field)

        self.sim_initial_speed_field = QDoubleSpinBox()
        self.sim_initial_speed_field.setRange(0.0, 1.0)
        self.sim_initial_speed_field.setDecimals(4)
        self.sim_initial_speed_field.setValue(0.01)
        sim_layout.addRow("Initial speed (deg7s):", self.sim_initial_speed_field)

        self.sim_randomize_checkbox = QCheckBox("Randomize Initial State")
        sim_layout.addRow(self.sim_randomize_checkbox)

        self.sim_settings_group.setContentLayout(sim_layout)
        controls_layout.addWidget(self.sim_settings_group)

        self.swingup_group = CollapsibleGroupBox("Swing-Up Settings")
        swingup_layout = QFormLayout()

        self.swingup_checkbox = QCheckBox("Enable Swing-Up")
        swingup_layout.addRow(self.swingup_checkbox)

        self.catch_angle_field = QDoubleSpinBox()
        self.catch_angle_field.setDecimals(3)
        self.catch_angle_field.setRange(0.0, math.pi)
        self.catch_angle_field.setValue(0.2)
        swingup_layout.addRow("Catch Angle (deg):", self.catch_angle_field)

        self.catch_momentum_field = QDoubleSpinBox()
        self.catch_momentum_field.setDecimals(3)
        self.catch_momentum_field.setRange(0.0, 10.0)
        self.catch_momentum_field.setValue(0.2)
        swingup_layout.addRow("Catch Momentum (deg/s):", self.catch_momentum_field)

        self.swingup_group.setContentLayout(swingup_layout)
        controls_layout.addWidget(self.swingup_group)


        self.swingup_led = QLabel()
        self.swingup_led.setFixedSize(15, 15)
        self.swingup_led.setStyleSheet(self.led_style(False))
        self.controller_led = QLabel()
        self.controller_led.setFixedSize(15, 15)
        self.controller_led.setStyleSheet(self.led_style(False))
        controls_layout.addWidget(QLabel("Swing-Up Active:"))
        controls_layout.addWidget(self.swingup_led)
        controls_layout.addWidget(QLabel("Controller Active:"))
        controls_layout.addWidget(self.controller_led)

        controls_layout.addStretch()

        # Center column: Plot + Visualizer
        center_layout = QVBoxLayout()

        # Dictionary of plot names -> (shared_var_key, y_range, value_getter)
        self.available_plots = {
            "Cart Position": ("position", (-350, 350), lambda v: v["position"].value),
            "Pendulum Angle": ("angle", (0, 2 * math.pi), lambda v: v["angle"].value),
            "Control Output": ("control", (-10, 10), lambda v: v["control_signal"].value),
            "Loop Execution Time": ("loop", (0, 0.02), lambda v: v["loop_time"].value),
            "Angular Momentum": ("momentum", (-1, 1), lambda v: v["angle"].value * v["control_signal"].value),
        }

        self.plot_area = DropPlotArea(self.available_plots, self.shared_vars)
        center_layout.addWidget(self.plot_area, 3)

        self.visualizer = PendulumVisualizer()
        self.visualizer.setStyleSheet("background-color: #222; border: 1px solid #444;")
        center_layout.addWidget(self.visualizer, 1)

        # Right column: Sidebar
        sidebar_layout = QVBoxLayout()
        self.plot_list = PlotList(self.plot_area)
        for plot_name in self.available_plots:
            self.plot_list.addItem(plot_name)
        self.plot_list.setDisabled(False)
        sidebar_layout.addWidget(self.plot_list)
        sidebar_layout.addWidget(self.plot_list.button_container)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setFixedWidth(250)

        #master_layout.addLayout(controls_layout, stretch=1)
        controls_widget = QWidget()
        controls_widget.setLayout(controls_layout)
        controls_widget.setFixedWidth(250)
        master_layout.addWidget(controls_widget)

        master_layout.addLayout(center_layout, stretch=3)
        master_layout.addWidget(sidebar_widget)

        self.timer = QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()

    def get_sim_vars_from_ui(self):
        return {
            "cart_mass": self.sim_cmass_field.value(),
            "pendulum_mass": self.sim_pmass_field.value(),
            "length": self.sim_length_field.value(),
            "friction": self.sim_friction_field.value(),
            "damping": self.sim_damping_field.value()
        }

    def open_settings_window(self):
        settings_dialog = SettingsWindow(self.settings, self)
        settings_dialog.exec_()

    def connect_to_shared_vars(self, shared_vars):
        self.shared_vars = shared_vars
        self.visualizer.shared_vars = shared_vars
        if self.plot_area:
            self.plot_area.shared_vars = shared_vars

    def update_plots(self):
        """Refresh all plot widgets and the visualizer."""
        if not self.shared_vars:
            return
        if self.plot_area:
            self.plot_area.update_all()
        self.visualizer.update()

    def get_available_controllers(self, controller_dir=None):
        """Scan the controllers directory for available modules."""
        if controller_dir is None:
            # Works both when bundled and in development
            if getattr(sys, 'frozen', False):
                # If bundled by PyInstaller
                base_dir = sys._MEIPASS
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))

            controller_dir = os.path.join(base_dir, "..", "controllers")
            controller_dir = os.path.abspath(controller_dir)

        controllers = []
        controller_params = {}

        if not os.path.isdir(controller_dir):
            print(f"[ERROR] Controller directory not found: {base_dir}, {controller_dir}")
            return controllers, controller_params
    
        for filename in os.listdir(controller_dir):
            if ((filename.startswith("__") == False) and (filename.endswith(".py"))):
                if filename.endswith(".py"):
                    controller_name = filename[:-3]  # Remove .py extension
                    controllers.append(controller_name)

                    # Extract #/VARS ... #/ENDVARS
                    with open(os.path.join(controller_dir, filename), "r") as f:
                        lines = f.readlines()
                    inside_block = False
                    params = []
                    for line in lines:
                        line = line.strip()
                        if line == "#/VARS":
                            inside_block = True
                        elif line == "#/ENDVARS":
                            break
                        elif inside_block and line.startswith("#/"):
                            try:
                                var_line = line[2:].strip()  # remove "#/"
                                if ":" in var_line:
                                    param_name, var_type = var_line.split(":", 1)
                                    params.append((param_name.strip(), var_type.strip()))
                                else:
                                    params.append((var_line.strip(), "float"))  # default to float
                            except ValueError:
                                print(f"[WARNING] Could not parse line: {line}")

                    controller_params[controller_name] = params


        return controllers, controller_params

    def display_param_fields(self, controller_name):
        # Clear previous inputs
        for i in reversed(range(self.controller_form_layout.count())):
            widget = self.controller_form_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.controller_param_fields.clear()
    
        # Load parameter list: [("Kp", "float"), ("Enabled", "bool"), ...]
        param_list = self.controller_params.get(controller_name, [])
    
        for param_name, param_type in param_list:
            label = QLabel(param_name + ":")
    
            if param_type == "float":
                field = QDoubleSpinBox()
                field.setDecimals(4)
                field.setRange(-1000.0, 1000.0)
                field.setValue(0.0)
            elif param_type == "int":
                field = QSpinBox()
                field.setRange(-1000, 1000)
                field.setValue(0)
            elif param_type == "bool":
                field = QCheckBox()
            else:  # fallback: string
                field = QLineEdit()
    
            self.controller_form_layout.addRow(label, field)
            self.controller_param_fields[param_name] = field

    def get_controller_param_values(self):
        values = {}
        for name, widget in self.controller_param_fields.items():
            if isinstance(widget, QDoubleSpinBox) or isinstance(widget, QSpinBox):
                values[name] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[name] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                values[name] = widget.text()
        return values

    def check_swingup_completion(self):
        if self.swingup_proc and not self.swingup_proc.is_alive():
            self.swingup_timer.stop()
            self.swingup_proc.join()
            self.swingup_proc = None
            self.swingup_led.setStyleSheet(self.led_style(False))
            if self.controller_start_func:
                self.controller_proc = self.controller_start_func(
                    self.shared_vars, *self.controller_param_values.values()
                )
                self.controller_led.setStyleSheet(self.led_style(True))
    
    def start_system(self):
        """Start the selected simulation or hardware backend and controller."""
        # === System selection ===
        system_choice = self.system_selector.currentText()
        # Get user-defined sim vars and update settings (but don't persist to disk)
        sim_vars = self.get_sim_vars_from_ui()
        self.settings.update_sim_variables(sim_vars)

        if system_choice == "Linearized Simulation":
            if self.sim_proc and self.sim_proc.is_alive():
                print("Simulation already running.")
                return

            print("Starting simulation...")
            self.shared_vars = {
                "position": multiprocessing.Value('d', 0.0),
                "angle": multiprocessing.Value('d', 0.0),
                "control_signal": multiprocessing.Value('d', 0.0),
                "loop_time": multiprocessing.Value('d', 0.0)
            }

            self.sim_proc = start_linear_simulation_backend(self.shared_vars, sim_vars)
            self.connect_to_shared_vars(self.shared_vars)

        elif system_choice == "Nonlinear Simulation":
            if self.sim_proc and self.sim_proc.is_alive():
                print("Simulation already running.")
                return

            print("Starting nonlinear simulation...")
            self.shared_vars = {
                "position": multiprocessing.Value('d', 0.0),
                "angle": multiprocessing.Value('d', 0.0),
                "control_signal": multiprocessing.Value('d', 0.0),
                "loop_time": multiprocessing.Value('d', 0.0)
            }

            self.sim_proc = start_nonlinear_simulation_backend(self.shared_vars, sim_vars)
            self.connect_to_shared_vars(self.shared_vars)

        elif system_choice == "COM5":
            print("Connecting...")
            self.shared_vars = {
                "position": multiprocessing.Value('d', 0.0),
                "angle": multiprocessing.Value('d', 0.0),
                "control_signal": multiprocessing.Value('d', 0.0),
                "loop_time": multiprocessing.Value('d', 0.0)
            }

            print(f"Real hardware mode selected: {system_choice}")
            self.sim_proc = start_serial_backend(self.shared_vars)
            self.connect_to_shared_vars(self.shared_vars)
        
        # === Controller selection ===
        controller_name = self.controller_dropdown.currentText()
        param_values = self.get_controller_param_values()

        try:
            controller_module = importlib.import_module(f"controllers.{controller_name}")
            start_func_name = f"start_{controller_name}"
            start_func = getattr(controller_module, start_func_name)

            if self.swingup_checkbox.isChecked():
                from controllers.__phase_swingup import start_phase_swingup

                self.controller_start_func = start_func
                self.controller_param_values = param_values
                catch_angle = self.catch_angle_field.value()
                catch_momentum = self.catch_momentum_field.value()

                self.swingup_proc = start_phase_swingup(
                    self.shared_vars, catch_angle, catch_momentum
                )
                self.swingup_timer = QTimer()
                self.swingup_timer.setInterval(50)
                self.swingup_timer.timeout.connect(self.check_swingup_completion)
                self.swingup_timer.start()
                self.swingup_led.setStyleSheet(self.led_style(True))
                self.controller_led.setStyleSheet(self.led_style(False))
            else:
                self.controller_proc = start_func(self.shared_vars, *param_values.values())
                self.controller_led.setStyleSheet(self.led_style(True))
                self.swingup_led.setStyleSheet(self.led_style(False))

        except Exception as e:
            print(f"[ERROR] Failed to start controller '{controller_name}': {e}")


    def stop_system(self):
        """Terminate any running simulation and controllers."""
        if self.sim_proc and self.sim_proc.is_alive():
            print("Stopping simulation...")
            if self.controller_proc and self.controller_proc.is_alive():
                self.controller_proc.terminate()
                self.controller_proc.join()
            if self.swingup_proc and self.swingup_proc.is_alive():
                self.swingup_proc.terminate()
                self.swingup_proc.join()
            if self.swingup_timer:
                self.swingup_timer.stop()
            self.controller_led.setStyleSheet(self.led_style(False))
            self.swingup_led.setStyleSheet(self.led_style(False))
            self.sim_proc.terminate()
            self.sim_proc.join()
            self.sim_proc = None
            self.shared_vars = None
        else:
            print("No simulation running to stop.")

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if not self.isMaximized():
                self.resize(1200, 700)
        super().changeEvent(event)

def run_gui(shared_vars=None):
    """Convenience function for launching ``MainWindow``."""
    app = QApplication(sys.argv)
    window = MainWindow()
    if shared_vars:
        # When embedding the GUI in another process, allow passing in existing
        # shared memory values.
        window.connect_to_shared_vars(shared_vars)
    window.show()
    sys.exit(app.exec_())

