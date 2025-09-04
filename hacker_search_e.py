"""
Hacker Search Engines — Pro GUI (Multi-Select Results + Theme Toggle)
--------------------------------------------------------------------
Features:
1. Reliable Back navigation (QStackedWidget)
2. Double-click category = open results instantly
3. Wider Link column, smooth scrolling
4. Multi-select rows in results (open/copy multiple links)
5. Dark/Light theme toggle
"""

import sys
import webbrowser

# --- Prefer PySide6, fallback to PyQt5 ---
try:
    from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression
    from PySide6.QtGui import QAction, QKeySequence, QStandardItemModel, QStandardItem, QColor, QPalette
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QListWidget, QListWidgetItem, QPushButton, QTabWidget, QTableView, QHeaderView,
        QMenu, QMessageBox, QAbstractItemView, QStyleFactory, QStatusBar,
        QStackedWidget, QToolBar
    )
    PYSIDE = True
except Exception:
    from PyQt5.QtCore import Qt, QSortFilterProxyModel, QRegExp as QRegularExpression
    from PyQt5.QtGui import QAction, QKeySequence, QStandardItemModel, QStandardItem, QColor, QPalette
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QListWidget, QListWidgetItem, QPushButton, QTabWidget, QTableView, QHeaderView,
        QMenu, QMessageBox, QAbstractItemView, QStyleFactory, QStatusBar,
        QStackedWidget, QToolBar
    )
    PYSIDE = False

# --- Import your dataset ---
try:
    from search_engines_data import SEARCH_ENGINES
except Exception as e:
    SEARCH_ENGINES = {}
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


APP_NAME = "Hacker Search Engines Pro"


def set_dark_fusion_palette(app):
    """Apply a clean dark Fusion theme."""
    app.setStyle(QStyleFactory.create("Fusion"))
    palette = QPalette()

    bg = QColor(37, 37, 38)
    base = QColor(30, 30, 30)
    alt = QColor(45, 45, 48)
    text = QColor(220, 220, 220)
    disabled = QColor(127, 127, 127)
    highlight = QColor(14, 99, 156)
    link = QColor(85, 170, 255)

    palette.setColor(QPalette.Window, bg)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, base)
    palette.setColor(QPalette.AlternateBase, alt)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, bg)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.Link, link)

    app.setPalette(palette)


def set_light_fusion_palette(app):
    """Apply clean light Fusion theme."""
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setPalette(app.style().standardPalette())


# --- Results Table ---
class ResultsTable(QTableView):
    def __init__(self, rows):
        super().__init__()

        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)  # ✅ Multi-select
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)

        # Smooth scrolling
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(15)
        self.horizontalScrollBar().setSingleStep(15)

        # Allow horizontal scroll
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # Model
        self.model_raw = QStandardItemModel(0, 3, self)
        self.model_raw.setHorizontalHeaderLabels(["Name", "Link", "Description"])
        for name, url, desc in rows:
            items = [
                QStandardItem(str(name)),
                QStandardItem(str(url)),
                QStandardItem(str(desc if desc else "-")),
            ]
            for it in items:
                it.setEditable(False)
            self.model_raw.appendRow(items)

        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model_raw)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        self.setModel(self.proxy)

        # Column widths
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 600)
        self.setColumnWidth(2, 400)

        # Events
        self.doubleClicked.connect(self._open_link)

        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

    def set_filter(self, text: str):
        if PYSIDE:
            self.proxy.setFilterRegularExpression(QRegularExpression(text))
        else:
            self.proxy.setFilterRegExp(text)

    def _open_link(self):
        """Open all selected links in browser."""
        indexes = self.selectionModel().selectedRows(1)  # column 1 = Link
        for idx in indexes:
            link_text = self.proxy.data(idx)
            if link_text and str(link_text).lower().startswith("http"):
                webbrowser.open(str(link_text))

    def _menu(self, pos):
        """Context menu supporting multiple selections."""
        indexes = self.selectionModel().selectedRows(1)
        if not indexes:
            return
        menu = QMenu(self)
        open_act = menu.addAction("Open Selected Links")
        copy_link = menu.addAction("Copy Selected Links")
        action = menu.exec_(self.viewport().mapToGlobal(pos))
        links = [self.proxy.data(i) for i in indexes]
        links = [l for l in links if l and str(l).startswith("http")]
        if action == open_act:
            for l in links:
                webbrowser.open(l)
        elif action == copy_link:
            QApplication.clipboard().setText("\n".join(links))


