import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from web3 import Web3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from utils import generate_cert_hash, make_qr_code

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key_123")

UPLOAD_FOLDER = os.path.join("static", "uploads")
QR_FOLDER = os.path.join("static", "qrcodes")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["QR_FOLDER"] = QR_FOLDER

# 1. MongoDB Setup with strict 2-second timeout to prevent infinite page loading
try:
    mongo_client = MongoClient(
        os.getenv("MONGO_URI", "mongodb://localhost:27017/cert_verify_db"),
        serverSelectionTimeoutMS=2000
    )
    mongo_client.server_info()
    db = mongo_client["cert_verify_db"]
    students_col = db["students"]
    certs_col = db["certificates"]
    mongo_connected = True
except Exception as e:
    print(f"[!] MongoDB Warning: {e}")
    mongo_connected = False
    students_col = None
    certs_col = None

# 2. Web3 / Ganache Setup with strict 2-second timeout
w3 = Web3(Web3.HTTPProvider(
    os.getenv("GANACHE_URL", "http://127.0.0.1:7545"),
    request_kwargs={'timeout': 2}
))
contract_address = os.getenv("CONTRACT_ADDRESS")
contract = None
admin_account = None

abi_file_path = "contract/Certificate_abi.json"
if os.path.exists(abi_file_path) and w3.is_connected() and contract_address:
    try:
        with open(abi_file_path, "r") as f:
            contract_abi = json.load(f)
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        admin_account = w3.eth.accounts[0]
    except Exception as err:
        print(f"[!] Contract load error: {err}")


@app.route("/")
def index():
    return render_template("index.html", student_logged_in=False)


# ================= ADMIN ROUTES ================= #

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid Admin Credentials", "danger")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return render_template("dashboard.html", active_tab="overview")


@app.route("/admin/register_student", methods=["POST"])
def register_student():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    if not mongo_connected:
        flash("MongoDB is offline. Please start MongoDB service.", "danger")
        return redirect(url_for("admin_dashboard"))

    student_id = request.form.get("student_id", "").strip()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    department = request.form.get("department", "").strip()
    grad_year = request.form.get("grad_year", "").strip()
    cgpa = request.form.get("cgpa", "").strip()

    if students_col.find_one({"student_id": student_id}):
        flash("Student ID already exists in system!", "warning")
        return redirect(url_for("admin_dashboard"))

    students_col.insert_one({
        "student_id": student_id,
        "name": name,
        "email": email,
        "password": password,
        "department": department,
        "grad_year": grad_year,
        "cgpa": cgpa,
        "created_at": datetime.now()
    })
    flash("Student account registered successfully!", "success")
    return redirect(url_for("view_records"))


