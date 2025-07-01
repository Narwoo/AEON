# app/workers/export_worker.py
import os
from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal

class ExportWorker(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)

    def __init__(self, export_params):
        super().__init__()
        self.params = export_params

    def run(self):
        images_to_process = self.params['images']
        total_images = len(images_to_process)
        folder_name = f"{self.params['repeats']}_{self.params['trigger_word']}"
        output_path = os.path.join(self.params['output_dir'], folder_name)
        os.makedirs(output_path, exist_ok=True)
        self.progress.emit(0, total_images, f"Export-Ordner erstellt: {output_path}")

        for i, image_info in enumerate(images_to_process):
            try:
                msg = f"Verarbeite: {os.path.basename(image_info['path'])}"
                self.progress.emit(i + 1, total_images, msg)
                
                img = Image.open(image_info['path'])
                
                # Gesichtsbereich extrahieren
                top, right, bottom, left = image_info['face_loc']
                
                # Sicherheits-Puffer hinzufügen, um mehr vom Kopf zu erfassen
                pad_x = (right - left) // 4
                pad_y = (bottom - top) // 4
                
                left = max(0, left - pad_x)
                top = max(0, top - pad_y)
                right = min(img.width, right + pad_x)
                bottom = min(img.height, bottom + pad_y)
                
                face_image = img.crop((left, top, right, bottom))
                
                # Größe anpassen
                target_size = (self.params['resolution'], self.params['resolution'])
                face_image = face_image.resize(target_size, Image.Resampling.LANCZOS)
                
                # Speichern mit eindeutigem Namen
                base_filename = f"{self.params['trigger_word']}_{i+1}"
                save_path = os.path.join(output_path, f"{base_filename}.png")
                face_image.save(save_path, "PNG")
            except Exception as e:
                self.progress.emit(i + 1, total_images, f"  -> FEHLER bei {os.path.basename(image_info['path'])}: {e}")

        self.finished.emit(f"Export von {total_images} Bildern nach {output_path} abgeschlossen.")