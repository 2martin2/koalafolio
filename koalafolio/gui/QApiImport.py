# -*- coding: utf-8 -*-
"""
Created on Wen Oct 01 15:36:21 2019

@author: Martin
"""

import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import koalafolio.gui.QLogger as logger
import koalafolio.gui.QSettings as settings
import koalafolio.gui.Qcontrols as controls
import koalafolio.Import.apiImport as apiImport
import datetime

localLogger = logger.globalLogger

qt = qtcore.Qt


class ApiKeyModel(qtcore.QObject):
    databaseUnlocked = qtcore.pyqtSignal()
    databaseLocked = qtcore.pyqtSignal()
    databaseWritten = qtcore.pyqtSignal()
    databaseRemoved = qtcore.pyqtSignal()

    def __init__(self, database, *args, **kwargs):
        super(ApiKeyModel, self).__init__(*args, **kwargs)

        self.database = database
        self.databaseApiNameModel = qtcore.QStringListModel()

        self.databaseApiNameModel = qtcore.QStringListModel()
        self.databaseUnlocked.connect(self.loadDatabaseApiNames)
        self.databaseWritten.connect(self.loadDatabaseApiNames)

        self.apiSelectModel = qtcore.QStringListModel()
        self.refreshApiNames()

    def refreshApiNames(self):
        self.apiSelectModel.setStringList(apiImport.apiNames)

    def lockDatabase(self):
        self.database.lockDatabase()
        self.databaseLocked.emit()

    def unlockDatabase(self, pw):
        data = self.database.readDatabase(pw)
        if data is not None:
            self.databaseUnlocked.emit()

    def createDatabase(self, pw):
        self.database.createDatabase(pw)
        self.databaseUnlocked.emit()

    def addKeys(self, pw, apiname, key, secret):
        self.database.addKeys(pw, apiname, key, secret)
        self.databaseWritten.emit()

    def deleteKeys(self, pw, apiname):
        self.database.deleteKeys(pw, apiname)
        self.databaseWritten.emit()

    def loadDatabaseApiNames(self):
        self.databaseApiNameModel.setStringList(list(self.database.data))

    def deleteDatabase(self):
        self.database.deleteDatabase()
        self.databaseRemoved.emit()

    def getApiKeys(self, apiname):
        try:
            data = self.database.data[apiname]
            if data is not None:
                return data["apikey"], data["secret"]
            else:
                return None, None
        except KeyError as ex:
            localLogger.error("api not supported: " + str(ex))
            return None, None

