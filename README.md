# 📸 SnapClass — AI-Powered Classroom Attendance System

![SnapClass Logo](https://i.ibb.co/YTYGn5qV/logo.png)

SnapClass is an intelligent classroom attendance tracking application built with **Streamlit**, **InsightFace**, **OpenCV**, and **Supabase**. It streamlines attendance taking using deep-learning face recognition, live WebRTC video streaming, automated session controls, and a complete student attendance dispute resolution system.

---

## ✨ Features

### 👨‍🏫 Teacher Portal
- **AI Face Recognition Attendance**: Take attendance automatically from classroom photos using InsightFace face embeddings.
- **📹 Live WebRTC Stream Mode**: Conduct real-time automated attendance scanning during live lectures.
- **⏱️ Attendance Session Workflow**: One-click session initialization, active session tracking, and automatic CSV report generation.
- **📩 Student Dispute Resolution**: Review, approve, or reject student claims for unrecognized attendance with a real-time pending dispute badge (`🔔 Disputes`).
- **🛡️ Auto Session Termination**: Automatically ends active attendance sessions when the teacher logs out or closes the browser tab.

### 👨‍🎓 Student Portal
- **🔐 Multi-Authentication**: Secure login via Application ID & Password or instant **FaceID Login**.
- **📚 Course Enrollment**: Easily enroll in subjects using unique join codes or QR share links.
- **🔔 Attendance Notifications & Claims**: View real-time attendance status (`✅ PRESENT` / `❌ UNRECOGNIZED`) for past sessions.
- **⚠️ Raise Attendance Issue**: Submit a dispute claim if present in class but missed by AI scanning.
- **🔄 Session Persistence**: Query-parameter session restoration retains user login across browser reloads (`F5`).

---

## 🛠️ Tech Stack

- **Frontend & App Framework**: [Streamlit](https://streamlit.io/)
- **Face Recognition AI Engine**: [InsightFace](https://github.com/deepinsight/insightface) (ArcFace) + [Scikit-Learn](https://scikit-learn.org/)
- **Live Streaming**: [streamlit-webrtc](https://github.com/whitphx/streamlit-webrtc) + OpenCV + PyAV
- **Database & Backend**: [Supabase](https://supabase.com/) (PostgreSQL & Realtime Storage)
- **Security & Hashing**: Bcrypt password hashing
- **UI & Styling**: Custom CSS with Google Fonts (*Outfit* & *Climate Crisis*)

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
Ensure you have Python 3.9+ installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/mdafrid6370-beep/SnapClass.git
cd SnapClass
```

### 3. Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Supabase Environment Secrets
Create `.streamlit/secrets.toml` in your project root with your Supabase credentials:
```toml
SUPABASE_URL = "https://your-supabase-project.supabase.co"
SUPABASE_KEY = "your-supabase-anon-key"
```

### 6. Run the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📂 Project Structure

```
SnapClass/
├── app.py                      # Main entrypoint and router
├── requirements.txt            # Project dependencies
├── .streamlit/
│   └── secrets.toml            # Database environment secrets
├── src/
│   ├── components/             # Reusable UI cards, headers, and modal dialogs
│   │   ├── header.py
│   │   ├── footer.py
│   │   ├── subject_card.py
│   │   ├── dialog_enroll.py
│   │   ├── dialog_create_subject.py
│   │   └── dialog_raise_issue.py
│   ├── database/               # Supabase database client and query helpers
│   │   ├── config.py
│   │   └── db.py
│   ├── pipelines/              # Face embedding and WebRTC AI processing pipelines
│   │   ├── face_pipeline.py
│   │   └── webrtc_pipeline.py
│   ├── screens/                # Main application screens
│   │   ├── home_screen.py
│   │   ├── student_screen.py
│   │   └── teacher_screen.py
│   └── ui/                     # Global styling and base layouts
│       └── base_layout.py
```

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
