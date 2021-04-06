# -*- coding: utf-8 -*-
"""
Created on Sun Sep 16 20:17:51 2018

@author: Martin
"""

import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import koalafolio.gui.Qcontrols as controls
import koalafolio.PcpCore.core as core
import koalafolio.gui.Qpages as qpages
import koalafolio.gui.QSettings as settings
import datetime
import koalafolio.gui.QLogger as logger
import koalafolio.exp.profitExport as profex

qt = qtcore.Qt
localLogger = logger.globalLogger


# %% export page for exporting csv, txt, xls ...
class ExportPage(qpages.Page):
    def __init__(self, parent, controller):
        super(ExportPage, self).__init__(parent=parent, controller=controller)

        self.fileDialog = qtwidgets.QFileDialog(self)
        # self.fileDialog.setDirectory(self.controller.appPath)

        self.exportProfitFrame = controls.StyledFrame(self)
        self.exportProfitFrame.setFixedWidth(275)

        # heading
        self.exportProfitLabel = qtwidgets.QLabel("export profit", self.exportProfitFrame)
        font = self.exportProfitLabel.font()
        font.setPointSize(14)
        self.exportProfitLabel.setFont(font)

        self.headingLayout = qtwidgets.QHBoxLayout()
        self.headingLayout.addStretch()
        self.headingLayout.addWidget(self.exportProfitLabel)
        self.headingLayout.addStretch()

        # start and end date
        self.fromDateLabel = qtwidgets.QLabel("start: ", self.exportProfitFrame)
        self.toDateLabel = qtwidgets.QLabel("end: ", self.exportProfitFrame)
        self.fromDateEdit = qtwidgets.QDateEdit(self.exportProfitFrame)
        self.fromDateEdit.setCalendarPopup(True)
        self.toDateEdit = qtwidgets.QDateEdit(self.exportProfitFrame)
        self.toDateEdit.setCalendarPopup(True)

        self.dateLayout = qtwidgets.QHBoxLayout()
        self.dateLayout.addWidget(self.fromDateLabel)
        self.dateLayout.addWidget(self.fromDateEdit)
        self.dateLayout.addStretch()
        self.dateLayout.addWidget(self.toDateLabel)
        self.dateLayout.addWidget(self.toDateEdit)
        # self.dateLayout.addStretch()

        # year
        self.yearLabel = qtwidgets.QLabel("year: ", self.exportProfitFrame)
        self.yearDateEdit = qtwidgets.QSpinBox(self.exportProfitFrame)
        self.yearDateEdit.valueChanged.connect(self.yearChanged)
        self.yearDateEdit.setMinimum(0)
        self.yearDateEdit.setMaximum(datetime.datetime.now().year)
        self.yearDateEdit.setValue(datetime.datetime.now().year)

        self.yearLayout = qtwidgets.QHBoxLayout()
        self.yearLayout.addStretch()
        self.yearLayout.addWidget(self.yearLabel)
        self.yearLayout.addWidget(self.yearDateEdit)
        self.yearLayout.addStretch()

        self.optionsLayout = qtwidgets.QGridLayout()

        # currency
        self.currencyLabel = qtwidgets.QLabel("currency", self.exportProfitFrame)
        self.currencyBox = qtwidgets.QComboBox(self.exportProfitFrame)
        listModel = qtcore.QStringListModel()
        currencys = list(core.CoinValue())
        listModel.setStringList(currencys)
        self.currencyBox.setModel(listModel)
        defaultCurrency = settings.mySettings.reportCurrency()
        self.currencyBox.setCurrentIndex(currencys.index(defaultCurrency))

        self.optionsLayout.addWidget(self.currencyLabel, 0, 1)
        self.optionsLayout.addWidget(self.currencyBox, 0, 2)

        # language
        self.languageLabel = qtwidgets.QLabel("language", self.exportProfitFrame)
        self.languageBox = qtwidgets.QComboBox(self.exportProfitFrame)
        lanListModel = qtcore.QStringListModel()
        languages = self.controller.exportTranslator.getLanguages()
        lanListModel.setStringList(languages)
        self.languageBox.setModel(lanListModel)
        defaultLanguage = settings.mySettings.getTaxSetting('exportLanguage')
        self.languageBox.setCurrentIndex(languages.index(defaultLanguage))

        self.optionsLayout.addWidget(self.languageLabel, 1, 1)
        self.optionsLayout.addWidget(self.languageBox, 1, 2)

        # tax timelimit
        self.timeLimitLabel = qtwidgets.QLabel("tax year limit", self.exportProfitFrame)
        self.timeLimitBox = qtwidgets.QCheckBox(self.exportProfitFrame)
        self.timeLimitEdit = qtwidgets.QSpinBox(self.exportProfitFrame)
        self.timeLimitEdit.setValue(1)
        self.timeLimitEdit.setMinimum(0)
        self.timeLimitBox.setCheckState(qt.Checked)

        self.optionsLayout.addWidget(self.timeLimitBox, 2, 0)
        self.optionsLayout.addWidget(self.timeLimitLabel, 2, 1)
        self.optionsLayout.addWidget(self.timeLimitEdit, 2, 2)

        # include tax free trades
        self.taxFreeTradesLabel = qtwidgets.QLabel("include tax free trades", self.exportProfitFrame)
        self.taxFreeTradesBox = qtwidgets.QCheckBox(self.exportProfitFrame)
        self.taxFreeTradesBox.setCheckState(qt.Checked)

        # self.taxFreeTradesLayout = qtwidgets.QHBoxLayout()
        self.optionsLayout.addWidget(self.taxFreeTradesBox, 3, 0)
        self.optionsLayout.addWidget(self.taxFreeTradesLabel, 3, 1)
        # self.taxFreeTradesLayout.addStretch()

        # todo: add export checkboxes

        # include fees
        # label
        # checkbox

        # include exchanges
        # label
        # checkbox

        # daywise matching
        # label
        # checkbox

        self.timeLimitBox.stateChanged.connect(self.timeLimitCheckBoxChanged)
        self.timeLimitCheckBoxChanged()

        # export button
        self.exportProfitButton = qtwidgets.QPushButton("export", self.exportProfitFrame)
        self.exportProfitButton.clicked.connect(self.exportProfit)

        self.buttonLayout = qtwidgets.QHBoxLayout()
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.exportProfitButton)
        self.buttonLayout.addStretch()

        self.optionsHorzLayout = qtwidgets.QHBoxLayout()
        self.optionsHorzLayout.addLayout(self.optionsLayout)
        self.optionsHorzLayout.addStretch()

        self.vertLayout = qtwidgets.QVBoxLayout(self.exportProfitFrame)
        self.vertLayout.addLayout(self.headingLayout)
        self.vertLayout.addLayout(self.yearLayout)
        self.vertLayout.addLayout(self.dateLayout)
        self.vertLayout.addLayout(self.optionsHorzLayout)
        # self.vertLayout.addLayout(self.currencyLayout)
        # self.vertLayout.addLayout(self.timeLimitLayout)
        # self.vertLayout.addLayout(self.taxFreeTradesLayout)
        # self.vertLayout.addLayout(self.)
        self.vertLayout.addStretch()
        self.vertLayout.addLayout(self.buttonLayout)

        self.horzLayout = qtwidgets.QHBoxLayout(self)
        self.horzLayout.addWidget(self.exportProfitFrame)
        self.horzLayout.addStretch()



    def refresh(self):
        pass

    def yearChanged(self):
        year = self.yearDateEdit.value()
        self.fromDateEdit.setDate(qtcore.QDate(year, 1, 1))
        self.toDateEdit.setDate(qtcore.QDate(year, 12, 31))

    def timeLimitCheckBoxChanged(self):
        if self.timeLimitBox.isChecked():
            self.timeLimitEdit.setEnabled(True)
            self.taxFreeTradesBox.setEnabled(True)
        else:
            self.timeLimitEdit.setEnabled(False)
            self.taxFreeTradesBox.setEnabled(False)

    def exportProfit(self):
        self.fileDialog.setDefaultSuffix("xlsx")

        datestr = str(datetime.datetime.now()).replace(' ', '_').replace(':', '_').replace('-', '_').replace('.', '_')
        filename = 'profit' + '-' + datestr + '.xlsx'
        pathReturn = self.fileDialog.getSaveFileName(self, "save file", filename, "Excel (*.xlsx *.xls)")
        if pathReturn[0]:
            minDate = self.fromDateEdit.date().toPyDate()
            maxDate = self.toDateEdit.date().toPyDate()
            currency = self.currencyBox.currentText()
            language = self.languageBox.currentText()
            taxyearlimit = None
            if self.timeLimitBox.isChecked():
                taxyearlimit = self.timeLimitEdit.value()
            includeTaxFreeTrades = self.taxFreeTradesBox.isChecked()
            profex.createProfitExcel(self.controller.coinList, pathReturn[0], minDate, maxDate, currency=currency,
                                     taxyearlimit=taxyearlimit, includeTaxFreeTrades=includeTaxFreeTrades,
                                     lang=language, translator=self.controller.exportTranslator)
