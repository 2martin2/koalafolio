# -*- coding: utf-8 -*-
"""
Created on Wen Jan 02 14:21:00 2019

@author: Martin
"""

import koalafolio.PcpCore.logger as logger
from PyQt5.QtCore import QObject, Qt, pyqtSignal


class QLogger(QObject, logger.Logger):
    newLogMessage = pyqtSignal(str, str)

    def __init__(self):
        super(QLogger, self).__init__()

    def warning(self, message):
        super(QLogger, self).warning(message)
        warning = "## Warning: " + message + " !"
        self.newLogMessage.emit(warning, 'w')

    def error(self, message):
        super(QLogger, self).error(message)
        error = "### Error: " + message + " !!"
        self.newLogMessage.emit(error, 'e')

    def info(self, message):
        super(QLogger, self).info(message)
        info = "# Info: " + message
        self.newLogMessage.emit(info, 'i')

globalLogger = QLogger()

