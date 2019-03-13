# -*- coding: utf-8 -*-
"""
Created on Sun Mar 10 10:39:51 2019

@author: Martin
"""


import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as qtwidgets
import PyQt5.QtCore as qtcore
import PyQt5.QtChart as qtchart
import gui.Qcontrols as controls
import PcpCore.core as core
import gui.QSettings as settings
import gui.QStyle as style
import datetime
import gui.QLogger as logger

qt = qtcore.Qt
localLogger = logger.globalLogger

# container for switchable charts
class ChartCont(qtwidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super(ChartCont, self).__init__(*args, **kwargs)

        self.setObjectName('ChartCont')
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameShape(qtwidgets.QFrame.StyledPanel)

        self.charts = []
        self.chartIndex = None

        self.rightButton = qtwidgets.QPushButton('>', self)
        self.rightButton.clicked.connect(self.rightButtonClicked)
        self.leftButton = qtwidgets.QPushButton('<', self)
        self.leftButton.clicked.connect(self.leftButtonClicked)
        for button in [self.leftButton, self.rightButton]:
            button.setFixedSize(qtcore.QSize(20, 20))
        self.updateButtonPosition()

    def updateButtonPosition(self, height=20):
        leftPos = qtcore.QPoint(5, 5)
        rightPos = qtcore.QPoint(self.width() - self.rightButton.width() - 5, 5)
        self.rightButton.move(rightPos)
        self.leftButton.move(leftPos)
        for button in [self.leftButton, self.rightButton]:
            button.setFixedSize(qtcore.QSize(20, height))
            button.raise_()

    def addChart(self, chart):
        self.charts.append(chart)
        chart.setParent(self)
        self.setChartIndex(len(self.charts)-1)
        self.setFixedWidth(max([chart.width() for chart in self.charts]))
        self.setFixedHeight(max([chart.height() for chart in self.charts]))
        self.updateButtonPosition()

    def deleteCharts(self):
        self.charts = []
        self.setFixedWidth(max([chart.width() for chart in self.charts]))
        self.setFixedHeight(max([chart.height() for chart in self.charts]))
        self.updateButtonPosition()

    def setChartIndex(self, index):
        if index < 0:
            index = len(self.charts) - index
        if index in range(len(self.charts)):
            if self.chartIndex is not None:
                self.charts[self.chartIndex].setVisible(False)
            self.charts[index].setVisible(True)
            self.chartIndex = index
            self.updateButtonPosition(self.charts[self.chartIndex].chartView.heading.height())
            return True
        return False

    def leftButtonClicked(self):
        if self.chartIndex is not None:
            if not self.setChartIndex(self.chartIndex - 1):
                self.setChartIndex(len(self.charts)-1)

    def rightButtonClicked(self):
        if self.chartIndex is not None:
            if not self.setChartIndex(self.chartIndex + 1):
                self.setChartIndex(0)




# labeled donut/pie chart
class LabeledDonatChart(qtwidgets.QFrame):
    def __init__(self, width, height, numberLabels=3, heading='', *args, **kwargs):
        super(LabeledDonatChart, self).__init__(*args, **kwargs)

        # widget properties
        self.setObjectName('LabeledDonatChart')
        self.setFrameShape(qtwidgets.QFrame.StyledPanel)
        self.setFixedWidth(width)
        self.setFixedHeight(height)
        self.setContentsMargins(0, 0, 0, 0)
        # donut chart
        self.series = qtchart.QPieSeries()
        self.series.setHoleSize(0.6)

        self.chart = qtchart.QChart()
        self.chart.setBackgroundVisible(False)
        self.chart.addSeries(self.series)
        self.chart.legend().hide()
        self.chart.setMargins(qtcore.QMargins(0, 0, 0, 0))
        self.chart.setMinimumWidth(width)
        self.chart.setMinimumHeight(height)

        self.chartView = LabeledChartView(width, height, numberLabels, heading, self.chart, self)
        self.chartView.setRenderHint(qtgui.QPainter.Antialiasing)

        self.layout = qtwidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.chartView)


    def addSlice(self, label, value, borderwith=-1, isLabelVisible=False):
        slice = self.series.append(label, value)
        slice.setBorderWidth(borderwith)
        slice.setLabelVisible(isLabelVisible)
        return slice

    def setSeries(self, series):
        self.chart.removeAllSeries()
        self.chart.addSeries(series)
        self.series = series
        # self.series.setHoleSize(0.6)

    def setLabelToolTip(self, strings):
        self.chartView.setLabelToolTip(strings)

    def setHeadingToolTip(self, string):
        self.chartView.setHeadingToolTip(string)

    def __iter__(self):
        return iter(self.series.slices())


