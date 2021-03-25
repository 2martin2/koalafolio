# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 15:15:19 2018

@author: Martin
"""

# todo: check why default section is written to file ?!


import koalafolio.gui.QLogger as logger
import PyQt5.QtCore as qtcore
import koalafolio.PcpCore.settings as settings

qt = qtcore.Qt
localLogger = logger.globalLogger


class QSettings(settings.Settings):
    def __init__(self, *args, **kwargs):
        super(QSettings, self).__init__(*args, **kwargs)

    def initSettings(self):
        # set default settings

        # window settings
        self['window'] = {}
        self['window']['windowsize'] = '1400x600'
        self['window']['windowpos'] = '200,200'
        self['window']['windowstate'] = '0'
        self['window']['windowTitle'] = 'KoalaFolio'
        self['window']['windowstyle'] = 'Fusion'
        self['window']['stylesheetname'] = 'defaultStyle'
        # color settings
        self['color'] = {}
        self['color']['BACKGROUND'] = '42,46,51'
        self['color']['TEXT_NORMAL'] = '255,255,255'
        self['color']['TEXT_HIGHLIGHTED'] = '42,46,51'
        self['color']['PRIMARY'] = '75,180,255'
        self['color']['SECONDARY'] = '255,105,75'
        self['color']['TERTIARY'] = '75,255,240'
        self['color']['NEGATIV'] = '255,90,75'
        self['color']['POSITIV'] = '90,255,75'
        self['color']['NEUTRAL'] = '200,200,200'
        # gui settings
        self['gui'] = {}
        self['gui']['filterUseRegex'] = 'True'
        self['gui']['portfolioFilterRow'] = '3'
        self['gui']['tradeFilterRow'] = '2'
        self['gui']['portfolioFilterDir'] = (str(qt.DescendingOrder))
        self['gui']['tradeFilterDir'] = str(qt.AscendingOrder)
        self['gui']['toolTipsEnabled'] = 'True'
        self['gui']['performanceChartIndex'] = '0'
        self['gui']['tradesEditLock'] = 'True'
        self['gui']['hideLowBalanceCoins'] = 'True'
        self['gui']['hideLowValueCoins'] = 'False'
        self['gui']['lowValueFilterLimit(reportCurrency)'] = '50'
        self['gui']['loadPriceHistoryChart'] = 'False'

        super(QSettings, self).initSettings()

    def getWindowProperties(self):
        windowProperties = {}
        try:
            size = [int(s) for s in self['window']['windowsize'].split('x')]
            pos = [int(s) for s in self['window']['windowpos'].split(',')]
        except Exception as ex:
            localLogger.error('error parsing window geometry: ' + str(ex))
            localLogger.info('using default window geometry')
            size = [1200, 800]
            pos = [200, 200]
        windowProperties['geometry'] = qtcore.QRect(pos[0], pos[1], size[0], size[1])
        try:
            state = qt.WindowState(int(self['window']['windowstate']))
        except Exception as ex:
            localLogger.error('error parsing window state: ' + str(ex))
            localLogger.info('using default window state')
            state = qt.WindowNoState
        windowProperties['state'] = state
        return windowProperties

    def setWindowProperties(self, geometry, state):
        if state == qt.WindowNoState:  # only set window size if window is in normal state
            self['window']['windowpos'] = str(geometry.x()) + ',' + str(geometry.y())
            self['window']['windowSize'] = str(geometry.width()) + 'x' + str(geometry.height())
        self['window']['windowState'] = str(int(state))

    def getColors(self):
        def convertColor(colorStr, *default):
            try:
                color = colorStr.split(',')
                r = int(color[0])
                g = int(color[1])
                b = int(color[2])
                return r, g, b  # return tuple
            except Exception as ex:
                localLogger.warning('error parsing color ' + colorStr + ': ' + str(ex))
                localLogger.info('using default color')
                return default

        colorDict = {}
        for key in self['color']:
            if key == 'default':
                continue
            if key == 'TEXT_NORMAL':
                colorDict[key.upper()] = convertColor(self['color'][key], 0, 0, 0)
                continue
            colorDict[key.upper()] = convertColor(self['color'][key], 255, 255, 255)
        return colorDict

    def getColor(self, name):
        colors = self.getColors()
        if name in colors:
            return colors[name]
        else:
            return 255, 255, 255  # return white if invalid colorname

    def setColor(self, name, *value):
        for key in self['colors']:
            if key.lower() == name.lower():
                self['colors'][key] = str(value).replace('(', '').replace(')', '')

    def getGuiSettings(self):
        gui = {}
        try:
            gui['filterUseRegex'] = self.getboolean('gui', 'filterUseRegex')
        except ValueError:
            gui['filterUseRegex'] = True
        try:
            gui['portfolioFilterRow'] = self.getint('gui', 'portfolioFilterRow')
        except ValueError:
            gui['portfolioFilterRow'] = 3
        try:
            gui['tradeFilterRow'] = self.getint('gui', 'tradeFilterRow')
        except ValueError:
            gui['tradeFilterRow'] = 2
        try:
            gui['portfolioFilterDir'] = self.getint('gui', 'portfolioFilterDir')
        except ValueError:
            gui['portfolioFilterDir'] = qt.AscendingOrder
        try:
            gui['tradeFilterDir'] = self.getint('gui', 'tradeFilterDir')
        except ValueError:
            gui['tradeFilterDir'] = qt.AscendingOrder
        try:
            gui['toolTipsEnabled'] = self.getboolean('gui', 'toolTipsEnabled')
        except ValueError:
            gui['toolTipsEnabled'] = True
        try:
            gui['performanceChartIndex'] = self.getint('gui', 'performanceChartIndex')
        except ValueError:
            gui['performanceChartIndex'] = 0
        try:
            gui['tradesEditLock'] = self.getboolean('gui', 'tradesEditLock')
        except ValueError:
            gui['tradesEditLock'] = True
        try:
            gui['hideLowBalanceCoins'] = self.getboolean('gui', 'hideLowBalanceCoins')
        except ValueError:
            gui['hideLowBalanceCoins'] = True
        try:
            gui['hideLowValueCoins'] = self.getboolean('gui', 'hideLowValueCoins')
        except ValueError:
            gui['hideLowValueCoins'] = False
        try:
            gui['lowValueFilterLimit(reportCurrency)'] = self.getfloat('gui', 'lowValueFilterLimit(reportCurrency)')
        except ValueError:
            gui['lowValueFilterLimit(reportCurrency)'] = 50
        try:
            gui['loadPriceHistoryChart'] = self.getboolean('gui', 'loadPriceHistoryChart')
        except ValueError:
            gui['loadPriceHistoryChart'] = False
        return gui

    def getGuiSetting(self, key):
        return self.getGuiSettings()[key]

    def setGuiSettings(self, gui):
        for key in gui:
            if key in self['gui']:
                self['gui'][key] = str(gui[key])
            else:
                raise KeyError('invalid key ' + key + ' for gui settings')


mySettings = QSettings()
