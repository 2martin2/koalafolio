# -*- coding: utf-8 -*-
"""
Created on Sun Sep  15 15:15:19 2019

@author: Martin
"""
from koalafolio.web.exchanges import ExchangesStatic
from koalafolio.web.chaindata import ChaindataStatic
from koalafolio.gui.helper.QLogger import globalLogger
from pandas import DataFrame
from Cryptodome.Cipher import AES
from os import remove as os_remove
from os.path import exists as os_exists, join as os_join, isfile
from hashlib import sha256
from json import dumps as json_dumps, loads as json_loads
from Cryptodome.Cipher._mode_eax import EaxMode

localLogger = globalLogger


# static class for static data
class ApiImportStatic:
    SUPPORTED_APIS = ExchangesStatic.SUPPORTED_EXCHANGES + ChaindataStatic.SUPPORTED_CHAINS
    @staticmethod
    def getApiHistory(apiname, apitype, start, end, apikey=None, secret=None, address=None):
        if apiname not in ApiImportStatic.SUPPORTED_APIS:
            raise KeyError("invalid api name")
        else:
            localLogger.info("requesting data from " + str(apiname))
            try:
                if apitype == "exchange":
                    return ExchangesStatic.getTradeHistoryCcxt(apiname, apikey, secret, start, end)
                elif apitype == "chaindata":
                    return ChaindataStatic.getBlockdaemonRewardsForAddress(apiname, apikey, address, start, end)
                else:
                    raise ValueError("invalid type in getApiHistory: " + str(apitype))
            except Exception as ex:
                localLogger.warning("could not load data from api (" + str(apiname) + "): " + str(ex))
                return DataFrame()

    # get dict of ApiModels
    @staticmethod
    def getApiModels():
        apiModels = {}
        for apiname in ExchangesStatic.SUPPORTED_EXCHANGES:
            apiModels[apiname] = ApiModel(
                name=str(apiname),
                apitype="exchange",
                note="get data from " + str(apiname) + ". "
            )
        for apiname in ChaindataStatic.SUPPORTED_CHAINS:  # apitype is blockdaemon chaindata
            apiModels[apiname] = ApiModel(
                name=str(apiname),
                apitype="chaindata",
                note="Koala provides default api key for blockdaemon api.\n" \
                     "However it is recommended to create your own key.\n" \
                     "Key can be created at https://app.blockdaemon.com (Login->workspace->API Suite->Connect.\n" \
                     "More Infos can be found in their documentation: https://docs.blockdaemon.com/"
            )
        return apiModels


# %% Trade
class ApiModel:
    def __init__(self, name='', apitype='', note=''):
        self.apiName = name
        self.apiType = apitype
        self.apiNote = note

    def toDict(self):
        return {
            "apiName": self.apiName,
            "apiType": self.apiType,
            "apiNote": self.apiNote
        }


class BaseDatabase:
    def __init__(self, dbname: str, path: str=None, loggingenabled: bool=False):

        self.databaseFound = False
        self.databaseLocked = True
        self.data = None
        self.filepath = None
        self.filename = dbname
        self.loggingEnabled = loggingenabled
        if path:
            self.setPath(path)

    def logWarning(self, msg: str):
        if self.loggingEnabled:
            localLogger.warning(msg)

    def logInfo(self, msg: str):
        if self.loggingEnabled:
            localLogger.info(msg)

    def logError(self, msg: str):
        if self.loggingEnabled:
            localLogger.error(msg)

    def setPath(self, path: str):
        # check path
        if os_exists(path):
            # set path
            self.filepath = os_join(path, self.filename).replace('\\', '/')
            if isfile(self.filepath):
                self.databaseFound = True
            else:
                self.databaseFound = False

    def encryptData(self, pw: str, data: dict) -> tuple[EaxMode, bytes, bytes]:
        dbkey = sha256(pw.encode()).hexdigest()
        cipher = AES.new(dbkey[:32].encode('utf-8'), AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(json_dumps(data).encode("utf-8"))
        return cipher, ciphertext, tag

    def decryptData(self, pw: str, ciphertext: bytes, tag: bytes, nonce: bytes) -> dict:
        key = sha256(pw.encode()).hexdigest()
        cipher = AES.new(key[:32].encode('utf-8'), AES.MODE_EAX, nonce)
        return json_loads(cipher.decrypt_and_verify(ciphertext, tag))

    def checkPw(self, pw: str) -> bool:
        with open(self.filepath, "rb") as file_in:
            nonce, tag, ciphertext = [file_in.read(x) for x in (16, 16, -1)]
        try:
            self.decryptData(pw, ciphertext, tag, nonce)
            return True
        except ValueError:
            return False

    def readDatabase(self, pw: str) -> dict:
        with open(self.filepath, "rb") as file_in:
            nonce, tag, ciphertext = [file_in.read(x) for x in (16, 16, -1)]
        try:
            self.data = self.decryptData(pw, ciphertext, tag, nonce)
            self.databaseLocked = False
            self.logInfo("api database loaded")
            return self.data
        except ValueError:
            self.logWarning("decrypting api database failed, check password")
            return None

    def saveDatabase(self, pw: str):
        if self.checkPw(pw):
            cipher, ciphertext, tag = self.encryptData(pw, self.data)
            with open(self.filepath, "wb") as file_out:
                [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]
        else:
            self.logWarning("invalid password")

    def addDBEntry(self, pw: str, apiname: str, newData: dict):
        if not self.checkPw(pw):
            self.logWarning("invalid password")
            return
        if self.data is not None:
            self.data[apiname] = newData
            self.saveDatabase(pw)
        else:
            self.logWarning("api database need be be unlocked before it can be changed")

    def deleteDBEntry(self, pw: str, apiname: str):
        if not self.checkPw(pw):
            self.logWarning("invalid password")
            return
        if self.data is not None:
            if apiname in self.data:
                self.data.pop(apiname)
                self.saveDatabase(pw)
        else:
            self.logWarning("api database need be be unlocked before it can be changed")

    def createDatabase(self, pw: str):
        if self.databaseFound:
            self.logWarning("database already created, please delete the old database to create a new one.")
        else:
            self.data = {}
            cipher, ciphertext, tag = self.encryptData(pw, self.data)
            with open(self.filepath, "wb") as file_out:
                [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]
            self.databaseFound = True
            self.databaseLocked = False
            self.logInfo("api database created")

    def lockDatabase(self):
        self.data = None
        self.databaseLocked = True

    def deleteDatabase(self):
        self.lockDatabase()
        os_remove(self.filepath)
        self.databaseFound = 0


# database for user data. Will be created on user request
class ApiUserDatabase(BaseDatabase):
    def __init__(self, path: str=None):
        super(ApiUserDatabase, self).__init__(dbname='key.db', path=path, loggingenabled=True)


# database for default data. Will be uploaded to github and stores default data like default api keys
# api keys are created from koala specific account, users can create their own keys later
# encrypt data so it can not be parsed so easily from repo.
# all data in this default db is potentially exposed so no critical data will be stored here
class ApiDefaultDatabase(BaseDatabase):
    def __init__(self, path: str=None):
        if path:
            super(ApiDefaultDatabase, self).__init__(dbname='defaultApiData.db', path=path, loggingenabled=False)
            self.pw = "koala"

            # create
            # self.createDatabase(self.pw)
            # newKey = "some_key"
            # self.addDBEntry(self.pw, apiname="blockdaemon", newData=newKey)

            # read database
            self.readDatabase(self.pw)
            # print("defaultDBData: " + str(self.data))


