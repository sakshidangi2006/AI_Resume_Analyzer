from flask import Flask, request, render_template, redirect, session
from db import Base, engine, SessionLocal
import models
import PyPDF2
import docx
import json
from ai import analyze_resume

app = Flask(__name__)
app.secret_key = "secret123"

Base.metadata.create_all(bind=engine)

@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

# ---- SIGNUP ----
@app.route("/signup", methods=["GET", "POST"])
def signup():
    db = SessionLocal()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = db.query(models.User).filter_by(email=email).first()
        if existing_user:
            return render_template("signup.html", error="User already exists.")

        user = models.User(email=email, password=password)
        db.add(user)
        db.commit()
        return redirect("/login")
    return render_template("signup.html")

# ---- LOGIN ----
@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = db.query(models.User).filter_by(email=email, password=password).first()
        if user:
            session["user"] = user.email
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid credentials.")

    return render_template("login.html")

# ---- FORGOT PASSWORD ----
@app.route("/forgot-password")
def forgot_password():
    return render_template("forgot_password.html")

# ---- DASHBOARD ----
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    result = None
    if request.method == "POST":
        user_goal = request.form.get("role")
        resume_text = request.form.get("resume")
        file = request.files.get("file")

        if file and file.filename != "":
            if file.filename.lower().endswith(".pdf"):
                try:
                    pdf_reader = PyPDF2.PdfReader(file.stream)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                    resume_text = text
                except Exception as err:
                    result = {"error": f"PDF error: {str(err)}"}

            elif file.filename.lower().endswith(".docx"):
                try:
                    doc = docx.Document(file.stream)
                    text = "\n".join([para.text for para in doc.paragraphs])
                    resume_text = text
                except Exception as err:
                    result = {"error": f"Docx error: {str(err)}"}

        job_description = request.form.get("job_description", "")

        if resume_text and user_goal and result is None:
            try:
                result = analyze_resume(resume_text, user_goal, job_description)
                db = SessionLocal()
                user = db.query(models.User).filter_by(email=session["user"]).first()
                report = models.Reports(
                    user_id=user.id,
                    resume_text=resume_text,
                    result=json.dumps(result)
                )
                db.add(report)
                db.commit()
            except Exception as err:
                result = {"error": f"AI error: {str(err)}"}

    return render_template("dashboard.html", user=session.get("user"), result=result)

# ---- HISTORY ----
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    db = SessionLocal()
    user = db.query(models.User).filter_by(email=session["user"]).first()
    reports = db.query(models.Reports).filter_by(user_id=user.id).all()

    parsed_reports = []
    for report in reports:
        try:
            parsed_reports.append({
                "id": report.id,
                "resume_text": report.resume_text,        # FIX: was report.resume
                "result": json.loads(report.result)        # FIX: was report.results (typo)
            })
        except Exception as err:
            parsed_reports.append({
                "id": report.id,
                "resume_text": report.resume_text,
                "result": {"error": f"Parsing error: {str(err)}"}
            })

    return render_template("history.html", reports=parsed_reports)

# ---- DELETE REPORT ----
@app.route("/history/delete/<int:report_id>", methods=["POST"])
def delete_report(report_id):
    if "user" not in session:
        return redirect("/login")

    db = SessionLocal()
    user = db.query(models.User).filter_by(email=session["user"]).first()

    # Only delete if the report belongs to the logged-in user (security check)
    report = db.query(models.Reports).filter_by(id=report_id, user_id=user.id).first()
    if report:
        db.delete(report)
        db.commit()

    return redirect("/history")

# ---- LOGOUT ----
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)