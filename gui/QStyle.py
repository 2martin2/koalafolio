# -*- coding: utf-8 -*-
"""
Created on Sun Sep 16 09:57:14 2018

@author: Martin
"""

import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwigets
import PyQt5.QtCore as qtcore
import gui.QLogger as logger
import os
import re
import gui.QSettings as settings
import colorsys

localLogger = logger.globalLogger


# color helper
def chnageLightness(colorTuple, dif):
    dif = dif/100
    colorTupleNorm = tuple(ct/255 for ct in colorTuple)
    color_hls = colorsys.rgb_to_hls(*colorTupleNorm)
    lightness = color_hls[1] + dif
    lightness = 0 if lightness < 0 else lightness
    lightness = 1 if lightness > 1 else lightness
    color_rbg = colorsys.hls_to_rgb(color_hls[0], lightness, color_hls[2])
    return int(color_rbg[0]*255), int(color_rbg[1]*255), int(color_rbg[2]*255)

def TupleToHexColor(tuple):
    hexcode = '#'
    for elem in tuple:
        hexcode += format(elem, '02x')
    return hexcode

class StyleSheetHandler():
    def __init__(self, target):
        self.target = target
        self.stylePath = ""
        self.presetFiles = {'defaultStyle': 'defaultStyle.qss', 'defaultStyle2': 'defaultStyle2.qss'}
        self.files = {}
        self.presetStyleSheets = {'defaultStyle': defaultStylesheet, 'defaultStyle2': defaultStylesheet2}
        self.activeStyleSheet = self.presetStyleSheets['defaultStyle']
        self.QColors = {}

    def setPath(self, appDir):
        self.stylePath = os.path.join(appDir, 'Styles')
        if self.createPath():
            self.savePresetSheets()
            self.checkFiles()

    def createPath(self):
        if not os.path.isdir(self.stylePath):
            try:
                os.mkdir(self.stylePath)
                return True
            except Exception as ex:
                localLogger.warning('creating style folder failed: ' + str(ex))
                return False
        return True

    def savePresetSheets(self):
        for key in self.presetStyleSheets:
            try:
                with open(os.path.join(self.stylePath, self.presetFiles[key]), 'w') as file:
                    file.write(self.presetStyleSheets[key])
            except Exception as ex:
                localLogger.error('saving ' + key + ' stylesheet failed: ' + str(ex))

    def checkFiles(self):
        try:
            allFiles = [f for f in os.listdir(self.stylePath) if os.path.isfile(os.path.join(self.stylePath, f))]
            filePattern = re.compile("^(.*)\.qss$", re.IGNORECASE)
            for file in allFiles:
                fileMatch = filePattern.match(file)
                if fileMatch:
                    self.files[fileMatch.group(1)] = file
        except Exception as ex:
            localLogger.error('checking stylesheets failed: ' + str(ex))

    def loadSheet(self, key):
        try:
            with open(os.path.join(self.stylePath, self.files[key]), 'r') as file:
                self.activeStyleSheet = file.read()
        except Exception as ex:
            localLogger.error('reading ' + key + ' stylesheet failed: ' + str(ex))
            self.activeStyleSheet = self.presetStyleSheets['defaultStyle']
        self.setStyle()

    def setStyle(self):
        try:
            self.replaceColors()
            self.target.setStyleSheet(self.activeStyleSheet)
        except Exception as ex:
            localLogger.error('setting stylesheet on target failed: ' + str(ex))

    def replaceColors(self):
        # constants
        colors = settings.mySettings.getColors()
        for colorName in colors:
            self.QColors[colorName] = qtgui.QColor(*colors[colorName])
            # calculate light/ dark colors
            colorMidLight = chnageLightness(colors[colorName], 10)
            colorNameMidLight = colorName + '_MIDLIGHT'
            colorMidDark = chnageLightness(colors[colorName], -10)
            colorNameMidDark = colorName + '_MIDDARK'
            colorLight = chnageLightness(colors[colorName], 25)
            colorNameLight = colorName + '_LIGHT'
            colorDark = chnageLightness(colors[colorName], -25)
            colorNameDark = colorName + '_DARK'
            # replace color (dark and light first, otherwise they will be replaced partly)
            hexColorMidLight = TupleToHexColor(colorMidLight)
            self.activeStyleSheet = self.activeStyleSheet.replace(colorNameMidLight, hexColorMidLight)
            hexColorMidDark = TupleToHexColor(colorMidDark)
            self.activeStyleSheet = self.activeStyleSheet.replace(colorNameMidDark, hexColorMidDark)
            hexColorLight = TupleToHexColor(colorLight)
            self.activeStyleSheet = self.activeStyleSheet.replace(colorNameLight, hexColorLight)
            hexColorDark = TupleToHexColor(colorDark)
            self.activeStyleSheet = self.activeStyleSheet.replace(colorNameDark, hexColorDark)
            hexColor = TupleToHexColor(colors[colorName])
            self.activeStyleSheet = self.activeStyleSheet.replace(colorName, hexColor)

        # set palette
        # palette = self.target.palette()
        # palette.setColor(qtgui.QPalette.Window, QColors['BACKGROUND'])
        # palette.setColor(qtgui.QPalette.WindowText, QColors['TEXT_NORMAL'])
        # palette.setColor(qtgui.QPalette.Base, QColors['BACKGROUND'])
        # palette.setColor(qtgui.QPalette.ToolTipBase, QColors['BACKGROUND'])
        # palette.setColor(qtgui.QPalette.ToolTipText, QColors['TEXT_NORMAL'])
        # palette.setColor(qtgui.QPalette.Text, QColors['TEXT_NORMAL'])
        # palette.setColor(qtgui.QPalette.Button, QColors['PRIMARY'])
        # palette.setColor(qtgui.QPalette.ButtonText, QColors['TEXT_HIGHLIGHTED'])
        # palette.setColor(qtgui.QPalette.BrightText, QColors['TEXT_HIGHLIGHTED'])
        # self.target.setPalette(palette)




