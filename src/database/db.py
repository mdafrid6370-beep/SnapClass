import streamlit as st
import json
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


def get_teacher_by_username(username):
    try:
        response = supabase.table("teachers").select("*").eq("username", username).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None

def teacher_login(username, password):
    teacher = get_teacher_by_username(username)
    if teacher and check_pass(password, teacher['password']):
        return teacher
    return None

def get_student_by_id(student_id):
    try:
        response = supabase.table("students").select("*").eq("student_id", str(student_id)).execute()
        return response.data[0] if response.data else None
    except Exception:
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

def end_all_active_sessions_for_teacher(teacher_id):
    if not teacher_id:
        return
    try:
        subjects = get_teacher_subjects(teacher_id)
        if subjects:
            now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            for s in subjects:
                sid = s.get('subject_id')
                if sid:
                    supabase.table("attendance_sessions").update({"is_active": False, "end_time": now_str}).eq("subject_id", sid).eq("is_active", True).execute()
    except Exception:
        pass

def get_session_attendance(session_id):
    response = supabase.table("attendance_logs").select("*, students(*), subjects(*)").eq("session_id", session_id).execute()
    return response.data

# ----------------------------------------------------
# Attendance Issues & Dispute Functions
# ----------------------------------------------------

def _parse_notes_dict(notes_val):
    if not notes_val:
        return {}
    if isinstance(notes_val, dict):
        return notes_val
    try:
        parsed = json.loads(notes_val)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}

def create_attendance_issue(session_id, subject_id, student_id, student_name, reason="Unrecognized in session"):
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    issue_data = {
        "session_id": session_id,
        "subject_id": subject_id,
        "student_id": str(student_id),
        "student_name": student_name,
        "reason": reason,
        "status": "pending",
        "timestamp": now_str
    }

    # 1. Try dedicated table attendance_issues first
    try:
        res = supabase.table("attendance_issues").insert(issue_data).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass

    # 2. Database persistence via attendance_sessions.notes (Supabase cloud sync)
    if session_id:
        try:
            sess_res = supabase.table("attendance_sessions").select("session_id, notes").eq("session_id", session_id).execute()
            if sess_res.data:
                sess = sess_res.data[0]
                notes_dict = _parse_notes_dict(sess.get("notes"))
                disputes = notes_dict.get("disputes", [])
                
                issue_id = f"{session_id}_{student_id}"
                issue_data["issue_id"] = issue_id

                existing_idx = None
                for idx, d in enumerate(disputes):
                    if str(d.get("student_id")) == str(student_id):
                        existing_idx = idx
                        break

                if existing_idx is not None:
                    disputes[existing_idx] = issue_data
                else:
                    disputes.append(issue_data)

                notes_dict["disputes"] = disputes
                supabase.table("attendance_sessions").update({"notes": json.dumps(notes_dict)}).eq("session_id", session_id).execute()
                return issue_data
        except Exception:
            pass

    # 3. Fallback to local session_state if DB completely unreachable
    if "local_attendance_issues" not in st.session_state:
        st.session_state.local_attendance_issues = []
    issue_data["issue_id"] = f"{session_id}_{student_id}"
    st.session_state.local_attendance_issues.append(issue_data)
    return issue_data

def get_student_attendance_issues(student_id):
    # 1. Try dedicated table first
    try:
        res = supabase.table("attendance_issues").select("*, subjects(*)").eq("student_id", str(student_id)).execute()
        if res.data:
            return res.data
    except Exception:
        pass

    # 2. Check attendance_sessions notes from Supabase
    found_issues = []
    try:
        sess_res = supabase.table("attendance_sessions").select("*, subjects(*)").not_.is_("notes", "null").execute()
        for s in (sess_res.data or []):
            notes_dict = _parse_notes_dict(s.get("notes"))
            disputes = notes_dict.get("disputes", [])
            for d in disputes:
                if str(d.get("student_id")) == str(student_id):
                    d_copy = dict(d)
                    if not d_copy.get("subjects"):
                        d_copy["subjects"] = s.get("subjects")
                    found_issues.append(d_copy)
    except Exception:
        pass

    if found_issues:
        return found_issues

    # 3. Local session_state fallback
    all_issues = st.session_state.get("local_attendance_issues", [])
    return [i for i in all_issues if str(i.get("student_id")) == str(student_id)]