class ApiKeyView(qtwidgets.QWidget):
    importFromApi = qtcore.pyqtSignal([str, str, str, int, int])
    saveFromApi = qtcore.pyqtSignal([str, str, str, int, int])

    def __init__(self, *args, **kwargs):
        super(ApiKeyView, self).__init__(*args, **kwargs)

        self.apiLabel = controls.Heading('API import', self)

        frame1 = self.initNewDbUI()
        frame2 = self.initReadDbUI()

        self.stackedContentLayout = qtwidgets.QStackedLayout()
        self.stackedContentLayout.addWidget(frame1)
        self.stackedContentLayout.addWidget(frame2)

        self.databaseLocked()

        # direct api call
        self.directApiLabel = controls.SubHeading("enter api keys, always use read only keys for this application!!", self.newDbFrame)

        self.directApiSelectLabel = qtwidgets.QLabel("API: ", self)
        self.directApiSelectDropdown = qtwidgets.QComboBox(self)
        self.directApiSelectDropdown.currentTextChanged.connect(self.updateExchangeNote)
        self.keyLabel = qtwidgets.QLabel('key: ', self)
        self.keyInput = qtwidgets.QLineEdit(self)
        self.keyInput.setEchoMode(qtwidgets.QLineEdit.Password)
        self.secretLabel = qtwidgets.QLabel('secret: ', self)
        self.secretInput = qtwidgets.QLineEdit(self)
        self.secretInput.setEchoMode(qtwidgets.QLineEdit.Password)
        today = datetime.datetime.now()
        self.startDateLabel = qtwidgets.QLabel('start: ', self)
        self.startDateInput = qtwidgets.QDateTimeEdit(datetime.datetime(year=today.year-1, month=1, day=1), self)
        self.endDateLabel = qtwidgets.QLabel('end: ', self)
        self.endDateInput = qtwidgets.QDateTimeEdit(today, self)

        self.directApiGridLayout = qtwidgets.QGridLayout()
        self.directApiGridLayout.addWidget(self.directApiSelectLabel, 0, 0)
        self.directApiGridLayout.addWidget(self.directApiSelectDropdown, 0, 1)
        self.directApiGridLayout.addWidget(self.keyLabel, 1, 0)
        self.directApiGridLayout.addWidget(self.keyInput, 1, 1)
        self.directApiGridLayout.addWidget(self.secretLabel, 2, 0)
        self.directApiGridLayout.addWidget(self.secretInput, 2, 1)
        self.directApiGridLayout.addWidget(self.startDateLabel, 3, 0)
        self.directApiGridLayout.addWidget(self.startDateInput, 3, 1)
        self.directApiGridLayout.addWidget(self.endDateLabel, 4, 0)
        self.directApiGridLayout.addWidget(self.endDateInput, 4, 1)

        self.directApiNote = qtwidgets.QLabel('select api from dropdown', self)
        self.directApiImportButton = qtwidgets.QPushButton('import', self)
        self.directApiImportButton.clicked.connect(self.directImportFromApi)
        self.directApiSaveButton = qtwidgets.QPushButton('save as csv', self)
        self.directApiSaveButton.clicked.connect(self.directSaveFromApi)


        self.directApiHorzButtonLayout = qtwidgets.QHBoxLayout()
        self.directApiHorzButtonLayout.addStretch()
        self.directApiHorzButtonLayout.addWidget(self.directApiSaveButton)
        self.directApiHorzButtonLayout.addWidget(self.directApiImportButton)
        self.directApiHorzButtonLayout.addStretch()

        self.vLayout = qtwidgets.QVBoxLayout(self)
        self.vLayout.addWidget(self.apiLabel)
        self.vLayout.addLayout(self.stackedContentLayout)
        self.vLayout.addWidget(self.directApiLabel)
        self.vLayout.addLayout(self.directApiGridLayout)
        self.vLayout.addWidget(self.directApiNote)
        self.vLayout.addLayout(self.directApiHorzButtonLayout)


    def initNewDbUI(self):
        self.newDbFrame = controls.StyledFrame(self)

        # create new db
        self.newDbLabel = controls.SubHeading("create a new password to store the api keys encrypted on disk")

        self.newKeyLabel = qtwidgets.QLabel("new password: ", self.newDbFrame)
        self.newKeyLabel2 = qtwidgets.QLabel("repeat password: ", self.newDbFrame)

        self.newKeyEdit = qtwidgets.QLineEdit(self.newDbFrame)
        self.newKeyEdit.setEchoMode(qtwidgets.QLineEdit.Password)
        self.newKeyEdit.returnPressed.connect(self.createNewDb)
        self.newKeyEdit2 = qtwidgets.QLineEdit(self.newDbFrame)
        self.newKeyEdit2.setEchoMode(qtwidgets.QLineEdit.Password)
        self.newKeyEdit2.returnPressed.connect(self.createNewDb)

        self.createButton = qtwidgets.QPushButton("create", self.newDbFrame)
        self.clearButton = qtwidgets.QPushButton("clear", self.newDbFrame)
        self.createButton.clicked.connect(self.createNewDb)
        self.clearButton.clicked.connect(self.clearNewKeys)

        self.newDbGridLayout = qtwidgets.QGridLayout()
        self.newDbGridLayout.addWidget(self.newKeyLabel, 0, 0)
        self.newDbGridLayout.addWidget(self.newKeyEdit, 0, 1)
        self.newDbGridLayout.addWidget(self.newKeyLabel2, 1, 0)
        self.newDbGridLayout.addWidget(self.newKeyEdit2, 1, 1)

        self.newDbButtonLayout = qtwidgets.QHBoxLayout()
        self.newDbButtonLayout.addStretch()
        self.newDbButtonLayout.addWidget(self.createButton)
        self.newDbButtonLayout.addWidget(self.clearButton)
        self.newDbButtonLayout.addStretch()

        self.newDbVLayout = qtwidgets.QVBoxLayout(self.newDbFrame)
        self.newDbVLayout.addWidget(self.newDbLabel)
        self.newDbVLayout.addLayout(self.newDbGridLayout)
        self.newDbVLayout.addLayout(self.newDbButtonLayout)
        self.newDbVLayout.addStretch()

        # return base frame
        return self.newDbFrame

    def initReadDbUI(self):
        # api import
        self.apiFrame = controls.StyledFrame(self)

        self.pwLabel = qtwidgets.QLabel('password: ', self.apiFrame)
        self.pwInput = qtwidgets.QLineEdit(self.apiFrame)
        self.pwInput.setEchoMode(qtwidgets.QLineEdit.Password)
        self.pwInput.returnPressed.connect(self.unlockDb)

        self.pwLayout = qtwidgets.QGridLayout()
        self.pwLayout.addWidget(self.pwLabel, 0, 0)
        self.pwLayout.addWidget(self.pwInput, 0, 1)

        self.unlockDbButton = qtwidgets.QPushButton("unlock db", self.apiFrame)
        self.unlockDbButton.clicked.connect(self.unlockDb)
        self.lockDbButton = qtwidgets.QPushButton("lock db", self.apiFrame)
        self.lockDbButton.clicked.connect(self.lockDb)
        self.deleteDbButton = qtwidgets.QPushButton("delete db", self.apiFrame)
        self.deleteDbButton.clicked.connect(self.deleteDatabase)
        self.deleteDbButton.setDisabled(True)
        self.deleteDbButtonEnableBox = qtwidgets.QCheckBox(self.apiFrame)
        self.deleteDbButtonEnableBox.stateChanged.connect(self.deleteDbButtonEnableBoxChanged)
        self.deleteDbButtonEnableBox.setChecked(False)

        self.dbButtonLayout = qtwidgets.QHBoxLayout()
        self.dbButtonLayout.addStretch()
        self.dbButtonLayout.addWidget(self.unlockDbButton)
        self.dbButtonLayout.addWidget(self.lockDbButton)
        self.dbButtonLayout.addWidget(self.deleteDbButton)
        self.dbButtonLayout.addWidget(self.deleteDbButtonEnableBox)
        self.dbButtonLayout.addStretch()

        self.lockedStateLabel = qtwidgets.QLabel("database is locked", self.apiFrame)

        self.lockedStateLayout = qtwidgets.QHBoxLayout()
        self.lockedStateLayout.addStretch()
        self.lockedStateLayout.addWidget(self.lockedStateLabel)
        self.lockedStateLayout.addStretch()

        self.apiSelectLabel = qtwidgets.QLabel("API: ", self.apiFrame)
        self.apiSelectDropdown = qtwidgets.QComboBox(self.apiFrame)

        self.apiGridLayout = qtwidgets.QGridLayout()
        self.apiGridLayout.addWidget(self.apiSelectLabel, 0, 0)
        self.apiGridLayout.addWidget(self.apiSelectDropdown, 0, 1)
        self.apiGridLayout.setColumnStretch(1, 1)

        self.loadKeysButton = qtwidgets.QPushButton("load keys", self.apiFrame)
        self.loadKeysButton.clicked.connect(self.loadKeys)
        self.saveKeysButton = qtwidgets.QPushButton("save keys", self.apiFrame)
        self.saveKeysButton.clicked.connect(self.saveKeys)
        self.deleteKeysButton = qtwidgets.QPushButton("delete keys", self.apiFrame)
        self.deleteKeysButton.clicked.connect(self.deleteKeys)

        self.dbButtonLayout2 = qtwidgets.QHBoxLayout()
        self.dbButtonLayout2.addStretch()
        self.dbButtonLayout2.addWidget(self.loadKeysButton)
        self.dbButtonLayout2.addWidget(self.saveKeysButton)
        self.dbButtonLayout2.addWidget(self.deleteKeysButton)
        self.dbButtonLayout2.addStretch()

        # layout
        self.apiLayout = qtwidgets.QVBoxLayout(self.apiFrame)
        self.apiLayout.addStretch()
        self.apiLayout.addLayout(self.pwLayout)
        self.apiLayout.addLayout(self.dbButtonLayout)
        self.apiLayout.addLayout(self.lockedStateLayout)
        self.apiLayout.addLayout(self.apiGridLayout)
        self.apiLayout.addLayout(self.dbButtonLayout2)
        self.apiLayout.addStretch()

        return self.apiFrame

    def setModel(self, model):
        self.model = model
        # connect signals
        model.databaseUnlocked.connect(self.databaseUnlocked)
        model.databaseLocked.connect(self.databaseLocked)
        model.databaseWritten.connect(self.databaseWritten)
        model.databaseRemoved.connect(self.databaseRemoved)
        # set dropdown models
        self.apiSelectDropdown.setModel(model.databaseApiNameModel)
        self.directApiSelectDropdown.setModel(model.apiSelectModel)
        self.directApiSelectDropdown.setCurrentIndex(0)
        # set model
        if self.model.database.databaseFound:
            self.stackedContentLayout.setCurrentIndex(1)
        else:
            self.stackedContentLayout.setCurrentIndex(0)

    def databaseUnlocked(self):
        self.stackedContentLayout.setCurrentIndex(1)

        self.pwInput.setDisabled(True)
        self.unlockDbButton.setDisabled(True)
        self.lockDbButton.setEnabled(True)
        self.saveKeysButton.setEnabled(True)
        self.loadKeysButton.setEnabled(True)
        self.deleteKeysButton.setEnabled(True)
        self.apiSelectDropdown.setCurrentIndex(0)
        self.lockedStateLabel.setText("database is unlocked")

    def databaseLocked(self):
        self.lockDbButton.setDisabled(True)
        self.saveKeysButton.setDisabled(True)
        self.loadKeysButton.setDisabled(True)
        self.deleteKeysButton.setDisabled(True)
        self.pwInput.setEnabled(True)
        self.unlockDbButton.setEnabled(True)
        self.lockedStateLabel.setText("database is locked")

    def databaseWritten(self):
        self.apiSelectDropdown.setCurrentIndex(0)

    def databaseRemoved(self):
        self.stackedContentLayout.setCurrentIndex(0)
        self.databaseLocked()
        self.pwInput.clear()

    def clearNewKeys(self):
        self.newKeyEdit.clear()
        self.newKeyEdit2.clear()

    def createNewDb(self):
        if self.newKeyEdit.text() != self.newKeyEdit2.text():
            localLogger.warning("entered passwords are not identical")
        elif len(self.newKeyEdit.text()) < 1:
            localLogger.warning("please enter a new password")
        else:
            pw = self.newKeyEdit.text()
            self.newKeyEdit.clear()
            self.newKeyEdit2.clear()
            self.pwInput.setText(pw)
            self.model.createDatabase(pw)

    def directImportFromApi(self):
        self.importFromApi.emit(self.directApiSelectDropdown.currentText(), self.keyInput.text(),
                                self.secretInput.text(),
                                self.startDateInput.dateTime().toSecsSinceEpoch(),
                                self.endDateInput.dateTime().toSecsSinceEpoch())

    def directSaveFromApi(self):
        self.saveFromApi.emit(self.directApiSelectDropdown.currentText(), self.keyInput.text(),
                              self.secretInput.text(),
                              self.startDateInput.dateTime().toSecsSinceEpoch(),
                              self.endDateInput.dateTime().toSecsSinceEpoch())

    def unlockDb(self):
        pw = self.pwInput.text()
        self.model.unlockDatabase(pw)

    def lockDb(self):
        self.pwInput.clear()
        self.keyInput.clear()
        self.secretInput.clear()
        self.apiSelectDropdown.clear()
        self.model.lockDatabase()

    def deleteDatabase(self):
        self.deleteDbButton.setDisabled(True)
        self.deleteDbButtonEnableBox.setCheckState(False)
        self.model.deleteDatabase()

    def loadKeys(self):
        apiname = self.apiSelectDropdown.currentText()
        key, secret = self.model.getApiKeys(apiname)
        if not key is None:
            try:
                index = self.directApiSelectDropdown.model().stringList().index(apiname)
            except ValueError:
                pass
            else:
                self.directApiSelectDropdown.setCurrentIndex(index)
                self.keyInput.setText(key)
                self.secretInput.setText(secret)

    def saveKeys(self):
        apiname = self.directApiSelectDropdown.currentText()
        key = self.keyInput.text()
        secret = self.secretInput.text()
        if key and secret:
            self.model.addKeys(self.pwInput.text(), apiname, key, secret)

    def deleteKeys(self):
        apiname = self.apiSelectDropdown.currentText()
        self.model.deleteKeys(self.pwInput.text(), apiname)

    def deleteDbButtonEnableBoxChanged(self, state):
        if state:
            self.deleteDbButton.setEnabled(True)
        else:
            self.deleteDbButton.setDisabled(True)

    def updateExchangeNote(self):
        self.directApiNote.setText(apiImport.apiNotes[self.directApiSelectDropdown.currentText()])
