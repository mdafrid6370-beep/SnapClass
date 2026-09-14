import cv2
import numpy as np
import streamlit as st

try:
    import av
    from streamlit_webrtc import VideoProcessorBase
    HAS_WEBRTC = True
except ImportError:
    HAS_WEBRTC = False
    VideoProcessorBase = object

from src.pipelines.face_pipeline import load_insightface_app, get_student_face_vectors


class LiveFaceAttendanceProcessor(VideoProcessorBase):
    def __init__(self):
        self.vector_data = get_student_face_vectors()
        self.detected_students = set()

    def recv(self, frame):
        if not HAS_WEBRTC or frame is None:
            return frame

        img = frame.to_ndarray(format="bgr24")

        try:
            app = load_insightface_app()
            faces = app.get(img)

            # Reload vectors if empty
            if not self.vector_data:
                self.vector_data = get_student_face_vectors()

            similarity_threshold = 0.45

            for face in faces:
                bbox = face.bbox.astype(int)
                encoding = face.normed_embedding

                if encoding is None and hasattr(face, 'embedding') and face.embedding is not None:
                    norm = np.linalg.norm(face.embedding)
                    encoding = face.embedding / norm if norm > 0 else face.embedding

                label = "Unknown"
                color = (0, 0, 255)  # Red box for unrecognized face

                if self.vector_data and encoding is not None:
                    encoding_arr = np.array(encoding, dtype=np.float64)
                    norm = np.linalg.norm(encoding_arr)
                    if norm > 0:
                        encoding_arr = encoding_arr / norm

                    similarities = np.dot(self.vector_data['X'], encoding_arr)
                    best_idx = np.argmax(similarities)
                    max_similarity = similarities[best_idx]

                    if max_similarity >= similarity_threshold:
                        student_id = self.vector_data['y'][best_idx]
                        self.detected_students.add(student_id)
                        label = f"Match: {student_id} ({max_similarity:.2f})"
                        color = (0, 255, 0)  # Green box for match

                # Draw bounding box
                cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                # Draw text background pill
                (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(img, (bbox[0], max(0, bbox[1] - 25)), (bbox[0] + w + 10, bbox[1]), color, -1)
                # Draw text label
                cv2.putText(img, label, (bbox[0] + 5, max(18, bbox[1] - 7)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        except Exception as e:
            pass

        return av.VideoFrame.from_ndarray(img, format="bgr24")
