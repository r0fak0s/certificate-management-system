from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import qrcode
import os
import uuid
from reportlab.lib.pagesizes import A4, landscape 
from reportlab.pdfgen import canvas
from flask import send_file
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import black, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate



app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

# Ensure folders exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QR_FOLDER = os.path.join(BASE_DIR, "static", "qrcodes")
pdf_folder = os.path.join(BASE_DIR, "static", "certificates")

os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(pdf_folder, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_DIR = os.path.join(BASE_DIR, "static", "fonts")

pdfmetrics.registerFont(
    TTFont("Montserrat", os.path.join(FONT_DIR, "Montserrat-Regular.ttf"))
)

pdfmetrics.registerFont(
    TTFont("MontserratBold", os.path.join(FONT_DIR, "Montserrat-Bold.ttf"))
)

pdfmetrics.registerFont(
    TTFont("Allura", os.path.join(FONT_DIR, "Allura-Regular.ttf"))
)


def generate_qr(cert_id):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    qr_folder = os.path.join(BASE_DIR, "static", "qrcodes")
    os.makedirs(qr_folder, exist_ok=True)

    verify_url = request.url_root.rstrip("/") + f"/verify/{cert_id}"

    qr_img = qrcode.make(verify_url)
    qr_path = os.path.join(qr_folder, f"{cert_id}.png")
    qr_img.save(qr_path)

    return qr_path

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def generate_certificate_pdf(cert):
    pdf_path = os.path.join(pdf_folder, f"{cert['id']}.pdf")
    qr_path = os.path.join(QR_FOLDER, f"{cert['id']}.png")
    logo_path = os.path.join(BASE_DIR, "static", "images", "logo.png")

    c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
    width, height = landscape(A4)

    # ======================
    # BACKGROUND
    # ======================
    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(0, 0, width, height, fill=1)
    # ======================
    # THIN BORDER
    # ======================
    c.setStrokeColor(HexColor("#0BB15D"))
    c.setLineWidth(3)
    c.rect(15, 15, width - 30, height - 30, fill=0)


    # Subtle diagonal pattern
    c.setStrokeColor(HexColor("#E6F2EC"))
    c.setLineWidth(1)
    for x in range(-int(height), int(width), 45):
        c.line(x, 0, x + height, height)

    # ======================
    # TOP HEADER
    # ======================
    c.setFillColor(HexColor("#1E3A34"))  # dark green
    c.rect(0, height - 75, width, 75, fill=1)

    # Accent line
    c.setFillColor(HexColor("#0BB15D"))
    c.rect(0, height - 82, width, 6, fill=1)

    # Logo (optional)
    
 
    if os.path.exists(logo_path):
        
        c.drawImage(
            logo_path,
            40,                      # left margin
            height - 170,             # SAFE vertical position
            220,
            75,
            preserveAspectRatio=True,
            mask="auto"
    )
      


    # ======================
    # TITLE
    # ======================
    c.setFillColor(black)
    c.setFont("MontserratBold", 36)
    c.drawCentredString(width / 2, height - 140, "CERTIFICATE")

    c.setFont("MontserratBold", 16)
    c.drawCentredString(width / 2, height - 175, "OF FORKLIFT TRAINING COMPLETION")

    # ======================
    # INTRO TEXT
    # ======================
    c.setFont("Montserrat", 12)
    c.setFillColor(HexColor("#444444"))
    c.drawCentredString(
        width / 2,
        height - 220,
        "Zebra Safety Services certifies that"
    )

    # ======================
    # RECIPIENT NAME
    # ======================
    c.setFont("Allura", 52)
    c.setFillColor(HexColor("#1E3A34"))
    c.drawCentredString(width / 2, height / 2 + 30, cert["name"])

    # Name underline
    c.setStrokeColor(HexColor("#0BB15D"))
    c.setLineWidth(1.5)
    c.line(width / 2 - 280, height / 2 + 10, width / 2 + 280, height / 2 + 10)

    # ======================
    # COURSE TITLE
    # ======================


    # Description
    c.setFont("Montserrat", 11)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(
        width / 2,
        height / 2 - 80,
        "has successfully completed site-specific forklift training,including safe operation in construction environments with variable terrain."
    )

    # ======================
    # WATERMARK SEAL (OPTIONAL)
    # ======================
    seal_path = "static/images/seal.png"
    if os.path.exists(seal_path):
        c.saveState()
        c.setFillAlpha(0.05)
        c.drawImage(
            seal_path,
            width / 2 - 220,
            height / 2 - 220,
            440,
            440,
            mask="auto"
        )
        c.restoreState()

    # ======================
    # FOOTER INFO
    # ======================
    # Divider line (move it slightly up)
    c.setStrokeColor(HexColor("#0BB15D"))
    c.setLineWidth(1)
    c.line(60, 150, width - 60, 150)

    # Signature lines (lowered for breathing space)
    c.setFont("Montserrat", 10)
    c.setFillColor(black)

    # Left signature
    c.line(80, 110, 280, 110)
    c.drawString(80, 90, "Authorized Signature")

    # Right signature
    c.line(width - 280, 110, width - 80, 110)
    c.drawString(width - 280, 90, "Training Director")

    # Certificate ID
    c.setFont("Montserrat", 9)
    c.drawCentredString(
        width / 2,
        120,
        f"Certificate ID: {cert['id']}"
    )

    # ======================
    # QR CODE (BOTTOM CENTER)
    # ======================
    if os.path.exists(qr_path):
        qr_size = 85
        c.drawImage(
        qr_path,
        (width - qr_size) / 2,
        25,
        qr_size,
        qr_size,
        mask="auto"
    )

    c.showPage()
    c.save()


def get_db():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "certificates.db")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("CREATE TABLE IF NOT EXISTS certificates (id TEXT, name TEXT, event TEXT, dob TEXT, gender TEXT, phone TEXT, nationality TEXT, email TEXT, address TEXT, state TEXT, nin TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT)")
    conn.commit()
    return conn


