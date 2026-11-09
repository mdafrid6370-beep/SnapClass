

import json
import insightface
from insightface.app import FaceAnalysis
import numpy as np
import streamlit as st
from PIL import Image, ImageOps
import cv2

from src.database.db import get_all_students


@st.cache_resource
def load_insightface_app():
    app = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
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
    Ensures image is correctly oriented according to EXIF data, resized for ultra-fast CPU inference,
    and converted to BGR NumPy array. Fixes frozen UI issues caused by high-resolution camera photos.
    """
    if isinstance(image_input, Image.Image):
        img = ImageOps.exif_transpose(image_input)
    elif isinstance(image_input, np.ndarray):
        img = Image.fromarray(image_input)
    else:
        img = Image.open(image_input)
        img = ImageOps.exif_transpose(img)

    # Downscale high-resolution camera images to max 640px for 50x faster CPU inference
    img.thumbnail((640, 640), Image.Resampling.LANCZOS)
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


def check_face_occlusion_and_pose(face, img_w, img_h):
    """
    Analyzes InsightFace facial keypoints, pose, bounding box, and detection score.
    Returns: (is_valid, warning_message)
    Detects:
    - Half-covered / occluded faces (hands, masks, cloth over face)
    - Sideways turned faces (|yaw| > 35 degrees)
    - Edge-cropped / cut-off faces at screen borders
    """
    bbox = face.bbox.astype(int)
    x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]

    # 1. Edge crop check (face cut off at screen border)
    margin = 5
    if x1 <= margin or y1 <= margin or x2 >= (img_w - margin) or y2 >= (img_h - margin):
        return False, "Face is cut off at the camera border. Please center your face in the frame."

    w = x2 - x1
    h = y2 - y1
    if h <= 0 or w <= 0:
        return False, "Invalid face detection bounds."

    # 2. Aspect ratio check (half-face or severe angle)
    aspect = w / float(h)
    if aspect < 0.48 or aspect > 1.25:
        return False, "Half of your face is covered or obscured."

    # 3. Head Pose (Yaw / Pitch) check
    if hasattr(face, 'pose') and face.pose is not None:
        pitch, yaw, roll = face.pose
        if abs(yaw) > 35.0:
            return False, "Face is turned too far to the side. Please look directly at the camera."
        if abs(pitch) > 30.0:
            return False, "Face is tilted too far up or down. Please look straight ahead."

    # 4. Keypoint Symmetry check (5 keypoints: Left Eye, Right Eye, Nose, Left Mouth, Right Mouth)
    if hasattr(face, 'kps') and face.kps is not None and len(face.kps) == 5:
        kps = face.kps
        left_eye, right_eye, nose = kps[0], kps[1], kps[2]

        dist_l_eye_nose = abs(nose[0] - left_eye[0])
        dist_r_eye_nose = abs(right_eye[0] - nose[0])
        if dist_l_eye_nose > 0 and dist_r_eye_nose > 0:
            ratio = dist_l_eye_nose / float(dist_r_eye_nose)
            if ratio < 0.35 or ratio > 2.85:
                return False, "Half of your face is covered or turned away."

    # 5. Detection Score
    det_score = getattr(face, 'det_score', 1.0)
    if det_score < 0.45:
        return False, "Face is unclear or partially covered."

    return True, None


def get_face_embeddings_with_quality(image_input):
    image_bgr = preprocess_image(image_input)
    img_h, img_w = image_bgr.shape[:2]

    app = load_insightface_app()
    faces = app.get(image_bgr)

    # Fallback with CLAHE lighting normalization if no faces found
    if len(faces) == 0:
        enhanced_bgr = apply_clahe_lighting_normalization(image_bgr)
        faces = app.get(enhanced_bgr)

    encodings = []
    quality_warnings = []

    for face in faces:
        is_valid, warn_msg = check_face_occlusion_and_pose(face, img_w, img_h)
        if not is_valid and warn_msg:
            quality_warnings.append(warn_msg)

        if hasattr(face, 'normed_embedding') and face.normed_embedding is not None:
            encodings.append((face.normed_embedding, is_valid, warn_msg))
        elif hasattr(face, 'embedding') and face.embedding is not None:
            norm = np.linalg.norm(face.embedding)
            enc = face.embedding / norm if norm > 0 else face.embedding
            encodings.append((enc, is_valid, warn_msg))

    return encodings, len(faces), quality_warnings


def get_face_embeddings(image_input):
    items, _, _ = get_face_embeddings_with_quality(image_input)
    return [item[0] for item in items]


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
    items, num_faces, quality_warnings = get_face_embeddings_with_quality(class_image_np)

    detected_student = {}
    vector_data = get_student_face_vectors()

    # Return primary occlusion warning if any face is invalid/half-covered
    occlusion_warning = quality_warnings[0] if quality_warnings else None

    if not vector_data or len(items) == 0:
        return detected_student, [], num_faces, occlusion_warning
    
    X_train = vector_data['X']
    y_train = vector_data['y']

    all_students = sorted(list(set(y_train)))
    similarity_threshold = 0.38

    for encoding, is_valid, _ in items:
        if not is_valid:
            continue

        encoding_arr = np.array(encoding, dtype=np.float64)
        norm = np.linalg.norm(encoding_arr)
        if norm > 0:
            encoding_arr = encoding_arr / norm

        similarities = np.dot(X_train, encoding_arr)
        best_idx = np.argmax(similarities)
        max_similarity = similarities[best_idx]

        if max_similarity >= similarity_threshold:
            predicted_id = y_train[best_idx]
            if predicted_id not in detected_student or max_similarity > detected_student[predicted_id]:
                detected_student[predicted_id] = float(max_similarity)

    return detected_student, all_students, num_faces, occlusion_warning



