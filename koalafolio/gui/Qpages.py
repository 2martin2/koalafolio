# -*- coding: utf-8 -*-
"""
Created on Sun Sep 16 20:17:51 2018

@author: Martin
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt
import koalafolio.gui.QSettings as settings
import koalafolio.gui.SettingsPage as settingsPage
import koalafolio.gui.QLogger as logger
import webbrowser

localLogger = logger.globalLogger


# %% styled Page
class Page(QFrame):
    def __init__(self, parent, controller):
        super(Page, self).__init__(parent=parent)
        self.controller = controller
        self.setObjectName("QPage")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setContentsMargins(0, 0, 0, 10)
        self.setLineWidth(2)
        self.setMidLineWidth(3)


# sub page
class SubPage(Page):
    def __init__(self, parent, controller):
        super(SubPage, self).__init__(parent=parent, controller=controller)
        self.setObjectName("QSubPage")


# %% settings page
class SettingsPage(Page):
    def __init__(self, parent, controller):
        super(SettingsPage, self).__init__(parent=parent, controller=controller)

        self.vertLayout = QVBoxLayout(self)

        # path label
        self.appPathPreButton = QPushButton("app path: ")
        self.appPathPreButton.clicked.connect(lambda: webbrowser.open('file:///' + controller.appPath))
        self.appPathLabel = QLabel(controller.appPath)
        self.dataPathPreButton = QPushButton("data path: ")
        self.dataPathPreButton.clicked.connect(lambda: webbrowser.open('file:///' + controller.dataPath))
        self.dataPathLabel = QLabel(controller.dataPath)
        self.appPathLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.dataPathLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.appPathPreButton.setContentsMargins(10, 0, 0, 0)
        self.dataPathPreButton.setContentsMargins(10, 0, 0, 0)
        self.appPathLabel.setContentsMargins(0, 0, 10, 0)
        self.dataPathLabel.setContentsMargins(0, 0, 10, 0)

        self.repoButton = QPushButton("repo")
        self.repoButton.clicked.connect(lambda: webbrowser.open('https://gitea.com/2martin2/koalafolio'))

        self.labelLayout = QHBoxLayout()
        self.labelLayout.addWidget(self.appPathPreButton)
        self.labelLayout.addWidget(self.appPathLabel)
        self.labelLayout.addWidget(self.dataPathPreButton)
        self.labelLayout.addWidget(self.dataPathLabel)
        self.labelLayout.addWidget(self.repoButton)
        self.labelLayout.addStretch()
        self.vertLayout.addLayout(self.labelLayout)

        # content
        self.settingsView = settingsPage.SettingsTreeView(self)
        self.settingsView.setModel(self.controller.settingsModel)
        self.settingsView.expandAll()
        self.settingsView.setColumnWidth(0, 350)
        self.settingsView.header().setStretchLastSection(True)

        # buttons
        self.resetDefaultButton = QPushButton("reset to default", self)
        self.reloadButton = QPushButton("reload", self)
        self.saveButton = QPushButton("save", self)
        self.saveRefreshButton = QPushButton("save and reload", self)

        self.resetDefaultButton.clicked.connect(self.resetDefaultSettings)
        self.reloadButton.clicked.connect(self.reloadSettings)
        self.saveButton.clicked.connect(self.saveSettings)
        self.saveRefreshButton.clicked.connect(self.saveRefreshSettings)

        self.horzButtonLayout = QHBoxLayout()
        self.horzButtonLayout.addStretch()
        self.horzButtonLayout.addWidget(self.resetDefaultButton)
        self.horzButtonLayout.addWidget(self.reloadButton)
        self.horzButtonLayout.addWidget(self.saveButton)
        self.horzButtonLayout.addWidget(self.saveRefreshButton)
        self.horzButtonLayout.addStretch()

        self.vertLayout.addWidget(self.settingsView)
        # self.vertLayout.addStretch()
        self.vertLayout.addLayout(self.horzButtonLayout)

    def refresh(self):
        pass

    def resetDefaultSettings(self):
        self.controller.settingsModel.resetDefault()
        self.settingsView.expandAll()
        self.controller.reinit()

    def reloadSettings(self):
        self.controller.settingsModel.restoreSettings()
        self.controller.reinit()

    def saveSettings(self):
        settings.mySettings.saveSettings()

    def saveRefreshSettings(self):
        settings.mySettings.saveSettings()
        self.controller.reinit()
# %% functions
