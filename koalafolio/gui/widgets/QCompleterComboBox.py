#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QComboBox, QCompleter
from PyQt5.QtCore import QStringListModel, Qt, QEvent


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


class QCompleterComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)  # Prevent adding new items

        self.original_items = []

        # Set up completer
        completer = StyledCompleter(parent=self)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # Case-insensitive matching
        self.setCompleter(completer)

        # Initialize model
        self.completerModel = QStringListModel()
        self.completer().setModel(self.completerModel)

        # Connect text input changes and enter key press
        self.lineEdit().textEdited.connect(self._handle_text_edited)
        self.lineEdit().returnPressed.connect(self.select_first_completion)

    def setModel(self, model):
        super().setModel(model)
        model.modelReset.connect(self.update_original_items)
        self.update_original_items()

    def update_original_items(self):
        self.original_items = self.model().stringList()
        # self.completerModel.setStringList(self.original_items)
        self.update_filter(self.lineEdit().text())

    def _handle_text_edited(self, text):
        if self.lineEdit().hasFocus():
            self.update_filter(text)
            # Only show completer popup if user is actually typing
            self.completer().complete()

    def update_filter(self, text: str):
        """Filter items strictly by prefix match"""
        filtered_items = [item for item in self.original_items if item.lower().startswith(text.lower())]
        # Update completer's model
        self.completerModel.setStringList(filtered_items)

    def getFirstCompletion(self):
        """ Get the first completion item """
        current_suggestions = self.completerModel.stringList()
        if current_suggestions:
            return current_suggestions[0]
        return ""

    def select_first_completion(self):
        completer = self.completer()
        if not completer:
            return
        # Get the completer's model
        completerModel = completer.completionModel()
        if not completerModel or completerModel.rowCount() == 0:
            self.clearEditText()
            return
        # get the index of the current selection of the completer popup
        index = completer.popup().currentIndex()
        # check if index is valid
        if not index.isValid():
            # if not, get the first item in the list
            index = completerModel.index(0, 0)
        if index.isValid():
            # Replace with suggestion
            self.setCurrentText(completerModel.data(index, Qt.DisplayRole))

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
        if self.lineEdit().text() not in self.original_items:
            self.select_first_completion()

