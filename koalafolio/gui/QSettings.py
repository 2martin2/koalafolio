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
        self['window']['windowtitle'] = 'KoalaFolio'
        self['window']['windowstyle'] = 'Fusion'
        self['window']['stylesheetname'] = 'defaultStyle'
        # color settings
        self['color'] = {}
        self['color']['background'] = '42,46,51'
        self['color']['text_normal'] = '255,255,255'
        self['color']['text_highlighted'] = '42,46,51'
        self['color']['primary'] = '75,180,255'
        self['color']['secondary'] = '255,105,75'
        self['color']['tertiary'] = '75,255,240'
        self['color']['negativ'] = '255,90,75'
        self['color']['positiv'] = '90,255,75'
        self['color']['neutral'] = '200,200,200'
        # gui settings
        self['gui'] = {}
        self['gui']['filteruseregex'] = 'True'
        self['gui']['portfolio_sort_row'] = '3'
        self['gui']['trade_sort_row'] = '2'
        self['gui']['portfolio_sort_dir'] = (str(qt.DescendingOrder))
        self['gui']['trade_sort_dir'] = str(qt.AscendingOrder)
        self['gui']['tooltipsenabled'] = 'True'
        self['gui']['performancechartindex'] = '0'
        self['gui']['tradeseditlock'] = 'True'
        self['gui']['hidelowbalancecoins'] = 'True'
        self['gui']['hidelowvaluecoins'] = 'False'
        self['gui']['lowvaluefilterlimit(reportcurrency)'] = '50'
        self['gui']['loadpricehistorychart'] = 'False'
        self['gui']['coinchartdatatype'] = 'buys'

        super(QSettings, self).initSettings()

    def initDescriptions(self):

        super(QSettings, self).initDescriptions()

        # window settings
        self.descriptions['window'] = {}
        self.descriptions['window']['windowsize'] = 'init window size'
        self.descriptions['window']['windowpos'] = 'init window pos'
        self.descriptions['window']['windowstate'] = '0: normal; 1: minimized; 2: maximized; 4 fullscreen;'
        self.descriptions['window']['windowtitle'] = 'title which is displayed in title bar'
        self.descriptions['window']['windowstyle'] = 'qt style, see https://doc.qt.io/qt-5/qtquickcontrols2-styles.html'
        self.descriptions['window']['stylesheetname'] = 'name of style sheet in koalafolio/Styles that should be used. copy and rename defaultStyle.qss to create alternative styles'
        # color settings
        self.descriptions['color'] = {}
        self.descriptions['color']['background'] = 'background color'
        self.descriptions['color']['text_normal'] = 'text color'
        self.descriptions['color']['text_highlighted'] = 'highlighted text'
        self.descriptions['color']['primary'] = 'primary style color'
        self.descriptions['color']['secondary'] = 'secondary style color'
        self.descriptions['color']['tertiary'] = 'tertiary style color'
        self.descriptions['color']['negativ'] = 'color for negative values'
        self.descriptions['color']['positiv'] = 'color for positive values'
        self.descriptions['color']['neutral'] = 'color for neutral values'
        # gui settings
        self.descriptions['gui'] = {}
        self.descriptions['gui']['filteruseregex'] = 'True: use regex in filter boxes'
        self.descriptions['gui']['portfolio_sort_row'] = 'last sorted row of portfolio table'
        self.descriptions['gui']['trade_sort_row'] = 'last sorted row of trade table'
        self.descriptions['gui']['portfolio_sort_dir'] = 'sort direction of portfolio table'
        self.descriptions['gui']['trade_sort_dir'] = 'sort direction of trade table'
        self.descriptions['gui']['tooltipsenabled'] = 'True: enable tool tips'
        self.descriptions['gui']['performancechartindex'] = '0: crypto performance; 1: fiat performance'
        self.descriptions['gui']['tradeseditlock'] = 'True: lock editing of trades in trade table'
        self.descriptions['gui']['hidelowbalancecoins'] = 'True: coins with low or negative balance will be excluded from portfolio table'
        self.descriptions['gui']['hidelowvaluecoins'] = 'True: coins with low fiat value will be excluded from portfolio'
        self.descriptions['gui']['lowvaluefilterlimit(reportcurrency)'] = 'fiat value limit to hide coins'
        self.descriptions['gui']['loadpricehistorychart'] = 'True: historical prices will be shown in coin buy chart. Can cause high api load.'
        self.descriptions['gui']['coinchartdatatype'] = 'buys: show cummulative buys that hav not been sold yet (FIFO), balance: show balance chart including buys and sells.'

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
            if key == 'text_normal':
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
            gui['filteruseregex'] = self.getboolean('gui', 'filteruseregex')
        except ValueError:
            gui['filteruseregex'] = True
        try:
            gui['portfolio_sort_row'] = self.getint('gui', 'portfolio_sort_row')
        except ValueError:
            gui['portfolio_sort_row'] = 3
        try:
            gui['trade_sort_row'] = self.getint('gui', 'trade_sort_row')
        except ValueError:
            gui['trade_sort_row'] = 2
        try:
            gui['portfolio_sort_dir'] = self.getint('gui', 'portfolio_sort_dir')
        except ValueError:
            gui['portfolio_sort_dir'] = qt.AscendingOrder
        try:
            gui['trade_sort_dir'] = self.getint('gui', 'trade_sort_dir')
        except ValueError:
            gui['trade_sort_dir'] = qt.AscendingOrder
        try:
            gui['tooltipsenabled'] = self.getboolean('gui', 'tooltipsenabled')
        except ValueError:
            gui['tooltipsenabled'] = True
        try:
            gui['performancechartindex'] = self.getint('gui', 'performancechartindex')
        except ValueError:
            gui['performancechartindex'] = 0
        try:
            gui['tradeseditlock'] = self.getboolean('gui', 'tradeseditlock')
        except ValueError:
            gui['tradeseditlock'] = True
        try:
            gui['hidelowbalancecoins'] = self.getboolean('gui', 'hidelowbalancecoins')
        except ValueError:
            gui['hidelowbalancecoins'] = True
        try:
            gui['hidelowvaluecoins'] = self.getboolean('gui', 'hidelowvaluecoins')
        except ValueError:
            gui['hidelowvaluecoins'] = False
        try:
            gui['lowvaluefilterlimit(reportcurrency)'] = self.getfloat('gui', 'lowvaluefilterlimit(reportcurrency)')
        except ValueError:
            gui['lowvaluefilterlimit(reportcurrency)'] = 50
        try:
            gui['loadpricehistorychart'] = self.getboolean('gui', 'loadpricehistorychart')
        except ValueError:
            gui['loadpricehistorychart'] = False
        gui['coinchartdatatype'] = self['gui']['coinchartdatatype']
        return gui

    def getGuiSetting(self, key):
        return self.getGuiSettings()[key]

    def setGuiSettings(self, gui):
        for key in gui:
            if key in self['gui']:
                self['gui'][key] = str(gui[key])
            else:
                raise KeyError('invalid key ' + key + ' for gui settings')

    def setGuiSetting(self, key, value):
        if key in self['gui']:
            self['gui'][key] = str(value)
        else:
            raise KeyError('invalid key ' + key + ' for gui settings')


mySettings = QSettings()
