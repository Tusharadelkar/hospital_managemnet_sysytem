import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import database
import Hospital_management_system as hms
import matplotlib
import auth
matplotlib.use("Agg")  
app = Flask(__name__)
app.secret_key = "hospital_secret_key"

os.makedirs("static/charts", exist_ok=True)

# ── Login Required Decorator ──────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login_view"))
        return f(*args, **kwargs)
    return decorated

# ── Home ──────────────────────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    stats = hms.generate_statistics()
    total_doctors = len(database.db_get_doctors())
    total_appointments = len(database.db_get_appointments())
    return render_template("index.html", stats=stats,
                           total_doctors=total_doctors,
                           total_appointments=total_appointments)


# ── Patients ──────────────────────────────────────────────────────────────────
@app.route("/patients")
@login_required
def patients():
    search = request.args.get("search", "")
    patients_list = database.db_get_patients(search)
    return render_template("patients.html",
                           patients=patients_list, search=search)


@app.route("/patients/add", methods=["GET", "POST"])
@login_required
def add_patient():
    if request.method == "POST":
        try:
            name    = hms.validate_name(request.form["name"])
            age     = hms.validate_age(request.form["age"])
            gender  = request.form["gender"]
            disease = request.form["disease"].strip()
            contact = hms.validate_contact(request.form["contact"])
            database.db_add_patient(name, age, gender, disease, contact)
            flash(f"Patient '{name}' added successfully!", "success")
            return redirect(url_for("patients"))
        except (hms.InvalidNameError, hms.InvalidAgeError,
                hms.InvalidContactError) as e:
            flash(str(e), "error")
        except database.DatabaseError as e:
            flash(str(e), "error")
    return render_template("add_patient.html")


@app.route("/patients/edit/<int:pid>", methods=["GET", "POST"])
@login_required
def edit_patient(pid):
    patient = database.db_get_patient_by_id(pid)
    if not patient:
        flash("Patient not found.", "error")
        return redirect(url_for("patients"))

    if request.method == "POST":
        try:
            name    = hms.validate_name(request.form["name"])
            age     = hms.validate_age(request.form["age"])
            gender  = request.form["gender"]
            disease = request.form["disease"].strip()
            contact = hms.validate_contact(request.form["contact"])
            database.db_update_patient(pid, name, age, gender, disease, contact)
            flash("Patient updated successfully!", "success")
            return redirect(url_for("patients"))
        except (hms.InvalidNameError, hms.InvalidAgeError,
                hms.InvalidContactError) as e:
            flash(str(e), "error")
        except database.DatabaseError as e:
            flash(str(e), "error")
    return render_template("edit_patient.html", patient=patient)


@app.route("/patients/delete/<int:pid>", methods=["POST"])
@login_required
def delete_patient(pid):
    try:
        database.db_delete_patient(pid)
        flash("Patient deleted.", "success")
    except database.DatabaseError as e:
        flash(str(e), "error")
    return redirect(url_for("patients"))


# ── Doctors ───────────────────────────────────────────────────────────────────
@app.route("/doctors")
@login_required
def doctors():
    doctors_list = database.db_get_doctors()
    return render_template("doctors.html", doctors=doctors_list)


@app.route("/doctors/add", methods=["GET", "POST"])
@login_required
def add_doctor():
    if request.method == "POST":
        try:
            name           = hms.validate_name(request.form["name"])
            age            = hms.validate_age(request.form["age"])
            specialization = request.form["specialization"].strip()
            experience     = hms.validate_age(request.form["experience"])
            database.db_add_doctor(name, age, specialization, experience)
            flash(f"Dr. {name} added successfully!", "success")
            return redirect(url_for("doctors"))
        except (hms.InvalidNameError, hms.InvalidAgeError) as e:
            flash(str(e), "error")
        except database.DatabaseError as e:
            flash(str(e), "error")
    return render_template("add_doctor.html")


@app.route("/doctors/delete/<int:did>", methods=["POST"])
@login_required
def delete_doctor(did):
    try:
        database.db_delete_doctor(did)
        flash("Doctor deleted.", "success")
    except database.DatabaseError as e:
        flash(str(e), "error")
    return redirect(url_for("doctors"))


# ── Appointments ──────────────────────────────────────────────────────────────
@app.route("/appointments")
@login_required
def appointments():
    appts = database.db_get_appointments()
    return render_template("appointments.html", appointments=appts)


@app.route("/appointments/add", methods=["GET", "POST"])
@login_required
def add_appointment():
    patients_list = database.db_get_patients()
    doctors_list  = database.db_get_doctors()

    if request.method == "POST":
        try:
            pid  = int(request.form["patient_id"])
            did  = int(request.form["doctor_id"])
            date = request.form["date"]
            database.db_book_appointment(pid, did, date)
            flash("Appointment booked successfully!", "success")
            return redirect(url_for("appointments"))
        except database.DatabaseError as e:
            flash(str(e), "error")
        except ValueError:
            flash("Invalid patient or doctor ID.", "error")
    return render_template("add_appointment.html",
                           patients=patients_list, doctors=doctors_list)


# ── Charts / Reports ──────────────────────────────────────────────────────────
@app.route("/charts")
@login_required
def charts():
    hms.generate_charts()
    stats = hms.generate_statistics()
    return render_template("charts.html", stats=stats)


# ── Change Password ───────────────────────────────────────────────────────────
@app.route("/admin/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old     = request.form.get("old_password", "")
        new     = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        if new != confirm:
            flash("New passwords do not match.", "error")
            return render_template("change_password.html")
        try:
            auth.validate_password(new)
            auth.db_change_password(session["admin_id"], old, new)
            flash("Password changed successfully!", "success")
            return redirect(url_for("index"))
        except (ValueError, auth.AuthError) as e:
            flash(str(e), "error")
        except database.DatabaseError as e:
            flash(str(e), "error")
    return render_template("change_password.html")


# ── Login / Logout ────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login_view():
    # Already logged in → go to dashboard
    if "admin_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            admin = auth.login(username, password)
            session["admin_id"] = admin["admin_id"]
            session["username"] = admin["username"]
            flash(f"Welcome, {admin['username']}!", "success")
            return redirect(url_for("index"))
        except auth.AuthError as e:
            flash(str(e), "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login_view"))


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    database.setup_database()
    auth.setup_admin_table()
    auth.bootstrap_default_admin()
    app.run(debug=True)
