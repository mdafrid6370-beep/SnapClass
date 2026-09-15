import streamlit as st

def subject_card(name, code, section, stats=None, footer_callback=None):
    html = f"""
        <div style="background:white; border-left: 8px solid #EB459E; padding:25px; border-radius: 20px; border: 1px solid black; margin-bottom:20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <h3 style="margin:0; color: #000000; font-size: 1.5rem;">{name}</h3>
        <p style="color:#000000; margin:10px 0;">Code : <span style="background:#E0E3FF; color:#5865F2; padding:2px 8px; border-radius:5px; font-weight:600;">{code}</span> | Section : <b>{section}</b></p>
        """
    
    if stats:
        html += """
        <div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:15px;">
        """
        for icon, label, value in stats:
            val_str = str(value)
            if "Eligible" in val_str:
                badge_bg = "#DCFCE7"
                badge_color = "#166534"
            elif "Shortage" in val_str:
                badge_bg = "#FEE2E2"
                badge_color = "#991B1B"
            else:
                badge_bg = "#F3F4F6"
                badge_color = "#1F2937"

            html += f'<div style="background: {badge_bg}; color: {badge_color}; padding:6px 14px; border-radius:12px; font-size:0.9rem; font-weight:600;">{icon} <b>{value}</b> <span style="font-size:0.8rem; opacity:0.85;">{label}</span></div>'
        
        html += "</div>"

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)

    if footer_callback:
        footer_callback()


