import streamlit as st
from src.database.db import create_attendance_issue

@st.dialog("⚠️ Raise Attendance Issue")
def raise_issue_dialog(session_id, subject_id, subject_name, student_id, student_name):
    st.markdown(f"**Course:** {subject_name}")
    st.markdown(f"**Session ID:** #{session_id}")
    st.caption("Were you present in class but marked absent / unrecognized? Submit a report for your teacher to review.")

    reason = st.text_area("Provide details / reason", placeholder="E.g., I was present in Row 2, but AI scanning missed my seat.")

    if st.button("Submit Issue to Teacher", type="primary", width="stretch"):
        if reason:
            create_attendance_issue(session_id, subject_id, student_id, student_name, reason)
            st.toast("✅ Issue submitted to your teacher successfully!")
            st.rerun()
        else:
            st.warning("Please enter details/reason before submitting.")
