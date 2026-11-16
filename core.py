"""Core logic: QR signing/verification, card generation, QR decoding, attendance logging."""
import hashlib
import hmac
import io
import os
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo

import cv2
import numpy as np
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont

try:  # pyzbar needs the system lib libzbar0; fall back to OpenCV if missing
    from pyzbar import pyzbar
except Exception:  # pragma: no cover
    pyzbar = None

DEFAULT_SECRET = "demo-secret-change-me"
TZ = ZoneInfo("Asia/Karachi")
LOG_COLUMNS = ["date", "time", "student_id", "name", "department", "course"]


# ---------- Tamper-resistant payloads ----------
def sign(student_id: str, secret: str) -> str:
    return hmac.new(secret.encode(), student_id.encode(), hashlib.sha256).hexdigest()[:12]


def make_payload(student_id: str, secret: str) -> str:
    return f"{student_id}.{sign(student_id, secret)}"


def verify_payload(payload: str, secret: str):
    """Return student_id if signature is valid, else None."""
    if "." not in payload:
        return None
    student_id, sig = payload.rsplit(".", 1)
    return student_id if hmac.compare_digest(sig, sign(student_id, secret)) else None


# ---------- QR cards ----------
def make_qr(payload: str, box_size: int = 8) -> Image.Image:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=box_size, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def _font(size: int, bold: bool = False):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def make_card(row, secret: str) -> Image.Image:
    """Printable ID card: header, student details, and signed QR."""
    W, H = 760, 420
    card = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, W, 70], fill=(46, 125, 50))
    d.text((24, 18), "STUDENT ATTENDANCE ID", font=_font(28, True), fill="white")
    d.rectangle([0, 0, W - 1, H - 1], outline=(46, 125, 50), width=4)
    d.text((28, 110), str(row["name"]), font=_font(32, True), fill=(20, 20, 20))
    d.text((28, 165), f"ID: {row['student_id']}", font=_font(24), fill=(60, 60, 60))
    d.text((28, 205), str(row["department"]), font=_font(22), fill=(60, 60, 60))
    d.text((28, 240), f"Semester {row['semester']}", font=_font(22), fill=(60, 60, 60))
    d.text((28, 360), "Show this card to the webcam", font=_font(18), fill=(120, 120, 120))
    qr = make_qr(make_payload(row["student_id"], secret), box_size=8).resize((280, 280))
    card.paste(qr, (W - 280 - 30, 100))
    return card


def cards_zip(students: pd.DataFrame, secret: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for _, row in students.iterrows():
            img = io.BytesIO()
            make_card(row, secret).save(img, "PNG")
            z.writestr(f"{row['student_id']}.png", img.getvalue())
    return buf.getvalue()


# ---------- Decoding ----------
def decode_image(bgr: np.ndarray):
    """Return list of (text, polygon_points) for every QR found in the image."""
    results = []
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    variants = [gray, cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)]
    scales = [1.0, 1.5]
    for img, s in zip(variants, scales):
        if pyzbar is not None:
            for obj in pyzbar.decode(img):
                if obj.type == "QRCODE":
                    pts = np.array([(p.x / s, p.y / s) for p in obj.polygon], dtype=np.int32)
                    results.append((obj.data.decode("utf-8", "ignore"), pts))
        if not results:
            text, pts, _ = cv2.QRCodeDetector().detectAndDecode(img)
            if text:
                results.append((text, (pts.reshape(-1, 2) / s).astype(np.int32)))
        if results:
            break
    return results


def annotate(bgr: np.ndarray, pts: np.ndarray, label: str, ok: bool) -> np.ndarray:
    out = bgr.copy()
    color = (50, 160, 50) if ok else (40, 40, 220)
    cv2.polylines(out, [pts.reshape(-1, 1, 2)], True, color, 4)
    x, y = int(pts[:, 0].min()), max(int(pts[:, 1].min()) - 12, 24)
    cv2.putText(out, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)
    return out


# ---------- Attendance ----------
def now():
    return datetime.now(TZ)


def mark_attendance(log: pd.DataFrame, student, course: str):
    """Returns (new_log, status) where status is 'marked' or 'duplicate'."""
    n = now()
    today = n.strftime("%Y-%m-%d")
    dup = (
        (log["date"] == today)
        & (log["student_id"] == student["student_id"])
        & (log["course"] == course)
    ).any()
    if dup:
        return log, "duplicate"
    row = {
        "date": today,
        "time": n.strftime("%H:%M:%S"),
        "student_id": student["student_id"],
        "name": student["name"],
        "department": student["department"],
        "course": course,
    }
    return pd.concat([log, pd.DataFrame([row])], ignore_index=True), "marked"
