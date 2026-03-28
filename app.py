import os
from flask import Flask, render_template, request, redirect, url_for, flash
import database
import Hospital_management_system as hms
import matplotlib
matplotlib.use("Agg")  
app = Flask(__name__)
app.secret_key = "hospital_secret_key"

os.makedirs("static/charts", exist_ok=True)

# ── Home ──────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    stats = hms.generate_statistics()
    total_doctors = len(database.db_get_doctors())
    total_appointments = len(database.db_get_appointments())
    return render_template("index.html", stats=stats,
                           total_doctors=total_doctors,
                           total_appointments=total_appointments)


# ── Patients ──────────────────────────────────────────────────────────────────
@app.route("/patients")
def patients():
    search = request.args.get("search", "")
    patients_list = database.db_get_patients(search)
    return render_template("patients.html",
                           patients=patients_list, search=search)


@app.route("/patients/add", methods=["GET", "POST"])
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
def delete_patient(pid):
    try:
        database.db_delete_patient(pid)
        flash("Patient deleted.", "success")
    except database.DatabaseError as e:
        flash(str(e), "error")
    return redirect(url_for("patients"))


# ── Doctors ───────────────────────────────────────────────────────────────────
@app.route("/doctors")
def doctors():
    doctors_list = database.db_get_doctors()
    return render_template("doctors.html", doctors=doctors_list)


@app.route("/doctors/add", methods=["GET", "POST"])
def add_doctor():
    if request.method == "POST":
        try:
            name           = hms.validate_name(request.form["name"])
            age            = hms.validate_age(request.form["age"])
            specialization = request.form["specialization"].strip()
            experience     = hms.validate_age(request.form["experience"])  # reuse int validation
            database.db_add_doctor(name, age, specialization, experience)
            flash(f"Dr. {name} added successfully!", "success")
            return redirect(url_for("doctors"))
        except (hms.InvalidNameError, hms.InvalidAgeError) as e:
            flash(str(e), "error")
        except database.DatabaseError as e:
            flash(str(e), "error")
    return render_template("add_doctor.html")


@app.route("/doctors/delete/<int:did>", methods=["POST"])
def delete_doctor(did):
    try:
        database.db_delete_doctor(did)
        flash("Doctor deleted.", "success")
    except database.DatabaseError as e:
        flash(str(e), "error")
    return redirect(url_for("doctors"))


# ── Appointments ──────────────────────────────────────────────────────────────
@app.route("/appointments")
def appointments():
    appts = database.db_get_appointments()
    return render_template("appointments.html", appointments=appts)


@app.route("/appointments/add", methods=["GET", "POST"])
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
def charts():
    hms.generate_charts()
    stats = hms.generate_statistics()
    return render_template("charts.html", stats=stats)


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    database.setup_database()
    app.run(debug=True)
