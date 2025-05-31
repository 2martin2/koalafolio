# a filterable combobox widget
# layout: text, combobox, filterbuttons
# filterbuttons open a menu with filter checkboxes

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QPushButton, QHBoxLayout, QVBoxLayout,
    QDialog, QCheckBox, QDialogButtonBox, QFormLayout, QMenu, QAction, QWidgetAction
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QAbstractListModel, QModelIndex, QVariant, QPoint
from koalafolio.gui.widgets.QCompleterComboBox import QCompleterComboBoxView

class StringPropertyListModel(QAbstractListModel):
    def __init__(self, string_list, properties_list, parent=None):
        super().__init__(parent)
        self._strings = string_list
        self._properties = properties_list

    def rowCount(self, parent=QModelIndex()):
        return len(self._strings)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        if role == Qt.DisplayRole:
            return self._strings[row]
        if role == Qt.UserRole:
            return self._properties[row]
        return QVariant()


class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_filters = {}  # key: set of allowed values

    def set_filter(self, key, allowed_values):
        self.active_filters[key] = set(allowed_values)
        self.invalidateFilter()

    def clear_filter(self, key):
        if key in self.active_filters:
            del self.active_filters[key]
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        props = model.data(model.index(source_row, 0), Qt.UserRole)
        for key, allowed in self.active_filters.items():
            if allowed and props.get(key) not in allowed:
                return False
        return True

class FilterableComboBoxView(QWidget):
    def __init__(self, label_text="", parent=None):
        super().__init__(parent)
        self.proxyModel = FilterProxyModel(self)
        self.filter_properties = {}  # key: list of possible values
        self.active_filter_values = {}  # key: set of currently enabled values

        self.label = QLabel(label_text, self)
        self.combobox = QCompleterComboBoxView(self)
        self.combobox.setModel(self.proxyModel)

        self.filter_buttons = {}  # key: QPushButton
        self.filter_menus = {}  # key: QMenu

        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.combobox)
        self.filter_buttons_layout = QHBoxLayout()
        layout.addLayout(self.filter_buttons_layout)
        self.setLayout(layout)

    def setModel(self, model):
        self.proxyModel.setSourceModel(model)
        self.generateFilterProperties(model)
        self.createFilterButtons()
        self.createFilterMenus()

    def generateFilterProperties(self, model):
        # Only accept key: list properties
        self.filter_properties.clear()
        for row in range(model.rowCount()):
            props = model.data(model.index(row, 0), Qt.UserRole)
            for key, value in props.items():
                if key not in self.filter_properties:
                    self.filter_properties[key] = []
                if value not in self.filter_properties[key]:
                    self.filter_properties[key].append(value)
        # At start, all values are enabled
        self.active_filter_values = {k: set(v) for k, v in self.filter_properties.items()}

    def createFilterButtons(self):
        # Remove old buttons
        for btn in self.filter_buttons.values():
            self.filter_buttons_layout.removeWidget(btn)
            btn.deleteLater()
        self.filter_buttons.clear()
        # Create new buttons
        for key, values in self.filter_properties.items():
            btn = QPushButton(key, self)
            btn.setCheckable(False)
            btn.clicked.connect(lambda checked, k=key: self.open_filter_popup(k))
            self.filter_buttons_layout.addWidget(btn)
            self.filter_buttons[key] = btn
            
    def createFilterMenus(self):
        self.filter_menus = {}
        for key, values in self.filter_properties.items():
            self.filter_menus[key] = self._create_single_filter_menu(key, values)

    def _create_single_filter_menu(self, key, values):
        menu = QMenu(self)
        menu.setSeparatorsCollapsible(False)
        actions = {}

        # Add Select All checkbox at the top using QWidgetAction
        select_all_widget = QCheckBox("Select All", menu)
        select_all_action = QWidgetAction(menu)
        select_all_action.setDefaultWidget(select_all_widget)
        menu.addAction(select_all_action)
        menu.addSeparator()

        # Add value checkboxes using QWidgetAction
        for value in values:
            cb = QCheckBox(str(value), menu)
            cb.setChecked(value in self.active_filter_values.get(key, set(values)))
            action = QWidgetAction(menu)
            action.setDefaultWidget(cb)
            menu.addAction(action)
            actions[value] = cb

        def update_select_all_state():
            all_checked = all(cb.isChecked() for cb in actions.values())
            select_all_widget.blockSignals(True)
            select_all_widget.setChecked(all_checked)
            select_all_widget.blockSignals(False)

        def update_filters():
            selected_values = [v for v, cb in actions.items() if cb.isChecked()]
            self.active_filter_values[key] = set(selected_values)
            self.proxyModel.set_filter(key, selected_values)
            update_select_all_state()

        for value, cb in actions.items():
            cb.toggled.connect(update_filters)

        def on_select_all_toggled(checked):
            for cb in actions.values():
                cb.blockSignals(True)
                cb.setChecked(checked)
                cb.blockSignals(False)
            update_filters()

        select_all_widget.toggled.connect(on_select_all_toggled)
        update_select_all_state()

        # Keep a reference to the menu to prevent garbage collection
        def on_menu_about_to_hide():
            self._current_menu = None
        menu.aboutToHide.connect(on_menu_about_to_hide)

        return menu
        
    def open_filter_popup(self, key):
        menu = self.filter_menus[key]
        button = self.filter_buttons[key]
        self._current_menu = menu
        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))
        
    def model(self):
        return self.proxyModel

# Simple test window with default data
def main():
    app = QApplication(sys.argv)
    string_list = ["Apple", "Banana", "Carrot", "Date", "Eggplant"]
    properties_list = [
        {"type": "Fruit", "color": "red"},
        {"type": "Fruit", "color": "yellow"},
        {"type": "Vegetable", "color": "orange"},
        {"type": "Fruit", "color": "orange"},
        {"type": "Vegetable", "color": "yellow"},
    ]
    filter_properties = {
        "type": ["Fruit", "Vegetable"],
        "organic": True  # just a placeholder, type is bool
    }
    model = StringPropertyListModel(string_list, properties_list)
    window = QWidget()
    layout = QVBoxLayout(window)
    filterable = FilterableComboBoxView(label_text="Select:", parent=window)
    filterable.setModel(model)
    layout.addWidget(filterable)
    window.setWindowTitle("Filterable ComboBox Test")
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

