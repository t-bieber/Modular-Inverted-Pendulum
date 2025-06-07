"""
main_window.py

This file implements the main GUI window for the Modular Inverted Pendulum project.
It provides controls for starting/stopping the simulation or hardware, selecting controllers, and enabling swing-up mode.
The right side of the window displays real-time plots of system variables and a visualizer for the cart-pendulum system.
The GUI communicates with simulation or hardware backends using shared variables and multiprocessing.
"""

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QCheckBox, QLabel, QFrame
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath
from PyQt5.QtCore import QTimer, Qt, QEvent, QPointF, QRectF
import pyqtgraph as pg
import sys
import time
import math
import multiprocessing
from backends.sim_backend import start_simulation_backend
from controllers.pid_controller import start_pid_controller

class PendulumVisualizer(QWidget):
    def __init__(self, shared_vars=None):
        super().__init__()
        self.shared_vars = shared_vars  # Set once at initialization
        self.cart_width = 50
        self.cart_height = 20
        self.pendulum_length = 80
        self.setMinimumSize(400, 200)
        
        # Visual styling
        self.track_color = QColor(100, 100, 100)
        self.cart_color = QColor(70, 130, 180)  # Steel blue
        self.pendulum_color = QColor(220, 220, 220)  # Light gray
        self.bob_color = QColor(200, 50, 50)  # Red
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.shared_vars:
            # Draw placeholder when no data
            painter.drawText(self.rect(), Qt.AlignCenter, "No pendulum data")
            return
            
        try:
            # Get current values (safe access)
            x_pos = self.shared_vars["position"].value
            angle = self.shared_vars["angle"].value
        except (KeyError, AttributeError):
            return
            
        width = self.width()
        height = self.height()
        center_y = height // 2
        
        # Scale x position (1 meter = 100 pixels)
        x_scaled = width // 2 + x_pos * 500
        
        # Draw track
        painter.setPen(QPen(self.track_color, 2))
        track_y = center_y + self.cart_height//2 + 5
        painter.drawLine(0, track_y, width, track_y)
        
        # Draw cart
        cart_rect = QRectF(
            x_scaled - self.cart_width//2,
            center_y - self.cart_height//2,
            self.cart_width,
            self.cart_height
        )
        painter.setBrush(QBrush(self.cart_color))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(cart_rect)
        
        # Draw pendulum
        pivot = QPointF(x_scaled, center_y)
        end_x = pivot.x() + self.pendulum_length * math.sin(angle)
        end_y = pivot.y() + self.pendulum_length * math.cos(angle)
        
        painter.setPen(QPen(self.pendulum_color, 3))
        painter.drawLine(pivot, QPointF(end_x, end_y))
        
        # Draw pendulum bob
        painter.setBrush(QBrush(self.bob_color))
        painter.drawEllipse(QPointF(end_x, end_y), 10, 10)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modular Inverted Pendulum Control")
        self.setMinimumSize(800, 600)  # Optional: set a minimum size
        self.showMaximized()           # Start maximized

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
        self.stop_button.clicked.connect(self.stop_system)

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
        ranges = [(-100, 100), (0, 2 * math.pi), (-10, 10), (0, 0.02)]
        for title in titles:
            plot = pg.PlotWidget(title=title)
            plot.showGrid(x=True, y=True)
            plot.setYRange(ranges[titles.index(title)][0], ranges[titles.index(title)][1])
            curve = plot.plot(pen=pg.mkPen(color='y', width=2))
            self.plot_widgets.append((plot, curve))
            self.plot_data.append([])
            right_layout.addWidget(plot)

        # === Pendulum Visualizer Placeholder ===
        self.visualizer = PendulumVisualizer()
        self.visualizer.setStyleSheet("background-color: #222; border: 1px solid #444;")
        right_layout.addWidget(self.visualizer)

        # Combine layouts
        master_layout.addLayout(controls_layout, stretch=1)
        master_layout.addLayout(right_layout, stretch=3)

        # === Timer for Plot Updates ===
        self.timer = QTimer()
        self.timer.setInterval(10)  # 100Hz
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()

    def connect_to_shared_vars(self, shared_vars):
        self.shared_vars = shared_vars
        self.visualizer.shared_vars = shared_vars  # Set once

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

        # update visualizer
        self.visualizer.update()
    
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

            ### PID GAIN ###
            Kp = 20.0
            Ki = 0.0
            Kd = 1.0
            self.pid_proc = start_pid_controller(self.shared_vars, Kp, Ki, Kd)

        else:
            print(f"Real hardware mode selected: {system_choice}")
            # TODO: implement serial backend init

    def stop_system(self):
        if self.sim_proc and self.sim_proc.is_alive():
            print("Stopping simulation...")
            self.pid_proc.terminate()
            self.pid_proc.join()
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
    app = QApplication(sys.argv)
    window = MainWindow()
    if shared_vars:
        window.connect_to_shared_vars(shared_vars)
    window.show()
    sys.exit(app.exec_())
