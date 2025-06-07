from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QCheckBox, QLabel, QFrame
)
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg
import sys
import time
import math
import multiprocessing
from backends.sim_backend import start_simulation_backend

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inverted Pendulum GUI")
        self.showMaximized()

        self.shared_vars = None
        self.sim_proc = None

        # === Master Layout ===
        master_layout = QHBoxLayout()
        self.setLayout(master_layout)

        # === LEFT COLUMN: Controls ===
        controls_layout = QVBoxLayout()

        # System selection
        self.system_selector = QComboBox()
        self.system_selector.addItems(["Simulation", "COM1", "COM2", "COM3"])
        controls_layout.addWidget(QLabel("System:"))
        controls_layout.addWidget(self.system_selector)

        # Start/Stop
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        self.start_button.clicked.connect(self.start_system)

        # Controller Selector
        self.controller_dropdown = QComboBox()
        self.controller_dropdown.addItems(["PID", "LQR", "Init"])
        controls_layout.addWidget(QLabel("Controller:"))
        controls_layout.addWidget(self.controller_dropdown)

        # Swing-up toggle
        self.swingup_checkbox = QCheckBox("Enable Swing-Up")
        controls_layout.addWidget(self.swingup_checkbox)

        # Spacer
        controls_layout.addStretch()

        # === RIGHT COLUMN: Plots + Visualizer ===
        right_layout = QVBoxLayout()

        self.plot_widgets = []
        self.plot_data = []

        titles = ["Cart Position", "Pendulum Angle", "Control Output", "Loop Execution Time"]
        for title in titles:
            plot = pg.PlotWidget(title=title)
            plot.showGrid(x=True, y=True)
            plot.setYRange(-100, 100)
            curve = plot.plot(pen=pg.mkPen(color='y', width=2))
            self.plot_widgets.append((plot, curve))
            self.plot_data.append([])
            right_layout.addWidget(plot)

        # === Pendulum Visualizer Placeholder ===
        self.visualizer_frame = QFrame()
        self.visualizer_frame.setFrameShape(QFrame.StyledPanel)
        self.visualizer_frame.setFixedHeight(200)
        self.visualizer_frame.setStyleSheet("background-color: #222; border: 1px solid #444;")
        right_layout.addWidget(self.visualizer_frame)

        # Combine layouts
        master_layout.addLayout(controls_layout, stretch=1)
        master_layout.addLayout(right_layout, stretch=3)

        # === Timer for Plot Updates ===
        self.timer = QTimer()
        self.timer.setInterval(50)  # 20Hz
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()

    def connect_to_shared_vars(self, shared_vars):
        self.shared_vars = shared_vars

    def update_plots(self):
        if not self.shared_vars:
            return

        pos = self.shared_vars["position"].value
        angle = self.shared_vars["angle"].value
        control = self.shared_vars["control_signal"].value
        loop_time = self.shared_vars["loop_time"].value

        values = [pos, angle, control, loop_time]
        for i, (_, curve) in enumerate(self.plot_widgets):
            if len(self.plot_data[i]) > 200:
                self.plot_data[i].pop(0)
            self.plot_data[i].append(values[i])
            curve.setData(self.plot_data[i])
    
    def start_system(self):
        system_choice = self.system_selector.currentText()

        if system_choice == "Simulation":
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

            self.sim_proc = start_simulation_backend(self.shared_vars)
            self.connect_to_shared_vars(self.shared_vars)

            # Start dummy controller
            ctrl_proc = multiprocessing.Process(
                target=dummy_controller,
                args=(self.shared_vars["control_signal"],)
                )
            ctrl_proc.start()

        else:
            print(f"Real hardware mode selected: {system_choice}")
            # TODO: implement serial backend init

def dummy_controller(control_signal):
    t = 0
    while True:
        control_signal.value = math.sin(5*t)
        t += 0.01
        time.sleep(0.01)

def run_gui(shared_vars=None):
    app = QApplication(sys.argv)
    window = MainWindow()
    if shared_vars:
        window.connect_to_shared_vars(shared_vars)
    window.show()
    sys.exit(app.exec_())