# --- Results Page ---
class ResultsPage(QWidget):
    """Results page with tabs (multi-select enabled)."""
    def __init__(self, on_back):
        super().__init__()
        self.on_back = on_back

        layout = QVBoxLayout(self)

        # Top bar
        top = QHBoxLayout()
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Quick filter…")
        top.addWidget(QLabel("Filter:"))
        top.addWidget(self.filter_edit, 1)
        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.on_back)
        top.addWidget(back_btn)
        layout.addLayout(top)

        # Tabs (results only)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.filter_edit.textChanged.connect(self._apply_filter)

    def populate(self, data: dict[str, list[tuple]]):
        self.tabs.clear()
        for cat, rows in data.items():
            table = ResultsTable(rows)
            self.tabs.addTab(table, cat)

    def _apply_filter(self, text: str):
        table = self.tabs.currentWidget()
        if isinstance(table, ResultsTable):
            table.set_filter(text)


# --- Category Page ---
class CategoryPage(QWidget):
    def __init__(self, categories: list[str], on_submit):
        super().__init__()
        self.on_submit = on_submit

        main = QVBoxLayout(self)
        header = QLabel("Select Categories")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        main.addWidget(header)

        # Search
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter categories…")
        self.search_edit.textChanged.connect(self.apply_filter)
        search_row.addWidget(self.search_edit)
        main.addLayout(search_row)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.setAlternatingRowColors(True)
        for c in sorted(categories, key=str.lower):
            QListWidgetItem(c, self.list_widget)
        self.list_widget.itemDoubleClicked.connect(self._open_single_category)
        main.addWidget(self.list_widget, 1)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch(1)
        submit_btn = QPushButton("Show Results ▶")
        submit_btn.clicked.connect(self._submit)
        footer.addWidget(submit_btn)
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.window().close)
        footer.addWidget(exit_btn)
        main.addLayout(footer)

    def apply_filter(self, text: str):
        text = text.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text not in item.text().lower())

    def _submit(self):
        selected = [i.text() for i in self.list_widget.selectedItems()]
        self.on_submit(selected)

    def _open_single_category(self, item):
        self.on_submit([item.text()])


# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1200, 700)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Pages
        self.category_page = CategoryPage(list(SEARCH_ENGINES.keys()), self._open_results_for)
        self.results_page = ResultsPage(self.show_categories)

        # Stacked navigation
        self.stack = QStackedWidget()
        self.stack.addWidget(self.category_page)  # index 0
        self.stack.addWidget(self.results_page)   # index 1
        self.setCentralWidget(self.stack)

        # Toolbar
        tb = QToolBar("Main")
        self.addToolBar(tb)

        # Back action
        self.act_back = QAction("Back", self)
        self.act_back.setShortcut(QKeySequence("Esc"))
        self.act_back.triggered.connect(self.show_categories)
        tb.addAction(self.act_back)

        # Theme toggle
        self.act_theme = QAction("Toggle Dark/Light", self)
        self.act_theme.setCheckable(True)
        self.act_theme.setChecked(True)  # start in Dark
        self.act_theme.triggered.connect(self._toggle_theme)
        tb.addAction(self.act_theme)

        self.show_categories()

    def show_categories(self):
        self.stack.setCurrentIndex(0)
        self.status.showMessage("Select categories. Tip: double-click a category to open it.")

    def show_results(self):
        self.stack.setCurrentIndex(1)
        self.status.showMessage("Double-click a row to open link(s). Right-click for more.")

    def _open_results_for(self, cats: list[str]):
        if not cats:
            QMessageBox.warning(self, "No Selection", "Choose at least one category.")
            return
        data = {c: SEARCH_ENGINES.get(c, []) for c in cats}
        self.results_page.populate(data)
        self.show_results()

    def _toggle_theme(self):
        if self.act_theme.isChecked():
            set_dark_fusion_palette(QApplication.instance())
        else:
            set_light_fusion_palette(QApplication.instance())


def main():
    app = QApplication(sys.argv)
    set_dark_fusion_palette(app)

    win = MainWindow()
    win.show()

    try:
        sys.exit(app.exec())
    except Exception:
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
