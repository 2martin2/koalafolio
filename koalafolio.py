# -*- coding: utf-8 -*-
"""
Created on Thu Apr 04 09:57:14 2019

@author: Martin
"""

import koalafolio.gui_root
import koalafolio.PcpCore.logger
import koalafolio.gui.QLogger as logger
import koalafolio.PcpCore.settings
import koalafolio.gui.QSettings as settings
import sys
import PyQt5.QtWidgets as qtwidgets
import os

# %% variables
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    running_mode = 'Frozen/executable'
else:
    try:
        app_full_path = os.path.realpath(__file__)
        application_path = os.path.dirname(app_full_path)
        running_mode = "Non-interactive"
    except NameError:
        application_path = os.getcwd()
        running_mode = 'Interactive'

def main():
    koalafolio.PcpCore.logger.globalLogger = logger.globalLogger
    koalafolio.PcpCore.settings.mySettings = settings.mySettings
    app = qtwidgets.QApplication(sys.argv)
    #    app.setStyle(qtwidgets.QStyleFactory.create('Fusion'))
    window = koalafolio.gui_root.PortfolioApp()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()