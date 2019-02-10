# -*- coding: utf-8 -*-
"""
Created on Wen Jan 02 14:21:00 2019

@author: Martin
"""

import shutil
import os.path


class Logger():
    def __init__(self):
        self.filePath = None
        self.logFile = None

    def warning(self, message):
        warning = "## Warning: " + message + " !"
        print(warning)
        self.printToFile(warning)

    def error(self, message):
        error = "### Error: " + message + " !!"
        print(error)
        self.printToFile("!!--------------------------!!---------------------------!!")
        self.printToFile(error)
        self.printToFile("!!--------------------------!!---------------------------!!")

    def info(self, message):
        info = "# Info: " + message
        print(info)
        self.printToFile(info)

    def setPath(self, dir):
        self.filePath = os.path.join(dir, 'logfile.txt')
        self.backupLogFile()
        # self.openLogFile()
        self.info('Start of Logging')
        return self

    def printToFile(self, message):
        # if self.logFile:
        try:
            with open(self.filePath, 'a') as logFile:
                logFile.write(message)
                logFile.write('\n')
                # logFile.close()
        except Exception as ex:
            print('error in logger: ' + str(ex))

    def backupLogFile(self):
        if os.path.isfile(self.filePath):
            try:
                shutil.copy(self.filePath, self.filePath + '.bak')
                logFile = open(self.filePath, 'w')
                logFile.close()
            except Exception as ex:
                print('error in logger: ' + str(ex))


globalLogger = Logger()
