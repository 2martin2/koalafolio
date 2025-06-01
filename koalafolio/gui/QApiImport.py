# -*- coding: utf-8 -*-
"""
Created on Wen Oct 01 15:36:21 2019

@author: Martin
"""

from PyQt5.QtWidgets import (
    QWidget, QStackedLayout, QLabel, QLineEdit, QPushButton, QGridLayout,
    QDateTimeEdit, QHBoxLayout, QVBoxLayout, QCheckBox, QComboBox
)
from PyQt5.QtCore import QStringListModel, QObject, pyqtSignal
import helper.QLogger as logger
import widgets.Qcontrols as controls
from koalafolio.gui.widgets.QFilterableComboBox import QFilterableComboBoxView, QStringPropertyListModel
from koalafolio.Import.apiImport import ApiImportStatic
from datetime import datetime

localLogger = logger.globalLogger


class ApiKeyModel(QObject):
    databaseUnlocked = pyqtSignal()
    databaseLocked = pyqtSignal()
    databaseWritten = pyqtSignal()
    databaseRemoved = pyqtSignal()

    def __init__(self, database, defaultdata, *args, **kwargs):
        super(ApiKeyModel, self).__init__(*args, **kwargs)

        self.database = database
        self.defaultApiKeys = defaultdata

        self.apiModels = ApiImportStatic.getApiModels()

        self.databaseApiNameModel = QStringPropertyListModel()
        self.databaseUnlocked.connect(self.loadDatabaseApiNames)
        self.databaseWritten.connect(self.loadDatabaseApiNames)


        self.apiSelectModel = QStringPropertyListModel()  # model for ComboBox
        self.refreshApiNames()
        self.addressSelectModels = {}
        self.initAddressSelectModels()
        self.refreshAddressSelectModels()

    def refreshApiNames(self):
        print("refreshing api names")
        # convert dict of apiModels to list of dicts
        apiModelsList = [self.apiModels[apiname].toDict() for apiname in self.apiModels]
        self.apiSelectModel.setDataFromDict(apiModelsList, string_key="apiName", properties_keys=["apiType"])

    def initAddressSelectModels(self):
        # add QStringListModel in addressSelectModels for each exchange api
        for apiname in self.apiModels:
            if self.apiModels[apiname].apiType == "chaindata":
                self.addressSelectModels[apiname] = QStringListModel()

    def refreshAddressSelectModels(self):
        # set default String List for addressSelectModels
        for apiname in self.addressSelectModels:
            self.addressSelectModels[apiname].setStringList(["All(0)"])

    def lockDatabase(self):
        self.database.lockDatabase()
        self.databaseLocked.emit()

    def unlockDatabase(self, pw):
        data = self.database.readDatabase(pw)
        if data is not None:
            self.databaseUnlocked.emit()

    def isDataBaseLocked(self) -> bool:
        return self.database.databaseLocked

    def createDatabase(self, pw: str):
        self.database.createDatabase(pw)
        self.databaseUnlocked.emit()

    def addDBEntry(self, pw: str, apiname: str, apikey: str = None, secret: str = None, addressList: list = []):
        apitype = self.getApiType(apiname)
        newData = {}
        newData["apiname"] = apiname
        if apitype == "exchange":
            newData["apikey"] = apikey
            newData["secret"] = secret
        elif apitype == "chaindata":
            newData["apikey"] = apikey
            newData["address"] = addressList
        self.database.addDBEntry(pw, apiname, newData)
        self.databaseWritten.emit()

    def deleteDBEntry(self, pw, apiname):
        self.database.deleteDBEntry(pw, apiname)
        self.databaseWritten.emit()

    def loadDatabaseApiNames(self):
        # convert database data to list of dicts with properties and ignore invalid apinames
        apiNamesList = [apiname for apiname in self.database.data if apiname in self.apiModels]
        apiNamesList = [{"apiname": apiname, "apitype": self.getApiType(apiname)} for apiname in apiNamesList]
        self.databaseApiNameModel.setDataFromDict(apiNamesList, string_key="apiname", properties_keys=["apitype"])

    def deleteDatabase(self):
        self.database.deleteDatabase()
        self.databaseRemoved.emit()

    def getApiKeyAndSecret(self, apiname: str) -> tuple[str, str]:
        if apiname in self.database.data:
            try:
                data = self.database.data[apiname]
                if data is not None:
                    return data["apikey"], data["secret"]
                else:
                    return "", ""
            except KeyError as ex:
                localLogger.error("api " + str(apiname) + " not part of database. ex: " + str(ex))
        return "", ""

    def getApiKeyAndAddressList(self, apiname) -> tuple[str, list]:
        if apiname in self.database.data:
            try:
                data = self.database.data[apiname]
                if data is not None:
                    addressList = data["address"]
                    # support old version where only single address as str was saved, convert to list
                    if isinstance(addressList, str):
                        addressList = [addressList]
                    return data["apikey"], addressList
            except KeyError as ex:
                localLogger.error("api " + str(apiname) + " not part of database. ex: " + str(ex))
        return "", []

    def getApiType(self, apiname):
        return self.apiModels[apiname].apiType

    def getApiNote(self, apiname):
        return self.apiModels[apiname].apiNote

    def getDefaultApikey(self, apiname):
        if apiname in self.defaultApiKeys:
            return self.defaultApiKeys[apiname]
        else:
            return ""

    def getAddressModel(self, apiname: str):
        return self.addressSelectModels[apiname]

    # append new Address to existing StringListModel for currently selected Api
    def addAddress(self, apiname: str, address: str):
        model: QStringListModel
        model = self.addressSelectModels[apiname]
        addressList = model.stringList()
        if not address:
            localLogger.warning("no valid address")
        elif address in addressList:
            localLogger.warning("address already present")
        else:  # address valid and not present
            # append new Address
            addressList.append(address)
            # update All Item
            addressList[0] = "All(" + str(model.rowCount()) + ")"
            # add new List to Model
            model.setStringList(addressList)

    # remove currently selected Address from StringListModel of currently selected Api
    def removeAddress(self, apiname: str, index: int):
        # don't remove default All Item
        if index > 0:
            model: QStringListModel
            model = self.addressSelectModels[apiname]
            model.removeRow(index)
            # update All Item
            addressList = model.stringList()
            addressList[0] = "All(" + str(model.rowCount() - 1) + ")"
            model.setStringList(addressList)


