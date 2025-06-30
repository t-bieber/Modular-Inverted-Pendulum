"""
plot_widgets.py

Utility widgets for plotting simulation data within the GUI.
Status: Working
"""

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from pyqtgraph import GraphicsLayoutWidget, mkPen


class PlotContainer(GraphicsLayoutWidget):
    """Widget containing a single scrolling plot."""

    def __init__(self, plot_name, y_range, getter):
        super().__init__()
        self.plot_name = plot_name
        # ``getter`` is a callable that extracts the value to plot from the
        # shared variable dictionary.
        self.getter = getter
        self.data = [0] * 200
        self.max_points = 200
        self.plot_item = self.addPlot(title=plot_name)
        self.plot_item.showGrid(x=True, y=True)
        self.plot_item.setYRange(*y_range)
        self.curve = self.plot_item.plot(pen=mkPen(color=(51, 102, 255), width=2))

    def update_plot(self, shared_vars):
        """Append the latest value and redraw the curve."""
        value = self.getter(shared_vars)
        self.data.append(value)
        if len(self.data) > self.max_points:
            self.data.pop(0)
        self.curve.setData(self.data)


class PlotList(QListWidget):
    """List widget with helpers to manage plots."""

    def __init__(self, drop_area):
        super().__init__()
        self.drop_area = drop_area
        # Keep reference to ``DropPlotArea`` so we can add/remove plots
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setFrameShape(QFrame.StyledPanel)

        # Add control buttons below the list
        self.button_layout = QVBoxLayout()

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_plot)
        self.button_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_selected_plot)
        self.button_layout.addWidget(self.remove_button)

        self.up_button = QPushButton("Move Up")
        self.up_button.clicked.connect(self.move_plot_up)
        self.button_layout.addWidget(self.up_button)

        self.down_button = QPushButton("Move Down")
        self.down_button.clicked.connect(self.move_plot_down)
        self.button_layout.addWidget(self.down_button)

        self.button_container = QWidget()
        self.button_container.setLayout(self.button_layout)

        # Disable editing or dragging
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragDropMode(QAbstractItemView.NoDragDrop)

        self.add_plot("Pendulum Angle")
        self.add_plot("Setpoint Angle")
        self.add_plot("Control Output")


    def populate(self, plot_names):
        self.clear()
        for name in plot_names:
            self.addItem(name)

    def get_selected_plot_name(self):
        item = self.currentItem()
        return item.text() if item else None

    def add_plot(self, plot_name = None):
        if plot_name is False:
            plot_name = self.get_selected_plot_name()
        if plot_name and plot_name not in self.drop_area.active_plot_widgets:
            key, y_range, getter = self.drop_area.available_plots[plot_name]
            plot_widget = PlotContainer(plot_name, y_range, getter)
            self.drop_area.layout.addWidget(plot_widget)
            self.drop_area.active_plot_widgets[plot_name] = plot_widget

    def remove_selected_plot(self):
        plot_name = self.get_selected_plot_name()
        if plot_name:
            self.drop_area.remove_plot(plot_name)

    def move_plot_up(self):
        plot_name = self.get_selected_plot_name()
        if plot_name and plot_name in self.drop_area.active_plot_widgets:
            widgets = self.drop_area.active_plot_widgets
            names = list(widgets.keys())
            idx = names.index(plot_name)
            if idx > 0:
                names[idx], names[idx - 1] = names[idx - 1], names[idx]
                self._reorder_plots(names)

    def move_plot_down(self):
        plot_name = self.get_selected_plot_name()
        if plot_name and plot_name in self.drop_area.active_plot_widgets:
            widgets = self.drop_area.active_plot_widgets
            names = list(widgets.keys())
            idx = names.index(plot_name)
            if idx < len(names) - 1:
                names[idx], names[idx + 1] = names[idx + 1], names[idx]
                self._reorder_plots(names)

    def _reorder_plots(self, ordered_names):
        # Remove all widgets and re-add in the desired order
        for i in reversed(range(self.drop_area.layout.count())):
            item = self.drop_area.layout.itemAt(i)
            widget = item.widget()
            if widget:
                self.drop_area.layout.removeWidget(widget)
                widget.setParent(None)

        new_widgets = {}
        for name in ordered_names:
            key, y_range, getter = self.drop_area.available_plots[name]
            widget = PlotContainer(name, y_range, getter)
            self.drop_area.layout.addWidget(widget)
            new_widgets[name] = widget

        self.drop_area.active_plot_widgets = new_widgets


class DropPlotArea(QWidget):
    """Container that holds active plot widgets."""

    def __init__(self, available_plots, shared_vars):
        super().__init__()
        self.layout = QVBoxLayout()     # type: ignore
        if self.layout is not None:
            self.setLayout(self.layout) # type: ignore
        self.available_plots = available_plots  # name -> (key, range, getter)
        self.shared_vars = shared_vars
        self.active_plot_widgets = {}

    def remove_plot(self, plot_name):
        if plot_name in self.active_plot_widgets:
            widget = self.active_plot_widgets.pop(plot_name)
            self.layout.removeWidget(widget)    # type: ignore
            widget.setParent(None)

    def update_all(self):
        """Update each active plot widget with the latest values."""
        for widget in self.active_plot_widgets.values():
            widget.update_plot(self.shared_vars)
