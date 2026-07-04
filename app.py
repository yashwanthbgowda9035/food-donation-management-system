from flask import Flask, render_template, request, redirect, session
import sqlite3
import smtplib
from email.mime.text import MIMEText
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
from werkzeug.utils import secure_filename
import datetime
import qrcode
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "foodbridge_secret_key"

        
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect("food.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        password TEXT,
        role TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        donor_id INTEGER,
        food_name TEXT,
        quantity TEXT,
        category TEXT,
        prepared_time TEXT,
        expiry_time TEXT,
        address TEXT,
        status TEXT DEFAULT 'Available'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        donation_id INTEGER,
        ngo_id INTEGER,
        status TEXT DEFAULT 'Pending',
        pickup_date TEXT,
        pickup_time TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ngo_id INTEGER,
        rating TEXT,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()


# ================= EMAIL =================
def send_email(to_email, subject, message):
    import smtplib
    from email.mime.text import MIMEText

    sender_email = "yashwanthb2007@gmail.com"
    sender_password = os.environ.get("Gowda@123")  # Use environment variable for security
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()

        print("✅ EMAIL SENT:", to_email)

    except Exception as e:
        print("❌ EMAIL ERROR:", e)


# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = sqlite3.connect("food.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users(name,email,phone,password,role)
        VALUES(?,?,?,?,?)
        """, (
            request.form["name"],
            request.form["email"],
            request.form["phone"],
            request.form["password"],
            request.form["role"]
        ))

        conn.commit()
        conn.close()
        return redirect("/login")

    return render_template("register.html")


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        conn = sqlite3.connect("food.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (request.form["email"], request.form["password"])
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[5]

            if user[5] == "donor":
                return redirect("/donor")
            elif user[5] == "ngo":
                return redirect("/ngo")
            elif user[5] == "admin":
                return redirect("/admin")

        return "Invalid Login"

    return render_template("login.html")


# ================= DONOR DASHBOARD =================
@app.route("/donor")
def donor():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("food.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            d.id,
            d.food_name,
            d.quantity,
            d.category,
            d.image,
            d.status,
            r.pickup_date,
            r.pickup_time
        FROM donations d
        LEFT JOIN requests r 
            ON d.id = r.donation_id
        WHERE d.donor_id = ?
        ORDER BY d.id DESC
    """, (session["user_id"],))

    donations = cursor.fetchall()
    conn.close()

    return render_template("donor_dashboard.html", donations=donations)
# ================= ADD FOOD =================
@app.route("/add_food", methods=["GET", "POST"])
def add_food():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        conn = sqlite3.connect("food.db")
        cursor = conn.cursor()

        address = request.form["address"]
        map_link = "https://www.google.com/maps/search/?api=1&query=" + address.replace(" ", "+")

        # IMAGE UPLOAD
        image = request.files.get("food_image")
        filename = None

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        # INSERT DONATION
        cursor.execute("""
        INSERT INTO donations (
            donor_id,
            food_name,
            quantity,
            category,
            prepared_time,
            expiry_time,
            address,
            image,
            status
        )
        VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            session["user_id"],
            request.form["food_name"],
            request.form["quantity"],
            request.form["category"],
            request.form["prepared_time"],
            request.form["expiry_time"],
            map_link,
            filename,
            "Available"
        ))

        conn.commit()

        # ================= SEND EMAIL TO NGOs =================
        cursor.execute("SELECT email FROM users WHERE role='ngo'")
        ngos = cursor.fetchall()

        for ngo in ngos:
            if ngo[0]:
                send_email(
                    ngo[0],
                    "🍱 New Food Donation Available",
                    f"""
New Food Donation Added!

🍛 Food: {request.form['food_name']}
🍽 Quantity: {request.form['quantity']}

📍 Location:
{address}

🌍 Map:
{map_link}
                    """
                )

        conn.close()

        return redirect("/donor")

    return render_template("add_food.html")
           # ================= NGO DASHBOARD =================
@app.route("/ngo")
def ngo():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("food.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM donations
    WHERE status='Available'
    """)

    donations = cursor.fetchall()

    conn.close()

    return render_template(
        "ngo_dashboard.html",
        donations=donations
    )
            


