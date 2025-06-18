"""
visualizer.py

Widget for visualizing the cart-pendulum system state.
"""

import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import QWidget


class PendulumVisualizer(QWidget):
    """Simple QWidget that draws the pendulum and cart."""

    def __init__(self, shared_vars=None):
        super().__init__()
        self.shared_vars = shared_vars  # Set once at initialization
        # Dimensions for drawing the cart and pendulum
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
        # Called by Qt whenever the widget needs to be redrawn
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

        # Scale x position
        x_scaled = width // 2 + x_pos

        # Draw track
        painter.setPen(QPen(self.track_color, 2))
        track_y = center_y + self.cart_height // 2 + 5
        painter.drawLine(0, track_y, width, track_y)

        # Draw cart
        cart_rect = QRectF(
            x_scaled - self.cart_width // 2,
            center_y - self.cart_height // 2,
            self.cart_width,
            self.cart_height,
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
