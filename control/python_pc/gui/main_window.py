"""
main_window.py

This file implements the main GUI window for the Modular Inverted Pendulum project.
It provides controls for starting/stopping the simulation or hardware, selecting
controllers, and enabling swing-up mode on the left side.
The right side of the window displays real-time plots of system variables
and a visualizer for the cart-pendulum system.
The GUI communicates with simulation or hardware backends using shared variables
and multiprocessing.
"""

### === external imports ===
import importlib
import logging
import math
import multiprocessing
import sys

from backends.linear_sim_backend import start_linear_simulation_backend
from backends.nonlinear_sim_backend import start_nonlinear_simulation_backend
from backends.serial_backend import start_serial_backend
from PyQt5.QtCore import QEvent, QTimer
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .collapsible_groupbox import CollapsibleGroupBox
from .gui_helpers import create_spinbox
from .plot_widgets import DropPlotArea, PlotList
from .settings_window import SettingsWindow
from .visualizer import PendulumVisualizer
from utils.shared_vars import create_shared_vars
from utils.controller_loader import get_available_controllers
from utils.settings_manager import SettingsManager
from backend_manager import BackendManager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, settings: SettingsManager | None = None):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("Modular Inverted Pendulum Control")
        self.setMinimumSize(800, 600)
        self.showMaximized()

        self.init_backend_state()
        self.setup_ui()
        self.connect_signals()
        self.init_plot_update_timer()

    def init_backend_state(self):
        self.backend_manager = BackendManager()
        self.plot_list = None
        self.plot_area = None
        self.shared_vars = None
        self.sim_proc = None
        self.controller_proc = None
        self.swingup_proc = None
        self.controller_start_func = None
        self.controller_param_values = None
        self.swingup_timer = None
        self.controller_param_fields = {}

        self.led_style = lambda active: (
            "background-color: #00cc00; border-radius: 7px;"
            if active else "background-color: #003300; border-radius: 7px;"
        )

    def setup_ui(self):
        central_widget = QWidget()
        master_layout = QHBoxLayout()
        central_widget.setLayout(master_layout)
        self.setCentralWidget(central_widget)

        self.setup_menu_bar()
        controls_widget = self.setup_controls_panel()
        center_layout = self.setup_center_panel()
        sidebar_widget = self.setup_sidebar_panel()

        master_layout.addWidget(controls_widget)
        master_layout.addLayout(center_layout, stretch=3)
        master_layout.addWidget(sidebar_widget)

    def setup_menu_bar(self):
        menubar = self.menuBar()
        if menubar is None:
            raise Exception("Failed to create menuBar")
        run_menu = menubar.addMenu("&Run")
        if run_menu is None:
            raise Exception("Failed to create run_menu")
        hardware_menu = run_menu.addMenu("&Hardware")
        if hardware_menu is None:
            raise Exception("Failed to create hardware_menu")
        hardware_menu.addAction("Connect", self.connect_hardware)
        hardware_menu.addAction("Disconnect", self.disconnect_hardware)

        sim_menu = run_menu.addMenu("&Simulations")
        if sim_menu is None:
            raise Exception("Failed to create sim_menu")
        sim_menu.addAction("Start Linear Sim", self.start_linear_sim)
        sim_menu.addAction("Stop Linear Sim", self.stop_linear_sim)
        sim_menu.addAction("Start Nonlinear Sim", self.start_nonlinear_sim)
        sim_menu.addAction("Stop Nonlinear Sim", self.stop_nonlinear_sim)

        settings_menu = menubar.addMenu("&Settings")
        if settings_menu is None:
            raise Exception("Failed to create settings_menu")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings_window)
        settings_menu.addAction(settings_action)
        about_action = QAction("About", self)
        settings_menu.addAction(about_action)

    def setup_controls_panel(self):
        layout = QVBoxLayout()

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        # self.system_selector = QComboBox()
        # self.system_selector.addItems([
        #     "Linearized Simulation", "Nonlinear Simulation", "COM5"
        # ])
        # self.system_selector.setToolTip("Select the system to control (simulation or hardware).")
        # layout.addWidget(QLabel("System:"))
        # layout.addWidget(self.system_selector)

        layout.addWidget(QLabel("Controller:"))
        self.controller_dropdown = QComboBox()
        layout.addWidget(self.controller_dropdown)

        self.controller_group = CollapsibleGroupBox("Controller Tuning")
        self.controller_form_layout = QFormLayout()
        self.controller_group.setContentLayout(self.controller_form_layout)
        layout.addWidget(self.controller_group)

        self.controllers, self.controller_params = get_available_controllers()
        self.controller_dropdown.addItems(self.controllers)
        self.display_param_fields(self.controller_dropdown.currentText())

        self.sim_settings_group = CollapsibleGroupBox("Simulation Settings")
        sim_layout = QFormLayout()

        self.sim_cmass_field = create_spinbox(0.01, 10.0, 0.01, 0.5)
        sim_layout.addRow("Cart mass (kg):", self.sim_cmass_field)
        self.sim_pmass_field = create_spinbox(0.01, 10.0, 0.01, 0.2)
        sim_layout.addRow("Pendulum mass (kg):", self.sim_pmass_field)
        self.sim_length_field = create_spinbox(0.01, 2.0, 0.01, 0.5)
        sim_layout.addRow("Length (m):", self.sim_length_field)
        self.sim_friction_field = create_spinbox(0.0, 1.0, 0.01, 0.01)
        sim_layout.addRow("Cart Friction:", self.sim_friction_field)
        self.sim_damping_field = create_spinbox(0.0, 1.0, 0.01, 0.01)
        sim_layout.addRow("Pendulum Friction:", self.sim_damping_field)
        self.sim_initial_angle_field = create_spinbox(0.0, 359.99, 0.1, 180.00)
        sim_layout.addRow("Initial angle (deg):", self.sim_initial_angle_field)
        self.sim_initial_speed_field = create_spinbox(0.0, 1.0, 0.001, 0.01)
        self.sim_initial_speed_field.setDecimals(4)
        sim_layout.addRow("Initial speed (deg/s):", self.sim_initial_speed_field)
        self.sim_randomize_checkbox = QCheckBox("Randomize Initial State")
        sim_layout.addRow(self.sim_randomize_checkbox)

        self.sim_settings_group.setContentLayout(sim_layout)
        layout.addWidget(self.sim_settings_group)

        self.swingup_group = CollapsibleGroupBox("Swing-Up Settings")
        swingup_layout = QFormLayout()

        self.swingup_checkbox = QCheckBox("Enable Swing-Up")
        swingup_layout.addRow(self.swingup_checkbox)
        self.catch_angle_field = create_spinbox(0.0, float(math.pi), 0.01, 0.2)
        self.catch_angle_field.setDecimals(3)
        swingup_layout.addRow("Catch Angle (deg):", self.catch_angle_field)
        self.catch_momentum_field = create_spinbox(0.0, 10.0, 0.01, 0.2)
        self.catch_momentum_field.setDecimals(3)
        swingup_layout.addRow("Catch Momentum (deg/s):", self.catch_momentum_field)

        self.swingup_group.setContentLayout(swingup_layout)
        layout.addWidget(self.swingup_group)

        self.swingup_led = QLabel()
        self.swingup_led.setFixedSize(15, 15)
        self.swingup_led.setStyleSheet(self.led_style(False))
        self.controller_led = QLabel()
        self.controller_led.setFixedSize(15, 15)
        self.controller_led.setStyleSheet(self.led_style(False))
        layout.addWidget(QLabel("Swing-Up Active:"))
        layout.addWidget(self.swingup_led)
        layout.addWidget(QLabel("Controller Active:"))
        layout.addWidget(self.controller_led)

        layout.addStretch()

        widget = QWidget()
        widget.setLayout(layout)
        widget.setFixedWidth(250)
        return widget

    def setup_center_panel(self):
        layout = QVBoxLayout()

        self.available_plots = {
            "Cart Position": ("position", (-350, 350), lambda v: v["position"].value),
            "Pendulum Angle": ("angle", (0, 2 * math.pi), lambda v: v["angle"].value),
            "Setpoint Angle": (
                "desired_angle",
                (math.radians(175), math.radians(185)),
                lambda v: v["desired_angle"].value,
            ),
            "Control Output": (
                "control",
                (-255, 255),
                lambda v: v["control_signal"].value,
            ),
            "Loop Execution Time": ("loop", (0, 0.02), lambda v: v["loop_time"].value),
            "Angular Momentum": (
                "momentum",
                (-1, 1),
                lambda v: v["angle"].value * v["control_signal"].value,
            ),
        }

        self.plot_area = DropPlotArea(self.available_plots, self.shared_vars)
        layout.addWidget(self.plot_area, 3)

        self.visualizer = PendulumVisualizer()
        self.visualizer.setStyleSheet("background-color: #222; border: 1px solid #444;")
        layout.addWidget(self.visualizer, 1)

        return layout

    def setup_sidebar_panel(self):
        layout = QVBoxLayout()
        self.plot_list = PlotList(self.plot_area)
        for plot_name in self.available_plots:
            self.plot_list.addItem(plot_name)
        self.plot_list.setDisabled(False)
        layout.addWidget(self.plot_list)
        layout.addWidget(self.plot_list.button_container)

        widget = QWidget()
        widget.setLayout(layout)
        widget.setFixedWidth(250)
        return widget

    def connect_signals(self):
        self.start_button.clicked.connect(self.start_controller)
        self.stop_button.clicked.connect(self.stop_system)
        self.controller_dropdown.currentTextChanged.connect(self.display_param_fields)

    def init_plot_update_timer(self):
        self.timer = QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()

    def update_plots(self):
        if not self.shared_vars:
            return
        if self.plot_area:
            self.plot_area.update_all()
        self.visualizer.update()

    def open_settings_window(self):
        settings_dialog = SettingsWindow(self.settings, self)
        settings_dialog.exec_()

    def connect_to_shared_vars(self, shared_vars):
        self.shared_vars = shared_vars
        self.visualizer.shared_vars = shared_vars
        if self.plot_area:
            self.plot_area.shared_vars = shared_vars

    def changeEvent(self, event: QEvent):  # type: ignore[override]
        if event.type() == QEvent.WindowStateChange:  # type: ignore[attr-defined]
            if not self.isMaximized():
                self.resize(1200, 700)
        super().changeEvent(event)

    def display_param_fields(self, controller_name):
        for i in reversed(range(self.controller_form_layout.count())):
            item = self.controller_form_layout.itemAt(i)
            if item is not None:
                widget: QWidget = item.widget()
                if widget:
                    widget.deleteLater()
        self.controller_param_fields.clear()

        param_list = self.controller_params.get(controller_name, [])

        for param_name, param_type in param_list:
            label = QLabel(param_name + ":")
            if param_type == "float":
                field = QDoubleSpinBox()
                field.setDecimals(4)
                field.setRange(-9000.0, 9000.0)
                field.setValue(0.0)
            elif param_type == "int":
                field = QSpinBox()
                field.setRange(-9000, 9000)
                field.setValue(0)
            elif param_type == "bool":
                field = QCheckBox()
            else:
                field = QLineEdit()

            self.controller_form_layout.addRow(label, field)
            self.controller_param_fields[param_name] = field

    def get_controller_param_values(self):
        values = {}
        for name, widget in self.controller_param_fields.items():
            if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                values[name] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[name] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                values[name] = widget.text()
        return values

    def check_swingup_completion(self):
        if self.swingup_proc and not self.swingup_proc.is_alive():
            if self.swingup_timer is not None:
                self.swingup_timer.stop()
            self.swingup_proc.join()
            self.swingup_proc = None
            self.swingup_led.setStyleSheet(self.led_style(False))
            if self.controller_start_func and self.controller_param_values is not None:
                self.controller_proc = self.controller_start_func(
                    self.shared_vars, *self.controller_param_values.values()
                )
                self.controller_led.setStyleSheet(self.led_style(True))

    def start_controller(self):
        # system_choice = self.system_selector.currentText()
        # sim_vars = self.get_sim_vars_from_ui()
        # if self.settings is not None:
        #     self.settings.update_sim_variables(sim_vars)

        # if system_choice == "Linearized Simulation":
        #     if self.sim_proc and self.sim_proc.is_alive():
        #         logger.info("Simulation already running.")
        #         return
        #     logger.info("Starting simulation...")
        #     self.shared_vars = create_shared_vars()
        #     self.sim_proc = start_linear_simulation_backend(self.shared_vars, sim_vars)

        # elif system_choice == "Nonlinear Simulation":
        #     if self.sim_proc and self.sim_proc.is_alive():
        #         logger.info("Simulation already running.")
        #         return
        #     logger.info("Starting nonlinear simulation...")
        #     self.shared_vars = create_shared_vars()
        #     self.sim_proc = start_nonlinear_simulation_backend(self.shared_vars, sim_vars)

        # elif system_choice == "COM5":
        #     logger.info("Connecting...")
        #     self.shared_vars = create_shared_vars()
        #     self.sim_proc = start_serial_backend(self.shared_vars)

        # self.connect_to_shared_vars(self.shared_vars) # we don't do that here anymore, instead on hardware connect

        controller_name = self.controller_dropdown.currentText()
        param_values = self.get_controller_param_values()

        try:
            controller_module = importlib.import_module(f"controllers.{controller_name}")
            start_func = getattr(controller_module, f"start_{controller_name}")

            if self.swingup_checkbox.isChecked():
                #TODO do something
                pass
            else:
                self.controller_proc = start_func(
                    self.shared_vars, *param_values.values()
                )
                self.controller_led.setStyleSheet(self.led_style(True))
                self.swingup_led.setStyleSheet(self.led_style(False))

        except Exception as e:
            logger.error("Failed to start controller '%s': %s", controller_name, e, exc_info=True)

    def stop_system(self):
        logger.info("Stopping controller...")
        if self.shared_vars is not None:
            self.shared_vars["controller_active"] = False
            logger.info("controller_active = false")
        if self.controller_proc and self.controller_proc.is_alive():
            self.controller_proc.terminate()
            self.controller_proc.join()
        self.controller_led.setStyleSheet(self.led_style(False))
        self.sim_proc = None 
        # self.shared_vars = None # TODO maybe don't do that?

    def connect_hardware(self):
        sv = self.backend_manager.start_hardware()
        self.connect_to_shared_vars(sv)

    def disconnect_hardware(self):
        self.backend_manager.stop_hardware()

    def start_linear_sim(self):
        self.backend_manager.start_linear_sim()

    def stop_linear_sim(self):
        self.backend_manager.stop_linear_sim()

    def start_nonlinear_sim(self):
        self.backend_manager.start_nonlinear_sim()

    def stop_nonlinear_sim(self):
        self.backend_manager.stop_nonlinear_sim()

    def get_sim_vars_from_ui(self):
        return {
            "cart_mass": self.sim_cmass_field.value(),
            "pendulum_mass": self.sim_pmass_field.value(),
            "length": self.sim_length_field.value(),
            "friction": self.sim_friction_field.value(),
            "damping": self.sim_damping_field.value(),
        }
