from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QToolButton, QLabel, QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt


class CollapsibleGroupBox(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)

        # === Toggle Button (arrow icon) ===
        self.toggle_button = QToolButton()
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)

        # === Title Label ===
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("QLabel { font-weight: bold; }")

        # === Header Layout (arrow + title) ===
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.addWidget(self.toggle_button)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()

        # === Content Widget (hidden on collapse) ===
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 0, 0, 0)  # indent content

        # === Main Layout ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.header_widget)
        main_layout.addWidget(self.content_widget)

        # Connect click behavior
        self.toggle_button.clicked.connect(self.toggle_content)

        self.content_widget.setVisible(False)

    def toggle_content(self):
        visible = self.toggle_button.isChecked()
        self.content_widget.setVisible(visible)
        self.toggle_button.setArrowType(Qt.DownArrow if visible else Qt.RightArrow)

    def setContentLayout(self, layout):
        # Clear old layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        self.content_layout.addLayout(layout)
