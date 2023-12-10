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
        self.databaseUnlocked.connect(self.loadDatabaseApiNames)
        self.databaseWritten.connect(self.loadDatabaseApiNames)

        self.apiSelectModel = qtcore.QStringListModel()
        self.refreshApiNames()

        self.apiModels = apiImport.apiModels

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

    def addDBEntry(self, pw, apiname, key=None, secret=None, address=None):
        apitype = self.getApiType(apiname)
        newData = {}
        newData["apiname"] = apiname
        if apitype == "exchange":
            newData["apikey"] = key
            newData["secret"] = secret
        elif apitype == "chaindata":
            newData["address"] = address
        self.database.addDBEntry(pw, apiname, newData)
        self.databaseWritten.emit()

    def deleteDBEntry(self, pw, apiname):
        self.database.deleteDBEntry(pw, apiname)
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
            localLogger.error("api " + str(apiname) + " not part of database: " + str(ex))
            return None, None

    def getApiAddress(self, apiname):
        try:
            data = self.database.data[apiname]
            if data is not None:
                return data["address"]
            else:
                return None
        except KeyError as ex:
            localLogger.error("api " + str(apiname) + " not part of database: " + str(ex))
            return None

    def getApiType(self, apiname):
        return self.apiModels[apiname].apiType

    def getApiNote(self, apiname):
        return self.apiModels[apiname].apiNote