class ApiKeyView(QWidget):
    importFromApi = pyqtSignal([str, str, int, int, str, str, list])
    saveFromApi = pyqtSignal([str, str, int, int, str, str, list])

    def __init__(self, *args, **kwargs):
        super(ApiKeyView, self).__init__(*args, **kwargs)

        self.apiLabel = controls.Heading('API import', self)

        # stacked Layout for database UI (create new or open existing DB)
        self.stackedContentLayoutDB = QStackedLayout()
        self.stackedContentLayoutDB.addWidget(self.initNewDbUI())
        self.stackedContentLayoutDB.addWidget(self.initReadDbUI())

        # stacked Layout for api layout (switch exchange and chaindata UI)
        self.stackedContentLayoutApi = QStackedLayout()
        self.stackedContentLayoutApi.addWidget(self.initApiExchangeUI())
        self.stackedContentLayoutApi.addWidget(self.initApiChaindataUISelectAddress())
        self.stackedContentLayoutApi.addWidget(self.initApiChaindataUIAddAddress())

        self.databaseLocked()

        # start of direct api call UI
        self.directApiLabel = controls.SubHeading("enter api keys, always use read only keys for this application!!",
                                                  self.newDbFrame)

        self.directApiSelectLabel = QLabel("API: ", self)
        self.directApiSelectDropdown = QFilterableComboBoxView(parent=self)
        self.directApiSelectDropdown.currentTextChanged.connect(self.directApiSelectDropdownChanged)

        today = datetime.now()
        self.startDateLabel = QLabel('start: ', self)
        self.startDateInput = QDateTimeEdit(datetime(year=today.year - 1, month=1, day=1), self)
        self.endDateLabel = QLabel('end: ', self)
        self.endDateInput = QDateTimeEdit(today, self)
        self.keyLabel = QLabel('key: ', self)
        self.keyInput = QLineEdit(self)
        self.keyInput.setEchoMode(QLineEdit.Password)

        self.directApiGridLayout = QGridLayout()
        self.directApiGridLayout.addWidget(self.directApiSelectLabel, 0, 0)
        self.directApiGridLayout.addWidget(self.directApiSelectDropdown, 0, 1)
        self.directApiGridLayout.addWidget(self.startDateLabel, 1, 0)
        self.directApiGridLayout.addWidget(self.startDateInput, 1, 1)
        self.directApiGridLayout.addWidget(self.endDateLabel, 2, 0)
        self.directApiGridLayout.addWidget(self.endDateInput, 2, 1)
        self.directApiGridLayout.addWidget(self.keyLabel, 3, 0)
        self.directApiGridLayout.addWidget(self.keyInput, 3, 1)
        self.directApiGridLayout.setColumnStretch(1, 100)

        self.directApiNote = QLabel('select api from dropdown', self)
        self.directApiImportButton = QPushButton('import', self)
        self.directApiImportButton.clicked.connect(self.directImportFromApi)
        self.directApiSaveButton = QPushButton('save as csv', self)
        self.directApiSaveButton.clicked.connect(self.directSaveFromApi)

        self.directApiHorzButtonLayout = QHBoxLayout()
        self.directApiHorzButtonLayout.addStretch()
        self.directApiHorzButtonLayout.addWidget(self.directApiSaveButton)
        self.directApiHorzButtonLayout.addWidget(self.directApiImportButton)
        self.directApiHorzButtonLayout.addStretch()

        self.vLayout = QVBoxLayout(self)
        self.vLayout.addWidget(self.apiLabel)
        # add Stretch with fixed hight
        self.vLayout.addSpacing(10)
        self.vLayout.addLayout(self.stackedContentLayoutDB)
        self.vLayout.addSpacing(30)
        self.vLayout.addWidget(self.directApiLabel)
        self.vLayout.addLayout(self.directApiGridLayout)
        self.vLayout.addLayout(self.stackedContentLayoutApi)
        self.vLayout.addWidget(self.directApiNote)
        # add Stretch with high priority
        self.vLayout.addStretch(100)
        self.vLayout.addLayout(self.directApiHorzButtonLayout)

    # init UI for exchange api with key secret pair
    def initApiExchangeUI(self):
        self.apiExchangeFrame = controls.StyledFrame(self)

        self.secretLabel = QLabel('secret: ', self.apiExchangeFrame)
        self.secretInput = QLineEdit(self.apiExchangeFrame)
        self.secretInput.setEchoMode(QLineEdit.Password)

        self.apiExchangeGridLayout = QGridLayout(self.apiExchangeFrame)
        self.apiExchangeGridLayout.addWidget(self.secretLabel, 0, 0)
        self.apiExchangeGridLayout.addWidget(self.secretInput, 0, 1)

        return self.apiExchangeFrame

    # init UI for Chaindata UI with apikey and address
    def initApiChaindataUISelectAddress(self):
        self.apiChaindataFrameSelectAddress = controls.StyledFrame(self)

        self.addressLabel = QLabel('address: ', self.apiChaindataFrameSelectAddress)
        self.addressSelectDropdown = QComboBox(self.apiChaindataFrameSelectAddress)

        self.addressInputAddButton = QPushButton('+', self.apiChaindataFrameSelectAddress)
        self.addressInputAddButton.clicked.connect(self.addChainAddress)
        self.addressInputRemoveButton = QPushButton('-', self.apiChaindataFrameSelectAddress)
        self.addressInputRemoveButton.clicked.connect(self.removeChainAddress)

        self.apiChaindataGridLayoutSelectAddress = QGridLayout(self.apiChaindataFrameSelectAddress)
        self.apiChaindataGridLayoutSelectAddress.addWidget(self.addressLabel, 0, 0)
        self.apiChaindataGridLayoutSelectAddress.addWidget(self.addressSelectDropdown, 0, 1)
        self.apiChaindataGridLayoutSelectAddress.addWidget(self.addressInputAddButton, 0, 2)
        self.apiChaindataGridLayoutSelectAddress.addWidget(self.addressInputRemoveButton, 0, 3)
        self.apiChaindataGridLayoutSelectAddress.setColumnStretch(1, 100)

        return self.apiChaindataFrameSelectAddress

    def initApiChaindataUIAddAddress(self):
        self.apiChaindataFrameAddAddress = controls.StyledFrame(self)

        self.addressLabelNewAddress = QLabel('address: ', self.apiChaindataFrameAddAddress)
        self.addressInputNewAddress = QLineEdit(self.apiChaindataFrameAddAddress)

        self.addressInputFinishButton = QPushButton(chr(10003), self.apiChaindataFrameAddAddress)
        self.addressInputFinishButton.clicked.connect(self.saveNewChainAddress)
        self.addressInputCancelButton = QPushButton('x', self.apiChaindataFrameAddAddress)
        self.addressInputCancelButton.clicked.connect(self.cancelNewChainAddress)

        self.apiChaindataGridLayoutAddAddress = QGridLayout(self.apiChaindataFrameAddAddress)
        self.apiChaindataGridLayoutAddAddress.addWidget(self.addressLabelNewAddress, 0, 0)
        self.apiChaindataGridLayoutAddAddress.addWidget(self.addressInputNewAddress, 0, 1)
        self.apiChaindataGridLayoutAddAddress.addWidget(self.addressInputFinishButton, 0, 2)
        self.apiChaindataGridLayoutAddAddress.addWidget(self.addressInputCancelButton, 0, 3)
        self.apiChaindataGridLayoutAddAddress.setColumnStretch(1, 100)

        return self.apiChaindataFrameAddAddress

    def initNewDbUI(self):
        self.newDbFrame = controls.StyledFrame(self)

        # create new db
        self.newDbLabel = controls.SubHeading("create a new password to store the api keys encrypted on disk")

        self.newKeyLabel = QLabel("new password: ", self.newDbFrame)
        self.newKeyLabel2 = QLabel("repeat password: ", self.newDbFrame)

        self.newKeyEdit = QLineEdit(self.newDbFrame)
        self.newKeyEdit.setEchoMode(QLineEdit.Password)
        self.newKeyEdit.returnPressed.connect(self.createNewDb)
        self.newKeyEdit2 = QLineEdit(self.newDbFrame)
        self.newKeyEdit2.setEchoMode(QLineEdit.Password)
        self.newKeyEdit2.returnPressed.connect(self.createNewDb)

        self.createButton = QPushButton("create", self.newDbFrame)
        self.clearButton = QPushButton("clear", self.newDbFrame)
        self.createButton.clicked.connect(self.createNewDb)
        self.clearButton.clicked.connect(self.clearNewKeys)

        self.newDbGridLayout = QGridLayout()
        self.newDbGridLayout.addWidget(self.newKeyLabel, 0, 0)
        self.newDbGridLayout.addWidget(self.newKeyEdit, 0, 1)
        self.newDbGridLayout.addWidget(self.newKeyLabel2, 1, 0)
        self.newDbGridLayout.addWidget(self.newKeyEdit2, 1, 1)

        self.newDbButtonLayout = QHBoxLayout()
        self.newDbButtonLayout.addStretch()
        self.newDbButtonLayout.addWidget(self.createButton)
        self.newDbButtonLayout.addWidget(self.clearButton)
        self.newDbButtonLayout.addStretch()

        self.newDbVLayout = QVBoxLayout(self.newDbFrame)
        self.newDbVLayout.addWidget(self.newDbLabel)
        self.newDbVLayout.addLayout(self.newDbGridLayout)
        self.newDbVLayout.addLayout(self.newDbButtonLayout)
        self.newDbVLayout.addStretch()

        # return base frame
        return self.newDbFrame

    def initReadDbUI(self):
        # api import
        self.apiFrame = controls.StyledFrame(self)

        self.pwLabel = QLabel('password: ', self.apiFrame)
        self.pwInput = QLineEdit(self.apiFrame)
        self.pwInput.setEchoMode(QLineEdit.Password)
        self.pwInput.returnPressed.connect(self.unlockDb)

        self.pwLayout = QGridLayout()
        self.pwLayout.addWidget(self.pwLabel, 0, 0)
        self.pwLayout.addWidget(self.pwInput, 0, 1)

        self.unlockDbButton = QPushButton("unlock db", self.apiFrame)
        self.unlockDbButton.clicked.connect(self.unlockDb)
        self.lockDbButton = QPushButton("lock db", self.apiFrame)
        self.lockDbButton.clicked.connect(self.lockDb)
        self.deleteDbButton = QPushButton("delete db", self.apiFrame)
        self.deleteDbButton.clicked.connect(self.deleteDatabase)
        self.deleteDbButton.setDisabled(True)
        self.deleteDbButtonEnableBox = QCheckBox(self.apiFrame)
        self.deleteDbButtonEnableBox.stateChanged.connect(self.deleteDbButtonEnableBoxChanged)
        self.deleteDbButtonEnableBox.setChecked(False)

        self.dbButtonLayout = QHBoxLayout()
        self.dbButtonLayout.addStretch()
        self.dbButtonLayout.addWidget(self.unlockDbButton)
        self.dbButtonLayout.addWidget(self.lockDbButton)
        self.dbButtonLayout.addWidget(self.deleteDbButton)
        self.dbButtonLayout.addWidget(self.deleteDbButtonEnableBox)
        self.dbButtonLayout.addStretch()

        self.lockedStateLabel = QLabel("database is locked", self.apiFrame)

        self.lockedStateLayout = QHBoxLayout()
        self.lockedStateLayout.addStretch()
        self.lockedStateLayout.addWidget(self.lockedStateLabel)
        self.lockedStateLayout.addStretch()

        self.apiSelectLabel = QLabel("API: ", self.apiFrame)
        self.apiSelectDropdown = QFilterableComboBoxView(parent=self.apiFrame)

        self.apiGridLayout = QGridLayout()
        self.apiGridLayout.addWidget(self.apiSelectLabel, 0, 0)
        self.apiGridLayout.addWidget(self.apiSelectDropdown, 0, 1)
        self.apiGridLayout.setColumnStretch(1, 1)

        self.loadApiEntryButton = QPushButton("load api", self.apiFrame)
        self.loadApiEntryButton.clicked.connect(self.loadApiEntry)
        self.saveApiEntryButton = QPushButton("save api", self.apiFrame)
        self.saveApiEntryButton.clicked.connect(self.saveApiEntry)
        self.deleteDBEntryButton = QPushButton("delete api", self.apiFrame)
        self.deleteDBEntryButton.clicked.connect(self.deleteDBEntry)

        self.dbButtonLayout2 = QHBoxLayout()
        self.dbButtonLayout2.addStretch()
        self.dbButtonLayout2.addWidget(self.loadApiEntryButton)
        self.dbButtonLayout2.addWidget(self.saveApiEntryButton)
        self.dbButtonLayout2.addWidget(self.deleteDBEntryButton)
        self.dbButtonLayout2.addStretch()

        # layout
        self.apiLayout = QVBoxLayout(self.apiFrame)
        self.apiLayout.addStretch()
        self.apiLayout.addLayout(self.pwLayout)
        self.apiLayout.addLayout(self.dbButtonLayout)
        self.apiLayout.addLayout(self.lockedStateLayout)
        self.apiLayout.addLayout(self.apiGridLayout)
        self.apiLayout.addLayout(self.dbButtonLayout2)
        self.apiLayout.addStretch()

        return self.apiFrame

    def setModel(self, model: ApiKeyModel):
        self.model = model
        # connect signals
        model.databaseUnlocked.connect(self.databaseUnlocked)
        model.databaseLocked.connect(self.databaseLocked)
        model.databaseWritten.connect(self.databaseWritten)
        model.databaseRemoved.connect(self.databaseRemoved)
        # set dropdown models
        self.apiSelectDropdown.setModel(model=model.databaseApiNameModel)
        self.directApiSelectDropdown.setModel(model=model.apiSelectModel)

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
        self.apiSelectDropdown.setEnabled(True)
        self.lockedStateLabel.setText("database is unlocked")

    def databaseLocked(self):
        self.lockDbButton.setDisabled(True)
        self.saveApiEntryButton.setDisabled(True)
        self.loadApiEntryButton.setDisabled(True)
        self.deleteDBEntryButton.setDisabled(True)
        self.pwInput.setEnabled(True)
        self.unlockDbButton.setEnabled(True)
        self.apiSelectDropdown.setDisabled(True)
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
        apiname, apitype, addressIndex, addressList, apikey, apisecret = self.prepareApiData()
        self.importFromApi.emit(apiname,
                                apitype,
                                self.startDateInput.dateTime().toSecsSinceEpoch(),
                                self.endDateInput.dateTime().toSecsSinceEpoch(),
                                apikey,
                                apisecret,
                                addressList)

    def directSaveFromApi(self):
        apiname, apitype, addressIndex, addressList, apikey, apisecret = self.prepareApiData()
        self.saveFromApi.emit(apiname,
                              apitype,
                              self.startDateInput.dateTime().toSecsSinceEpoch(),
                              self.endDateInput.dateTime().toSecsSinceEpoch(),
                              apikey,
                              apisecret,
                              addressList)

    def prepareApiData(self):
        apiname = self.directApiSelectDropdown.currentText()
        apitype = self.model.getApiType(apiname)
        addressIndex = self.addressSelectDropdown.currentIndex()
        addressList = []
        apikey = self.keyInput.text()
        apisecret = self.secretInput.text()
        if apitype == "chaindata":
            if not apikey:
                apikey = self.model.getDefaultApikey("blockdaemon")
            if addressIndex == 0:
                addressList = self.addressSelectDropdown.model().stringList()[1:]
            else:
                addressList = [self.addressSelectDropdown.currentText()]
        return apiname, apitype, addressIndex, addressList, apikey, apisecret

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
        apiname = apiname.lower()
        if not apiname in self.model.apiModels:
            localLogger.warning("invalid apiname in db apiname: " + str(apiname))
            return
        apitype = self.model.getApiType(apiname)
        if apitype == "exchange":
            apikey, secret = self.model.getApiKeyAndSecret(apiname)
        elif apitype == "chaindata":
            apikey, addressList = self.model.getApiKeyAndAddressList(apiname)
        # get index from directApiSelectDropdown
        index = self.directApiSelectDropdown.findText(apiname)
        self.directApiSelectDropdown.setCurrentIndex(index)
        if apitype == "exchange":
            self.keyInput.setText(apikey)
            self.secretInput.setText(secret)
        elif apitype == "chaindata":
            self.keyInput.setText(apikey)
            addressModel: QStringListModel
            addressModel = self.model.getAddressModel(apiname)
            addressList = ["All(" + str(len(addressList)) + ")"] + addressList
            addressModel.setStringList(addressList)

    def saveApiEntry(self):
        apiname = self.directApiSelectDropdown.currentText()
        apitype = self.model.getApiType(apiname)
        if apitype == "exchange":
            apikey = self.keyInput.text()
            secret = self.secretInput.text()
            if apikey and secret:
                self.model.addDBEntry(self.pwInput.text(), apiname, apikey=apikey, secret=secret)
        elif apitype == "chaindata":
            apikey = self.keyInput.text()
            addressModel: QStringListModel
            addressModel = self.model.getAddressModel(apiname)
            addressList = addressModel.stringList()
            # remove All Item
            addressList.pop(0)
            self.model.addDBEntry(self.pwInput.text(), apiname, apikey=apikey, addressList=addressList)

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
        # check if api from dropdown exists in model, else ignore
        apiname = self.directApiSelectDropdown.currentText()
        if apiname in self.model.apiModels:
            # remove previous Input from InputBoxes
            self.addressInputNewAddress.clear()
            self.keyInput.clear()
            self.secretInput.clear()
            # update note
            self.directApiNote.setText(self.model.getApiNote(apiname))
            # update Api UI depending on selected Api Type
            apitype = self.model.getApiType(apiname)
            if apitype == "exchange":
                self.stackedContentLayoutApi.setCurrentIndex(0)
                if not self.model.isDataBaseLocked():
                    apikey, secret = self.model.getApiKeyAndSecret(apiname)
                    self.keyInput.setText(apikey)
                    self.secretInput.setText(secret)
            elif apitype == "chaindata":
                self.stackedContentLayoutApi.setCurrentIndex(1)
                self.addressSelectDropdown.setModel(self.model.getAddressModel(apiname))
                self.addressSelectDropdown.setCurrentIndex(0)
                if not self.model.isDataBaseLocked():
                    apikey, addressList = self.model.getApiKeyAndAddressList(apiname)
                    if apikey:
                        self.keyInput.setText(apikey)
                    for address in addressList:
                        self.model.addAddress(apiname, address)

    def addChainAddress(self):
        # switch to AddressAddUI
        self.stackedContentLayoutApi.setCurrentIndex(2)
        self.addressInputNewAddress.clear()

    def removeChainAddress(self):
        # remove selected Address from ComboBoxModel
        apiname = self.directApiSelectDropdown.currentText()
        index = self.addressSelectDropdown.currentIndex()
        self.model.removeAddress(apiname, index)
        self.addressSelectDropdown.setCurrentIndex(0)

    def saveNewChainAddress(self):
        # add new Address to ComboBoxModel
        apiname = self.directApiSelectDropdown.currentText()
        address = self.addressInputNewAddress.text()
        self.model.addAddress(apiname, address)
        self.addressSelectDropdown.setCurrentIndex(self.addressSelectDropdown.count() - 1)
        # switch to AddressSelectUI
        self.stackedContentLayoutApi.setCurrentIndex(1)

    def cancelNewChainAddress(self):
        # switch to AddressSelectUI
        self.stackedContentLayoutApi.setCurrentIndex(1)
