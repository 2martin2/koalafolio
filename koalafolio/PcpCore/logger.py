# -*- coding: utf-8 -*-
"""
Created on Wen Jan 02 14:21:00 2019

@author: Martin
"""

import shutil
import os.path


class Logger:
    def __init__(self):
        self.filePath = None
        # self.logFile = None

        self.debugMode = False
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

    def debug(self, message):
        if self.debugMode:
            debug = "# Debug: " + message
            print(debug)
            self.printToFile(debug)

    def setPath(self, dir):
        self.filePath = os.path.join(dir, 'logfile.txt')
        self.backupLogFile()
        self.info('Start of Logging')
        return self

    def printToFile(self, message):
        if self.filePath:
            try:
                with open(self.filePath, 'a') as logFile:
                    logFile.write(message)
                    logFile.write('\n')
                    # logFile.close()
            except Exception as ex:
                print('error in Logger.printToFile: ' + str(ex))

    def backupLogFile(self):
        if os.path.isfile(self.filePath):
            try:
                shutil.copy(self.filePath, self.filePath + '.bak')
            except Exception as ex:  # copy not possible/ skip bakup creation
                print('backup of logfile could not be created: ' + str(ex))
        # try to write logfile ( exceptions will be handled in gui_root
        logFile = open(self.filePath, 'w')
        logFile.close()



globalLogger = Logger()
