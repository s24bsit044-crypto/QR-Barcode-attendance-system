# QR Code Classroom Attendance System

An automated, contactless classroom attendance tracking web application built with **Python**, **OpenCV**, **Pyzbar**, and **Streamlit**. Designed for instant deployment on **Streamlit Community Cloud** and GitHub.

---

## Group Members & Leadership
* **Group Leader:** Irfan Ali
* **Group Members:** Sharaf Jan, Qubad Bano, Salma, Nadia
* **Supervisor:** Mr. Zeeshan
* **Institution:** Department of Computer Science, University of Gwadar

---

## Features
1. **Student QR ID Generation:** Instantly generate official student QR code badges containing ID and Name.
2. **Live Webcam Scanning & Verification:** Scan QR codes directly via camera feed with automatic duplicate entry prevention.
3. **Real-Time CSV Logging:** Automatically records date, time, student ID, and name into an attendance spreadsheet.
4. **Export & Download:** Download attendance logs instantly as a CSV file for university record keeping.

---

## Local Installation & Quickstart

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/qr-attendance-system.git
   cd qr-attendance-system
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note for Linux/Debian users: ensure zbar library is installed via `sudo apt-get install libzbar0`)*

3. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
