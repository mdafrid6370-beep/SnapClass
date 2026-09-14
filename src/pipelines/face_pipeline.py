

import json
import insightface
from insightface.app import FaceAnalysis
import numpy as np
import streamlit as st

from src.database.db import get_all_students


@st.cache_resource
def load_insightface_app():
    app = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app

def get_face_embeddings(image_np):
    app = load_insightface_app()
    # Convert RGB to BGR for InsightFace if 3-channel image
    if len(image_np.shape) == 3 and image_np.shape[2] == 3:
        image_bgr = image_np[:, :, ::-1]
    else:
        image_bgr = image_np

    faces = app.get(image_bgr)
    encodings = []

    for face in faces:
        # normed_embedding is a 512-d normalized L2 embedding vector
        if hasattr(face, 'normed_embedding') and face.normed_embedding is not None:
            encodings.append(face.normed_embedding)
        elif hasattr(face, 'embedding') and face.embedding is not None:
            norm = np.linalg.norm(face.embedding)
            encodings.append(face.embedding / norm if norm > 0 else face.embedding)

    return encodings

@st.cache_resource
def get_student_face_vectors():
    X = []
    y = []

    student_db = get_all_students()

    if not student_db:
        return None
    
    for student in student_db:
        embedding = student.get('face_embedding')
        if embedding:
            if isinstance(embedding, str):
                try:
                    embedding = json.loads(embedding)
                except Exception:
                    continue
            arr = np.array(embedding, dtype=np.float64)
            norm = np.linalg.norm(arr)
            if norm > 0:
                arr = arr / norm
            X.append(arr)
            y.append(student.get('student_id'))

    if len(X) == 0:
        return None
    
    return {'X': np.array(X), 'y': y}


def train_classifier():
    st.cache_resource.clear()
    vectors = get_student_face_vectors()
    return bool(vectors)

def predict_attendance(class_image_np):
    encodings = get_face_embeddings(class_image_np)

    detected_student = {}

    vector_data = get_student_face_vectors()

    if not vector_data:
        return detected_student, [], len(encodings)
    
    X_train = vector_data['X']
    y_train = vector_data['y']

    all_students = sorted(list(set(y_train)))
    # Cosine similarity threshold for InsightFace ArcFace (range -1.0 to 1.0; >= 0.45 is match)
    similarity_threshold = 0.45

    for encoding in encodings:
        encoding_arr = np.array(encoding, dtype=np.float64)
        norm = np.linalg.norm(encoding_arr)
        if norm > 0:
            encoding_arr = encoding_arr / norm

        similarities = np.dot(X_train, encoding_arr)
        best_idx = np.argmax(similarities)
        max_similarity = similarities[best_idx]

        if max_similarity >= similarity_threshold:
            predicted_id = y_train[best_idx]
            detected_student[predicted_id] = True

    return detected_student, all_students, len(encodings)



