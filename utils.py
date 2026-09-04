import hashlib
import qrcode
import os

def generate_cert_hash(student_id: str, student_name: str, department: str, file_bytes: bytes) -> str:
    """Creates a SHA-256 hash using student details and certificate file bytes."""
    data = student_id.strip() + student_name.strip() + department.strip()
    hasher = hashlib.sha256()
    hasher.update(data.encode('utf-8'))
    hasher.update(file_bytes)
    return hasher.hexdigest()

def make_qr_code(cert_hash: str, output_path: str):
    """Generates a QR code holding the certificate hash."""
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )
    qr.add_data(cert_hash)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)