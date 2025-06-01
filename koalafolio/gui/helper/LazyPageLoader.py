# -*- coding: utf-8 -*-
"""
Lazy Page Loader for optimized startup performance

Created for koalafolio optimization
"""

from PyQt5.QtCore import QObject, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class LazyPageLoader(QObject):
    """Handles lazy loading of GUI pages to improve startup performance"""

    pageLoaded = pyqtSignal(int, QWidget)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.loaded_pages = {}
        self.loading_pages = set()

    def loadPage(self, page_index, page_class_name):
        """Load a page lazily when first accessed"""
        if page_index in self.loaded_pages:
            return self.loaded_pages[page_index]

        if page_index in self.loading_pages:
            return None  # Already loading

        self.loading_pages.add(page_index)

        # Use QTimer to load page in next event loop iteration
        QTimer.singleShot(0, lambda: self._loadPageAsync(page_index, page_class_name))

        return None

    def _loadPageAsync(self, page_index, page_class_name):
        """Actually load the page asynchronously"""
        try:
            # Import and create the page
            if page_class_name == 'PortfolioPage':
                from pages.PortfolioPage import PortfolioPage
                page = PortfolioPage(parent=self.parent, controller=self.parent)
            elif page_class_name == 'TradesPage':
                from pages.TradesPage import TradesPage
                page = TradesPage(parent=self.parent, controller=self.parent)
            elif page_class_name == 'ImportPage':
                from pages.ImportPage import ImportPage
                page = ImportPage(parent=self.parent, controller=self.parent)
            elif page_class_name == 'ExportPage':
                import pages.ExportPage as exportpage
                page = exportpage.ExportPage(parent=self.parent, controller=self.parent)
            elif page_class_name == 'SettingsPage':
                import pages.Qpages as pages
                page = pages.SettingsPage(parent=self.parent, controller=self.parent)
            else:
                raise ValueError(f"Unknown page class: {page_class_name}")

            self.loaded_pages[page_index] = page
            self.loading_pages.discard(page_index)
            self.pageLoaded.emit(page_index, page)

        except Exception as ex:
            print(f"Error loading page {page_class_name} at index {page_index}: {ex}")
            import traceback
            traceback.print_exc()
            self.loading_pages.discard(page_index)

    def getPage(self, page_index):
        """Get a loaded page or None if not loaded yet"""
        return self.loaded_pages.get(page_index)

    def isPageLoaded(self, page_index):
        """Check if a page is loaded"""
        return page_index in self.loaded_pages

    def isPageLoading(self, page_index):
        """Check if a page is currently loading"""
        return page_index in self.loading_pages


class PlaceholderPage(QWidget):
    """Placeholder widget shown while pages are loading"""

    def __init__(self, page_name="Page", parent=None):
        super().__init__(parent)
        self.page_name = page_name
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)

        # Add loading indicator with larger font
        loading_label = QLabel(f"Loading {self.page_name}...")
        loading_label.setAlignment(Qt.AlignCenter)
        font = loading_label.font()
        font.setPointSize(14)
        font.setBold(True)
        loading_label.setFont(font)

        # Add progress indicator (simple animated dots)
        self.progress_label = QLabel("●○○")
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_font = self.progress_label.font()
        progress_font.setPointSize(16)
        self.progress_label.setFont(progress_font)

        layout.addStretch()
        layout.addWidget(loading_label)
        layout.addWidget(self.progress_label)
        layout.addStretch()

        # Animate the progress indicator
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.updateProgress)
        self.animation_timer.start(500)  # Update every 500ms
        self.animation_state = 0

    def updateProgress(self):
        """Update the progress animation"""
        states = ["●○○", "○●○", "○○●", "○●○"]
        self.progress_label.setText(states[self.animation_state])
        self.animation_state = (self.animation_state + 1) % len(states)

    def refresh(self):
        """Placeholder refresh method"""
        pass
