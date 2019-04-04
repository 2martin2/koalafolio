# -*- coding: utf-8 -*-
"""
Created on Thu Apr 04 09:57:14 2019

@author: Martin
"""

import gui_root
import PcpCore.logger
import gui.QLogger as logger
import PcpCore.settings
import gui.QSettings as settings
import sys
import PyQt5.QtWidgets as qtwidgets

def main():
    PcpCore.logger.globalLogger = logger.globalLogger
    PcpCore.settings.mySettings = settings.mySettings
    app = qtwidgets.QApplication(sys.argv)
    #    app.setStyle(qtwidgets.QStyleFactory.create('Fusion'))
    window = gui_root.PortfolioApp()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()