@app.route("/")
def index():
    return redirect("/login")


@app.route("/create", methods=["GET", "POST"])
@admin_required
def create_certificate():

    if request.method == "POST":
        cert_id = str(uuid.uuid4())

        db = get_db()
        db.execute("""
            INSERT INTO certificates (
                id, name, event, dob, gender, phone,
                nationality, email, address, state, nin
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cert_id,
            request.form["name"],
            request.form["event"],
            request.form["dob"],
            request.form["gender"],
            request.form["phone"],
            request.form["nationality"],
            request.form["email"],
            request.form["address"],
            request.form["state"],
            request.form["nin"]
        ))
        db.commit()

        generate_qr(cert_id)
        generate_certificate_pdf({
            "id": cert_id,
            "name": request.form["name"],
            "event": request.form["event"]
        })

        return redirect("/admin")  # 👈 BACK TO DASHBOARD

    return render_template("create.html")




@app.route("/download/<cert_id>")
def download(cert_id):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    pdf_folder = os.path.join(BASE_DIR, "static", "certificates")

    pdf_path = os.path.join(pdf_folder, f"{cert_id}.pdf")

    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    else:
        return "Certificate not found", 404
    
@app.route("/registrants")
@admin_required
def registrants():
    db = get_db()
    users = db.execute("""
        SELECT rowid AS id, name, phone, email, nationality, state
        FROM certificates
        ORDER BY rowid DESC
    """).fetchall()
    return render_template("registrants.html", registrants=users)

@app.route("/registrant/<int:id>")
@admin_required
def registrant(id):
    db = get_db()
    r = db.execute(
        "SELECT * FROM certificates WHERE rowid = ?",
        (id,)
    ).fetchone()

    return f"""
    <h3>{r['name']}</h3>
    <div class="info-grid">
        <p><b>DOB:</b> {r['dob']}</p>
        <p><b>Gender:</b> {r['gender']}</p>
        <p><b>Phone:</b> {r['phone']}</p>
        <p><b>Email:</b> {r['email']}</p>
        <p><b>Nationality:</b> {r['nationality']}</p>
        <p><b>State:</b> {r['state']}</p>
        <p><b>NIN:</b> {r['nin']}</p>
    </div>
    """
    return render_template("registrant_detail.html", r=r)

@app.route("/preview/<cert_id>")
@admin_required
def preview(cert_id):
    return send_file(
        os.path.join(pdf_folder, f"{cert_id}.pdf"),
        mimetype="application/pdf"
    )

@app.route("/admin")
@admin_required
def admin():
    db = get_db()
    certs = db.execute(
        "SELECT id, name, event FROM certificates ORDER BY rowid DESC"
    ).fetchall()
    count = db.execute("SELECT COUNT(*) FROM certificates").fetchone()[0]
    return render_template("admin.html", certs=certs, count=count)



@app.route("/settings")
@admin_required
def settings():
    return render_template("settings.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        admin = db.execute(
            "SELECT * FROM admins WHERE username = ?",
            (username,)
        ).fetchone()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin"] = admin["id"]
            return redirect("/admin")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
@admin_required
def logout():
    session.pop("admin", None)
    return redirect("/login")


@app.route("/verify/<cert_id>")
def verify(cert_id):
    db = get_db()
    cert = db.execute(
        "SELECT * FROM certificates WHERE id = ?",
        (cert_id,)
    ).fetchone()

    return render_template("verify.html", cert=cert)

@app.route("/change-password", methods=["GET", "POST"])
@admin_required
def change_password():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]

        db = get_db()
        admin = db.execute(
            "SELECT * FROM admins WHERE id = ?",
            (session["admin"],)
        ).fetchone()

        if not check_password_hash(admin["password_hash"], old_password):
            return render_template(
                "change_password.html",
                error="Old password incorrect"
            )

        new_hash = generate_password_hash(new_password)

        db.execute(
            "UPDATE admins SET password_hash = ? WHERE id = ?",
            (new_hash, session["admin"])
        )
        db.commit()
        db.close()

        return redirect("/admin")

    return render_template("change_password.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))



