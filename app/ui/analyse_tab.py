# app/ui/analyse_tab.py
import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog, 
                             QScrollArea, QGridLayout, QLabel, QListWidget, QListWidgetItem, 
                             QSplitter, QInputDialog, QMenu)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QAction

from ..workers.face_worker import FaceRecognitionWorker
from ..ui_utils import create_progress_log_area

class AnalyseTab(QWidget):
    data_updated = pyqtSignal()

    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("Erkannte Personen:"))
        self.person_list_widget = QListWidget()
        self.person_list_widget.currentItemChanged.connect(self.display_person_gallery)
        self.person_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.person_list_widget.customContextMenuRequested.connect(self.show_person_context_menu)
        left_layout.addWidget(self.person_list_widget)
        splitter.addWidget(left_panel)
        
        right_panel_widget = QWidget()
        right_layout = QVBoxLayout(right_panel_widget)
        self.load_button = QPushButton("Bilderordner laden & Gesichter erkennen")
        self.load_button.setFixedHeight(40)
        self.load_button.clicked.connect(self.start_face_recognition)
        right_layout.addWidget(self.load_button)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.gallery_container = QWidget()
        self.gallery_layout = QGridLayout(self.gallery_container)
        self.scroll_area.setWidget(self.gallery_container)
        right_layout.addWidget(self.scroll_area)
        
        progress_log_area, self.progress_bar, self.log_window = create_progress_log_area()
        right_layout.addWidget(progress_log_area)
        
        splitter.addWidget(right_panel_widget)
        splitter.setSizes([300, 1300])

    def start_face_recognition(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Ordner auswählen")
        if folder_path:
            self.clear_all()
            self.log_window.clear()
            self.log_window.setVisible(True)
            self.progress_bar.setVisible(True)
            image_extensions = ['.jpg', '.jpeg', '.png']
            self.project_data['all_image_paths'] = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if any(f.lower().endswith(ext) for ext in image_extensions)]
            
            self.load_button.setEnabled(False)
            self.thread = QThread()
            self.worker = FaceRecognitionWorker(self.project_data['all_image_paths'])
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_recognition_finished)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()

    def on_recognition_finished(self, person_data):
        self.project_data['persons'] = person_data
        self.update_person_list()
        self.load_button.setEnabled(True)
        self.data_updated.emit()

    def update_person_list(self):
        self.person_list_widget.clear()
        all_item = QListWidgetItem(f"Alle Bilder ({len(self.project_data.get('all_image_paths', []))})")
        all_item.setData(Qt.ItemDataRole.UserRole, {'type': 'all', 'data': self.project_data.get('all_image_paths', [])})
        self.person_list_widget.addItem(all_item)
        for person_name, data in sorted(self.project_data['persons'].items()):
            item = QListWidgetItem(f"{person_name} ({len(data['images'])})")
            item.setData(Qt.ItemDataRole.UserRole, {'type': 'person', 'name': person_name, 'data': data['images']})
            self.person_list_widget.addItem(item)
        if self.person_list_widget.count() > 0:
            self.person_list_widget.setCurrentRow(0)

    def display_person_gallery(self, current_item, previous_item):
        if current_item is None: return
        for i in reversed(range(self.gallery_layout.count())): 
            self.gallery_layout.itemAt(i).widget().deleteLater()
        
        item_data = current_item.data(Qt.ItemDataRole.UserRole)
        image_paths = []
        if item_data['type'] == 'all':
            image_paths = item_data['data']
        elif item_data['type'] == 'person':
            image_paths = [img_info['path'] for img_info in item_data['data']]
        
        self.populate_gallery(image_paths)

    def populate_gallery(self, image_paths):
        column_count = 8
        thumbnail_size = (192, 192)
        row, col = 0, 0
        for image_path in image_paths:
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(thumbnail_size[0], thumbnail_size[1], Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.gallery_layout.addWidget(label, row, col)
            col += 1
            if col >= column_count: col, row = 0, row + 1


    def show_person_context_menu(self, pos):
        item = self.person_list_widget.itemAt(pos)
        item_data = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not item_data or item_data['type'] == 'all': return
        menu = QMenu()
        rename_action = QAction("Umbenennen", self)
        rename_action.triggered.connect(lambda: self.rename_person(item))
        menu.addAction(rename_action)
        menu.exec(self.person_list_widget.mapToGlobal(pos))
    
    def rename_person(self, item):
        item_data = item.data(Qt.ItemDataRole.UserRole)
        old_name = item_data['name']
        new_name, ok = QInputDialog.getText(self, "Person umbenennen", "Neuer Name:", text=old_name)
        if ok and new_name and new_name != old_name and new_name not in self.project_data['persons']:
            self.project_data['persons'][new_name] = self.project_data['persons'].pop(old_name)
            self.update_person_list()
            self.data_updated.emit()

    def update_progress(self, current, total, message):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.log_window.append(message)

    def clear_all(self):
        self.person_list_widget.clear()
        self.project_data['persons'] = {}
        self.project_data['all_image_paths'] = []
        for i in reversed(range(self.gallery_layout.count())):
            self.gallery_layout.itemAt(i).widget().deleteLater()