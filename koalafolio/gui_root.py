# -*- coding: utf-8 -*-
"""
Created on Sun Sep 16 09:57:14 2018

@author: Martin
"""

# Core imports - needed immediately
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QSplashScreen, QLabel,
                             QProgressBar, QMessageBox, QSystemTrayIcon, QMenu,
                             QAction, QStyle)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QRect
from sys import argv, exit
from os import path

# Essential application imports
import koalafolio.PcpCore.logger as coreLogger
import koalafolio.gui.QLogger as logger
import koalafolio.PcpCore.arguments as arguments
import koalafolio.PcpCore.settings as coreSettings
import koalafolio.gui.QSettings as settings
import koalafolio.gui.QStyle as style
import koalafolio.exp.QTranslate as translator

from koalafolio.gui.widgets.QCompleterComboBox import StyledCompleter
# Defer heavy imports - will be imported when needed
# import koalafolio.gui.QLoggerWidget as loggerwidget
# import koalafolio.gui.Qpages as pages
# import koalafolio.gui.QExportPage as exportpage
# import koalafolio.gui.Qcontrols as controls
# import koalafolio.gui.QPortfolioTable as ptable
# import koalafolio.gui.QTradeTable as ttable
# import koalafolio.gui.QThreads as threads
# import koalafolio.gui.SettingsPage as settingsPage
# import koalafolio.Import.apiImport as apiImport
# import requests
# from koalafolio.gui.TradesPage import TradesPage
# from koalafolio.gui.ImportPage import ImportPage
# from koalafolio.gui.PortfolioPage import PortfolioPage


qt = Qt
# %% constants


# %% Custom splash screen with better text positioning
class CustomSplashScreen(QSplashScreen):
    """Custom splash screen with improved text positioning"""

    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.message = ""
        self.text_color = Qt.white
        self.text_alignment = Qt.AlignBottom | Qt.AlignCenter

        # Set larger font (30% bigger)
        font = self.font()
        current_size = font.pointSize()
        if current_size <= 0:
            current_size = 12
        new_size = int(current_size * 1.3)
        font.setPointSize(new_size)
        font.setBold(True)
        self.setFont(font)

    def showMessage(self, message, alignment=None, color=None):
        """Override to store message and trigger repaint"""
        self.message = message
        if alignment is not None:
            self.text_alignment = alignment
        if color is not None:
            self.text_color = color
        self.repaint()

    def drawContents(self, painter):
        """Custom drawing to position text higher"""
        if not self.message:
            return

        painter.setPen(self.text_color)
        painter.setFont(self.font())

        # Calculate text position - move up by one text height
        font_metrics = painter.fontMetrics()
        text_height = font_metrics.height()

        # Get the rectangle for drawing
        rect = self.rect()

        # Move the bottom up by one text height plus some padding
        adjusted_rect = QRect(rect.x(), rect.y(),
                                   rect.width(), rect.height() - text_height - 10)

        painter.drawText(adjusted_rect, self.text_alignment, self.message)


# %% Background version check thread
class VersionCheckThread(QThread):
    versionChecked = pyqtSignal(str)

    def __init__(self, package_name='koalafolio'):
        super().__init__()
        self.package_name = package_name

    def run(self):
        try:
            import requests
            response = requests.get(f'https://pypi.org/pypi/{self.package_name}/json', timeout=5)
            latest_version = str(response.json()['info']['version'])
            self.versionChecked.emit(latest_version)
        except Exception as ex:
            logger.globalLogger.warning(f'Could not check latest version: {ex}')
            self.versionChecked.emit('')


# %% Lazy import helper functions
def lazy_import_heavy_modules():
    """Import heavy modules when actually needed"""
    global loggerwidget, pages, exportpage, controls, ptable, ttable, threads
    global settingsPage, apiImport
    global TradesPage, ImportPage, PortfolioPage

    import koalafolio.gui.QLoggerWidget as loggerwidget
    import koalafolio.gui.Qpages as pages
    import koalafolio.gui.QExportPage as exportpage
    import koalafolio.gui.Qcontrols as controls
    import koalafolio.gui.QPortfolioTable as ptable
    import koalafolio.gui.QTradeTable as ttable
    import koalafolio.gui.QThreads as threads
    import koalafolio.gui.SettingsPage as settingsPage
    import koalafolio.Import.apiImport as apiImport
    from koalafolio.gui.TradesPage import TradesPage
    from koalafolio.gui.ImportPage import ImportPage
    from koalafolio.gui.PortfolioPage import PortfolioPage