defaultStylesheetTemplate = "* {{ background-color: {0} }} " \
                            "QFrame {{ border: 0px solid black; background-color: {0} }} "
# defaultStyleSheetColored = defaultStylesheetTemplate.format(settings.mySettings['window']['windowColor'])


defaultStylesheet2 = r"""* {
    background-color: BACKGROUND;
    alternate-background-color: BACKGROUND_MIDDARK;
    color: TEXT_NORMAL;
}

/* frames */
QFrame {
    border: 0px solid PRIMARY_DARK;
    margin: 0px 0px 0px 0px;
    padding: 0px 0px 0px 0px;
}
/* pages */
QFrame#QPage{
    padding: 0px 0px 0px 0px;
    border: 2px solid PRIMARY;
    border-radius: 15px
}

QFrame#QSubPage{
    margin: 10px 0px 0px 0px;
}

/* line edit */
QLineEdit{
    border: 1px solid PRIMARY_DARK;
    border-radius: 2px;
}

/* buttons*/
QPushButton {
    border: 1px solid PRIMARY_DARK;
    border-radius: 6px;
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 PRIMARY, stop: 1 PRIMARY_MIDLIGHT);
    padding: 4px 7px 4px 7px;
}

QPushButton:pressed {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 PRIMARY_MIDLIGHT, stop: 1 PRIMARY);
}

QPushButton:flat {
    border: none;
}

QPushButton:default {
    border-color: PRIMARY;
}

/* import and settings treeview */
QTreeView{
    border: 0px solid BACKGROUND;
    background: BACKGROUND;
}

/* statusbar list view */
QListView#statusbar{
    border: 3px inset PRIMARY;
}

/* trades and portfolio table */
QTableView{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 PRIMARY_LIGHT, stop:1 BACKGROUND);
}

QTableView QTableCornerButton::section {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT, stop:1 PRIMARY);
    border: 1px solid PRIMARY_DARK;
}

/* header of all tablels/trees and lists */
QHeaderView::section {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT, stop:1 PRIMARY);
    color: TEXT_NORMAL;
    padding-left: 4px;
    border: 1px solid PRIMARY_DARK;
}

/*QHeaderView::section:checked
{
    background-color: red;
}*/

/* scrollbars */
QScrollBar:horizontal, QScrollBar:vertical{
    border: 1px solid qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT, stop:1 PRIMARY);
}
QScrollBar:horizontal{
    height: 10px;
    margin: 0px 10px 0px 10px;
}
QScrollBar:vertical {
    width: 10px;
    margin: 10px 0px 10px 0px;
}

QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT, stop:1 PRIMARY);
    border: 0px solid PRIMARY_DARK
}
QScrollBar::handle:horizontal {
    min-width: 10px;
}
QScrollBar::handle:vertical {
    min-height: 10px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal, QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: 0px solid PRIMARY_MIDDARK;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT, stop:1 PRIMARY);
    subcontrol-origin: margin;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 10px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 10px;
}
QScrollBar::add-line:horizontal {
    subcontrol-position: right;
}
QScrollBar::sub-line:horizontal {
    subcontrol-position: left;
}
QScrollBar::add-line:vertical {
    subcontrol-position: bottom;
}
QScrollBar::sub-line:vertical {
    subcontrol-position: top;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
    border: 0px solid BACKGROUND
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}


/* date edit for export */
QDateEdit * {
    background-color: PRIMARY_MIDLIGHT;
    color: TEXT_NORMAL;
}

QCalendarWidget *{
    background-color: BACKGROUND
}

QCalendarWidget QAbstractItemView
{
background-color: BACKGROUND;
selection-background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT, stop:1 PRIMARY);
selection-color: TEXT_NORMAL;
}

"""

