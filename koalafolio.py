# -*- coding: utf-8 -*-
"""
Created on Sun Sep 16 09:57:14 2018

@author: Martin
"""

import gui_root
import PcpCore.logger
import gui.QLogger as logger
import PcpCore.settings
import gui.QSettings as settings
import sys
import PyQt5.QtWidgets as qtwidgets

if __name__ == '__main__':
    PcpCore.logger.globalLogger = logger.globalLogger
    PcpCore.settings.mySettings = settings.mySettings
    app = qtwidgets.QApplication(sys.argv)
    #    app.setStyle(qtwidgets.QStyleFactory.create('Fusion'))
    window = gui_root.PortfolioApp()

    sys.exit(app.exec_())