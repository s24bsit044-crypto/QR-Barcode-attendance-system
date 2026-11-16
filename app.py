import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="QR Attendance System - University of Gwadar",
    page_icon="🎓",
    layout="wide"
)

# Header info
st.title("🎓 QR Code Classroom Attendance System")
st.markdown("### Department of Computer Science | University of Gwadar")
st.markdown("---")

# Sidebar Project Metadata
with st.sidebar:
    st.header("📋 Project Details")
    st.markdown("**Group Leader:** Irfan Ali")
    st.markdown("**Members:** Sharaf Jan, Qubad Bano, Salma, Nadia")
    st.markdown("**Supervisor:** Mr. Zeeshan")
    st.markdown("---")
    st.info("Upload or generate student IDs, use your webcam or upload QR snapshots to log attendance instantly.")

# Initialize Attendance File
ATTENDANCE_FILE = "attendance_log.csv"
if not os.path.exists(ATTENDANCE_FILE):
    df_init = pd.DataFrame(columns=["Student_ID", "Name", "Date", "Time"])
    df_init.to_csv(ATTENDANCE_FILE, index=False)

# Tabs for workflow
tab1, tab2, tab3 = st.tabs(["1. Student ID Generator", "2. Attendance Scanner / Logger", "3. View Attendance Logs"])

with tab1:
    st.subheader("Generate Student QR Code ID Cards")
    col1, col2 = st.columns(2)
    
    with col1:
        s_id = st.text_input("Student Registration ID", value="UG-IT-2026-001")
        s_name = st.text_input("Student Full Name", value="Irfan Ali")
        generate_btn = st.button("Generate QR Code")
        
    with col2:
        if generate_btn:
            data_string = f"ID:{s_id},Name:{s_name}"
            img = qrcode.make(data_string)
            buf = BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.image(byte_im, caption=f"QR ID Card for {s_name} ({s_id})", width=200)
            st.download_button(
                label="Download QR Badge",
                data=byte_im,
                file_name=f"{s_id}_qr.png",
                mime="image/png"
            )

with tab2:
    st.subheader("Simulated / Live Attendance Scanner")
    st.markdown("Enter student credentials or scan badge to record attendance securely.")
    
    with st.form("attendance_form"):
        scan_id = st.text_input("Enter Student ID (e.g., UG-IT-2026-001)")
        scan_name = st.text_input("Enter Student Name (e.g., Irfan Ali)")
        submit_attendance = st.form_submit_button("Mark Attendance")
        
        if submit_attendance:
            if scan_id and scan_name:
                now = datetime.now()
                curr_date = now.strftime("%Y-%m-%d")
                curr_time = now.strftime("%H:%M:%S")
                
                df_att = pd.read_csv(ATTENDANCE_FILE)
                # Check duplicate
                exists = df_att[(df_att["Student_ID"] == scan_id) & (df_att["Date"] == curr_date)]
                
                if exists.empty:
                    new_entry = pd.DataFrame({"Student_ID": [scan_id], "Name": [scan_name], "Date": [curr_date], "Time": [curr_time]})
                    df_att = pd.concat([df_att, new_entry], ignore_index=True)
                    df_att.to_csv(ATTENDANCE_FILE, index=False)
                    st.success(f"Attendance successfully recorded for {scan_name} ({scan_id}) at {curr_time}!")
                else:
                    st.warning(f"Attendance for {scan_name} ({scan_id}) has already been marked today ({curr_date}).")
            else:
                st.error("Please provide both Student ID and Name.")

with tab3:
    st.subheader("Live Attendance Records & Reports")
    if os.path.exists(ATTENDANCE_FILE):
        df_records = pd.read_csv(ATTENDANCE_FILE)
        st.dataframe(df_records, use_container_width=True)
        
        if not df_records.empty:
            csv_data = df_records.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Complete Attendance CSV",
                data=csv_data,
                file_name="classroom_attendance_report.csv",
                mime="text/csv"
            )
            
            if st.button("Clear Attendance Log"):
                pd.DataFrame(columns=["Student_ID", "Name", "Date", "Time"]).to_csv(ATTENDANCE_FILE, index=False)
                st.rerun()
        else:
            st.info("No attendance records found yet.")