def get_teacher_attendance_issues(teacher_id):
    # 1. Try dedicated table first
    try:
        res = supabase.table("attendance_issues").select("*, subjects!inner(*), students(*)").eq("subjects.teacher_id", teacher_id).execute()
        if res.data:
            return res.data
    except Exception:
        pass

    # 2. Check attendance_sessions notes from Supabase
    found_issues = []
    try:
        subjects = get_teacher_subjects(teacher_id)
        teacher_sub_ids = [s.get('subject_id') for s in (subjects or []) if s.get('subject_id')]
        if teacher_sub_ids:
            sess_res = supabase.table("attendance_sessions").select("*, subjects(*)").in_("subject_id", teacher_sub_ids).not_.is_("notes", "null").execute()
            for s in (sess_res.data or []):
                notes_dict = _parse_notes_dict(s.get("notes"))
                disputes = notes_dict.get("disputes", [])
                for d in disputes:
                    d_copy = dict(d)
                    if not d_copy.get("subjects"):
                        d_copy["subjects"] = s.get("subjects")
                    found_issues.append(d_copy)
    except Exception:
        pass

    if found_issues:
        return found_issues

    # 3. Local session_state fallback
    all_issues = st.session_state.get("local_attendance_issues", [])
    subjects = get_teacher_subjects(teacher_id)
    teacher_sub_ids = [s.get('subject_id') for s in (subjects or [])]
    return [i for i in all_issues if i.get('subject_id') in teacher_sub_ids]

def resolve_attendance_issue(issue_id, status, session_id, student_id, subject_id):
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # 1. Try dedicated table
    try:
        supabase.table("attendance_issues").update({"status": status}).eq("issue_id", issue_id).execute()
    except Exception:
        pass

    # 2. Try attendance_sessions notes in Supabase
    if session_id:
        try:
            sess_res = supabase.table("attendance_sessions").select("session_id, notes").eq("session_id", session_id).execute()
            if sess_res.data:
                sess = sess_res.data[0]
                notes_dict = _parse_notes_dict(sess.get("notes"))
                disputes = notes_dict.get("disputes", [])
                updated = False
                for d in disputes:
                    if str(d.get("issue_id")) == str(issue_id) or (str(d.get("student_id")) == str(student_id) and str(d.get("session_id")) == str(session_id)):
                        d["status"] = status
                        updated = True
                if updated:
                    notes_dict["disputes"] = disputes
                    supabase.table("attendance_sessions").update({"notes": json.dumps(notes_dict)}).eq("session_id", session_id).execute()
        except Exception:
            pass

    # 3. Update local session state
    all_issues = st.session_state.get("local_attendance_issues", [])
    for i in all_issues:
        if str(i.get("issue_id")) == str(issue_id) or (str(i.get("student_id")) == str(student_id) and str(i.get("session_id")) == str(session_id)):
            i["status"] = status

    # 4. If approved, update or insert into attendance_logs so student gets marked PRESENT!
    if status == "approved" and session_id and student_id:
        try:
            existing = supabase.table("attendance_logs").select("*").eq("session_id", session_id).eq("student_id", str(student_id)).execute()
            if existing.data:
                supabase.table("attendance_logs").update({"is_present": True, "timestamp": now_str}).eq("session_id", session_id).eq("student_id", str(student_id)).execute()
            else:
                log_entry = {
                    "session_id": session_id,
                    "student_id": str(student_id),
                    "subject_id": subject_id,
                    "timestamp": now_str,
                    "is_present": True
                }
                supabase.table("attendance_logs").insert([log_entry]).execute()
        except Exception:
            pass


