from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QPushButton, QLabel
)
from PyQt5.QtCore import Qt

class SettingsWindow(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(300, 200)
        self.settings = settings_manager

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.form = QFormLayout()
        layout.addLayout(self.form)

        self.inputs = {}
        sim_vars = self.settings.get_sim_variables()

        for key, value in sim_vars.items():
            spin = QDoubleSpinBox()
            spin.setDecimals(4)
            spin.setRange(0.0, 100.0)
            spin.setValue(value)
            self.inputs[key] = spin
            self.form.addRow(QLabel(key.capitalize()), spin)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button, alignment=Qt.AlignRight)

    def save_settings(self):
        for key, spin in self.inputs.items():
            self.settings.set_sim_variable(key, spin.value())
        self.settings.save_settings()
        self.accept()
