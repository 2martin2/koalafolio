# -*- coding: utf-8 -*-
"""
Created on Wen Jan 02 14:21:00 2019

@author: Martin
"""

import koalafolio.PcpCore.logger as logger
import PyQt5.QtCore as qtcore

qt = qtcore.Qt


class QLogger(qtcore.QObject, logger.Logger):
    newLogMessage = qtcore.pyqtSignal(str, str)

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

