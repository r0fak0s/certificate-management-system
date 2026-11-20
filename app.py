from flask import Flask, render_template, request, redirect, url_for, abort
import sqlite3
import qrcode
import os
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape 
from reportlab.pdfgen import canvas
from flask import send_file
from flask import session
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import black, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont



app = Flask(__name__)
# Render terminates HTTPS at its proxy; trust the forwarded scheme/host headers.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Fail closed: never start with a predictable or missing session secret.
secret_key = os.environ.get("SECRET_KEY")
if not secret_key or len(secret_key) < 32:
    raise RuntimeError("Set SECRET_KEY in the environment to a random value of at least 32 characters.")
app.config.update(
    SECRET_KEY=secret_key,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "true").lower() == "true",
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=1800,
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)

csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# On Render, set STORAGE_DIR to the mounted persistent disk (for example /var/data).
STORAGE_DIR = os.environ.get("STORAGE_DIR", BASE_DIR)
DB_PATH = os.environ.get("DB_PATH", "certificates.db")
QR_FOLDER = os.path.join(STORAGE_DIR, "QR_FOLDER", "static", "qrcodes")
pdf_folder = os.path.join(STORAGE_DIR, "static", "certificates")
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(pdf_folder, exist_ok=True)

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
    os.makedirs(QR_FOLDER, exist_ok=True)

    verify_url = request.url_root.rstrip("/") + f"/verify/{cert_id}"

    qr_img = qrcode.make(verify_url)
    qr_path = os.path.join(QR_FOLDER, f"{cert_id}.png")
    qr_img.save(qr_path)

    return qr_path

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
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
    c.setFont("MontserratBold", 12)
    c.setFillColor(HexColor("#222222"))
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
    c.setFont("MontserratBold", 11)
    c.setFillColor(HexColor("#292929"))
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

    # Date and proprietor fields
    c.setFillColor(HexColor("#222222"))
    c.setFont("MontserratBold", 10)

    # Print the administrator-selected date above the left line.
    raw_date = cert.get("certificate_date", "")
    try:
        display_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%d %B %Y")
    except (TypeError, ValueError):
        display_date = raw_date or ""

    c.drawCentredString(180, 116, display_date)
    c.line(80, 110, 280, 110)
    c.drawCentredString(180, 90, "DATE")

    # Proprietor field on the right
    c.line(width - 280, 110, width - 80, 110)
    c.drawCentredString(width - 180, 90, "PROPRIETOR")

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
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id TEXT, name TEXT, event TEXT, dob TEXT, gender TEXT, phone TEXT,
            nationality TEXT, email TEXT, address TEXT, state TEXT, nin TEXT,
            certificate_date TEXT
        )
    """)
    conn.execute("""CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
    )""")
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(certificates)").fetchall()}
    if "certificate_date" not in columns:
        conn.execute("ALTER TABLE certificates ADD COLUMN certificate_date TEXT")
    conn.commit()
    return conn


def close_db(conn):
    if conn is not None:
        conn.close()


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/create", methods=["GET", "POST"])
@admin_required
def create_certificate():

    if request.method == "POST":
        certificate_date = request.form.get("certificate_date", "").strip()
        try:
            # Past dates are intentionally allowed for administrator-entered certificates.
            datetime.strptime(certificate_date, "%Y-%m-%d")
        except (TypeError, ValueError):
            return render_template(
                "create.html",
                error="Please enter a valid certificate date."
            )

        cert_id = str(uuid.uuid4())

        db = get_db()
        db.execute("""
            INSERT INTO certificates (
                id, name, event, dob, gender, phone,
                nationality, email, address, state, nin, certificate_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            request.form["nin"],
            request.form["certificate_date"]
        ))
        db.commit()
        db.close()

        generate_qr(cert_id)
        generate_certificate_pdf({
            "id": cert_id,
            "name": request.form["name"],
            "event": request.form["event"],
            "certificate_date": certificate_date
        })

        return redirect("/admin")  # 👈 BACK TO DASHBOARD

    return render_template("create.html")




@app.route("/download/<cert_id>")
def download(cert_id):
    if not is_valid_cert_id(cert_id):
        abort(404)
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
    db.close()
    return render_template("registrants.html", registrants=users)

@app.route("/registrant/<int:id>")
@admin_required
def registrant(id):
    db = get_db()
    r = db.execute("SELECT rowid AS id, * FROM certificates WHERE rowid = ?", (id,)).fetchone()
    db.close()
    if r is None:
        abort(404)
    # Render through Jinja so database values are HTML-escaped (prevents stored XSS).
    return render_template("registrant_detail.html", r=r)

@app.route("/preview/<cert_id>")
@admin_required
def preview(cert_id):
    if not is_valid_cert_id(cert_id):
        abort(404)
    path = os.path.join(pdf_folder, f"{cert_id}.pdf")
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, mimetype="application/pdf")

@app.route("/admin")
@admin_required
def admin():
    db = get_db()
    certs = db.execute(
        "SELECT id, name, event FROM certificates ORDER BY rowid DESC"
    ).fetchall()
    count = db.execute("SELECT COUNT(*) FROM certificates").fetchone()[0]
    db.close()
    return render_template("admin.html", certs=certs, count=count)



@app.route("/settings")
@admin_required
def settings():
    return render_template("settings.html")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        admin = db.execute(
            "SELECT * FROM admins WHERE username = ?", (username,)
        ).fetchone()
        db.close()

        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()  # prevent session fixation
            session["admin"] = admin["id"]
            session.permanent = True
            return redirect(url_for("admin"))

        return render_template("login.html", error="Invalid username or password"), 401

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@admin_required
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/verify/<cert_id>")
def verify(cert_id):
    db = get_db()
    cert = db.execute(
        "SELECT * FROM certificates WHERE id = ?",
        (cert_id,)
    ).fetchone()
    db.close()
    return render_template("verify.html", cert=cert)

@app.route("/change-password", methods=["GET", "POST"])
@admin_required
def change_password():
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        if len(new_password) < 12:
            return render_template(
                "change_password.html",
                error="New password must be at least 12 characters long."
            ), 400

        db = get_db()
        admin = db.execute(
            "SELECT * FROM admins WHERE id = ?", (session["admin"],)
        ).fetchone()
        if not admin or not check_password_hash(admin["password_hash"], old_password):
            db.close()
            return render_template(
                "change_password.html", error="Current password is incorrect."
            ), 400

        db.execute(
            "UPDATE admins SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_password), session["admin"])
        )
        db.commit()
        db.close()
        session.clear()  # require a fresh login after changing credentials
        return redirect(url_for("login"))

    return render_template("change_password.html")


def is_valid_cert_id(cert_id):
    # Certificate IDs are UUIDs; reject path-like input before building file paths.
    try:
        uuid.UUID(cert_id)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cache-Control", "no-store")
    if request.is_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))