# %% variables
import sys
import os

if getattr(sys, 'frozen', False):  # running as pyinstaller executable
    application_path = os.path.dirname(sys.executable)
    internal_dir = os.path.join(application_path, "_internal")  # Check for _internal
    running_mode = 'Frozen/executable'
else:
    try:
        app_full_path = os.path.realpath(__file__)
        application_path = os.path.dirname(app_full_path)
        running_mode = "Non-interactive"
    except NameError:
        application_path = os.getcwd()
        running_mode = 'Interactive'

def getResourcePath(relative_path) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', application_path)
    if running_mode == 'Frozen/executable':
        base_path = internal_dir
        # Check where the files are stored
        internalPath = os.path.join(internal_dir, relative_path)
        if os.path.exists(internalPath):
            return internalPath
        else:
            return os.path.join(application_path, relative_path)  # Try the exe folder
    return os.path.join(base_path, relative_path)

# %% classes
class PortfolioApp(QWidget):
    PORTFOLIOPAGEINDEX = 0
    TRADESPAGEINDEX = 1
    IMPORTPAGEINDEX = 2
    EXPORTPAGEINDEX = 3
    SETTINGSPAGEINDEX = 4
    startRefresh = pyqtSignal()
    endRefresh = pyqtSignal()
    styleSheetChanged = pyqtSignal(str)

    def __init__(self, parent=None, userDataPath = "", username="", splash=None):
        super(PortfolioApp, self).__init__(parent=parent)

        self.userDataPath = userDataPath
        self.username = username
        self.splash = splash
        self.latestVersion = ""
        self.heavy_modules_loaded = False
        self.data_loaded = False

        self.setObjectName("MainWindow")

        # Update splash
        if self.splash:
            self.splash.showMessage("Initializing environment...", Qt.AlignBottom | Qt.AlignCenter)
            QApplication.processEvents()

        self.initEnv()

        if self.splash:
            self.splash.showMessage("Setting up window...", Qt.AlignBottom | Qt.AlignCenter)
            QApplication.processEvents()

        self.initWindow()

        # Start version check in background (non-blocking)
        self.versionCheckThread = VersionCheckThread()
        self.versionCheckThread.versionChecked.connect(self.onVersionChecked)
        self.versionCheckThread.start()

        if self.splash:
            self.splash.showMessage("Loading modules...", Qt.AlignBottom | Qt.AlignCenter)
            QApplication.processEvents()

        # Load heavy modules
        lazy_import_heavy_modules()
        self.heavy_modules_loaded = True

        if self.splash:
            self.splash.showMessage("Initializing data models...", Qt.AlignBottom | Qt.AlignCenter)
            QApplication.processEvents()

        # init data
        self.initData()

        if self.splash:
            self.splash.showMessage("Setting up interface...", Qt.AlignBottom | Qt.AlignCenter)
            QApplication.processEvents()

        # init style
        self.initStyle()

        # init gui
        self.layoutUI()

        if self.splash:
            self.splash.showMessage("Starting application...", Qt.AlignBottom | Qt.AlignCenter)
            QApplication.processEvents()

        self.show()
        self.showFrame(self.PORTFOLIOPAGEINDEX)

        # Start background initialization
        self.startBackgroundInitialization()

        self.logger.info('application initialized')

    def onVersionChecked(self, latest_version):
        """Handle version check result"""
        self.latestVersion = latest_version
        if latest_version and self.settings['general']['version'] != latest_version:
            self.logger.info('new version ' + latest_version + ' available. Install with "pip install koalafolio --upgrade"')

    def startBackgroundInitialization(self):
        """Start background threads and data loading"""
        # Use QTimer to defer heavy operations until after UI is shown
        QTimer.singleShot(100, self.loadDataInBackground)

    def loadDataInBackground(self):
        """Load data in background after UI is ready"""
        try:
            # start the background threads
            self.startThreads()

            # Load data asynchronously
            QTimer.singleShot(200, lambda: self.coinList.restoreCoins())
            QTimer.singleShot(300, lambda: self.tradeList.restoreTrades())

            self.data_loaded = True
            self.logger.info('background data loading completed')
        except Exception as ex:
            self.logger.error(f'Error in background initialization: {ex}')

    def initGraphics(self):
        self.buttonPortfolio.setStyleSheet("QPushButton {border-image: url(" +
                                           os.path.join(self.graphicsPath, 'portfolio.png').replace('\\', '/') +
                                           ") 0 15 0 15 stretch;}")
        self.buttonTrades.setStyleSheet("QPushButton {border-image: url(" +
                                        os.path.join(self.graphicsPath, 'trades.png').replace('\\', '/') +
                                        ") 0 15 0 15 stretch;}")
        self.buttonImport.setStyleSheet("QPushButton {border-image: url(" +
                                        os.path.join(self.graphicsPath, 'import.png').replace('\\', '/') +
                                        ") 0 15 0 15 stretch;}")
        self.buttonExport.setStyleSheet("QPushButton {border-image: url(" +
                                        os.path.join(self.graphicsPath, 'export.png').replace('\\', '/') +
                                        ") 0 15 0 15 stretch;}")
        self.buttonSettings.setStyleSheet("QPushButton {border-image: url(" +
                                          os.path.join(self.graphicsPath, 'settings.png').replace('\\', '/') +
                                          ") 0 15 0 15 stretch;}")


    def reinit(self):
        self.startRefresh.emit()
        # delete button styles before style update, otherwise qt will crash
        self.buttonPortfolio.setStyleSheet("")
        self.buttonTrades.setStyleSheet("")
        self.buttonImport.setStyleSheet("")
        self.buttonExport.setStyleSheet("")
        self.buttonSettings.setStyleSheet("")
        self.initStyle()
        self.initGraphics()
        self.endRefresh.emit()

    # load environment/ settings
    def initEnv(self):
        # handle paths
        self.appPath = application_path
        self.graphicsPath = getResourcePath('graphics')
        self.ImportPath = getResourcePath('Import')

        if self.username:
            dataFolderName = "Data_" + str(self.username)
        else:
            dataFolderName = "Data"

        # check if valid userDataPath has been provided as argument
        if self.userDataPath and os.path.isdir(self.userDataPath):
            # check access to data folder (does not work on windows)
            if not os.access(self.userDataPath, os.X_OK):
                print('provided datadir is not writable')
                sys.exit(0)
            # try to write to userDataPath
            self.dataPath = os.path.join(self.userDataPath, dataFolderName)
            try:
                os.stat(self.userDataPath)
                self.logger = logger.globalLogger.setPath(self.dataPath)
            except Exception:
                # try to create userDataPath
                try:
                    os.mkdir(self.dataPath)
                    self.logger = logger.globalLogger.setPath(self.dataPath)
                except Exception as ex:
                    print('provided datadir is not valid: ' + str(ex))
                    sys.exit(0)
        else:  # no datadir provided, try to find writable location
            # check access to app folder (does not work on windows)
            if os.access(self.appPath, os.X_OK):
                self.userDataPath = self.appPath
            else:
                print('user data can not be saved in koala dir: ' + str(self.appPath))
                from PyQt5.QtCore import QStandardPaths
                self.userDataPath = os.path.abspath(QStandardPaths.writableLocation(
                                                    QStandardPaths.AppDataLocation))
                print('user data will be saved in: ' + str(self.userDataPath))
                if not os.path.isdir(self.userDataPath):
                    try:
                        os.mkdir(self.userDataPath)
                    except Exception as ex:
                        print('error creating user data folder: ' + str(ex))
                        sys.exit(0)

            self.dataPath = os.path.join(self.userDataPath, dataFolderName)

            # check DataFolder
            try:
                os.stat(self.dataPath)
                self.logger = logger.globalLogger.setPath(self.dataPath)  # test logfile
            except:  # folder not found/ not writable
                try:  # try to create Data folder in app path
                    os.mkdir(self.dataPath)
                    self.logger = logger.globalLogger.setPath(self.dataPath)
                except:  # creation of data folder not possible
                    # create data folder in system appDataPath
                    print('user data can not be saved in dir: ' + str(self.appPath))
                    self.userDataPath = os.path.abspath(QStandardPaths.writableLocation(
                                                        QStandardPaths.AppDataLocation))
                    print('user data will be saved in: ' + str(self.userDataPath))
                    self.dataPath = os.path.join(self.userDataPath, dataFolderName)
                    try:
                        os.stat(self.dataPath)
                        self.logger = logger.globalLogger.setPath(self.dataPath)
                    except:  # folder not found/ not writable
                        try:  # try to create Data folder in app path (could be skipped in case of PermissionError)
                            if not os.path.isdir(self.userDataPath):
                                os.mkdir(self.userDataPath)
                            os.mkdir(self.dataPath)
                            self.logger = logger.globalLogger.setPath(self.dataPath)
                        except Exception as ex:
                            print('creating data folder failed: ' + str(ex))
                            sys.exit(0)

        # valid data path, create user data
        #self.logger = logger.globalLogger.setPath(self.dataPath)
        self.settings = settings.mySettings.setPath(self.dataPath)
        self.styleSheetHandler = style.StyleSheetHandler(self)
        self.styleSheetHandler.setPath(self.dataPath)
        self.exportTranslator = translator.ExportTranslator(dataPath=self.dataPath)
        style.myStyle = self.styleSheetHandler
        QTimer.singleShot(500, self.initDBComponents)

    def initDBComponents(self):
        """Initialize db components in background"""
        try:
            self.apiUserDatabase = apiImport.ApiUserDatabase(path=self.dataPath)
            self.apiDefaultDatabase = apiImport.ApiDefaultDatabase(path=self.ImportPath)

            self.logger.info('databases initialized')
        except Exception as ex:
            logger.globalLogger.error('error initializing db components: ' + str(ex))


    # setup window style
    def initWindow(self):
        self.logger.info('initializing window ...')
        #        self.setWindowFlags(qtcore.Qt.FramelessWindowHint)
        windowProps = self.settings.getWindowProperties()
        self.setWindowState(windowProps['state'])
        self.setGeometry(windowProps['geometry'])
        self.logger.info('window initialized')

    def initStyle(self):
        self.logger.info('initializing style ...')
        windowTitle = self.settings['window']['windowtitle']
        if self.username:
            windowTitle += ' ' + str(self.username)
        if self.latestVersion:
            windowTitle += ' ' + self.settings['general']['version'] + ' (latest: ' + str(self.latestVersion) + ')'
        else:
            windowTitle += ' ' + self.settings['general']['version']
        self.setWindowTitle(windowTitle)
        try:
            app_icon = QIcon()
            app_icon.addFile(os.path.join(self.appPath, 'KoalaIcon.png'), QSize(256, 256))
            self.setWindowIcon(app_icon)
        except Exception as ex:
            print(str(ex))
        try:
            from PyQt5.QtWidgets import QStyleFactory
            self.setStyle(QStyleFactory.create(self.settings['window']['windowstyle']))
        except Exception as ex:
            self.logger.error('window style is invalid: ' + str(ex))
            self.logger.info('using window style Fusion')
            self.setStyle(QStyleFactory.create('Fusion'))
        # load stylesheet
        self.styleSheetHandler.loadSheet(self.settings['window']['stylesheetname'])
        self.logger.info('style initialized')
        self.styleSheetChanged.connect(StyledCompleter.updateAllStyles)
        self.styleSheetChanged.emit(self.styleSheet())

    def initData(self):
        self.logger.info('initializing data ...')
        self.logList = loggerwidget.QLogModel()
        self.settingsModel = settingsPage.SettingsModel(self.settings)
        self.tradeList = ttable.QTradeTableModel(self.dataPath)
        self.coinList = ptable.QPortfolioTableModel(self.dataPath)

        self.logger.newLogMessage.connect(lambda status, statusType: self.logList.addString(status, statusType))
        self.tradeList.tradesAdded.connect(lambda tradeList: self.coinList.addTrades(tradeList))
        self.tradeList.tradesRemoved.connect(lambda tradeList: self.coinList.deleteTrades(tradeList))
        self.tradeList.histPricesUpdated.connect(self.coinList.histPricesChanged)
        self.tradeList.histPriceUpdateFinished.connect(self.coinList.histPriceUpdateFinished)
        self.settingsModel.displayCurrenciesChanged.connect(self.coinList.updateDisplayCurrencies)
        self.settingsModel.useWalletTaxFreeLimitYearsChanged.connect(self.coinList.taxYearWalletChanged)
        self.settingsModel.displayCurrenciesChanged.connect(self.tradeList.updateDisplayCurrencies)

        self.logger.info('data initialized')


    # setup layout
    def layoutUI(self):
        self.logger.info('initializing gui layout ...')
        self.mainLayout = QHBoxLayout(self)
        self.setContentsMargins(0, 0, 0, 0)

        # sidebar with buttons for pagecontrol
        from PyQt5.QtWidgets import QFrame, QPushButton
        self.sidebarFrame = QFrame(self)
        self.sidebarFrame.setFrameShape(QFrame.StyledPanel)
        self.sidebarFrame.setFrameShadow(QFrame.Raised)
        self.sidebarFrame.setFixedWidth(120)

        # buttons sidebar
        self.buttonPortfolio = QPushButton("", self.sidebarFrame)
        self.buttonTrades = QPushButton("", self.sidebarFrame)
        self.buttonImport = QPushButton("", self.sidebarFrame)
        self.buttonExport = QPushButton("", self.sidebarFrame)
        self.buttonSettings = QPushButton("", self.sidebarFrame)

        self.initGraphics()

        self.buttonPortfolio.setToolTip('portfolio')
        self.buttonTrades.setToolTip('trades')
        self.buttonImport.setToolTip('import')
        self.buttonExport.setToolTip('export')
        self.buttonSettings.setToolTip('settings')

        self.buttonPortfolio.clicked.connect(lambda: self.showFrame(self.PORTFOLIOPAGEINDEX))
        self.buttonTrades.clicked.connect(lambda: self.showFrame(self.TRADESPAGEINDEX))
        self.buttonImport.clicked.connect(lambda: self.showFrame(self.IMPORTPAGEINDEX))
        self.buttonExport.clicked.connect(lambda: self.showFrame(self.EXPORTPAGEINDEX))
        self.buttonSettings.clicked.connect(lambda: self.showFrame(self.SETTINGSPAGEINDEX))
        buttonHeight = 120
        self.sidebarButtons = [self.buttonPortfolio, self.buttonTrades, self.buttonImport, self.buttonExport, self.buttonSettings]
        self.sidebarLayout = QVBoxLayout(self.sidebarFrame)
        for button in (self.sidebarButtons):
            button.setFixedHeight(buttonHeight)
            #            button.setCheckable(True)
            self.sidebarLayout.addWidget(button)

        self.sidebarLayout.addStretch()

        # %% statusbar for displaying status and progress of ongoing actions
        self.statusbar = controls.StatusBar(self, height=80, dataPath=self.dataPath)
        self.statusbar.setModel(self.logList)

        # %%  stacked Layout for content frames
        self.portfolioPage = PortfolioPage(parent=self, controller=self)
        self.tradesPage = TradesPage(parent=self, controller=self)
        self.importPage = ImportPage(parent=self, controller=self)
        self.exportPage = exportpage.ExportPage(parent=self, controller=self)
        self.settingsModel.useWalletTaxFreeLimitYearsChanged.connect(self.exportPage.taxYearWalletChanged)
        self.settingsPage = pages.SettingsPage(parent=self, controller=self)
        self.pages = [self.portfolioPage, self.tradesPage, self.importPage, self.exportPage, self.settingsPage]
        from PyQt5.QtWidgets import QStackedLayout
        self.stackedContentLayout = QStackedLayout()
        for page in self.pages:
            # stacked content layout
            self.stackedContentLayout.addWidget(page)

        # put frames in vertical layout
        self.verticalFrameLayout = QVBoxLayout()
        self.verticalFrameLayout.setSpacing(0)
        self.verticalFrameLayout.addLayout(self.stackedContentLayout)
        self.verticalFrameLayout.addWidget(self.statusbar)

        # put frames in horizontal layout
        self.horizontalFrameLayout = QHBoxLayout()
        self.horizontalFrameLayout.addWidget(self.sidebarFrame)
        self.horizontalFrameLayout.addLayout(self.verticalFrameLayout)

        # put subLayouts in main layout
        self.mainLayout.addLayout(self.horizontalFrameLayout)

        self.logger.info('gui layout initialized')

    def startThreads(self):
        self.logger.info('starting threads ...')
        self.priceThread = threads.UpdatePriceThread(self.coinList, self.tradeList)
        self.priceThread.coinPricesLoaded.connect(lambda prices, coins: self.coinList.setPrices(prices, coins))
        self.priceThread.coinIconsLoaded.connect(lambda icons, coins: self.coinList.setIcons(icons, coins))
        self.priceThread.coinPriceChartsLoaded.connect(lambda priceChartData: self.coinList.setPriceChartData(priceChartData))
        self.priceThread.historicalPricesLoaded.connect(lambda prices, tradesLeft:
                                                        self.tradeList.setHistPrices(prices, tradesLeft))
        self.priceThread.start()
        self.logger.info('threads started')

    def showFrame(self, pageIndex):
        """Show a frame for the given page index"""
        frame = self.pages[pageIndex]
        if hasattr(frame, 'refresh'):
            frame.refresh()
        self.stackedContentLayout.setCurrentIndex(pageIndex)
        # reset color of all buttons in sidebar
        # for buttonIndex in range(len(self.sidebarButtons)):
        #     button = self.sidebarButtons[buttonIndex]
        #     if buttonIndex == pageIndex:
        #         # do something with selected button
        #         #                button.config(bg=controls.changeColorBrightness(self.sidebar['bg'], 40))
        #         pass
        #     else:
        #         # do something with not selected buttons
        #         #                button.config(bg = self.sidebar['bg'])
        #         pass

    def closeEvent(self, event):
        # save window props
        geometry = self.geometry()
        state = self.windowState()
        self.settings.setWindowProperties(geometry, state)
        # save gui props
        self.settings.setGuiSettings(self.tradesPage.getGuiProps())
        self.settings.setGuiSettings(self.portfolioPage.getGuiProps())
        self.settings.saveSettings()
        event.accept()

    def printStatus(self, status, statusType='i'):
        self.logList.addString(status, statusType)

    # get TradeList
    def getTradeList(self):
        return self.tradeList

    # get CoinList
    def getCoinList(self):
        return self.coinList