class ApiKeyView(qtwidgets.QWidget):
    importFromApi = qtcore.pyqtSignal([str, str, int, int, str, str, str])
    saveFromApi = qtcore.pyqtSignal([str, str, int, int, str, str, str])

    def __init__(self, *args, **kwargs):
        super(ApiKeyView, self).__init__(*args, **kwargs)

        self.apiLabel = controls.Heading('API import', self)

        # stacked Layout for database UI (create new or open existing DB)
        self.stackedContentLayoutDB = qtwidgets.QStackedLayout()
        self.stackedContentLayoutDB.addWidget(self.initNewDbUI())
        self.stackedContentLayoutDB.addWidget(self.initReadDbUI())

        # stacked Layout for api layout (switch exchange and chaindata UI)
        self.stackedContentLayoutApi = qtwidgets.QStackedLayout()
        self.stackedContentLayoutApi.addWidget(self.initApiExchangeUI())
        self.stackedContentLayoutApi.addWidget(self.initApiChaindataUI())

        self.databaseLocked()

        # start of direct api call UI
        self.directApiLabel = controls.SubHeading("enter api keys, always use read only keys for this application!!",
                                                  self.newDbFrame)

        self.directApiSelectLabel = qtwidgets.QLabel("API: ", self)
        self.directApiSelectDropdown = qtwidgets.QComboBox(self)
        self.directApiSelectDropdown.currentTextChanged.connect(self.directApiSelectDropdownChanged)

        today = datetime.datetime.now()
        self.startDateLabel = qtwidgets.QLabel('start: ', self)
        self.startDateInput = qtwidgets.QDateTimeEdit(datetime.datetime(year=today.year - 1, month=1, day=1), self)
        self.endDateLabel = qtwidgets.QLabel('end: ', self)
        self.endDateInput = qtwidgets.QDateTimeEdit(today, self)

        self.directApiGridLayout = qtwidgets.QGridLayout()
        self.directApiGridLayout.addWidget(self.directApiSelectLabel, 0, 0)
        self.directApiGridLayout.addWidget(self.directApiSelectDropdown, 0, 1)
        self.directApiGridLayout.addWidget(self.startDateLabel, 1, 0)
        self.directApiGridLayout.addWidget(self.startDateInput, 1, 1)
        self.directApiGridLayout.addWidget(self.endDateLabel, 2, 0)
        self.directApiGridLayout.addWidget(self.endDateInput, 2, 1)
        self.directApiGridLayout.setColumnStretch(1, 100)

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
        self.vLayout.addStretch()
        self.vLayout.addLayout(self.stackedContentLayoutDB)
        self.vLayout.addStretch()
        self.vLayout.addWidget(self.directApiLabel)
        self.vLayout.addLayout(self.directApiGridLayout)
        self.vLayout.addLayout(self.stackedContentLayoutApi)
        self.vLayout.addWidget(self.directApiNote)
        self.vLayout.addStretch()
        self.vLayout.addLayout(self.directApiHorzButtonLayout)

    # init UI for axchange api with key secret pair
    def initApiExchangeUI(self):
        self.apiExchangeFrame = controls.StyledFrame(self)

        self.keyLabel = qtwidgets.QLabel('key: ', self.apiExchangeFrame)
        self.keyInput = qtwidgets.QLineEdit(self.apiExchangeFrame)
        self.keyInput.setEchoMode(qtwidgets.QLineEdit.Password)
        self.secretLabel = qtwidgets.QLabel('secret: ', self.apiExchangeFrame)
        self.secretInput = qtwidgets.QLineEdit(self.apiExchangeFrame)
        self.secretInput.setEchoMode(qtwidgets.QLineEdit.Password)

        self.apiExchangeGridLayout = qtwidgets.QGridLayout(self.apiExchangeFrame)
        self.apiExchangeGridLayout.addWidget(self.keyLabel, 0, 0)
        self.apiExchangeGridLayout.addWidget(self.keyInput, 0, 1)
        self.apiExchangeGridLayout.addWidget(self.secretLabel, 1, 0)
        self.apiExchangeGridLayout.addWidget(self.secretInput, 1, 1)

        return self.apiExchangeFrame

    # init UI for Chaindata UI with address
    def initApiChaindataUI(self):
        self.apiChaindataFrame = controls.StyledFrame(self)

        self.addressLabel = qtwidgets.QLabel('address: ', self.apiChaindataFrame)
        self.addressInput = qtwidgets.QLineEdit(self.apiChaindataFrame)

        self.apiChaindataGridLayout = qtwidgets.QGridLayout(self.apiChaindataFrame)
        self.apiChaindataGridLayout.addWidget(self.addressLabel, 0, 0)
        self.apiChaindataGridLayout.addWidget(self.addressInput, 0, 1)

        return self.apiChaindataFrame

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

        self.loadApiEntryButton = qtwidgets.QPushButton("load api", self.apiFrame)
        self.loadApiEntryButton.clicked.connect(self.loadApiEntry)
        self.saveApiEntryButton = qtwidgets.QPushButton("save api", self.apiFrame)
        self.saveApiEntryButton.clicked.connect(self.saveApiEntry)
        self.deleteDBEntryButton = qtwidgets.QPushButton("delete api", self.apiFrame)
        self.deleteDBEntryButton.clicked.connect(self.deleteDBEntry)

        self.dbButtonLayout2 = qtwidgets.QHBoxLayout()
        self.dbButtonLayout2.addStretch()
        self.dbButtonLayout2.addWidget(self.loadApiEntryButton)
        self.dbButtonLayout2.addWidget(self.saveApiEntryButton)
        self.dbButtonLayout2.addWidget(self.deleteDBEntryButton)
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
            self.stackedContentLayoutDB.setCurrentIndex(1)
        else:
            self.stackedContentLayoutDB.setCurrentIndex(0)

    def databaseUnlocked(self):
        self.stackedContentLayoutDB.setCurrentIndex(1)

        self.pwInput.setDisabled(True)
        self.unlockDbButton.setDisabled(True)
        self.lockDbButton.setEnabled(True)
        self.saveApiEntryButton.setEnabled(True)
        self.loadApiEntryButton.setEnabled(True)
        self.deleteDBEntryButton.setEnabled(True)
        self.apiSelectDropdown.setCurrentIndex(0)
        self.lockedStateLabel.setText("database is unlocked")

    def databaseLocked(self):
        self.lockDbButton.setDisabled(True)
        self.saveApiEntryButton.setDisabled(True)
        self.loadApiEntryButton.setDisabled(True)
        self.deleteDBEntryButton.setDisabled(True)
        self.pwInput.setEnabled(True)
        self.unlockDbButton.setEnabled(True)
        self.lockedStateLabel.setText("database is locked")

    def databaseWritten(self):
        self.apiSelectDropdown.setCurrentIndex(0)

    def databaseRemoved(self):
        self.stackedContentLayoutDB.setCurrentIndex(0)
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
        apiname = self.directApiSelectDropdown.currentText()
        self.importFromApi.emit(apiname,
                                self.model.getApiType(apiname),
                                self.startDateInput.dateTime().toSecsSinceEpoch(),
                                self.endDateInput.dateTime().toSecsSinceEpoch(),
                                self.keyInput.text(),
                                self.secretInput.text(),
                                self.addressInput.text())

    def directSaveFromApi(self):
        apiname = self.directApiSelectDropdown.currentText()
        self.saveFromApi.emit(apiname,
                              self.model.getApiType(apiname),
                              self.startDateInput.dateTime().toSecsSinceEpoch(),
                              self.endDateInput.dateTime().toSecsSinceEpoch(),
                              self.keyInput.text(),
                              self.secretInput.text(),
                              self.addressInput.text())

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

    def loadApiEntry(self):
        apiname = self.apiSelectDropdown.currentText()
        apitype = self.model.getApiType(apiname)
        if apitype == "exchange":
            key, secret = self.model.getApiKeys(apiname)
        elif apitype == "chaindata":
            address = self.model.getApiAddress(apiname)
        try:
            index = self.directApiSelectDropdown.model().stringList().index(apiname)
        except ValueError:
            pass
        else:
            self.directApiSelectDropdown.setCurrentIndex(index)
            if apitype == "exchange":
                self.keyInput.setText(key)
                self.secretInput.setText(secret)
            elif apitype == "chaindata":
                self.addressInput.setText(address)

    def saveApiEntry(self):
        apiname = self.directApiSelectDropdown.currentText()
        apitype = self.model.getApiType(apiname)
        if apitype == "exchange":
            key = self.keyInput.text()
            secret = self.secretInput.text()
            if key and secret:
                self.model.addDBEntry(self.pwInput.text(), apiname, key=key, secret=secret)
        elif apitype == "chaindata":
            address = self.addressInput.text()
            if address:
                self.model.addDBEntry(self.pwInput.text(), apiname, address=address)

    def deleteDBEntry(self):
        apiname = self.apiSelectDropdown.currentText()
        self.model.deleteDBEntry(self.pwInput.text(), apiname)

    def deleteDbButtonEnableBoxChanged(self, state):
        if state:
            self.deleteDbButton.setEnabled(True)
        else:
            self.deleteDbButton.setDisabled(True)

    # callback if selected Api is changed
    def directApiSelectDropdownChanged(self):
        # remove previous Input from InputBoxes
        self.addressInput.clear()
        self.keyInput.clear()
        self.secretInput.clear()
        # update note
        self.directApiNote.setText(self.model.getApiNote(self.directApiSelectDropdown.currentText()))
        # update Api UI depending on selected Api Type
        type = self.model.getApiType(self.directApiSelectDropdown.currentText())
        if type == "exchange":
            self.stackedContentLayoutApi.setCurrentIndex(0)
        elif type == "chaindata":
            self.stackedContentLayoutApi.setCurrentIndex(1)
