
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="KidConnect Messaging", layout="centered")

st.title("📣 KidConnect WhatsApp Messaging App")
st.markdown("This is a prototype Streamlit app to send WhatsApp messages via Vonage API.")

# Display current time
st.write("🕒", datetime.now().strftime("%A %d %B %Y, %H:%M:%S"))

# Simple form placeholder
with st.form("message_form"):
    number = st.text_input("Recipient WhatsApp Number", value="27712345678")
    message = st.text_area("Message", value="Hello Parent 👋")
    submitted = st.form_submit_button("Send Message")

    if submitted:
        st.success(f"Message sent to {number} ✅")
