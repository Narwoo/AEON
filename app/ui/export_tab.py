# app/ui/export_tab.py
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QFileDialog, QComboBox, 
                             QLineEdit, QSpinBox, QFormLayout, QGroupBox, QMessageBox)
from PyQt6.QtCore import QThread

from ..workers.export_worker import ExportWorker

class ExportTab(QWidget):
    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        settings_group = QGroupBox("Export-Einstellungen")
        form_layout = QFormLayout()

        self.person_selector = QComboBox()
        form_layout.addRow("Person auswählen:", self.person_selector)

        self.trigger_word_input = QLineEdit()
        self.repeats_input = QSpinBox()
        self.repeats_input.setRange(1, 100)
        self.repeats_input.setValue(15)
        form_layout.addRow("Trigger Word:", self.trigger_word_input)
        form_layout.addRow("Wiederholungen:", self.repeats_input)
        
        self.resolution_selector = QComboBox()
        self.resolution_selector.addItems([
            "512x512 - Standard für SD 1.5",
            "768x768 - Höhere Qualität",
            "1024x1024 - Standard für SDXL"
        ])
        form_layout.addRow("Auflösung:", self.resolution_selector)

        settings_group.setLayout(form_layout)
        main_layout.addWidget(settings_group)
        
        self.export_button = QPushButton("Datensatz exportieren")
        self.export_button.setFixedHeight(40)
        self.export_button.clicked.connect(self.start_export)
        main_layout.addWidget(self.export_button)
        main_layout.addStretch()

    def update_person_selector(self):
        current_selection = self.person_selector.currentText()
        self.person_selector.clear()
        sorted_persons = sorted(self.project_data['persons'].keys())
        if sorted_persons:
            self.person_selector.addItems(sorted_persons)
            if current_selection in sorted_persons:
                self.person_selector.setCurrentText(current_selection)

    def start_export(self):
        output_dir = QFileDialog.getExistingDirectory(self, "Export-Ordner auswählen")
        if not output_dir: return

        person_name = self.person_selector.currentText()
        if not person_name:
            QMessageBox.warning(self, "Fehler", "Bitte wähle eine Person zum Exportieren aus.")
            return

        resolution_text = self.resolution_selector.currentText().split('x')[0]
        export_params = {
            'images': self.project_data['persons'][person_name]['images'],
            'output_dir': output_dir,
            'trigger_word': self.trigger_word_input.text(),
            'repeats': self.repeats_input.value(),
            'resolution': int(resolution_text)
        }
        if not export_params['trigger_word']:
            QMessageBox.warning(self, "Fehler", "Bitte gib ein Trigger Word ein.")
            return

        # Den Export-Worker vollständig integrieren
        self.parent().parent().tabs.setCurrentIndex(0) # Wechsle zum Analyse-Tab
        analyse_tab = self.parent().parent().analyse_tab
        
        analyse_tab.log_window.setVisible(True)
        analyse_tab.progress_bar.setVisible(True)
        
        self.thread = QThread()
        self.worker = ExportWorker(export_params)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda msg: analyse_tab.log_window.append(f"\n--- {msg} ---\n"))
        self.worker.progress.connect(analyse_tab.update_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()