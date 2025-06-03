#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QComboBox, QCompleter
from PyQt5.QtCore import QStringListModel, Qt, QEvent, QSortFilterProxyModel, QTimer


class StyledCompleter(QCompleter):
    # Class-level storage for all instances and shared style
    _instances = set()
    _shared_stylesheet = ""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.stylesheet = ""
        # Register instance
        StyledCompleter._instances.add(self)
        # Apply current shared style if exists
        if StyledCompleter._shared_stylesheet:
            self.setStylesheet(StyledCompleter._shared_stylesheet)
        self.stylePopup()

    def __del__(self):
        # Clean up instance registration
        StyledCompleter._instances.discard(self)

    @classmethod
    def updateAllStyles(cls, style):
        """Class method to update all instances with new style"""
        cls._shared_stylesheet = style
        for instance in cls._instances:
            instance.setStylesheet(style)

    def setStylesheet(self, style):
        self.stylesheet = style
        self.stylePopup()

    def stylePopup(self):
        # delegate = QStyledItemDelegate(self)
        popup = self.popup()
        # popup.setItemDelegate(delegate)
        popup.setObjectName("StyledCompleterPopup")  # Allows styling via QSS
        # popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # popup.setAutoFillBackground(False)
        popup.setStyleSheet(self.stylesheet)

    def setModel(self, model):
        super().setModel(model)
        self.stylePopup()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            try:
                self.parent().lineEdit().clear()
            except AttributeError:
                pass
        return super().eventFilter(obj, event)


class PrefixFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_text = ""

    def setFilterText(self, text):
        self._filter_text = text
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self._filter_text:
            return True
        index = self.sourceModel().index(source_row, 0, source_parent)
        data = self.sourceModel().data(index, Qt.DisplayRole)
        return data.lower().startswith(self._filter_text.lower())


class QCompleterComboBoxView(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)  # Prevent adding new items

        # Set up proxy filter model
        self.proxyModel = PrefixFilterProxyModel(self)

        # Set up completer
        completer = StyledCompleter(parent=self)
        completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # Case-insensitive matching
        completer.setModel(self.proxyModel)
        self.setCompleter(completer)

        # Connect text input changes and enter key press
        self.lineEdit().textEdited.connect(self._handle_text_edited)
        self.lineEdit().returnPressed.connect(self.select_first_completion)

        self.activated.connect(self._on_activated)
        self.currentIndexChanged.connect(self._on_current_index_changed)

    # def currentText(self):
    #     # call data with current index
    #     return self.model().data(self.model().index(self.currentIndex(), 0), Qt.DisplayRole)

    def _on_activated(self, index):
        # Get the display text from the model and set it to the line edit
        text = self.model().data(self.model().index(index, 0), Qt.DisplayRole)
        self.lineEdit().setText(text)

    def _on_current_index_changed(self, index):
        # Get the display text from the model and set it to the line edit
        text = self.model().data(self.model().index(index, 0), Qt.DisplayRole)
        self.lineEdit().setText(text)

    def addItem(self, text, userData = ...):
        # raise notImplemented
        raise NotImplementedError("Use setModel() to set a model with items.")

    def addItems(self, items):
        # raise notImplemented
        raise NotImplementedError("Use setModel() to set a model with items.")

    def setModel(self, model):
        super().setModel(model)
        self.proxyModel.setSourceModel(model)

    def _handle_text_edited(self, text):
        # Only show completer popup if user is actually typing
        if self.lineEdit().hasFocus():
            self.update_filter(text)
            # process completer after the event loop has processed the text change
            # self._show_completer()
            QTimer.singleShot(0, self._show_completer)

    def _show_completer(self):
        self.completer().complete()

    def update_filter(self, text: str):
        self.proxyModel.setFilterText(text)

    def getFirstCompletion(self):
        if self.proxyModel.rowCount() > 0:
            index = self.proxyModel.index(0, 0)
            return self.proxyModel.data(index, Qt.DisplayRole)
        return ""

    def select_first_completion(self):
        completer = self.completer()
        if not completer:
            return
        completerModel = completer.completionModel()
        if not completerModel or completerModel.rowCount() == 0:
            self.clearEditText()
            return
        index = completer.popup().currentIndex()
        if not index.isValid():
            index = completerModel.index(0, 0)
        if index.isValid():
            # Replace with suggestion
            data = completerModel.data(index, Qt.DisplayRole)
            QTimer.singleShot(0, lambda: self.setCurrentText(data))

    def showPopup(self):
        # update current index based on current text
        index = self.findText(self.lineEdit().text())
        if index < 0:
            index = self.findText(self.getFirstCompletion())
        if index >= 0:
            self.setCurrentIndex(index)
        super().showPopup()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        # try to set completer text if current text is not in model
        if self.findText(self.currentText()) == -1:
            self.select_first_completion()

# create a test window with the QCompleterComboBoxView and a dummy QStringListModel
# for testing and run it if this file is run directly
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
    from PyQt5.QtCore import QStringListModel

    app = QApplication([])

    window = QWidget()
    layout = QVBoxLayout(window)

    model = QStringListModel(["Apple", "Banana", "Cherry", "Date", "Fig", "Grape"])
    combo = QCompleterComboBoxView()
    combo.setModel(model)

    layout.addWidget(combo)
    window.setLayout(layout)
    window.show()

    app.exec_()

