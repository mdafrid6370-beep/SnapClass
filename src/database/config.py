import os
import streamlit as st
from supabase import create_client, Client

url = None
key = None

try:
    if "SUPABASE_URL" in st.secrets:
        url = st.secrets["SUPABASE_URL"]
    if "SUPABASE_KEY" in st.secrets:
        key = st.secrets["SUPABASE_KEY"]
except Exception:
    pass

if not url:
    url = os.getenv("SUPABASE_URL")
if not key:
    key = os.getenv("SUPABASE_KEY")

if not url or not key:
    st.error("⚠️ **Database Secrets Missing**: `SUPABASE_URL` or `SUPABASE_KEY` has not been set yet!")
    st.info("""
    ### ⚙️ How to add secrets on Streamlit Cloud:
    1. Click **Manage app** (bottom right corner of your deployed app).
    2. Click **⋮ (Settings)** → **Secrets**.
    3. Paste your Supabase credentials:
    ```toml
    SUPABASE_URL = "https://your-project.supabase.co"
    SUPABASE_KEY = "your-supabase-anon-key"
    ```
    4. Click **Save**!
    """)
    st.stop()

supabase: Client = create_client(url, key)