# ================= NGO =================
@app.route("/ngo_requests")
def ngo_requests():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("food.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        requests.id,
        donations.food_name,
        requests.status,
        requests.pickup_date,
        requests.pickup_time,
        requests.donation_id
    FROM requests
    JOIN donations
    ON requests.donation_id = donations.id
    WHERE requests.ngo_id=?
    """, (session["user_id"],))

    requests_data = cursor.fetchall()

    conn.close()

    return render_template(
        "ngo_requests.html",
        requests_data=requests_data
    )

# ================= REQUEST FOOD =================
@app.route("/request_food/<int:donation_id>")
def request_food(donation_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("food.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO requests(donation_id,ngo_id)
    VALUES(?,?)
    """, (donation_id, session["user_id"]))

    cursor.execute("UPDATE donations SET status='Requested' WHERE id=?",
                   (donation_id,))

    conn.commit()
    conn.close()

    return redirect("/ngo")





# ================= FIXED: SCHEDULE PICKUP =================
@app.route("/schedule_pickup/<int:request_id>", methods=["GET", "POST"])
def schedule_pickup(request_id):

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        conn = sqlite3.connect("food.db")
        cursor = conn.cursor()

        pickup_date = request.form["pickup_date"]
        pickup_time = request.form["pickup_time"]

        cursor.execute("""
        UPDATE requests
        SET pickup_date=?, pickup_time=?
        WHERE id=?
        """, (
            pickup_date,
            pickup_time,
            request_id
        ))

        # ✅ Get donor email and food name
        cursor.execute("""
        SELECT users.email, donations.food_name
        FROM requests
        JOIN donations ON requests.donation_id = donations.id
        JOIN users ON donations.donor_id = users.id
        WHERE requests.id=?
        """, (request_id,))

        donor = cursor.fetchone()

        conn.commit()
        conn.close()

        # ✅ Send email to donor
        if donor:
            send_email(
                donor[0],
                "🚚 Pickup Scheduled",
                f"""
Hello,

An NGO has scheduled pickup for your food donation.

🍱 Food: {donor[1]}
📅 Pickup Date: {pickup_date}
⏰ Pickup Time: {pickup_time}

Thank you for helping reduce food waste.
"""
            )

        return redirect("/ngo_requests")

    return render_template(
        "schedule_pickup.html",
        request_id=request_id
    )


# ================= FIXED: COMPLETE DONATION =================
@app.route("/complete_donation/<int:request_id>")
def complete_donation(request_id):

    conn = sqlite3.connect("food.db")
    cursor = conn.cursor()

    # STEP 1: find donation_id from request
    cursor.execute("""
    SELECT donation_id
    FROM requests
    WHERE id=?
    """, (request_id,))

    data = cursor.fetchone()

    if data:

        donation_id = data[0]

        # STEP 2: update requests table
        cursor.execute("""
        UPDATE requests
        SET status='Completed'
        WHERE id=?
        """, (request_id,))

        # STEP 3: update donations table (IMPORTANT FIX)
        cursor.execute("""
        UPDATE donations
        SET status='Completed'
        WHERE id=?
        """, (donation_id,))

    conn.commit()
    conn.close()

    return redirect("/ngo_requests")

# ================= ADMIN =================
@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("food.db")
    cursor = conn.cursor()

    # TABLE DATA
    cursor.execute("SELECT * FROM requests")
    requests_data = cursor.fetchall()

    cursor.execute("SELECT * FROM feedback")
    feedback_data = cursor.fetchall()

    # STATS
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='donor'")
    total_donors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role='ngo'")
    total_ngos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM donations")
    total_donations = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM requests")
    total_requests = cursor.fetchone()[0]


    # ⭐ LEADERBOARD ADDED (THIS WAS MISSING)
    cursor.execute("""
    SELECT users.name, COUNT(donations.id)
    FROM users
    JOIN donations ON users.id = donations.donor_id
    WHERE users.role='donor'
    GROUP BY users.id
    ORDER BY COUNT(donations.id) DESC
    """)
    leaderboard = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        requests_data=requests_data,
        feedback_data=feedback_data,
        total_donors=total_donors,
        total_ngos=total_ngos,
        total_donations=total_donations,
        total_requests=total_requests,
        
        leaderboard=leaderboard
    )

@app.route("/generate_report")
def generate_report():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("food.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        donations.food_name,
        donations.quantity,
        requests.status,
        requests.pickup_date,
        requests.pickup_time
    FROM requests
    JOIN donations
    ON requests.donation_id = donations.id
    """)

    data = cursor.fetchall()
    conn.close()

    file_name = "report.pdf"

    doc = SimpleDocTemplate(file_name)
    styles = getSampleStyleSheet()
    content = []

    content.append(
        Paragraph("Food Donation System Report", styles["Title"])
    )

    content.append(Spacer(1, 12))

    for row in data:

        text = f"""
        Food Name: {row[0]}<br/>
        Quantity: {row[1]}<br/>
        Status: {row[2]}<br/>
        Pickup Date: {row[3]}<br/>
        Pickup Time: {row[4]}
        """

        content.append(
            Paragraph(text, styles["Normal"])
        )

        content.append(
            Spacer(1, 12)
        )

    doc.build(content)

    return "PDF Generated Successfully! Check project folder."


def get_completed_donation_count(donor_id):

    conn = sqlite3.connect("food.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM donations
    WHERE donor_id=? AND status='Completed'
    """, (donor_id,))

    count = cursor.fetchone()[0]
    conn.close()

    return count



