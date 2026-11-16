"""QR-Code Classroom Attendance System - Streamlit app."""
import os

import cv2
import numpy as np
import pandas as pd
import streamlit as st

import core

st.set_page_config(page_title="QR Attendance System", page_icon="✅", layout="wide")


def get_secret() -> str:
    try:
        if "QR_SECRET" in st.secrets:
            return st.secrets["QR_SECRET"]
    except Exception:
        pass
    return os.environ.get("QR_SECRET", core.DEFAULT_SECRET)


SECRET = get_secret()


@st.cache_data
def load_default_students() -> pd.DataFrame:
    return pd.read_csv("students.csv", dtype=str)


# ---------- Session state ----------
if "log" not in st.session_state:
    st.session_state.log = pd.DataFrame(columns=core.LOG_COLUMNS)
if "students" not in st.session_state:
    st.session_state.students = load_default_students()

students: pd.DataFrame = st.session_state.students

# ---------- Sidebar ----------
with st.sidebar:
    st.title("✅ QR Attendance")
    st.caption("Computer Vision & AI Module\nSupervisor: Mr. Zeeshan")
    course = st.text_input("Course / Session", value="Computer Vision & AI")
    st.metric("Registered students", len(students))
    today = core.now().strftime("%Y-%m-%d")
    present_today = (st.session_state.log["date"] == today).sum()
    st.metric("Present today", int(present_today))
    if SECRET == core.DEFAULT_SECRET:
        st.warning("Using the demo secret. Set QR_SECRET in Secrets for real use.")

tab_scan, tab_log, tab_students, tab_about = st.tabs(
    ["📷 Scan Attendance", "📋 Attendance Log", "🎓 Students & QR Cards", "ℹ️ About"]
)

# ---------- Scan ----------
with tab_scan:
    st.subheader("Scan a student QR card")
    mode = st.radio("Input", ["Webcam", "Upload image"], horizontal=True)
    if mode == "Webcam":
        img_file = st.camera_input("Hold the QR card steady in front of the camera, then take a photo")
    else:
        img_file = st.file_uploader("Upload a photo of the QR card", type=["png", "jpg", "jpeg"])

    if img_file is not None:
        data = np.frombuffer(img_file.getvalue(), np.uint8)
        frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
        found = core.decode_image(frame)

        if not found:
            st.error("No QR code detected. Move closer, improve lighting, and try again.")
        for payload, pts in found:
            sid = core.verify_payload(payload, SECRET)
            match = students[students["student_id"] == sid] if sid else students.iloc[0:0]

            if sid is None:
                st.error("❌ Invalid or tampered QR code. Attendance NOT recorded.")
                st.image(core.annotate(frame, pts, "INVALID", False)[:, :, ::-1])
            elif match.empty:
                st.error(f"❌ Signature valid but `{sid}` is not in the student list.")
                st.image(core.annotate(frame, pts, "UNREGISTERED", False)[:, :, ::-1])
            else:
                student = match.iloc[0]
                st.session_state.log, status = core.mark_attendance(st.session_state.log, student, course)
                if status == "marked":
                    st.success(f"✅ Welcome, **{student['name']}** ({student['student_id']})! Attendance marked.")
                    st.balloons()
                    label = f"{student['name']} - PRESENT"
                else:
                    st.warning(f"⚠️ **{student['name']}** already checked in today for this course.")
                    label = f"{student['name']} - DUPLICATE"
                st.image(core.annotate(frame, pts, label, status == "marked")[:, :, ::-1])

# ---------- Log ----------
with tab_log:
    st.subheader("Attendance records")
    log = st.session_state.log
    c1, c2 = st.columns(2)
    dates = ["All"] + sorted(log["date"].unique().tolist(), reverse=True)
    sel = c1.selectbox("Date", dates)
    view = log if sel == "All" else log[log["date"] == sel]
    st.dataframe(view, width="stretch", hide_index=True)

    absent_date = today if sel == "All" else sel
    present_ids = set(log[(log["date"] == absent_date) & (log["course"] == course)]["student_id"])
    absent = students[~students["student_id"].isin(present_ids)][["student_id", "name"]]
    with st.expander(f"Absent on {absent_date} ({len(absent)})"):
        st.dataframe(absent, width="stretch", hide_index=True)

    st.download_button("⬇️ Download attendance CSV", view.to_csv(index=False), "attendance_log.csv", "text/csv")
    if st.button("🗑️ Clear log (this session)"):
        st.session_state.log = pd.DataFrame(columns=core.LOG_COLUMNS)
        st.rerun()
    st.caption("Streamlit Cloud storage is temporary. Download the CSV after each class.")

# ---------- Students ----------
with tab_students:
    st.subheader("Student dataset")
    up = st.file_uploader(
        "Replace the dataset with your own CSV (columns: student_id,name,department,semester,email)", type="csv"
    )
    if up is not None:
        new = pd.read_csv(up, dtype=str)
        need = {"student_id", "name", "department", "semester"}
        if need.issubset(new.columns):
            st.session_state.students = new
            students = new
            st.success(f"Loaded {len(new)} students.")
        else:
            st.error(f"CSV must contain columns: {sorted(need)}")
    st.dataframe(students, width="stretch", hide_index=True)

    st.subheader("QR ID cards")
    pick = st.selectbox("Preview a card", students["student_id"] + " — " + students["name"])
    row = students[students["student_id"] == pick.split(" — ")[0]].iloc[0]
    st.image(core.make_card(row, SECRET), width=520)
    st.download_button("⬇️ Download ALL cards (ZIP)", core.cards_zip(students, SECRET), "qr_cards.zip", "application/zip")

# ---------- About ----------
with tab_about:
    st.markdown(
        """
**QR-Code Classroom Attendance System**  
Group: Irfan Ali (Leader), Sharaf Jan, Qubad Bano, Salma, Nadia · Supervisor: Mr. Zeeshan

**How it works**
1. Each student gets a printed card with a QR code containing `student_id.signature` (HMAC-SHA256), so forged codes are rejected.
2. The camera image is decoded with `pyzbar` (OpenCV fallback).
3. The ID is verified, checked against the student list, and duplicate check-ins for the same day and course are blocked.
4. The record is added to the log with a timestamp and can be downloaded as CSV.
        """
    )
