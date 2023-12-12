# -*- coding: utf-8 -*-
"""
Created on Sun Sep  15 15:15:19 2019

@author: Martin
"""
import koalafolio.gui.QLogger as logger
import koalafolio.web.exchanges as exchanges
import koalafolio.web.chaindata as chaindata
import pandas
from Cryptodome.Cipher import AES
import os
import hashlib
import json

localLogger = logger.globalLogger

# %% Trade
class ApiModel:
    def __init__(self, name='', apitype='', handle=None, note=''):
        self.apiName = name
        self.apiType = apitype
        self.apiHandle = handle
        self.apiNote = note


apiNames = ["binance", "bittrex", "bitmex", "coinbase", "coinbasepro", "gemini", "poloniex", "kraken", "Cardano"]
apiModels = {}

for key in apiNames:
    apiModels[key] = ApiModel(
        name=str(key),
        apitype="exchange",
        handle=None,
        note="get data from " + str(key) + ". "
    )

# add special api note for binance api
apiModels["binance"].apiNote = "get trades from binance. Can take very long due to stupid api implementation of binance"

# set type of Cardano api
apiModels["Cardano"].apiType = "chaindata"

for key in apiModels:
    if apiModels[key].apiType == "chaindata":
        apiModels[key].apiNote += "Koala provides default api key for blockdaemon api.\n" \
                                  "However it is recommended to create your own key for privacy reasons.\n" \
                                  "Key can be created at https://app.blockdaemon.com (Login->workspace->API Suite->Connect.\n" \
                                  "More Infos can be found in their documentation: https://docs.blockdaemon.com/"


apiModels["binance"].apiHandle = lambda apikey, secret, start, end: exchanges.getTradeHistoryBinance(apikey, secret, start, end)
apiModels["bittrex"].apiHandle = lambda apikey, secret, start, end: exchanges.getTradeHistoryBittrex(apikey, secret, start, end)
apiModels["bitmex"].apiHandle = lambda apikey, secret, start, end: exchanges.getTradeHistoryBitmex(apikey, secret, start, end)
apiModels["coinbase"].apiHandle = lambda apikey, secret, start, end: exchanges.getTradeHistoryCoinbase(apikey, secret, start, end)
apiModels["coinbasepro"].apiHandle = lambda apikey, secret, start, end: exchanges.getTradeHistoryCoinbasepro(apikey, secret, start, end)
apiModels["gemini"].apiHandle = lambda apikey, secret, start, end: exchanges.getTradeHistoryGemini(apikey, secret, start, end)
apiModels["poloniex"].apiHandle = lambda apikey, secret, start, end: exchanges.getTradeHistoryPoloniex(apikey, secret, start, end)
apiModels["kraken"].apiHandle = lambda apikey, secret, start, end: exchanges.getTradeHistoryKraken(apikey, secret, start, end)
apiModels["Cardano"].apiHandle = lambda apikey, address, start, end: chaindata.getCardanoRewardsForAddress(apikey, address, start, end)


def getApiHistory(apiname, apitype, start, end, apikey=None, secret=None, address=None):
    if apiname not in apiModels:
        raise KeyError("invalid api name")
    else:
        localLogger.info("requesting data from " + str(apiname))
        try:
            if apitype == "exchange":
                return apiModels[apiname].apiHandle(apikey, secret, start, end)
            elif apitype == "chaindata":
                return apiModels[apiname].apiHandle(apikey, address, int(start), int(end))
            else:
                raise ValueError("invalid type in getApiHistory: " + str(apitype))
        except Exception as ex:
            localLogger.warning("could not load data from api (" + str(apiname) + "): " + str(ex))
            return pandas.DataFrame()


class BaseDatabase():
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
        if os.path.exists(path):
            # set path
            self.filepath = os.path.join(path, self.filename).replace('\\', '/')
            if os.path.isfile(self.filepath):
                self.databaseFound = True
            else:
                self.databaseFound = False

    def encryptData(self, pw: str, data: dict) -> tuple[bytes, bytes, bytes]:
        dbkey = hashlib.sha256(pw.encode()).hexdigest()
        cipher = AES.new(dbkey[:32].encode('utf-8'), AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(json.dumps(data).encode("utf-8"))
        return cipher, ciphertext, tag

    def decryptData(self, pw: str, ciphertext: bytes, tag: bytes, nonce: bytes) -> dict:
        key = hashlib.sha256(pw.encode()).hexdigest()
        cipher = AES.new(key[:32].encode('utf-8'), AES.MODE_EAX, nonce)
        return json.loads(cipher.decrypt_and_verify(ciphertext, tag))

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

    def addDBEntry(self, pw: str, apiname: str, newData: str):
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
        os.remove(self.filepath)
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
            path = os.path.join(path, 'Import').replace('\\', '/')
            super(ApiDefaultDatabase, self).__init__(dbname='defaultApiData.db', path=path, loggingenabled=False)
            self.pw = "koala"

            # create
            # self.createDatabase(self.pw)
            # newKey = "somekey"
            # self.addDBEntry(self.pw, apiname="Cardano", newData=newKey)

            # read database
            self.readDatabase(self.pw)
            # print("defaultDBData: " + str(self.data))


