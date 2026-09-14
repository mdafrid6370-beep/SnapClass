
import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen

from src.components.dialog_auto_enroll import auto_enroll_dialog

from src.database.db import get_student_by_id, get_teacher_by_username

def main():
    st.set_page_config(
        page_title='SnapClass - Making Attendance faster using AI',
        page_icon= "https://i.ibb.co/YTYGn5qV/logo.png"
    )
    
    # Restore session from URL parameters on page reload / refresh
    if not st.session_state.get('is_logged_in'):
        role_param = st.query_params.get("session_role")
        if role_param == "student" and st.query_params.get("session_id"):
            stud = get_student_by_id(st.query_params.get("session_id"))
            if stud:
                st.session_state.is_logged_in = True
                st.session_state.user_role = 'student'
                st.session_state.student_data = stud
                st.session_state.login_type = 'student'
        elif role_param == "teacher" and st.query_params.get("session_user"):
            teacher = get_teacher_by_username(st.query_params.get("session_user"))
            if teacher:
                st.session_state.is_logged_in = True
                st.session_state.user_role = 'teacher'
                st.session_state.teacher_data = teacher
                st.session_state.login_type = 'teacher'

    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None

    match st.session_state['login_type']:
        case 'teacher':
            teacher_screen()

        case 'student':
            student_screen()
        
        case None:
            home_screen()


    join_code = st.query_params.get('join-code')
    if join_code:
        if st.session_state.login_type != 'student':
            st.session_state.login_type = 'student'
            st.rerun()
        if st.session_state.get('is_logged_in') and st.session_state.get('user_role') == 'student':
            auto_enroll_dialog(join_code)
main()