from datetime import datetime
import mysql.connector
from mysql.connector import Error as MySQLError
import models
from config import DB_CONFIG

class DatabaseError(Exception):
    pass

def setup_database():
    # Connect without specifying a database so we can CREATE it first.
    init_cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    try:
        conn = mysql.connector.connect(**init_cfg)
        cur  = conn.cursor()

        cur.execute("CREATE DATABASE IF NOT EXISTS hospital_db "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.execute("USE hospital_db")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id  INT          AUTO_INCREMENT PRIMARY KEY,
                name        VARCHAR(100) NOT NULL,
                age         TINYINT      UNSIGNED NOT NULL,
                gender      VARCHAR(20)  NOT NULL,
                disease     VARCHAR(150) NOT NULL,
                contact     CHAR(10)     NOT NULL,
                created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                doctor_id      INT          AUTO_INCREMENT PRIMARY KEY,
                name           VARCHAR(100) NOT NULL,
                age            TINYINT      UNSIGNED NOT NULL,
                specialization VARCHAR(100) NOT NULL,
                experience     TINYINT      UNSIGNED NOT NULL,
                created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id INT  AUTO_INCREMENT PRIMARY KEY,
                patient_id     INT  NOT NULL,
                doctor_id      INT  NOT NULL,
                date           DATE NOT NULL,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (doctor_id)  REFERENCES doctors(doctor_id)
                    ON DELETE CASCADE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS treatments (
                treatment_id   INT           AUTO_INCREMENT PRIMARY KEY,
                patient_id     INT           NOT NULL,
                doctor_id      INT           NOT NULL,
                visit_date     DATE          NOT NULL,
                diagnosis      VARCHAR(255)  NOT NULL,
                treatment_desc TEXT          NOT NULL,
                notes          TEXT,
                created_at     TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (doctor_id)  REFERENCES doctors(doctor_id)
                    ON DELETE CASCADE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS billing (
                bill_id        INT            AUTO_INCREMENT PRIMARY KEY,
                patient_id     INT            NOT NULL,
                treatment_id   INT,
                bill_date      DATE           NOT NULL,
                description    VARCHAR(255)   NOT NULL,
                amount         DECIMAL(10,2)  NOT NULL,
                paid           TINYINT(1)     NOT NULL DEFAULT 0,
                created_at     TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id)   REFERENCES patients(patient_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (treatment_id) REFERENCES treatments(treatment_id)
                    ON DELETE SET NULL
            )
        """)

        conn.commit()
        cur.close()
        conn.close()
        return True

    except MySQLError as e:
        print(f"\n  Database setup failed: {e}")
        return False



class DBConnection:
    def __enter__(self):
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(dictionary=True)  # rows as dicts
            return self.conn, self.cursor
        except MySQLError as e:
            raise DatabaseError(f"Cannot connect to MySQL: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and self.conn.is_connected():
            self.conn.rollback()
        if hasattr(self, "cursor") and self.cursor:
            self.cursor.close()
        if hasattr(self, "conn") and self.conn.is_connected():
            self.conn.close()
        return False   



#  DATABASE Patient
def db_add_patient(name, age, gender,
                   disease, contact):
    sql = ("INSERT INTO patients (name, age, gender, disease, contact) "
           "VALUES (%s, %s, %s, %s, %s)")
    try:
        with DBConnection() as (conn, cur):
            cur.execute(sql, (name, age, gender, disease, contact))
            conn.commit()
            return cur.lastrowid
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to add patient: {e}")


def db_get_patients(search: str = ""):
    try:
        with DBConnection() as (conn, cur):
            if search:
                sql = ("SELECT * FROM patients "
                       "WHERE name LIKE %s OR disease LIKE %s "
                       "ORDER BY patient_id")
                like = f"%{search}%"
                cur.execute(sql, (like, like))
            else:
                cur.execute("SELECT * FROM patients ORDER BY patient_id")
            rows = cur.fetchall()
        return [models.Patient(r["patient_id"], r["name"], r["age"],
                        r["gender"], r["disease"], r["contact"])
                for r in rows]
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch patients: {e}")


def db_get_patient_by_id(patient_id):
    try:
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM patients WHERE patient_id = %s",
                        (patient_id,))
            row = cur.fetchone()
        if not row:
            return None
        return models.Patient(row["patient_id"], row["name"], row["age"],
                       row["gender"], row["disease"], row["contact"])
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch patient: {e}")


def db_update_patient(patient_id, name, age,gender, disease, contact):
    sql = ("UPDATE patients "
           "SET name=%s, age=%s, gender=%s, disease=%s, contact=%s "
           "WHERE patient_id=%s")
    try:
        with DBConnection() as (conn, cur):
            cur.execute(sql, (name, age, gender, disease, contact, patient_id))
            conn.commit()
            return cur.rowcount > 0
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to update patient: {e}")


def db_delete_patient(patient_id):
    try:
        with DBConnection() as (conn, cur):
            cur.execute("DELETE FROM patients WHERE patient_id = %s",
                        (patient_id,))
            conn.commit()
            return cur.rowcount > 0
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to delete patient: {e}")
    


#  DATABASE Doctor
def db_add_doctor(name, age,
                  specialization, experience):
    sql = ("INSERT INTO doctors (name, age, specialization, experience) "
           "VALUES (%s, %s, %s, %s)")
    try:
        with DBConnection() as (conn, cur):
            cur.execute(sql, (name, age, specialization, experience))
            conn.commit()
            return cur.lastrowid
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to add doctor: {e}")

def db_get_doctors():
    try:
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM doctors ORDER BY doctor_id")
            rows = cur.fetchall()
        return [models.Doctor(r["doctor_id"], r["name"], r["age"],
                       r["specialization"], r["experience"])
                for r in rows]
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch doctors: {e}")

def db_get_doctor_by_id(doctor_id):
    try:
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM doctors WHERE doctor_id = %s",
                        (doctor_id,))
            row = cur.fetchone()
        if not row:
            return None
        return models.Doctor(row["doctor_id"], row["name"], row["age"],
                      row["specialization"], row["experience"])
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch doctor: {e}")
    
def db_delete_doctor(doctor_id):
    try:
        with DBConnection() as (conn, cur):
            cur.execute("DELETE FROM doctors WHERE doctor_id = %s",
                        (doctor_id,))
            conn.commit()
            return cur.rowcount > 0
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to delete doctor: {e}")

#  DATABASE Appointment
def db_book_appointment(patient_id,doctor_id, date):
    sql = ("INSERT INTO appointments (patient_id, doctor_id, date) "
           "VALUES (%s, %s, %s)")
    try:
        with DBConnection() as (conn, cur):
            cur.execute(sql, (patient_id, doctor_id, date))
            conn.commit()
            return cur.lastrowid
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to book appointment: {e}")


def db_get_appointments():
    sql = """
        SELECT a.appointment_id, a.patient_id, a.doctor_id, a.date,
               p.name AS patient_name, d.name AS doctor_name
        FROM   appointments a
        JOIN   patients p ON a.patient_id = p.patient_id
        JOIN   doctors  d ON a.doctor_id  = d.doctor_id
        ORDER  BY a.appointment_id
    """
    try:
        with DBConnection() as (conn, cur):
            cur.execute(sql)
            rows = cur.fetchall()
        return [models.Appointment(r["appointment_id"], r["patient_id"],
                            r["doctor_id"],      r["date"],
                            r["patient_name"],   r["doctor_name"])
                for r in rows]
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch appointments: {e}")
    

    
# ── TREATMENT functions ───────────────────────────────────────────────────────

def db_add_treatment(patient_id, doctor_id, visit_date,
                     diagnosis, treatment_desc, notes=""):
    """Record a treatment visit for a patient."""
    sql = """
        INSERT INTO treatments
            (patient_id, doctor_id, visit_date, diagnosis, treatment_desc, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        with DBConnection() as (conn, cur):
            cur.execute(sql, (patient_id, doctor_id, visit_date,
                              diagnosis, treatment_desc, notes))
            conn.commit()
            return cur.lastrowid
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to add treatment: {e}")


def db_get_treatments_by_patient(patient_id):
    """Return all treatment records for a patient, newest first."""
    sql = """
        SELECT t.treatment_id, t.visit_date, t.diagnosis,
               t.treatment_desc, t.notes,
               d.name AS doctor_name, d.specialization
        FROM   treatments t
        JOIN   doctors d ON t.doctor_id = d.doctor_id
        WHERE  t.patient_id = %s
        ORDER  BY t.visit_date DESC, t.treatment_id DESC
    """
    try:
        with DBConnection() as (conn, cur):
            cur.execute(sql, (patient_id,))
            return cur.fetchall()
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch treatments: {e}")


def db_delete_treatment(treatment_id):
    """Delete a treatment record (billing rows referencing it are SET NULL)."""
    try:
        with DBConnection() as (conn, cur):
            cur.execute("DELETE FROM treatments WHERE treatment_id = %s",
                        (treatment_id,))
            conn.commit()
            return cur.rowcount > 0
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to delete treatment: {e}")


# ── BILLING functions ─────────────────────────────────────────────────────────

def db_add_bill(patient_id, bill_date, description,
                amount, paid=False, treatment_id=None):
    """Add a billing entry for a patient."""
    sql = """
        INSERT INTO billing
            (patient_id, treatment_id, bill_date, description, amount, paid)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        with DBConnection() as (conn, cur):
            cur.execute(sql, (patient_id, treatment_id, bill_date,
                              description, float(amount), int(paid)))
            conn.commit()
            return cur.lastrowid
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to add bill: {e}")


def db_get_bills_by_patient(patient_id):
    """Return all billing rows for a patient, newest first."""
    sql = """
        SELECT b.bill_id, b.bill_date, b.description,
               b.amount, b.paid, b.treatment_id
        FROM   billing b
        WHERE  b.patient_id = %s
        ORDER  BY b.bill_date DESC, b.bill_id DESC
    """
    try:
        with DBConnection() as (conn, cur):
            cur.execute(sql, (patient_id,))
            return cur.fetchall()
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch bills: {e}")


def db_mark_bill_paid(bill_id):
    """Mark a single bill as paid."""
    try:
        with DBConnection() as (conn, cur):
            cur.execute("UPDATE billing SET paid = 1 WHERE bill_id = %s",
                        (bill_id,))
            conn.commit()
            return cur.rowcount > 0
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to update bill: {e}")


def db_delete_bill(bill_id):
    """Delete a billing entry."""
    try:
        with DBConnection() as (conn, cur):
            cur.execute("DELETE FROM billing WHERE bill_id = %s", (bill_id,))
            conn.commit()
            return cur.rowcount > 0
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to delete bill: {e}")


# ── PATIENT FULL REPORT ───────────────────────────────────────────────────────

def db_get_patient_report(patient_id):
    """
    Assemble a complete patient report as a plain dict.

    Returns:
        {
          "patient":      dict  – patient details,
          "visits":       list  – appointment dates with doctor names,
          "treatments":   list  – diagnosis + treatment rows,
          "billing":      list  – billing rows,
          "billing_summary": {
              "total_amount": float,
              "total_paid":   float,
              "total_due":    float,
          }
        }
    Raises DatabaseError if patient not found or DB error.
    """
    patient = db_get_patient_by_id(patient_id)
    if not patient:
        raise DatabaseError(f"No patient found with ID {patient_id}.")

    # ── visit dates from appointments ──
    visit_sql = """
        SELECT a.date AS visit_date,
               d.name AS doctor_name, d.specialization
        FROM   appointments a
        JOIN   doctors d ON a.doctor_id = d.doctor_id
        WHERE  a.patient_id = %s
        ORDER  BY a.date DESC
    """

    # ── billing summary ──
    bill_summary_sql = """
        SELECT
            COALESCE(SUM(amount), 0)              AS total_amount,
            COALESCE(SUM(CASE WHEN paid = 1
                         THEN amount ELSE 0 END), 0) AS total_paid
        FROM billing
        WHERE patient_id = %s
    """

    try:
        with DBConnection() as (conn, cur):
            # visits
            cur.execute(visit_sql, (patient_id,))
            visits = cur.fetchall()

            # billing summary
            cur.execute(bill_summary_sql, (patient_id,))
            brow = cur.fetchone()

        treatments = db_get_treatments_by_patient(patient_id)
        bills      = db_get_bills_by_patient(patient_id)

        total_amount = float(brow["total_amount"])
        total_paid   = float(brow["total_paid"])

        return {
            "patient": patient.to_dict(),
            "visits":  [
                {
                    "visit_date":     str(v["visit_date"]),
                    "doctor_name":    v["doctor_name"],
                    "specialization": v["specialization"],
                }
                for v in visits
            ],
            "treatments": [
                {
                    "treatment_id":   t["treatment_id"],
                    "visit_date":     str(t["visit_date"]),
                    "diagnosis":      t["diagnosis"],
                    "treatment_desc": t["treatment_desc"],
                    "notes":          t["notes"] or "",
                    "doctor_name":    t["doctor_name"],
                    "specialization": t["specialization"],
                }
                for t in treatments
            ],
            "billing": [
                {
                    "bill_id":      b["bill_id"],
                    "bill_date":    str(b["bill_date"]),
                    "description":  b["description"],
                    "amount":       float(b["amount"]),
                    "paid":         bool(b["paid"]),
                    "treatment_id": b["treatment_id"],
                }
                for b in bills
            ],
            "billing_summary": {
                "total_amount": total_amount,
                "total_paid":   total_paid,
                "total_due":    round(total_amount - total_paid, 2),
            },
        }

    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to generate patient report: {e}")


def db_get_patient_report_csv(patient_id):
    """
    Build a multi-section CSV string for the full patient report.
    Returns the CSV as a string (utf-8).  Caller streams it as a download.
    """
    import csv, io

    report = db_get_patient_report(patient_id)   # reuse the dict builder
    output = io.StringIO()
    w = csv.writer(output)

    # ── Section 1: Patient Details ────────────────────────────────────────
    w.writerow(["=== PATIENT DETAILS ==="])
    w.writerow(["Patient ID", "Name", "Age", "Gender", "Disease", "Contact"])
    p = report["patient"]
    w.writerow([p["patient_id"], p["name"], p["age"],
                p["gender"], p["disease"], p["contact"]])
    w.writerow([])

    # ── Section 2: Visit Dates ────────────────────────────────────────────
    w.writerow(["=== VISIT DATES ==="])
    w.writerow(["Visit Date", "Doctor Name", "Specialization"])
    if report["visits"]:
        for v in report["visits"]:
            w.writerow([v["visit_date"], v["doctor_name"], v["specialization"]])
    else:
        w.writerow(["No visits recorded."])
    w.writerow([])

    # ── Section 3: Treatment History ──────────────────────────────────────
    w.writerow(["=== TREATMENT HISTORY ==="])
    w.writerow(["Treatment ID", "Visit Date", "Diagnosis",
                "Treatment", "Notes", "Doctor", "Specialization"])
    if report["treatments"]:
        for t in report["treatments"]:
            w.writerow([t["treatment_id"], t["visit_date"], t["diagnosis"],
                        t["treatment_desc"], t["notes"],
                        t["doctor_name"], t["specialization"]])
    else:
        w.writerow(["No treatment records found."])
    w.writerow([])

    # ── Section 4: Billing ────────────────────────────────────────────────
    w.writerow(["=== BILLING ==="])
    w.writerow(["Bill ID", "Date", "Description", "Amount (INR)",
                "Paid", "Linked Treatment ID"])
    if report["billing"]:
        for b in report["billing"]:
            w.writerow([b["bill_id"], b["bill_date"], b["description"],
                        f"{b['amount']:.2f}",
                        "Yes" if b["paid"] else "No",
                        b["treatment_id"] or "—"])
    else:
        w.writerow(["No billing records found."])
    w.writerow([])

    # ── Section 5: Billing Summary ────────────────────────────────────────
    w.writerow(["=== BILLING SUMMARY ==="])
    w.writerow(["Total Billed (INR)", "Total Paid (INR)", "Amount Due (INR)"])
    s = report["billing_summary"]
    w.writerow([f"{s['total_amount']:.2f}",
                f"{s['total_paid']:.2f}",
                f"{s['total_due']:.2f}"])

    return output.getvalue()