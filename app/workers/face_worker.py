# app/workers/face_worker.py
import os
import face_recognition
from PyQt6.QtCore import QObject, pyqtSignal

class FaceRecognitionWorker(QObject):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int, int, str)

    def __init__(self, image_paths):
        super().__init__()
        self.image_paths = image_paths

    def run(self):
        total_images = len(self.image_paths)
        self.progress.emit(0, total_images, "Starte Gesichtserkennung...")
        known_persons = []
        person_data = {}

        for index, image_path in enumerate(self.image_paths):
            msg = f"Analysiere: {os.path.basename(image_path)}"
            self.progress.emit(index + 1, total_images, msg)
            try:
                image = face_recognition.load_image_file(image_path)
                face_locations = face_recognition.face_locations(image)
                current_face_encodings = face_recognition.face_encodings(image, face_locations)

                if not current_face_encodings:
                    self.progress.emit(index + 1, total_images, f"  -> Kein Gesicht in {os.path.basename(image_path)} gefunden.")
                    continue

                for i, face_encoding in enumerate(current_face_encodings):
                    person_name = None
                    for person in known_persons:
                        matches = face_recognition.compare_faces(person['encodings'], face_encoding, tolerance=0.6)
                        if True in matches:
                            person_name = person['name']
                            break
                    
                    if person_name is None:
                        person_name = f"Person {len(known_persons) + 1}"
                        known_persons.append({'name': person_name, 'encodings': [face_encoding]})
                        person_data[person_name] = {'images': []}
                        self.progress.emit(index + 1, total_images, f"  -> Neues Gesicht entdeckt: {person_name}")
                    
                    image_info = {'path': image_path, 'face_loc': face_locations[i]}
                    if image_info not in person_data[person_name]['images']:
                        person_data[person_name]['images'].append(image_info)
            except Exception as e:
                self.progress.emit(index + 1, total_images, f"  -> FEHLER bei {os.path.basename(image_path)}: {e}")

        self.progress.emit(total_images, total_images, "Analyse abgeschlossen.")
        self.finished.emit(person_data)