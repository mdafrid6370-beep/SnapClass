import streamlit as st

from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card
from src.database.db import (
    check_teacher_exists, create_teacher, teacher_login, get_teacher_subjects,
    get_attendance_for_teacher, create_attendance_session, get_active_session,
    end_attendance_session, end_all_active_sessions_for_teacher, get_session_attendance,
    get_teacher_attendance_issues, resolve_attendance_issue
)
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_add_photo import add_photos_dialog

from src.pipelines.face_pipeline import predict_attendance
from src.components.dialog_attendance_results import attendance_result_dialog
import numpy as np

from datetime import datetime

import pandas as pd

from src.database.config import supabase


class SessionAutoCloser:
    def __init__(self, teacher_id, session_id=None):
        self.teacher_id = teacher_id
        self.session_id = session_id
        self.is_closed = False

    def close(self):
        if not self.is_closed:
            self.is_closed = True
            if self.session_id:
                try:
                    end_attendance_session(self.session_id)
                except Exception:
                    pass
            if self.teacher_id:
                try:
                    end_all_active_sessions_for_teacher(self.teacher_id)
                except Exception:
                    pass

    def __del__(self):
        self.close()


def teacher_screen():

    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type=="login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()


def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    teacher_id = teacher_data.get('teacher_id')
    if 'teacher_session_closer' not in st.session_state:
        st.session_state['teacher_session_closer'] = SessionAutoCloser(teacher_id)

    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"""Welcome, {teacher_data['name']} """)
        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.query_params.clear()
            if teacher_id:
                end_all_active_sessions_for_teacher(teacher_id)
            if 'teacher_session_closer' in st.session_state:
                try:
                    st.session_state.teacher_session_closer.close()
                except Exception:
                    pass
                del st.session_state.teacher_session_closer
            st.session_state['is_logged_in'] = False
            st.session_state['login_type'] = None
            if 'teacher_data' in st.session_state:
                del st.session_state.teacher_data 
            st.rerun()

    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'
    
    # Calculate pending disputes count for badge
    teacher_issues = get_teacher_attendance_issues(teacher_id)
    pending_count = len([i for i in teacher_issues if i.get('status') == 'pending'])
    
    if pending_count > 0:
        if "dispute_toast_shown" not in st.session_state:
            st.toast(f"🔔 You have {pending_count} pending student attendance dispute(s)!")
            st.session_state.dispute_toast_shown = True
        
        st.warning(f"🔔 **Pending Student Disputes**: You have **{pending_count} pending claim(s)** from students who were marked unrecognized. Click **'Review Disputes'** to approve or reject.")

    dispute_label = f"🔔 Disputes ({pending_count} New)" if pending_count > 0 else "Disputes & Issues"

    tab1, tab2, tab3, tab4 = st.columns(4)

    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendance' else "tertiary"
        if st.button('Take Attendance', type=type1, width='stretch', icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else "tertiary"
        if st.button('Manage Subjects', type=type2, width='stretch', icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendance_records' else "tertiary"
        if st.button('Attendance Records', type=type3, width='stretch', icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()

    with tab4:
        if st.session_state.current_teacher_tab == 'attendance_issues':
            type4 = "primary"
        elif pending_count > 0:
            type4 = "secondary"
        else:
            type4 = "tertiary"

        if st.button(dispute_label, type=type4, width='stretch', icon=':material/report_problem:'):
            st.session_state.current_teacher_tab = 'attendance_issues'
            st.rerun()

    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()
    if st.session_state.current_teacher_tab == "attendance_issues":
        teacher_tab_attendance_issues()






def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"""Welcome, {teacher_data['name']} """)
        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            del st.session_state.teacher_data 
            st.rerun()


    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'
    tab1, tab2, tab3 = st.columns(3)


    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendance' else "tertiary"
        if st.button('Take Attendance',type=type1, width='stretch', icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else "tertiary"
        if st.button('Manage Subjects', type=type2, width='stretch', icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendance_records' else "tertiary"
        if st.button('Attendance Records',type=type3, width='stretch', icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()


    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()

    


    footer_dashboard()

def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header('Take AI Attendance')

    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.warning('You havent created any subjects yet! Please create one to begin!')
        return
    
    subject_options = {f"{s['name']} - {s['subject_code']}": s['subject_id'] for s in subjects}

    # --- 1. SUBJECT SELECTION ---
    selected_subject_label = st.selectbox('Select Subject', options=list(subject_options.keys()))
    selected_subject_id = subject_options[selected_subject_label]

    # --- 2. SESSION WORKFLOW CONTROL PANEL ---
    st.divider()

    enrolled_res = supabase.table('subject_students').select("*, students(*)").eq('subject_id', selected_subject_id).execute()
    enrolled_students = enrolled_res.data or []
    active_session = get_active_session(selected_subject_id)

    with st.container(border=True):
        st.subheader("⏱️ Attendance Session Workflow")
        
        if not active_session:
            st.info(f"📋 **Course:** {selected_subject_label} | **Enrolled Students:** {len(enrolled_students)}")
            if st.button("▶️ Start Attendance Session", type="primary", width="stretch", icon=":material/play_arrow:"):
                sess = create_attendance_session(selected_subject_id)
                if sess:
                    if 'teacher_session_closer' in st.session_state:
                        st.session_state.teacher_session_closer.session_id = sess['session_id']
                    st.toast(f"Attendance Session #{sess['session_id']} Started!")
                    st.rerun()
                else:
                    st.error("Failed to start session!")
        else:
            session_id = active_session['session_id']
            if 'teacher_session_closer' in st.session_state:
                st.session_state.teacher_session_closer.session_id = session_id

            start_ts = active_session.get('start_time', '')
            formatted_start = datetime.fromisoformat(start_ts).strftime("%I:%M %p") if start_ts else "N/A"

            st.success(f"🟢 **Active Session #{session_id}** | Started at: **{formatted_start}** | **Enrolled Students:** {len(enrolled_students)}")

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("⏹️ End Attendance Session", type="secondary", width="stretch", icon=":material/stop:"):
                    end_attendance_session(session_id)
                    if 'teacher_session_closer' in st.session_state:
                        st.session_state.teacher_session_closer.session_id = None
                    st.toast(f"Session #{session_id} Ended Successfully!")
                    st.rerun()

            with btn_col2:
                session_logs = get_session_attendance(session_id)
                if session_logs:
                    csv_data = []
                    for log in session_logs:
                        stud = log.get('students') or {}
                        sub = log.get('subjects') or {}
                        csv_data.append({
                            "Session ID": session_id,
                            "Timestamp": log.get('timestamp'),
                            "Subject": sub.get('name'),
                            "Subject Code": sub.get('subject_code'),
                            "Student ID": stud.get('student_id'),
                            "Student Name": stud.get('name'),
                            "Status": "Present" if log.get('is_present') else "Absent"
                        })
                    csv_df = pd.DataFrame(csv_data)
                    # Deduplicate so each student appears ONLY ONCE per session in CSV
                    csv_df = csv_df.sort_values(by="Status", ascending=False).drop_duplicates(subset=["Session ID", "Student ID"], keep="first")
                    csv_bytes = csv_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Export Session CSV",
                        data=csv_bytes,
                        file_name=f"session_{session_id}_attendance.csv",
                        mime="text/csv",
                        type="primary",
                        width="stretch"
                    )

    st.divider()

    # --- 3. ATTENDANCE SCANNING CONTROLS (Only available when a session is active) ---
    if not active_session:
        st.warning("⚠️ **Session Required**: Please click **'▶️ Start Attendance Session'** above to enable photo capture and face recognition for this class.")
        return

    # Add Photos button
    if st.button('Add Photos', type='primary', icon=':material/photo_prints:', width='stretch'):
        add_photos_dialog()

    st.divider()

    if st.session_state.attendance_images:
        st.header('Added Photos')
        gallery_cols = st.columns(4)

        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4 ]:
                st.image(img, width='stretch', caption=f'Photo {idx+1}')
    has_photos = bool(st.session_state.attendance_images)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button('Clear all photos', width='stretch', type='tertiary', icon=':material/delete:', disabled=not has_photos):
            st.session_state.attendance_images = []
            st.rerun()


    with c2:
        
        if st.button('Run Face Analysis', width='stretch', type='secondary', icon=':material/analytics:', disabled=not has_photos):
            with st.spinner('Deep scanning classroom photos...'):
                all_detected_ids = {}

                for idx, img in enumerate(st.session_state.attendance_images):
                    img_np = np.array(img.convert('RGB'))
                    detected, _, _ = predict_attendance(img_np)


                    if detected:
                        for sid in detected.keys():
                            student_id = str(sid)

                            all_detected_ids.setdefault(student_id, []).append(f"Photo {idx+1}")

                if not enrolled_students:
                    st.warning('No students enrolled in this course')
                else:

                    results, attendance_to_log  = [], []

                    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    active_sess_id = active_session['session_id'] if active_session else None


                    for node in enrolled_students:
                        student = node['students']
                        sources = all_detected_ids.get(str(student['student_id']), [])
                        is_present= len(sources) > 0

                        results.append({
                            "Name": student['name'],
                            "ID": student['student_id'],
                            "Source": ", ".join(sources) if is_present else "-",
                            "Status": "✅ Present" if is_present else "❌ Absent"
                        })

                        log_entry = {
                            'student_id': student['student_id'],
                            'subject_id': selected_subject_id,
                            'timestamp': current_timestamp,
                            'is_present': bool(is_present)
                        }
                        if active_sess_id:
                            log_entry['session_id'] = active_sess_id

                        attendance_to_log.append(log_entry)

                attendance_result_dialog(pd.DataFrame(results), attendance_to_log)

    with c3:
        show_live_stream = st.checkbox("📹 Live Stream Mode", key="teacher_live_stream_toggle")

    if show_live_stream:
        st.divider()
        st.subheader("📹 Live Video Classroom Scanner")
        try:
            from streamlit_webrtc import webrtc_streamer
            from src.pipelines.webrtc_pipeline import LiveFaceAttendanceProcessor
            from src.database.db import create_attendance

            if "webrtc_logged_students" not in st.session_state:
                st.session_state.webrtc_logged_students = set()

            ctx = webrtc_streamer(
                key="teacher_live_attendance",
                video_processor_factory=LiveFaceAttendanceProcessor,
                rtc_configuration={
                    "iceServers": [
                        {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302", "stun:stun2.l.google.com:19302", "stun:stun.services.mozilla.com", "stun:global.stun.twilio.com:3478"]}
                    ]
                },
                media_stream_constraints={"video": True, "audio": False}
            )

            if ctx.video_processor and ctx.video_processor.detected_students:
                current_detected = ctx.video_processor.detected_students
                new_matches = [sid for sid in current_detected if sid not in st.session_state.webrtc_logged_students]

                if new_matches:
                    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    active_sess_id = active_session['session_id'] if active_session else None
                    logs_to_insert = []

                    for match_id in new_matches:
                        st.session_state.webrtc_logged_students.add(match_id)
                        log_entry = {
                            'student_id': match_id,
                            'subject_id': selected_subject_id,
                            'timestamp': current_timestamp,
                            'is_present': True
                        }
                        if active_sess_id:
                            log_entry['session_id'] = active_sess_id
                        logs_to_insert.append(log_entry)

                    if logs_to_insert:
                        try:
                            create_attendance(logs_to_insert)
                            for match_id in new_matches:
                                st.toast(f"✅ Live Attendance Recorded for Student ID: {match_id}")
                        except Exception as e:
                            st.error(f"Live log error: {str(e)}")

                st.success(f"🟢 **Live Detected & Logged Students:** {', '.join(list(st.session_state.webrtc_logged_students))}")
        except ImportError:
            st.error("Live streaming dependencies not installed. Please run `pip install streamlit-webrtc av opencv-python-headless`.")















def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['teacher_id']
    col1, col2 = st.columns(2)
    with col1:
        st.header('Manage Subjects', width='stretch')

    with col2:
        if st.button('Create New Subject', width='stretch'):
            create_subject_dialog(teacher_id)


    # LIST all SUBJECTS
    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        for sub in subjects:
            stats = [
                ("🫂", "Students", sub['total_students']),
                ("🕰️", "Classes", sub['total_classes']),
            ]
        def share_btn():
            if st.button(f"Share Code: {sub['name']}", key=f"share_{sub['subject_code']}", icon=":material/share:"):
                share_subject_dialog(sub['name'], sub['subject_code'])
            st.space()

        subject_card(
            name = sub['name'],
            code = sub['subject_code'],
            section = sub['section'],
            stats=stats,
            footer_callback=share_btn
        )
    else:
        st.info("NO SUBJECTS FOUND. CREATE ONE ABOVE")


def teacher_tab_attendance_records():
    st.header('Attendance Records & Analytics')

    teacher_id = st.session_state.teacher_data['teacher_id']

    records = get_attendance_for_teacher(teacher_id)

    if not records:
        st.info("No attendance records found yet. Take attendance to view analytics and reports!")
        return
    
    data = []

    for r in records:
        ts = r.get('timestamp')
        student = r.get('students') or {}
        subject = r.get('subjects') or {}

        data.append({
            "ts_group": ts.split(".")[0] if ts else None,
            "Date/Time": datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N/A",
            "Subject": subject.get('name', 'N/A'),
            "Subject Code": subject.get('subject_code', 'N/A'),
            "Student Name": student.get('name', 'Unknown'),
            "Student ID": student.get('student_id', 'N/A'),
            "Status": "✅ Present" if r.get('is_present') else "❌ Absent",
            "is_present": 1 if r.get('is_present') else 0
        })

    df = pd.DataFrame(data)

    # 1. Summary Metrics
    total_sessions = len(df['ts_group'].unique())
    total_logs = len(df)
    overall_rate = (df['is_present'].sum() / total_logs * 100) if total_logs > 0 else 0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="Total Sessions Conducted", value=total_sessions)
    with m2:
        st.metric(label="Total Logs Recorded", value=total_logs)
    with m3:
        st.metric(label="Overall Attendance Rate", value=f"{overall_rate:.1f}%")

    st.divider()

    # 2. CSV Export Section
    st.subheader("📥 Export Reports")
    exp1, exp2 = st.columns(2)

    # Student Summary DataFrame for CSV
    student_summary = (
        df.groupby(['Student ID', 'Student Name', 'Subject'])
        .agg(
            Classes_Attended=('is_present', 'sum'),
            Total_Classes=('is_present', 'count')
        ).reset_index()
    )
    student_summary['Attendance %'] = (student_summary['Classes_Attended'] / student_summary['Total_Classes'] * 100).round(1)

    with exp1:
        raw_df = df[['Date/Time', 'Subject', 'Subject Code', 'Student ID', 'Student Name', 'Status']].sort_values(by="Status", ascending=False).drop_duplicates(subset=['Date/Time', 'Subject Code', 'Student ID'], keep='first')
        csv_raw = raw_df.to_csv(index=False)
        st.download_button(
            label="📄 Download Detailed Attendance Logs (CSV)",
            data=csv_raw,
            file_name=f"attendance_logs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary",
            width="stretch"
        )

    with exp2:
        csv_summary = student_summary.to_csv(index=False)
        st.download_button(
            label="📊 Download Student Summary Report (CSV)",
            data=csv_summary,
            file_name=f"student_summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="secondary",
            width="stretch"
        )



    # 4. At-Risk Students Warning (< 75% Attendance)
    at_risk = student_summary[student_summary['Attendance %'] < 75.0]
    if not at_risk.empty:
        st.warning("⚠️ **At-Risk Students Alert (Attendance < 75%)**")
        st.dataframe(at_risk[['Student ID', 'Student Name', 'Subject', 'Classes_Attended', 'Total_Classes', 'Attendance %']], hide_index=True, width='stretch')

    st.divider()

    # 5. Session History Summary Table
    st.subheader("📋 Session History")
    session_summary = (
        df.groupby(['ts_group', 'Date/Time', 'Subject', 'Subject Code'])
        .agg(
            Present_Count=('is_present', 'sum'),
            Total_Count=('is_present', 'count')
        ).reset_index()
    )
    session_summary['Attendance Stats'] = (
        "✅ " + session_summary['Present_Count'].astype(str) + " / "
        + session_summary['Total_Count'].astype(str) + ' Students'
    )
    display_df = (
        session_summary.sort_values(by='ts_group', ascending=False)
        [['Date/Time', 'Subject', 'Subject Code', 'Attendance Stats']]
    )

    st.dataframe(display_df, width='stretch', hide_index=True)



def login_teacher(username, password):
    if not username or not password:
        return False
    
    teacher = teacher_login(username, password)

    if teacher:
        st.session_state.user_role ='teacher'
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        st.query_params["session_role"] = "teacher"
        st.query_params["session_user"] = str(teacher['username'])
        return True
    

    return False
def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Login using password', text_alignment='center')
    st.space()
    st.space()


    teacher_username = st.text_input("Enter username", placeholder='ananyaroy')

    teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter password")

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button('Login', icon=':material/passkey:', shortcut='control+enter', width='stretch'):
            if login_teacher(teacher_username, teacher_pass):
                st.toast("welcome back!", icon="👋")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username and password combo")

    with btnc2:
        if st.button('Register Instead', type="primary", icon=':material/passkey:', width='stretch'):
            st.session_state.teacher_login_type = 'register'

    footer_dashboard()



def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    if not teacher_username or not teacher_name or not teacher_pass:
        return False, "All Fields are required!"
    if check_teacher_exists(teacher_username):
        return False, "Username already taken"
    if teacher_pass != teacher_pass_confirm:
        return False, "Password doesn't match"
    
    try:
        create_teacher(teacher_username, teacher_pass, teacher_name)
        return True, "Sucessfully Created! Login Now"
    except Exception as e:
        return False, "Unexpected Error!"
    

def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()



    st.header('Register your teacher profile')

    st.space()
    st.space()

    
    teacher_username = st.text_input("Enter username", placeholder='ananyaroy')

    teacher_name = st.text_input("Enter name", placeholder='Ananya Roy')

    teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter password")

    teacher_pass_confirm = st.text_input("Confirm your password", type='password', placeholder="Enter password")

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button('Register now', icon=':material/passkey:', shortcut='control+enter', width='stretch'):
            success, message = register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm)
            if success:
                st.success(message)
                import time
                time.sleep(2)
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)


    with btnc2:
        if st.button('Login Instead', type="primary", icon=':material/passkey:', width='stretch'):
            st.session_state.teacher_login_type = 'login'

    footer_dashboard()


def teacher_tab_attendance_issues():
    st.header('📩 Student Attendance Disputes & Issues')
    st.caption('Review student claims for unrecognized attendance during completed class sessions.')

    teacher_id = st.session_state.teacher_data['teacher_id']
    issues = get_teacher_attendance_issues(teacher_id)

    if not issues:
        st.info("No attendance disputes or student issues reported yet.")
        return

    pending_issues = [i for i in issues if i.get('status') == 'pending']
    resolved_issues = [i for i in issues if i.get('status') != 'pending']

    if pending_issues:
        st.subheader(f"⚠️ Pending Student Claims ({len(pending_issues)})")
        for issue in pending_issues:
            issue_id = issue.get('issue_id')
            student_name = issue.get('student_name', 'Student')
            student_id = issue.get('student_id', '')
            session_id = issue.get('session_id')
            subject_id = issue.get('subject_id')
            reason = issue.get('reason', 'No detail provided')
            ts = issue.get('timestamp', 'N/A')

            sub = issue.get('subjects') or {}
            sub_name = sub.get('name', 'Subject')

            with st.container(border=True):
                c_info, c_action1, c_action2 = st.columns([3, 1, 1], vertical_alignment='center')
                with c_info:
                    st.markdown(f"**{student_name}** (ID: {student_id}) — **{sub_name}**")
                    st.markdown(f"**Session ID:** #{session_id} | **Note:** *\"{reason}\"*")
                    st.caption(f"Filed at: {ts}")

                with c_action1:
                    if st.button("✅ Approve", key=f"app_{issue_id}", type="primary", width="stretch"):
                        resolve_attendance_issue(issue_id, "approved", session_id, student_id, subject_id)
                        st.toast(f"Approved attendance for {student_name}!")
                        st.rerun()

                with c_action2:
                    if st.button("❌ Reject", key=f"rej_{issue_id}", type="secondary", width="stretch"):
                        resolve_attendance_issue(issue_id, "rejected", session_id, student_id, subject_id)
                        st.toast(f"Rejected issue for {student_name}.")
                        st.rerun()

    if resolved_issues:
        st.divider()
        st.subheader("📋 Resolved Disputes History")
        res_data = []
        for r in resolved_issues:
            sub = r.get('subjects') or {}
            res_data.append({
                "Date/Time": r.get('timestamp', 'N/A'),
                "Student Name": r.get('student_name'),
                "Student ID": r.get('student_id'),
                "Subject": sub.get('name', 'N/A'),
                "Session ID": r.get('session_id'),
                "Reason": r.get('reason'),
                "Status": "✅ Approved (Present)" if r.get('status') == 'approved' else "❌ Rejected"
            })
        st.dataframe(pd.DataFrame(res_data), hide_index=True, width="stretch")