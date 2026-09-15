import streamlit as st

from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from PIL import Image
import numpy as np
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier
from src.database.db import get_all_students, create_student, student_login, get_student_subjects, get_student_attendance, unenroll_student_to_subject, get_student_attendance_issues
import time

from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card
from src.components.dialog_raise_issue import raise_issue_dialog

def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"""Welcome, {student_data['name']} """)
        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.query_params.clear()
            st.session_state['is_logged_in'] = False
            st.session_state['login_type'] = None
            if 'student_data' in st.session_state:
                del st.session_state.student_data 
            st.rerun()


    st.space()

    c1, c2 =st.columns(2)
    with c1:
        st.header('Your Enrolled Subjects')
    with c2:
        if st.button('Enroll in Subject', type='primary', width='stretch'):
            enroll_dialog()


    st.divider()


    with st.spinner('Loading your enrolled subjects..'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}

    for log in logs:
        sid = log['subject_id']

        if sid not in stats_map:
            stats_map[sid] = {"total":0, "attended": 0}

        stats_map[sid]['total'] +=1

        if log.get('is_present'):
            stats_map[sid]['attended'] += 1


    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sid = sub['subject_id']


        stats = stats_map.get(sid, {"total": 0, "attended": 0})
        tot = stats['total']
        att = stats['attended']
        pct = round((att / tot) * 100, 1) if tot > 0 else 100.0
        
        status_badge = f"{pct}% (Eligible)" if pct >= 75.0 else f"{pct}% (Shortage Alert)"
        status_icon = "🟢" if pct >= 75.0 else "🔴"

        def unenroll_button():
            if st.button("Unenroll from this course", type='tertiary', width='stretch', icon=':material/delete_forever:', key=f"unenroll_{sid}"):
                unenroll_student_to_subject(student_id, sid)
                st.toast(f'Unenrolled from {sub["name"]} successfully!')
                st.rerun()

        with cols[i % 2]:
            subject_card(
                name = sub['name'],
                code = sub['subject_code'],
                section = sub['section'],
                stats = [
                    ('📅', 'Total Sessions', tot),
                    ('✅', 'Attended', att),
                    (status_icon, 'Attendance', status_badge),
                ],
                footer_callback=unenroll_button
            )

    st.divider()

    # --- ATTENDANCE NOTIFICATIONS & ISSUES SECTION ---
    st.header('🔔 Attendance Notifications & Session Claims')
    st.caption('View session attendance alerts. If you were present but unrecognized in class, raise an issue for teacher review.')

    issues = get_student_attendance_issues(student_id)
    issue_map = {i.get('session_id'): i for i in issues if i.get('session_id')}

    if logs:
        # Group logs by session_id or timestamp
        for log in reversed(logs[-8:]):
            sub = log.get('subjects') or {}
            sess_id = log.get('session_id', 'N/A')
            sub_id = log.get('subject_id')
            sub_name = sub.get('name', 'Course')
            ts = log.get('timestamp', 'N/A')
            is_present = log.get('is_present')

            with st.container(border=True):
                col_info, col_action = st.columns([3, 1], vertical_alignment='center')
                with col_info:
                    status_badge = "✅ **PRESENT**" if is_present else "❌ **UNRECOGNIZED / ABSENT**"
                    st.markdown(f"**{sub_name}** | Session #{sess_id} | {status_badge}")
                    st.caption(f"Recorded at: {ts}")

                with col_action:
                    if is_present:
                        st.success("Attendance Verified")
                    else:
                        existing_issue = issue_map.get(sess_id)
                        if existing_issue:
                            st_val = existing_issue.get('status', 'pending')
                            if st_val == 'approved':
                                st.success("✅ Issue Approved! Marked Present")
                            elif st_val == 'rejected':
                                st.error("❌ Issue Rejected")
                            else:
                                st.warning("⏳ Issue Pending Review")
                        else:
                            if st.button("⚠️ Raise Issue", key=f"raise_{sess_id}_{sub_id}", type="secondary"):
                                raise_issue_dialog(sess_id, sub_id, sub_name, student_id, student_data.get('name'))
    else:
        st.info("No attendance records or session notifications yet.")

    footer_dashboard()