def main():
    args = arguments.parse_arguments()
    coreLogger.globalLogger = logger.globalLogger
    coreSettings.mySettings = settings.mySettings
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(argv)

    # Create and show splash screen with better styling
    try:
        splash_pixmap = QPixmap(getResourcePath('graphics/KoalaIcon.ico'))
        if splash_pixmap.isNull():
            # Fallback to PNG if ICO is not found
            splash_pixmap = QPixmap(getResourcePath('graphics/KoalaIcon.png'))
    except:
        # Create a simple colored splash if no icon is found
        splash_pixmap = QPixmap(300, 200)
        splash_pixmap.fill(Qt.darkGray)

    splash = CustomSplashScreen(splash_pixmap)
    splash.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    splash.showMessage("Loading Koalafolio...",
                      Qt.AlignBottom | Qt.AlignCenter,
                      Qt.white)
    splash.show()
    app.processEvents()  # Process events to make sure splash is displayed immediately

    try:
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        app_icon = QIcon()
        app_icon.addFile(getResourcePath('graphics/KoalaIcon.png'), QSize(256, 256))
        app.setWindowIcon(app_icon)
        app.setApplicationName('koalafolio')
    except Exception as ex:
        print(str(ex))

    # Initialize main window with splash reference
    window = PortfolioApp(userDataPath=args.datadir, username=args.username, splash=splash)

    # Close splash when main window is ready
    splash.finish(window)

    exit(app.exec_())

if __name__ == '__main__':
    main()
