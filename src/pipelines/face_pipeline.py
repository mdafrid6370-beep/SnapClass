

import json
import insightface
from insightface.app import FaceAnalysis
import numpy as np
import streamlit as st
from PIL import Image, ImageOps
import cv2

from src.database.db import get_all_students


@st.cache_resource
def load_insightface_app(det_size=(640, 640)):
    app = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=det_size)
    return app


def apply_clahe_lighting_normalization(image_bgr):
    """
    Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) on Lightness channel.
    Normalizes harsh shadows, dark room lighting, and background glare for stable face detection.
    """
    try:
        lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced_bgr = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return enhanced_bgr
    except Exception:
        return image_bgr


def preprocess_image(image_input):
    """
    Ensures image is correctly oriented according to EXIF data and converted to BGR NumPy array.
    Fixes upside-down/sideways face detection issues on mobile phones.
    """
    if isinstance(image_input, Image.Image):
        img = ImageOps.exif_transpose(image_input)
        image_np = np.array(img)
    elif isinstance(image_input, np.ndarray):
        image_np = image_input
    else:
        img = Image.open(image_input)
        img = ImageOps.exif_transpose(img)
        image_np = np.array(img)

    # Convert RGB to BGR for InsightFace if 3-channel image
    if len(image_np.shape) == 3 and image_np.shape[2] == 3:
        image_bgr = image_np[:, :, ::-1]
    elif len(image_np.shape) == 3 and image_np.shape[2] == 4:
        # RGBA to BGR
        image_bgr = image_np[:, :, :3][:, :, ::-1]
    else:
        image_bgr = image_np

    return image_bgr


def get_face_embeddings(image_input):
    image_bgr = preprocess_image(image_input)

    # Pass 1: Standard 640x640 detection
    app_640 = load_insightface_app(det_size=(640, 640))
    faces = app_640.get(image_bgr)

    # Pass 2: Fallback with CLAHE lighting normalization if no faces found
    if len(faces) == 0:
        enhanced_bgr = apply_clahe_lighting_normalization(image_bgr)
        faces = app_640.get(enhanced_bgr)

    # Pass 3: Fallback with 320x320 detection scale for close selfie crops if still no faces found
    if len(faces) == 0:
        app_320 = load_insightface_app(det_size=(320, 320))
        faces = app_320.get(image_bgr)

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
        sid = student.get('student_id')
        if not embedding or not sid:
            continue
            
        if isinstance(embedding, str):
            try:
                embedding = json.loads(embedding)
            except Exception:
                continue
                
        # Support single 512-d vector OR list of multiple 512-d vectors per student
        vector_list = []
        if isinstance(embedding, list) and len(embedding) > 0:
            if isinstance(embedding[0], list):
                vector_list = embedding
            elif isinstance(embedding[0], (int, float)):
                vector_list = [embedding]

        for vec in vector_list:
            arr = np.array(vec, dtype=np.float64)
            norm = np.linalg.norm(arr)
            if norm > 0:
                arr = arr / norm
                X.append(arr)
                y.append(sid)

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
    # Cosine similarity threshold for InsightFace ArcFace (range -1.0 to 1.0; >= 0.38 is match)
    similarity_threshold = 0.38

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
            # Store best match similarity score
            if predicted_id not in detected_student or max_similarity > detected_student[predicted_id]:
                detected_student[predicted_id] = float(max_similarity)

    return detected_student, all_students, len(encodings)



