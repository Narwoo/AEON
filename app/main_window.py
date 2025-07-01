# app/main_window.py
from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtGui import QAction

from .ui.analyse_tab import AnalyseTab
from .ui.export_tab import ExportTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AEON v0.2 - Die modulare Engine")
        self.showMaximized()
        
        self.project_data = {'persons': {}}

        self._create_menu_bar()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.analyse_tab = AnalyseTab(self.project_data)
        self.export_tab = ExportTab(self.project_data)
        
        self.tabs.addTab(self.analyse_tab, "1. Analyse & Verwaltung")
        self.tabs.addTab(self.export_tab, "2. Datensatz-Export")

        self.analyse_tab.data_updated.connect(self.export_tab.update_person_selector)
        
    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Datei")
        exit_action = QAction("Beenden", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)