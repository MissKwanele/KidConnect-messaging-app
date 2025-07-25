import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from requests.auth import HTTPBasicAuth

# --------------------
# Config from secrets.toml
# --------------------
VONAGE_API_KEY = st.secrets["vonage"]["api_key"]
VONAGE_API_SECRET = st.secrets["vonage"]["api_secret"]
VONAGE_FROM_NUMBER = st.secrets["vonage"]["from_number"]
WHITELIST = st.secrets["vonage"]["whitelist"]

SPREADSHEET_URL = st.secrets["google"]["spreadsheet_url"]
GOOGLE_SA_INFO = st.secrets["google_service_account"]

# --------------------
# Connect to Google Sheets
# --------------------
@st.cache_resource
def get_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_SA_INFO, scope)
    client = gspread.authorize(creds)
    sheet_main = client.open_by_url(SPREADSHEET_URL)
    parent_sheet = sheet_main.worksheet("Parents")
    termly_sheet = sheet_main.worksheet("TermlyActivities")
    return parent_sheet, termly_sheet

parent_sheet, termly_sheet = get_google_sheet()

# --------------------
# Authentication
# --------------------
def authenticate(user, password):
    users = {
        "principal": "admin123",
        "staff": "staff123"
    }
    return users.get(user) == password

# --------------------
# Send WhatsApp Message via Vonage
# --------------------
def send_whatsapp_message(to_number, message):
    url = "https://messages-sandbox.nexmo.com/v1/messages"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {
        "from": VONAGE_FROM_NUMBER,
        "to": to_number,
        "message_type": "text",
        "text": message,
        "channel": "whatsapp"
    }
    response = requests.post(url, headers=headers, json=payload,
                             auth=HTTPBasicAuth(VONAGE_API_KEY, VONAGE_API_SECRET))
    return response.status_code, response.text

# --------------------
# Streamlit UI
# --------------------
st.set_page_config(page_title="KidConnect Messaging", layout="centered")
st.title("📱 KidConnect WhatsApp Messenger")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.logged_in:
    st.subheader("🔐 Login")
    username = st.text_input("Username (principal/staff)")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.session_state.user = username
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# Dashboard after login
st.success(f"Logged in as {st.session_state.user.capitalize()}")
if st.session_state.user == "principal":
    tab1, tab2, tab3, tab4 = st.tabs(["Send Message", "Message Log", "Upload Parent List", "📅 Upload Termly Activities"])
else:
    tab1, tab2, tab3 = st.tabs(["Send Message", "Message Log", "Upload Parent List"])

with tab1:
    st.subheader("✉️ Compose Message")
    class_selected = st.radio("Select Class", ["All Classes", "English", "Afrikaans"])
    message_text = st.text_area("Message to Parents")
    send_now = st.button("Send Now")

    if send_now and message_text:
        data = parent_sheet.get_all_records()
        sent_count = 0
        for row in data:
            if class_selected != "All Classes" and row.get("Class") != class_selected:
                continue
            name = row.get("Name", "Parent")
            number = str(row.get("PhoneNumber", "")).strip()
            if number not in WHITELIST:
                st.warning(f"Skipping {name} ({number}): not in whitelist")
                continue
            full_msg = f"Hi {name}, {message_text}"
            status, resp = send_whatsapp_message(number, full_msg)
            if status == 202:
                st.success(f"Sent to {name} ({number})")
                sent_count += 1
                log_row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, number, row.get("Class", "Unknown"), message_text]
                parent_sheet.append_row(log_row)
                time.sleep(1)
            else:
                st.error(f"Failed to send to {name} ({number}): {resp}")
        st.info(f"Total messages sent: {sent_count}")

with tab2:
    st.subheader("📊 Message Log")
    try:
        df_log = pd.DataFrame(parent_sheet.get_all_records())
        st.dataframe(df_log)
    except Exception:
        st.error("Could not load message log.")

with tab3:
    st.subheader("📁 Upload Parent List (.csv)")
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file:
        df_parents = pd.read_csv(uploaded_file)
        parent_sheet.clear()
        parent_sheet.append_row(df_parents.columns.tolist())
        for _, row in df_parents.iterrows():
            parent_sheet.append_row(row.tolist())
        st.success("Parent list uploaded and saved to Google Sheet!")

if st.session_state.user == "principal":
    with tab4:
        st.subheader("📅 Upload Termly Activities (.csv)")
        uploaded_activities = st.file_uploader("Upload Termly Activities CSV", type=["csv"], key="activities")
        if uploaded_activities:
            df_activities = pd.read_csv(uploaded_activities)
            termly_sheet.clear()
            termly_sheet.append_row(df_activities.columns.tolist())
            for _, row in df_activities.iterrows():
                termly_sheet.append_row(row.tolist())
            st.success("Termly activities uploaded!")

        st.markdown("---")
        st.subheader("📖 View Uploaded Termly Activities")
        try:
            df_activities_view = pd.DataFrame(termly_sheet.get_all_records())
            st.dataframe(df_activities_view)
        except Exception:
            st.error("Could not load termly activities.")

st.markdown("---")
st.caption("Built with ❤️ using Streamlit by a Fellow Mommy | Vonage Sandbox Demo")