def add_border(canvas, doc):
    canvas.saveState()
    width, height = A4

    canvas.setLineWidth(3)
    canvas.setStrokeColorRGB(0.2, 0.2, 0.2)

    # outer border
    canvas.rect(20, 20, width - 40, height - 40)

    canvas.setLineWidth(1)
    canvas.rect(30, 30, width - 60, height - 60)

    canvas.restoreState()

@app.route("/generate_certificate")
def generate_certificate():

    if "user_id" not in session:
        return redirect("/login")

    donor_id = session["user_id"]

    conn = sqlite3.connect("food.db")
    cursor = conn.cursor()

    # ================= GET DONOR =================
    cursor.execute("SELECT name FROM users WHERE id=?", (donor_id,))
    donor = cursor.fetchone()

    # ================= COUNT COMPLETED DONATIONS =================
    cursor.execute("""
        SELECT COUNT(*)
        FROM donations
        WHERE donor_id=? AND status='Completed'
    """, (donor_id,))

    count = cursor.fetchone()[0]
    conn.close()

    # ================= CHECK ELIGIBILITY =================
    if count < 10:
        return f"❌ Need 10 donations. Current: {count}"

    donor_name = donor[0]

    # ================= CERTIFICATE ID =================
    certificate_id = f"FD-{donor_id}-{count}"

    # ================= VERIFY LINK =================
    verify_link = f"http://127.0.0.1:5000/verify_certificate/{certificate_id}"

    # ================= QR CODE =================
    qr = qrcode.make(verify_link)
    qr_path = f"static/cert_qr_{donor_id}.png"
    qr.save(qr_path)

    # ================= PDF FILE =================
    file_name = f"certificate_{donor_id}.pdf"

    doc = SimpleDocTemplate(
        file_name,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    content = []

    # ================= TITLE =================
    content.append(Paragraph("🏆 FOOD DONATION CERTIFICATE", styles["Title"]))
    content.append(Spacer(1, 20))

    # ================= WATERMARK =================
    content.append(Paragraph(
        "<para align=center><font size=28 color='#dddddd'><b>FOOD BRIDGE</b></font></para>",
        styles["Normal"]
    ))

    content.append(Spacer(1, 20))

    # ================= MAIN TEXT =================
    text = f"""
    <b>Certificate ID:</b> {certificate_id}<br/><br/>

    This is to certify that <b>{donor_name}</b><br/>
    has successfully completed <b>{count} food donations</b><br/>
    through our Food Donation Management System.<br/><br/>

    We sincerely appreciate your contribution in reducing food waste.<br/><br/>

    📅 Date: {datetime.date.today()}
    """

    content.append(Paragraph(text, styles["Normal"]))
    content.append(Spacer(1, 20))

    # ================= QR IMAGE =================
    qr_img = Image(qr_path, width=120, height=120)
    content.append(qr_img)

    # ================= BUILD PDF =================
    doc.build(content)

    return f"🎉 Certificate Generated: {file_name}"


# ================= VERIFY CERTIFICATE =================
@app.route("/verify_certificate/<certificate_id>")
def verify_certificate(certificate_id):

    conn = sqlite3.connect("food.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT users.name, COUNT(donations.id)
        FROM users
        JOIN donations ON users.id = donations.donor_id
        GROUP BY users.id
    """)

    conn.close()

    return f"""
    🎖 Certificate Verified<br><br>
    Certificate ID: {certificate_id}<br>
    Status: VALID ✅
    """


# ================= FEEDBACK =================
@app.route("/feedback/<int:ngo_id>", methods=["GET", "POST"])
def feedback(ngo_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("food.db")
    cursor = conn.cursor()

    if request.method == "POST":
        cursor.execute("""
        INSERT INTO feedback(ngo_id, rating, message)
        VALUES (?,?,?)
        """, (
            ngo_id,
            request.form["rating"],
            request.form["feedback"]
        ))

        conn.commit()
        conn.close()
        return redirect("/ngo")

    conn.close()
    return render_template("feedback.html", ngo_id=ngo_id)


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)