# -*- coding: utf-8 -*-
"""
Created on Sun Sep  15 15:15:19 2019

@author: Martin
"""
import koalafolio.gui.QLogger as logger
import koalafolio.web.krakenApi as krakenApi
import pandas
from Cryptodome.Cipher import AES
import os
import hashlib
import json

localLogger = logger.globalLogger

apiNames = ["kraken"]
apiHandle = {}
apiHandle["kraken"] = lambda key, secret: krakenApi.getTradeHistory(key, secret)

def getApiHistory(apiname, key, secret):
    if apiname not in apiNames:
        raise KeyError("invalid api name")
    else:
        try:
            return apiHandle[apiname](key, secret)
        except Exception as ex:
            localLogger.warning("could not load data from api " + str(apiname) + "): " + str(ex))
            return pandas.DataFrame()

# database
class ApiDatabase():
    def __init__(self, path=None):

        self.databaseFound = False
        self.data = None
        self.filename = "key.db"
        if path:
            self.setPath(path)

    def setPath(self, path):
        # check path
        if os.path.exists(path):
            # set path
            self.filepath = os.path.join(path, self.filename)
            if os.path.isfile(self.filepath):
                self.databaseFound = True
            else:
                self.databaseFound = False

    def encryptData(self, pw, data):
        key = hashlib.sha256(pw.encode()).hexdigest()
        cipher = AES.new(key[:32].encode('utf-8'), AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(json.dumps(data).encode("utf-8"))
        return cipher, ciphertext, tag

    def decryptData(self, pw, ciphertext, tag, nonce):
        key = hashlib.sha256(pw.encode()).hexdigest()
        cipher = AES.new(key[:32].encode('utf-8'), AES.MODE_EAX, nonce)
        return json.loads(cipher.decrypt_and_verify(ciphertext, tag)) # data

    def checkPw(self, pw):
        with open(self.filepath, "rb") as file_in:
            nonce, tag, ciphertext = [file_in.read(x) for x in (16, 16, -1)]
        try:
            self.decryptData(pw, ciphertext, tag, nonce)
            return True
        except ValueError:
            return False

    def readDatabase(self, pw):
        with open(self.filepath, "rb") as file_in:
            nonce, tag, ciphertext = [file_in.read(x) for x in (16, 16, -1)]
        try:
            self.data = self.decryptData(pw, ciphertext, tag, nonce)
            localLogger.info("api database loaded")
            return self.data
        except ValueError:
            localLogger.warning("decrypting api database failed, check password")
            return None

    def saveDatabase(self, pw):
        if self.checkPw(pw):
            cipher, ciphertext, tag = self.encryptData(pw, self.data)
            with open(self.filepath, "wb") as file_out:
                [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]
        else:
            localLogger.warning("invalid password")

    def addKeys(self, pw, apiname, apikey, secret):
        if not self.checkPw(pw):
            localLogger.warning("invalid password")
            return
        newData = {}
        newData["apiname"] = apiname
        newData["apikey"] = apikey
        newData["secret"] = secret
        if self.data is not None:
            self.data[apiname] = newData
            self.saveDatabase(pw)
        else:
            localLogger.warning("api database need be be unlocked before it can be changed")

    def deleteKeys(self, pw, apiname):
        if not self.checkPw(pw):
            localLogger.warning("invalid password")
            return
        if self.data is not None:
            if apiname in self.data:
                self.data.pop(apiname)
                self.saveDatabase(pw)
        else:
            localLogger.warning("api database need be be unlocked before it can be changed")

    def createDatabase(self, pw):
        if self.databaseFound:
            localLogger.warning("database already created, please delete the old database to create a new one.")
        else:
            self.data = {}
            cipher, ciphertext, tag = self.encryptData(pw, self.data)
            with open(self.filepath, "wb") as file_out:
                [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]
            self.databaseFound = True
            localLogger.info("api database created")

    def lockDatabase(self):
        self.data = None

    def deleteDatabase(self):
        self.lockDatabase()
        os.remove(self.filepath)
        self.databaseFound = 0