def student_screen():


    style_background_dashboard()
    style_base_layout()


    if "student_data" in st.session_state:
        student_dashboard()
        return
    
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Student Portal', text_alignment='center')
    st.space()

    tab_options = ["🔑 Password Login", "👤 FaceID Login", "📝 Register New Student"]
    
    if "active_student_portal_tab" not in st.session_state:
        st.session_state.active_student_portal_tab = "faceid"

    default_idx = 1
    if st.session_state.active_student_portal_tab == "password":
        default_idx = 0
    elif st.session_state.active_student_portal_tab == "faceid":
        default_idx = 1
    elif st.session_state.active_student_portal_tab == "register":
        default_idx = 2

    chosen_tab_label = st.radio(
        "Student Portal Navigation",
        tab_options,
        index=default_idx,
        horizontal=True,
        key="student_portal_nav_radio",
        label_visibility="collapsed"
    )

    if chosen_tab_label == "🔑 Password Login":
        st.session_state.active_student_portal_tab = "password"
    elif chosen_tab_label == "👤 FaceID Login":
        st.session_state.active_student_portal_tab = "faceid"
    else:
        st.session_state.active_student_portal_tab = "register"

    st.divider()

    # --- TAB 1: PASSWORD LOGIN ---
    if st.session_state.active_student_portal_tab == "password":
        st.subheader("Login using Application ID & Password")
        st.caption("Secure login preventing photo-spoofing attacks.")
        
        login_app_id = st.text_input("Application ID / Roll No", placeholder="E.g. APP1001 or 10024", key="student_pwd_id")
        login_pwd = st.text_input("Password", type="password", placeholder="Enter your password", key="student_pwd_val")
        
        st.space()
        if st.button("Login to Student Portal", type="primary", width="stretch", icon=":material/login:"):
            if login_app_id and login_pwd:
                stud = student_login(login_app_id, login_pwd)
                if stud:
                    st.session_state.is_logged_in = True
                    st.session_state.user_role = 'student'
                    st.session_state.student_data = stud
                    st.query_params["session_role"] = "student"
                    st.query_params["session_id"] = str(stud['student_id'])
                    st.toast(f"Welcome Back, {stud['name']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid Application ID or Password!")
            else:
                st.warning("Please fill in both Application ID and Password.")

    # --- TAB 2: FACEID LOGIN ---
    elif st.session_state.active_student_portal_tab == "faceid":
        st.subheader("Login using FaceID")
        st.caption("Snap a photo using your phone's camera or select a face photo to verify your identity.")
        
        faceid_method = st.radio(
            "Select Photo Method:",
            ["📱 Snap Photo / Upload File (Recommended for Mobile)", "💻 Desktop Live Camera Stream"],
            index=0,
            horizontal=True,
            key="faceid_input_method"
        )
        
        photo_source = None
        if faceid_method == "📱 Snap Photo / Upload File (Recommended for Mobile)":
            photo_source = st.file_uploader("Upload or Take Photo with Phone Camera", type=["jpg", "jpeg", "png"], key="student_faceid_file")
        else:
            photo_source = st.camera_input("Position face in center", key="student_faceid_cam")

        if photo_source:
            img = np.array(Image.open(photo_source))

            with st.spinner('AI is scanning..'):
                detected, all_ids, num_faces = predict_attendance(img)

                if num_faces == 0:
                    st.warning('Face not found!')
                elif num_faces > 1:
                    st.warning('Multiple faces found')
                else:
                    if detected:
                        student_id = list(detected.keys())[0]
                        all_students = get_all_students()
                        student = next((s for s in all_students if str(s['student_id']) == str(student_id)), None)

                        if student:
                            st.session_state.is_logged_in = True
                            st.session_state.user_role = 'student'
                            st.session_state.student_data = student
                            st.query_params["session_role"] = "student"
                            st.query_params["session_id"] = str(student['student_id'])
                            st.toast(f'Welcome Back {student["name"]}')
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.warning("⚠️ **Face Not Recognized!** Your face is not registered in SnapClass yet.")
                        st.session_state["pending_reg_photo"] = photo_source
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("📝 Register Account Now (Attaches Scanned Face)", type="primary", width="stretch", key="btn_redirect_reg"):
                                st.session_state.active_student_portal_tab = "register"
                                st.toast("Redirecting to Registration Page...")
                                time.sleep(0.5)
                                st.rerun()
                        
                        with col2:
                            with st.expander("Or Register Quick Form Inline", expanded=False):
                                new_app_id = st.text_input("Application ID / Roll No", placeholder="E.g. APP1001", key="inline_reg_id")
                                new_name = st.text_input("Full Name", placeholder="E.g. Hamza Rizvi", key="inline_reg_name")
                                new_pwd = st.text_input("Create Password", type="password", placeholder="Enter password", key="inline_reg_pwd")
                                new_pwd_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm password", key="inline_reg_pwd_confirm")
                                
                                if st.button("Complete Registration & Login", type="primary", width="stretch", key="btn_inline_reg_submit"):
                                    if not new_app_id or not new_name or not new_pwd:
                                        st.warning("Please fill in Application ID, Name, and Password!")
                                    elif new_pwd != new_pwd_confirm:
                                        st.error("Passwords do not match!")
                                    else:
                                        with st.spinner("Creating profile & learning face..."):
                                            encodings = get_face_embeddings(img)
                                            face_emb = encodings[0].tolist() if encodings else None
                                            
                                            response_data = create_student(
                                                new_name=new_name,
                                                face_embedding=face_emb,
                                                student_id=new_app_id,
                                                password=new_pwd
                                            )
                                            if response_data:
                                                train_classifier()
                                                st.session_state.is_logged_in = True
                                                st.session_state.user_role = 'student'
                                                st.session_state.student_data = response_data[0]
                                                st.query_params["session_role"] = "student"
                                                st.query_params["session_id"] = str(response_data[0]['student_id'])
                                                st.toast(f"Profile Created & Logged In! Welcome {new_name}!")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("Failed to create profile. Application ID may already exist.")

    # --- TAB 3: REGISTER NEW STUDENT ---
    elif st.session_state.active_student_portal_tab == "register":
        with st.container(border=True):
            st.subheader('Register New Student Profile')
            
            if "pending_reg_photo" in st.session_state and st.session_state.pending_reg_photo:
                st.info("📸 **Scanned Face Photo Attached!** We pre-loaded your face photo from your FaceID scan.")
                st.image(st.session_state.pending_reg_photo, width=180, caption="Attached Face Photo")

            reg_student_id = st.text_input("Application ID / Roll No", placeholder='E.g. APP1001 or 10024', key="reg_id")
            reg_name = st.text_input("Full Name", placeholder='E.g. Hamza Rizvi', key="reg_name")
            reg_pass = st.text_input("Create Password", type='password', placeholder="Enter password", key="reg_pass")
            reg_pass_confirm = st.text_input("Confirm Password", type='password', placeholder="Confirm password", key="reg_pass_confirm")
            
            st.caption("Optional: Take or upload a face snapshot to enable AI classroom attendance matching.")
            
            reg_method = st.radio(
                "Select Photo Method:",
                ["📱 Snap Photo / Upload File (Recommended for Mobile)", "💻 Desktop Live Camera Stream"],
                index=0,
                horizontal=True,
                key="reg_input_method"
            )
            
            reg_photo = None
            if reg_method == "📱 Snap Photo / Upload File (Recommended for Mobile)":
                reg_photo = st.file_uploader("Upload or Snap Face Photo", type=["jpg", "jpeg", "png"], key="reg_file_upload")
            else:
                reg_photo = st.camera_input("Capture Face Snapshot", key="reg_camera")

            final_photo = reg_photo or st.session_state.get("pending_reg_photo")

            if st.button('Register & Create Account', type='primary', width="stretch"):
                if not reg_student_id or not reg_name or not reg_pass:
                    st.warning('Please fill in Application ID, Name, and Password!')
                elif reg_pass != reg_pass_confirm:
                    st.error("Passwords do not match!")
                else:
                    with st.spinner('Creating profile..'):
                        face_emb = None
                        if final_photo:
                            img = np.array(Image.open(final_photo))
                            encodings = get_face_embeddings(img)
                            if encodings:
                                face_emb = encodings[0].tolist()

                        response_data = create_student(
                            new_name=reg_name,
                            face_embedding=face_emb,
                            student_id=reg_student_id,
                            password=reg_pass
                        )

                        if response_data:
                            train_classifier()
                            if "pending_reg_photo" in st.session_state:
                                del st.session_state["pending_reg_photo"]
                            st.session_state.is_logged_in = True
                            st.session_state.user_role = 'student'
                            st.session_state.student_data = response_data[0]
                            st.query_params["session_role"] = "student"
                            st.query_params["session_id"] = str(response_data[0]['student_id'])
                            st.toast(f'Profile Created! Welcome {reg_name}!')
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to create profile. Application ID may already exist.")



        
    footer_dashboard()