@app.route("/admin/issue_certificate", methods=["POST"])
def issue_certificate():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    if not contract or not w3.is_connected():
        flash("Ganache is not connected or contract is not deployed.", "danger")
        return redirect(url_for("admin_dashboard"))

    student_id = request.form.get("student_id", "").strip()
    name = request.form.get("name", "").strip()
    department = request.form.get("department", "").strip()
    cgpa = request.form.get("cgpa", "").strip()
    passing_year = request.form.get("passing_year", "").strip()
    distinction = request.form.get("distinction", "").strip()

    cert_pdf = request.files.get("cert_pdf")
    student_photo = request.files.get("student_photo")

    if not cert_pdf or not student_photo:
        flash("Please upload both Certificate PDF and Student Photo!", "warning")
        return redirect(url_for("admin_dashboard"))

    cert_filename = secure_filename(f"{student_id}_cert_{cert_pdf.filename}")
    photo_filename = secure_filename(f"{student_id}_photo_{student_photo.filename}")

    cert_path = os.path.join(app.config["UPLOAD_FOLDER"], cert_filename)
    photo_path = os.path.join(app.config["UPLOAD_FOLDER"], photo_filename)

    cert_bytes = cert_pdf.read()
    with open(cert_path, "wb") as f:
        f.write(cert_bytes)
    student_photo.save(photo_path)

    # SHA-256 Hash
    cert_hash = generate_cert_hash(student_id, name, department, cert_bytes)

    # Push to Ganache Blockchain
    try:
        tx_hash = contract.functions.issueCertificate(
            student_id, name, department, cert_hash
        ).transact({"from": admin_account})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        tx_hash_hex = receipt.transactionHash.hex()
    except Exception as e:
        flash(f"Blockchain Error: {str(e)}", "danger")
        return redirect(url_for("admin_dashboard"))

    # Generate QR Code
    qr_filename = f"{student_id}_qr.png"
    qr_full_path = os.path.join(app.config["QR_FOLDER"], qr_filename)
    make_qr_code(cert_hash, qr_full_path)

    # Save to MongoDB (both cert and auto-create student account if missing)
    if mongo_connected:
        # 1. Update/insert certificate collection
        certs_col.update_one(
            {"student_id": student_id},
            {"$set": {
                "student_id": student_id,
                "name": name,
                "department": department,
                "cgpa": cgpa,
                "passing_year": passing_year,
                "distinction": distinction,
                "cert_hash": cert_hash,
                "tx_hash": tx_hash_hex,
                "cert_pdf": cert_filename,
                "student_photo": photo_filename,
                "qr_code": qr_filename,
                "issue_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }},
            upsert=True
        )

        # 2. If student isn't registered yet, create default account with password '123'
        existing_student = students_col.find_one({"student_id": student_id})
        if not existing_student:
            students_col.insert_one({
                "student_id": student_id,
                "name": name,
                "email": f"{student_id.lower()}@college.edu",
                "password": "123",
                "department": department,
                "grad_year": passing_year,
                "cgpa": cgpa,
                "created_at": datetime.now()
            })

    flash("Certificate issued & recorded on Blockchain!", "success")
    return redirect(url_for("view_records"))


@app.route("/admin/records")
def view_records():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    records = list(certs_col.find()) if mongo_connected else []
    students = list(students_col.find()) if mongo_connected else []

    return render_template(
        "dashboard.html",
        active_tab="records",
        records=records,
        students=students
    )


# ================= STUDENT ROUTES ================= #

@app.route("/student/login", methods=["POST"])
def student_login():
    if not mongo_connected:
        flash("Database is offline. Please make sure MongoDB is running.", "danger")
        return redirect(url_for("index"))

    student_id = request.form.get("student_id", "").strip()
    password = request.form.get("password", "").strip()

    student = students_col.find_one({
        "student_id": {"$regex": f"^{student_id}$", "$options": "i"},
        "password": password
    })

    if not student:
        flash("Invalid Student Roll Number or Password!", "danger")
        return redirect(url_for("index"))

    session["student_id"] = student["student_id"]
    return redirect(url_for("student_portal"))


@app.route("/student/portal")
def student_portal():
    student_id = session.get("student_id")
    if not student_id or not mongo_connected:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("index"))

    student = students_col.find_one({"student_id": student_id})
    if not student:
        session.pop("student_id", None)
        flash("Student record not found.", "danger")
        return redirect(url_for("index"))

    cert = certs_col.find_one({"student_id": student_id})
    return render_template("index.html", student=student, cert=cert, student_logged_in=True)


@app.route("/student/logout")
def student_logout():
    session.pop("student_id", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


# ================= VERIFIER ROUTE ================= #

@app.route("/verify", methods=["GET", "POST"])
def verify():
    result = None
    if request.method == "POST":
        cert_hash = request.form.get("cert_hash", "").strip()

        if "qr_file" in request.files and request.files["qr_file"].filename != "":
            try:
                from PIL import Image
                from pyzbar.pyzbar import decode
                img = Image.open(request.files["qr_file"])
                decoded = decode(img)
                if decoded:
                    cert_hash = decoded[0].data.decode("utf-8").strip()
            except Exception as e:
                print(f"[!] QR decode error: {e}")

        if cert_hash and contract and w3.is_connected():
            try:
                is_valid, student_id, name, department, timestamp = contract.functions.verifyCertificate(cert_hash).call()
                if is_valid:
                    cert_doc = certs_col.find_one({"cert_hash": cert_hash}) if mongo_connected else None
                    result = {
                        "status": "VALID",
                        "student_id": student_id,
                        "name": name,
                        "department": department,
                        "issue_date": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A",
                        "cert_pdf": cert_doc.get("cert_pdf") if cert_doc else None,
                        "student_photo": cert_doc.get("student_photo") if cert_doc else None,
                    }
                else:
                    result = {"status": "INVALID", "message": "Certificate hash is not registered on the Blockchain."}
            except Exception as e:
                result = {"status": "INVALID", "message": f"Verification error: {str(e)}"}
        else:
            result = {"status": "INVALID", "message": "No valid hash found, or Blockchain network is unavailable."}

    return render_template("verify.html", result=result)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))