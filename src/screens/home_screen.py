import streamlit as st
from src.components.header import header_home
from src.components.footer import footer_home
from src.ui.base_layout import style_base_layout, style_background_home

def home_screen():
    style_background_home()
    style_base_layout()

    header_home()

    # --- HERO SECTION ---
    st.markdown("""
        <div style="text-align:center; max-width:850px; margin:0 auto 30px auto;">
            <h2 style="font-size:2.8rem; color:#2E1065; margin-bottom:15px; line-height:1.2;">
                AI-Powered Attendance Recognition System
            </h2>
            <p style="font-size:1.15rem; color:#1D1E24; line-height:1.6;">
                SnapClass is an intelligent classroom management platform leveraging InsightFace deep-learning embeddings, 
                live WebRTC video streams, automated session controls, and student dispute notifications.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- PORTAL SELECTION CARDS ---
    col1, col2 = st.columns(2, gap="large")

    with col1:
        with st.container(border=True):
            st.markdown("<h2 style='color:#2E1065; text-align:center;'>I'm Student</h2>", unsafe_allow_html=True)
            c_img1, c_img2, c_img3 = st.columns([1, 2, 1])
            with c_img2:
                st.image("https://i.ibb.co/844D9Lrt/mascot-student.png", width=140)
            st.caption("Access enrolled courses, view attendance logs, and report unrecognized attendance.")
            st.space()
            if st.button('Launch Student Portal 🚀', type='primary', width='stretch', key='btn_home_student'):
                st.session_state['login_type'] = 'student'
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("<h2 style='color:#2E1065; text-align:center;'>I'm Teacher</h2>", unsafe_allow_html=True)
            c_img1, c_img2, c_img3 = st.columns([1, 2, 1])
            with c_img2:
                st.image("https://i.ibb.co/CsmQQV6X/mascot-prof.png", width=160)
            st.caption("Take AI face attendance, run WebRTC live scans, manage courses, and resolve disputes.")
            st.space()
            if st.button('Launch Teacher Portal ⚡', type='secondary', width='stretch', key='btn_home_teacher'):
                st.session_state['login_type'] = 'teacher'
                st.rerun()

    st.divider()

    # --- FEATURES GRID ---
    st.markdown("<h2 style='text-align:center; color:#2E1065; margin-bottom:20px;'>✨ Core Platform Features</h2>", unsafe_allow_html=True)
    
    f1, f2 = st.columns(2, gap="medium")
    with f1:
        with st.container(border=True):
            st.markdown("### 🤖 Deep Learning Face Matching")
            st.markdown("High-accuracy face detection and 512-dimensional vector matching using InsightFace ArcFace models.")

        with st.container(border=True):
            st.markdown("### 🔔 Student Disputes & Alerts")
            st.markdown("Students can review session alerts and raise claims if unrecognized, allowing 1-click teacher approval.")

    with f2:
        with st.container(border=True):
            st.markdown("### 📹 Live WebRTC Video Stream")
            st.markdown("Real-time classroom camera video processing for instantaneous attendance recording during live lectures.")

        with st.container(border=True):
            st.markdown("### 🛡️ Automated Session Safety")
            st.markdown("Active attendance sessions automatically terminate when teachers log out or close the browser tab.")

    footer_home()