# chart view with labels in center
class LabeledChartView(qtchart.QChartView):
    def __init__(self, width, height, numberLabels=3, heading='', *args, **kwargs):
        super(LabeledChartView, self).__init__(*args, **kwargs)

        self.setMinimumHeight(height)
        self.setMinimumWidth(width)
        self.setObjectName('LabeledChartView')

        self.heading = qtwidgets.QLabel(heading, self)
        self.heading.setFont(qtgui.QFont("Arial", 12))
        if heading:
            self.heading.setVisible(True)
        else:
            self.heading.setVisible(False)
        self.heading.setMargin(3)
        self.heading.adjustSize()
        self.heading.setObjectName('heading')
        headingPos = qtcore.QPoint(self.width()/2 - self.heading.width()/2, 5)
        self.heading.move(headingPos)
        self.labels = [qtwidgets.QLabel('', self) for num in range(numberLabels)]
        for label in self.labels:
            label.setFont(qtgui.QFont("Arial", 12))
            label.setVisible(False)
            label.setMargin(0)
            label.adjustSize()

        self.setColor(qtgui.QColor(255, 255, 255))
        self.labelAlignment = qt.AlignRight

    def setHeadingPos(self, pos):
        self.heading.move(pos)

    def updateLabelPos(self):
        center = self.geometry().center()
        origins = [qtcore.QPoint(center) for label in self.labels]
        for origin, col in zip(origins, range(len(origins))):
            for label in self.labels[0:col]:  # put label underneath each other
                origin.setY(origin.y() + label.height())
            # move labels up to have the middle one in the center
            origin.setY(origin.y() - sum([label.height() for label in self.labels])/2)
            # move labels left to have them in the center
            origin.setX(origin.x() - self.labels[col].width()/2 + 2)

        if self.labelAlignment == qt.AlignLeft:
            maxWidth = max([label.width() for label in self.labels])
            for label, origin in zip(self.labels, origins):
                origin.setX(origin.x() - (maxWidth - label.width())/2)
        elif self.labelAlignment == qt.AlignRight:
            maxWidth = max([label.width() for label in self.labels])
            for label, origin in zip(self.labels, origins):
                origin.setX(origin.x() + (maxWidth - label.width())/2)
        for label, origin in zip(self.labels, origins):
            label.move(origin)

    def moveEvent(self, event):
        super(LabeledChartView, self).moveEvent(event)
        self.updateLabelPos()

    def resizeEvent(self, event):
        super(LabeledChartView, self).resizeEvent(event)
        self.updateLabelPos()

    def setText(self, texts, alignment=qt.AlignRight):
        self.labelAlignment = alignment
        for label, text in zip(self.labels, texts):
            label.setText(text)
            font = label.font()
            font.setPointSize(12)
            label.setFont(font)
            label.adjustSize()
        while(max([label.width() for label in self.labels]) > 90):
            for label in self.labels:
                font = label.font()
                font.setPointSize(font.pointSize() - 1)
                label.setFont(font)
                label.adjustSize()
        self.updateLabelPos()
        for label, text in zip(self.labels, texts):
            if text:
                label.setVisible(True)
            else:
                label.setVisible(False)

    def setLabelToolTip(self, strings):
        if settings.mySettings.getGuiSetting('toolTipsEnabled'):
            for label, string in zip(self.labels, strings):
                label.setToolTip(string)

    def setHeadingToolTip(self, string):
        self.heading.setToolTip(string)

    def setColor(self, cols, isBackgroundTransparent=True):
        try:
            if isBackgroundTransparent:
                for label, col in zip(self.labels, cols):
                    label.setStyleSheet('QLabel{background-color: rgba(0, 0, 0, 0); color:  ' + col.name() + ';}' +
                                        'QToolTip{border: 1px solid ' + col.name() + '}')
            else:
                for label, col in zip(self.labels, cols):
                    label.setStyleSheet('QLabel{border-radius: 5px ; color:  ' + col.name() + ';}' +
                                        'QToolTip{border: 1px solid ' + col.name() + '}')
        except TypeError:
            col = cols
            if isBackgroundTransparent:
                for label in self.labels:
                    label.setStyleSheet('QLabel{background-color: rgba(0, 0, 0, 0); color:  ' + col.name() + ';}' +
                                        'QToolTip{border: 1px solid ' + col.name() + '}')
            else:
                for label in self.labels:
                    label.setStyleSheet('QLabel{border-radius: 5px ; color:  ' + col.name() + ';}' +
                                        'QToolTip{border: 1px solid ' + col.name() + '}')


