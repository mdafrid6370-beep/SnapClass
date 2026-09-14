from datetime import datetime
from src.database.config import supabase
import bcrypt



def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_pass(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


def check_teacher_exists(username):
    # Check for unique username, returns false when username is already taken
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0 



def create_teacher(username, password, name):

    data = { "username" : username, "password": hash_pass(password), "name": name}
    response = supabase.table("teachers").insert(data).execute()
    return response.data


def teacher_login(username, password):
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher['password']):
            return teacher
    return None


def get_all_students():
    response = supabase.table('students').select("*").execute()
    return response.data

def create_student(new_name, face_embedding=None, student_id=None, password=None):
    data = {'name': new_name, 'face_embedding': face_embedding}
    if student_id is not None:
        data['student_id'] = student_id
    if password:
        data['password'] = hash_pass(password)
    response = supabase.table('students').insert(data).execute()
    return response.data

def student_login(student_id, password):
    response = supabase.table("students").select("*").eq("student_id", str(student_id)).execute()
    if response.data:
        student = response.data[0]
        hashed = student.get('password')
        if hashed:
            if check_pass(password, hashed):
                return student
        else:
            # Direct match fallback for legacy accounts without password
            return student
    return None



def create_subject(subject_code, name, section, teacher_id):
    data = {"subject_code": subject_code, "name": name, "section": section, "teacher_id": teacher_id}
    response = supabase.table("subjects").insert(data).execute()
    return response.data

def get_teacher_subjects(teacher_id):
    try:
        response = supabase.table('subjects').select("*").eq("teacher_id", teacher_id).execute()
        subjects = response.data or []

        for sub in subjects:
            sid = sub['subject_id']
            try:
                st_res = supabase.table('subject_students').select("student_id", count="exact").eq("subject_id", sid).execute()
                sub['total_students'] = st_res.count if st_res.count is not None else len(st_res.data or [])
            except Exception:
                sub['total_students'] = 0

            try:
                sess_res = supabase.table('attendance_sessions').select("session_id", count="exact").eq("subject_id", sid).execute()
                sub['total_classes'] = sess_res.count if sess_res.count is not None else len(sess_res.data or [])
            except Exception:
                sub['total_classes'] = 0

        return subjects
    except Exception as e:
        return []



def  enroll_student_to_subject(student_id, subject_id):
    data = {'student_id': student_id, "subject_id": subject_id}
    response= supabase.table('subject_students').insert(data).execute()
    return response.data


def  unenroll_student_to_subject(student_id, subject_id):
    response= supabase.table('subject_students').delete().eq('student_id', student_id).eq('subject_id', subject_id).execute()
    return response.data



def get_student_subjects(student_id):
    response = supabase.table('subject_students').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data


def get_student_attendance(student_id):
    response = supabase.table('attendance_logs').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data


def create_attendance(logs):
    response = supabase.table('attendance_logs').insert(logs).execute()
    return response.data

def get_attendance_for_teacher(teacher_id):
    response = supabase.table('attendance_logs').select("*, subjects!inner(*), students(*)").eq('subjects.teacher_id', teacher_id).execute()
    return response.data


# ----------------------------------------------------
# Attendance Session Workflow Functions
# ----------------------------------------------------

def create_attendance_session(subject_id, notes=None):
    data = {
        "subject_id": subject_id,
        "is_active": True,
        "notes": notes
    }
    response = supabase.table("attendance_sessions").insert(data).execute()
    return response.data[0] if response.data else None

def get_active_session(subject_id):
    response = supabase.table("attendance_sessions").select("*").eq("subject_id", subject_id).eq("is_active", True).execute()
    return response.data[0] if response.data else None

def end_attendance_session(session_id):
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    response = supabase.table("attendance_sessions").update({"is_active": False, "end_time": now_str}).eq("session_id", session_id).execute()
    return response.data

def get_session_attendance(session_id):
    response = supabase.table("attendance_logs").select("*, students(*), subjects(*)").eq("session_id", session_id).execute()
    return response.data


