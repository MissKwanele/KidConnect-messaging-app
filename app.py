import streamlit as st
import pandas as pd
from datetime import datetime
import time
import requests
import gspread
from requests.auth import HTTPBasicAuth
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------------
# CONFIGURATION
# -------------------------------
VONAGE_API_KEY = st.secrets["vonage"]["api_key"]
VONAGE_API_SECRET = st.secrets["vonage"]["api_secret"]
VONAGE_FROM_NUMBER = st.secrets["vonage"]["from_number"]
VONAGE_URL = "https://messages-sandbox.nexmo.com/v1/messages"

SPREADSHEET_URL = st.secrets["google"]["spreadsheet_url"]
CREDENTIAL_JSON = "kidconnect-whatsapp-bot.json"  # Make sure this is in the repo
SANDBOX_WHITELIST = st.secrets["vonage"]["whitelist"]

# -------------------------------
# GOOGLE SHEETS SETUP
# -------------------------------
@st.cache_resource
def get_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIAL_JSON, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
    return sheet

sheet = get_google_sheet()

# -------------------------------
# VONAGE WHATSAPP SEND FUNCTION
# -------------------------------
def send_whatsapp_message(to_number, text):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "from": VONAGE_FROM_NUMBER,
        "to": to_number,
        "message_type": "text",
        "text": text,
        "channel": "whatsapp"
    }

    response = requests.post(
        VONAGE_URL,
        headers=headers,
        json=payload,
        auth=HTTPBasicAuth(VONAGE_API_KEY, VONAGE_API_SECRET)
    )

    return response.status_code, response.text

# -------------------------------
# STREAMLIT UI
# -------------------------------
st.set_page_config(page_title="KidConnect Messaging", layout="centered")
st.title("📣 KidConnect WhatsApp Messaging App")
st.markdown("This is a demo prototype to send WhatsApp messages via Vonage Sandbox and log them to Google Sheets.")

st.write("🕒", datetime.now().strftime("%A %d %B %Y, %H:%M:%S"))

with st.form("send_form"):
    name = st.text_input("Parent Name", "Parent")
    number = st.text_input("Recipient WhatsApp Number", "2784XXXXXXX")
    message = st.text_area("Message", "Hello 👋 your child was absent today.")

    submit = st.form_submit_button("📤 Send Message")

    if submit:
        if number in SANDBOX_WHITELIST:
            personalized = f"Hi {name}, {message}"
            status_code, response = send_whatsapp_message(number, personalized)
            st.success(f"✅ Sent: {personalized}")
            sheet.append_row([datetime.now().isoformat(), name, number, message, status_code])
        else:
            st.error("This number is not whitelisted in the Vonage Sandbox.")