class HorizontalStackedBarChart(qtwidgets.QWidget):
    def __init__(self, width, height, *args, **kwargs):
        super(HorizontalStackedBarChart, self).__init__(*args, **kwargs)

        self.chartColor = qtgui.QColor(*settings.mySettings.getColor('NEUTRAL'))

        self.chart = qtchart.QChart()
        self.chart.setBackgroundVisible(False)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(qt.AlignRight)
        self.chart.legend().setLabelColor(self.chartColor)
        # self.chart.setTheme(qtchart.QChart.ChartThemeDark)

        categories = []
        self.barAxisCat = qtchart.QBarCategoryAxis()
        self.barAxisCat.append(categories)
        self.barAxisCat.setLabelsColor(self.chartColor)
        self.barAxisCat.setLabelsFont(qtgui.QFont('Arial', 8))
        # self.barAxisCat.setLabelsAngle(-90)
        self.barAxisCat.setGridLinePen(qtgui.QPen(qtgui.QBrush(), 0))
        self.chart.addAxis(self.barAxisCat, qt.AlignLeft)
        # self.barAxisVal = qtchart.QValueAxis()
        # self.barAxisVal.setGridLinePen(qtgui.QPen(qtgui.QBrush(), 0))
        # self.barAxisVal.setLabelsColor(self.chartColor)
        # self.barAxisVal.setLabelsFont(qtgui.QFont('Arial', 8))
        # self.barAxisVal.setLabelsAngle(-45)
        # self.chart.addAxis(self.barAxisVal, qt.AlignLeft)

        self.chartView = qtchart.QChartView(self.chart)
        self.chartView.setRenderHint(qtgui.QPainter.Antialiasing)
        self.chartView.setFixedHeight(height)
        self.chartView.setFixedWidth(width)

        self.layout = qtwidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.chartView)

    def updateChart(self, dicts, labels):
        self.sets = []
        for dict, label in zip(dicts, labels):
            self.sets.append(qtchart.QBarSet(label))
            for key in dict:
                self.sets[-1].append(dict[key])
        barSeries = qtchart.QHorizontalStackedBarSeries()
        barSeries.setLabelsVisible(False)
        barSeries.setBarWidth(0.2)
        for set in self.sets:
            barSeries.append(set)
        self.chart.removeAllSeries()
        self.chart.addSeries(barSeries)

        categories = list(dicts[0])
        self.barAxisCat.setCategories(categories)
        barSeries.attachAxis(self.barAxisCat)
        # barSeries.attachAxis(self.barAxisVal)

    def setColor(self, colors):
        for color, set in zip(colors, self.sets):
            set.setColor(color)
            set.setLabelColor(color)


class ProfitPerYearWidget(qtwidgets.QFrame):
    def __init__(self, width, height, *args, **kwargs):
        super(ProfitPerYearWidget, self).__init__(*args, **kwargs)

        self.chartColor = qtgui.QColor(*settings.mySettings.getColor('NEUTRAL'))

        self.layout = qtwidgets.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)

        self.setFixedHeight(height)
        self.setFixedWidth(width)

        self.yLabels = []
        self.headings = []
        self.labels = {}


    def updateChart(self, dict):
        self.yLabels = []
        self.headings = []
        self.labels = {}
        for y in dict:
            self.yLabels.append(qtwidgets.QLabel(str(y), self))
            self.labels[y] = {}
            for key in dict[y]:
                self.labels[y][key] = qtwidgets.QLabel(controls.floatToString(dict[y][key], 4), self)
        for label in dict[list(dict)[0]]:
            self.headings.append(qtwidgets.QLabel(label, self))

        for label, row in zip(self.yLabels, range(1, len(self.yLabels)+1)):
            label.setFont(qtgui.QFont('Arial', 9))
            label.adjustSize()
            self.layout.addWidget(label, row, 0, qt.AlignRight | qt.AlignVCenter)
        for label, col in zip(self.headings, range(1, len(self.headings)+1)):
            label.setFont(qtgui.QFont('Arial', 9))
            label.adjustSize()
            self.layout.addWidget(label, 0, col, qt.AlignBottom | qt.AlignHCenter)
        for y, row in zip(self.labels, range(1, len(self.yLabels)+1)):
            for key, col in zip(self.labels[y], range(1, len(self.headings)+1)):
                self.labels[y][key].setFont(qtgui.QFont('Arial', 11))
                self.labels[y][key].adjustSize()
                if dict[y][key] >= 0:
                    color = style.myStyle.getQColor('POSITIV')
                else:
                    color = style.myStyle.getQColor('NEGATIV')
                self.labels[y][key].setStyleSheet('QLabel {color: ' + color.name() + '}')
                self.layout.addWidget(self.labels[y][key], row, col, qt.AlignCenter)

    def setColor(self, colors):
        for color, set in zip(colors, self.sets):
            set.setColor(color)
            set.setLabelColor(color)


