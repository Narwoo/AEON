# app/ui_utils.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QTextEdit

def create_progress_log_area():
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 10, 0, 0)
    
    progress_bar = QProgressBar()
    progress_bar.setVisible(False)
    
    log_window = QTextEdit()
    log_window.setReadOnly(True)
    log_window.setFixedHeight(150)
    log_window.setVisible(False)
    
    layout.addWidget(progress_bar)
    layout.addWidget(log_window)
    
    return container, progress_bar, log_window