defaultStylesheet = r"""* {
    background-color: BACKGROUND;
    alternate-background-color: BACKGROUND_MIDDARK;
    color: TEXT_NORMAL;
}

/* frames */
QFrame {
    border: 0px solid PRIMARY_DARK;
    margin: 0px 0px 0px 0px;
    padding: 0px 0px 0px 0px;
}
/* pages */
QFrame#QPage{
    padding: 0px 0px 0px 0px;
    border: 2px solid PRIMARY;
    border-radius: 15px
}

QFrame#QSubPage{
    margin: 10px 0px 0px 0px;
}

/* line edit */
QLineEdit{
    border: 1px solid PRIMARY_DARK;
    border-radius: 2px;
}

/* buttons*/
QPushButton {
    border: 1px solid PRIMARY_DARK;
    border-radius: 6px;
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 PRIMARY, stop: 1 PRIMARY_MIDLIGHT);
    padding: 4px 7px 4px 7px;
    color: TEXT_HIGHLIGHTED;
}

QPushButton:pressed {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 PRIMARY_MIDLIGHT, stop: 1 PRIMARY);
}

QPushButton:flat {
    border: none;
}

QPushButton:default {
    border-color: PRIMARY;
}

/* import and settings treeview */
QTreeView{
    border: 0px solid BACKGROUND;
    background: BACKGROUND;
}

/* statusbar list view */
QListView#statusbar{
    border: 3px inset PRIMARY;
}

/* trades and portfolio table */
QTableView{
}

QTableView QTableCornerButton::section {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT, stop:1 PRIMARY);
    border: 1px solid PRIMARY_DARK;
}

/* header of all tablels/trees and lists */
QHeaderView::section {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT stop:1 PRIMARY);
    color: TEXT_HIGHLIGHTED;
    padding-left: 4px;
    border: 1px solid PRIMARY_DARK;
}

/*QHeaderView::section:checked
{
    background-color: red;
}*/

/* scrollbars */
QScrollBar:horizontal, QScrollBar:vertical{
    border: 1px solid qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT, stop:1 PRIMARY);
}
QScrollBar:horizontal{
    height: 10px;
    margin: 0px 10px 0px 10px;
}
QScrollBar:vertical {
    width: 10px;
    margin: 10px 0px 10px 0px;
}

QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT, stop:1 PRIMARY);
    border: 0px solid PRIMARY_DARK
}
QScrollBar::handle:horizontal {
    min-width: 10px;
}
QScrollBar::handle:vertical {
    min-height: 10px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal, QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: 0px solid PRIMARY_MIDDARK;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT, stop:1 PRIMARY);
    subcontrol-origin: margin;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 10px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 10px;
}
QScrollBar::add-line:horizontal {
    subcontrol-position: right;
}
QScrollBar::sub-line:horizontal {
    subcontrol-position: left;
}
QScrollBar::add-line:vertical {
    subcontrol-position: bottom;
}
QScrollBar::sub-line:vertical {
    subcontrol-position: top;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
    border: 0px solid BACKGROUND
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}


/* date edit for export */
QDateEdit * {
    background-color: PRIMARY_MIDLIGHT;
    color: TEXT_NORMAL;
}

QCalendarWidget *{
    background-color: BACKGROUND
}

QCalendarWidget QAbstractItemView
{
background-color: BACKGROUND;
selection-background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 PRIMARY, stop: 0.4 PRIMARY_MIDLIGHT, stop:1 PRIMARY);
selection-color: TEXT_NORMAL;
}
"""