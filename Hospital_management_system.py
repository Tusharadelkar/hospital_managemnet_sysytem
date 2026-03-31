import re
import csv
import os
from datetime import datetime
import mysql.connector
from mysql.connector import Error as MySQLError
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import auth
import database
from functools import wraps
from abc import ABC, abstractmethod

#  Custom eception
class InvalidNameError(Exception):
    pass

class InvalidAgeError(Exception):
    pass

class InvalidContactError(Exception):
    pass

class DatabaseError(Exception):
    pass


#  validations 
def validate_name(name):  
    if not re.fullmatch(r"[A-Za-z ]+", name.strip()):
        raise InvalidNameError(f"'{name}' is invalid. Use letters and spaces only.")
    return name.strip().title()

def validate_age(age_str):
    if not age_str.strip().isdigit():
        raise InvalidAgeError("Age must be a positive whole number.")
    age = int(age_str.strip())
    if not (0 <= age <= 120):
        raise InvalidAgeError(f"Age {age} is out of range (0–120).")
    return age

def validate_contact(contact):
    if not re.fullmatch(r"\d{10}", contact.strip()):
        raise InvalidContactError("Contact must be exactly 10 digits.")
    return contact.strip()

#  BASE CLASS: Person
class Person(ABC):
    def __init__(self, name: str, age: int):
        self.__name = name
        self.__age  = age

    def get_name(self):  
        return self.__name
    def get_age(self):  
        return self.__age
    
    def set_name(self, n): 
        self.__name = n
    def set_age(self,  a): 
        self.__age  = a
    
    @abstractmethod
    def display(self):
        print(f"  Name : {self.__name}")
        print(f"  Age  : {self.__age}")

#  DERIVED CLASS: Patient
class Patient(Person):
    def __init__(self, patient_id: int, name: str, age: int,
                 gender: str, disease: str, contact: str):
        super().__init__(name, age)
        self.__patient_id = patient_id
        self.__gender     = gender
        self.__disease    = disease
        self.__contact    = contact

    def get_patient_id(self):
        return self.__patient_id
    def get_gender(self): 
        return self.__gender
    def get_disease(self):
        return self.__disease
    def get_contact(self): 
        return self.__contact

    def set_gender(self, g):  
        self.__gender  = g
    def set_disease(self, d): 
        self.__disease = d
    def set_contact(self, c): 
        self.__contact = c

    def display(self):
        print(f"  Patient ID : {self.__patient_id}")
        super().display()
        print(f"  Gender     : {self.__gender}")
        print(f"  Disease    : {self.__disease}")
        print(f"  Contact    : {self.__contact}")

    def to_dict(self):
        """Handy for Flask JSON responses later."""
        return {
            "patient_id": self.__patient_id,
            "name":       self.get_name(),
            "age":        self.get_age(),
            "gender":     self.__gender,
            "disease":    self.__disease,
            "contact":    self.__contact,
        }

#  DERIVED CLASS: Doctor
class Doctor(Person):
    def __init__(self, doctor_id: int, name: str, age: int,
                 specialization: str, experience: int):
        super().__init__(name, age)
        self.__doctor_id      = doctor_id
        self.__specialization = specialization
        self.__experience     = experience

    def get_doctor_id(self):
        return self.__doctor_id
    def get_specialization(self):
        return self.__specialization
    def get_experience(self):
        return self.__experience

    def display(self):
        print(f"  Doctor ID      : {self.__doctor_id}")
        super().display()
        print(f"  Specialization : {self.__specialization}")
        print(f"  Experience     : {self.__experience} year(s)")

    def to_dict(self):
        return {
            "doctor_id":      self.__doctor_id,
            "name":           self.get_name(),
            "age":            self.get_age(),
            "specialization": self.__specialization,
            "experience":     self.__experience,
        }

#  APPOINTMENT CLASS
class Appointment:

    def __init__(self, appointment_id, patient_id,doctor_id, date,patient_name: str = "", doctor_name: str = ""):
        self.__appt_id      = appointment_id
        self.__patient_id   = patient_id
        self.__doctor_id    = doctor_id
        self.__date         = date
        self.__patient_name = patient_name
        self.__doctor_name  = doctor_name

    def get_appt_id(self):
        return self.__appt_id
    
    def get_patient_id(self): 
        return self.__patient_id
    
    def get_doctor_id(self): 
        return self.__doctor_id
    
    def get_date(self): 
        return str(self.__date)

    def display(self):
        print(f"  Appointment ID : {self.__appt_id}")
        print(f"  Patient        : {self.__patient_name} (ID {self.__patient_id})")
        print(f"  Doctor         : Dr. {self.__doctor_name} (ID {self.__doctor_id})")
        print(f"  Date           : {self.__date}")

    def to_dict(self):
        return {
            "appointment_id": self.__appt_id,
            "patient_id":     self.__patient_id,
            "patient_name":   self.__patient_name,
            "doctor_id":      self.__doctor_id,
            "doctor_name":    self.__doctor_name,
            "date":           str(self.__date),
        }

#  HELPER UTILITIES
def divider(title: str = ""):
    width = 54
    if title:
        pad = (width - len(title) - 2) // 2
        print("\n" + "─" * pad + f" {title} " + "─" * pad)
    else:
        print("─" * width)

def prompt(text):
    return input(f"  {text}: ").strip()

#  PATIENT UI
def ui_add_patient():
    divider("Add Patient")
    try:
        name    = validate_name(prompt("Name"))
        age     = validate_age(prompt("Age"))
        gender  = prompt("Gender (Male/Female/Other)").capitalize()
        disease = prompt("Disease / Condition")
        contact = validate_contact(prompt("Contact (10 digits)"))
        new_id  = database.db_add_patient(name, age, gender, disease, contact)
        print(f"\n  Patient '{name}' added! (ID: {new_id})")
    except (InvalidNameError, InvalidAgeError, InvalidContactError) as e:
        print(f"\n  Validation Error: {e}")
    except DatabaseError as e:
        print(f"\n DB Error: {e}")


def ui_view_patients():
    divider("All Patients")
    try:
        patients = database.db_get_patients()
        if not patients:
            print("  No patients found.")
            return
        for p in patients:
            p.display()
            divider()
    except DatabaseError as e:
        print(f"\n DB Error: {e}")


def ui_update_patient():
    divider("Update Patient")
    ui_view_patients()
    try:
        pid = int(prompt("Enter Patient ID to update"))
    except ValueError:
        print(" Invalid ID.")
        return

    try:
        patient = database.db_get_patient_by_id(pid)
    except DatabaseError as e:
        print(f"\n DB Error: {e}")
        return

    if not patient:
        print(f" No patient found with ID {pid}.")
        return

    print("  Leave a field blank to keep the current value.\n")
    try:
        n = prompt(f"Name    [{patient.get_name()}]")
        a = prompt(f"Age     [{patient.get_age()}]")
        g = prompt(f"Gender  [{patient.get_gender()}]")
        di = prompt(f"Disease [{patient.get_disease()}]")
        c = prompt(f"Contact [{patient.get_contact()}]")

        name    = validate_name(n)    if n  else patient.get_name()
        age     = validate_age(a)     if a  else patient.get_age()
        gender  = g.capitalize()      if g  else patient.get_gender()
        disease = di                  if di else patient.get_disease()
        contact = validate_contact(c) if c  else patient.get_contact()

        ok = database.db_update_patient(pid, name, age, gender, disease, contact)
        print(f"\n Patient ID {pid} updated!" if ok
              else f"\n  No changes saved.")
    except (InvalidNameError, InvalidAgeError, InvalidContactError) as e:
        print(f"\n Validation Error: {e}")
    except DatabaseError as e:
        print(f"\n DB Error: {e}")

def ui_delete_patient():
    divider("Delete Patient")
    ui_view_patients()
    try:
        pid = int(prompt("Enter Patient ID to delete"))
    except ValueError:
        print(" Invalid ID.")
        return
    try:
        patient = database.db_get_patient_by_id(pid)
        if not patient:
            print(f" No patient found with ID {pid}.")
            return
        confirm = prompt(
            f"Delete '{patient.get_name()}' and their appointments? (yes/no)"
        ).lower()
        if confirm == "yes":
            database.db_delete_patient(pid)
            print(f"\n Patient '{patient.get_name()}' deleted.")
        else:
            print("  Deletion cancelled.")
    except DatabaseError as e:
        print(f"\n DB Error: {e}")

def ui_search_patient():
    divider("Search Patient")
    keyword = prompt("Name or disease keyword")
    try:
        results = database.db_get_patients(search=keyword)
        if not results:
            print("  No matching patients found.")
            return
        for p in results:
            p.display()
            divider()
    except DatabaseError as e:
        print(f"\n DB Error: {e}")

#  DOCTOR UI
def ui_add_doctor():
    divider("Add Doctor")
    try:
        name = validate_name(prompt("Name"))
        age  = validate_age(prompt("Age"))
        spec = prompt("Specialization")
        exp_s = prompt("Years of Experience")
        if not exp_s.isdigit():
            raise ValueError("Experience must be a non-negative whole number.")
        new_id = database.db_add_doctor(name, int(age), spec, int(exp_s))
        print(f"\n Dr. '{name}' added! (ID: {new_id})")
    except (InvalidNameError, InvalidAgeError) as e:
        print(f"\n Validation Error: {e}")
    except ValueError as e:
        print(f"\n {e}")
    except DatabaseError as e:
        print(f"\n DB Error: {e}")

def ui_view_doctors():
    divider("All Doctors")
    try:
        doctors = database.db_get_doctors()
        if not doctors:
            print("  No doctors found.")
            return
        for d in doctors:
            d.display()
            divider()
    except DatabaseError as e:
        print(f"\n DB Error: {e}")


def ui_delete_doctor():
    divider("Delete doctors")
    ui_view_doctors()
    try:
        did = int(prompt("Enter doctors ID to delete"))
    except ValueError:
        print(" Invalid ID.")
        return

    try:
        doctor = database.db_get_doctor_by_id(did)
        if not doctor:
            print(f" No doctors found with ID {did}.")
            return
        confirm = prompt(
            f"Delete '{doctor.get_name()}' and their appointments? (yes/no)"
        ).lower()
        if confirm == "yes":
            database.db_delete_doctor(did)
            print(f"\n Doctor '{did.get_name()}' deleted.")
        else:
            print("  Deletion cancelled.")
    except DatabaseError as e:
        print(f"\n DB Error: {e}")

#  APPOINTMENT UI
def ui_book_appointment():
    divider("Book Appointment")
    try:
        patients = database.db_get_patients()
        doctors  = database.db_get_doctors()
    except DatabaseError as e:
        print(f"\n DB Error: {e}")
        return

    if not patients:
        print(" No patients found. Add a patient first.")
        return
    if not doctors:
        print(" No doctors found. Add a doctor first.")
        return

    print("\n  ── Patients ──")
    for p in patients:
        print(f"  [{p.get_patient_id()}] {p.get_name()}")
    print("\n  ── Doctors ──")
    for d in doctors:
        print(f"  [{d.get_doctor_id()}] Dr. {d.get_name()} – {d.get_specialization()}")

    try:
        pid      = int(prompt("\n  Patient ID"))
        did      = int(prompt("  Doctor  ID"))
        date_str = prompt("  Appointment Date (YYYY-MM-DD)")
        datetime.strptime(date_str, "%Y-%m-%d")   # validate format
    except ValueError as e:
        print(f"\n Invalid input: {e}")
        return

    try:
        # Verify IDs still exist
        if not database.db_get_patient_by_id(pid):
            print(f" Patient ID {pid} not found.")
            return
        if not database.db_get_doctor_by_id(did):
            print(f"  Doctor ID {did} not found.")
            return
        appt_id = database.db_book_appointment(pid, did, date_str)
        print(f"\n Appointment booked! (ID: {appt_id})")
    except DatabaseError as e:
        print(f"\n DB Error: {e}")


def ui_view_appointments():
    divider("All Appointments")
    try:
        appts = database.db_get_appointments()
        if not appts:
            print("  No appointments scheduled.")
            return
        for a in appts:
            a.display()
            divider()
    except DatabaseError as e:
        print(f"\n  DB Error: {e}")


def show_statistics():
    divider("Patient Statistics")
    stats = generate_statistics()

    print(f"  Total Patients       : {stats['total']}")
    print(f"  Average Age          : {stats['avg_age']}")
    print(f"  Maximum Age          : {stats['max_age']}")
    print(f"  Minimum Age          : {stats['min_age']}")
    print(f"  Most Common Disease  : {stats['common_disease']}")

    divider()


def get_dataframe():
    try:
        conn = mysql.connector.connect(**database.DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM patients")
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        if not data:
            return pd.DataFrame()

        return pd.DataFrame(data)

    except Exception as e:
        print("Error loading data:", e)
        return pd.DataFrame()
    

def generate_charts():
    disease = disease_distribution()

    if len(disease) > 0:
        disease.plot(kind='bar')
        plt.title("Disease Distribution")
        plt.xlabel("Disease")
        plt.ylabel("Number of Patients")
        plt.tight_layout()
        plt.savefig("static/charts/disease.png")
        plt.clf()

    gender = gender_distribution()

    if len(gender) > 0:
        gender.plot(kind='pie', autopct='%1.1f%%')
        plt.title("Gender Distribution")
        plt.ylabel('')
        plt.savefig("static/charts/gender.png")
        plt.clf()

def generate_statistics():
    df = get_dataframe()

    if df.empty:
        return {
            "total": 0,
            "avg_age": 0,
            "max_age": 0,
            "min_age": 0,
            "common_disease": "N/A"
        }

    ages = np.array(df["age"])

    stats = {
        "total": len(df),
        "avg_age": round(np.mean(ages), 2),
        "max_age": int(np.max(ages)),
        "min_age": int(np.min(ages)),
        "common_disease": df["disease"].mode()[0]
    }

    return stats


def disease_distribution():
    df = get_dataframe()

    if df.empty:
        return {}

    return df["disease"].value_counts()


def gender_distribution():
    df = get_dataframe()

    if df.empty:
        return {}

    return df["gender"].value_counts()


#  MENU SYSTEM
def patient_menu():
    while True:
        divider("Patient Menu")
        print(" 1. Add Patient")
        print(" 2. View All Patients")
        print(" 3. Update Patient")
        print(" 4. Delete Patient")
        print(" 5. Search Patient")
        print(" 0. Back")
        divider()
        choice = prompt("Your choice")
        if   choice == "1": ui_add_patient()
        elif choice == "2": ui_view_patients()
        elif choice == "3": ui_update_patient()
        elif choice == "4": ui_delete_patient()
        elif choice == "5": ui_search_patient()
        elif choice == "0": break
        else: print("Invalid option.")


def doctor_menu():
    while True:
        divider("Doctor Menu")
        print(" 1. Add Doctor")
        print(" 2. View All Doctors")
        print(" 3. Delete Doctors")
        print(" 0. Back")
        divider()
        choice = prompt("Your choice")
        if   choice == "1": ui_add_doctor()
        elif choice == "2": ui_view_doctors()
        elif choice == "3": ui_delete_doctor()
        elif choice == "0": break
        else: print(" Invalid option.")


def appointment_menu():
    while True:
        divider("Appointment Menu")
        print("  1. Book Appointment")
        print("  2. View All Appointments")
        print("  0. Back")
        divider()
        choice = prompt("Your choice")
        if   choice == "1": ui_book_appointment()
        elif choice == "2": ui_view_appointments()
        elif choice == "0": break
        else: print("  ✖  Invalid option.")


def db_add_treatment(patient_id, doctor_id, visit_date,
                     diagnosis, treatment_desc, notes=""):
    """Insert a treatment record. Returns new treatment_id."""
    sql = """
        INSERT INTO treatments
            (patient_id, doctor_id, visit_date, diagnosis, treatment_desc, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        with database.DBConnection() as (conn, cur):
            cur.execute(sql, (patient_id, doctor_id, visit_date,
                              diagnosis, treatment_desc, notes))
            conn.commit()
            return cur.lastrowid
    except database.DatabaseError:
        raise
    except MySQLError as e:
        raise database.DatabaseError(f"Failed to add treatment: {e}")


def db_get_treatments_by_patient(patient_id):
    """Return all treatment rows for a patient (newest first)."""
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
        with database.DBConnection() as (conn, cur):
            cur.execute(sql, (patient_id,))
            return cur.fetchall()
    except database.DatabaseError:
        raise
    except MySQLError as e:
        raise database.DatabaseError(f"Failed to fetch treatments: {e}")


def db_delete_treatment(treatment_id):
    """Delete a treatment record. Returns True if a row was removed."""
    try:
        with database.DBConnection() as (conn, cur):
            cur.execute("DELETE FROM treatments WHERE treatment_id = %s",
                        (treatment_id,))
            conn.commit()
            return cur.rowcount > 0
    except database.DatabaseError:
        raise
    except MySQLError as e:
        raise database.DatabaseError(f"Failed to delete treatment: {e}")


def db_add_bill(patient_id, bill_date, description,
                amount, paid=False, treatment_id=None):
    """Insert a billing entry. Returns new bill_id."""
    sql = """
        INSERT INTO billing
            (patient_id, treatment_id, bill_date, description, amount, paid)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        with database.DBConnection() as (conn, cur):
            cur.execute(sql, (patient_id, treatment_id, bill_date,
                              description, float(amount), int(paid)))
            conn.commit()
            return cur.lastrowid
    except database.DatabaseError:
        raise
    except MySQLError as e:
        raise database.DatabaseError(f"Failed to add bill: {e}")


def db_get_bills_by_patient(patient_id):
    """Return all billing rows for a patient (newest first)."""
    sql = """
        SELECT bill_id, bill_date, description, amount, paid, treatment_id
        FROM   billing
        WHERE  patient_id = %s
        ORDER  BY bill_date DESC, bill_id DESC
    """
    try:
        with database.DBConnection() as (conn, cur):
            cur.execute(sql, (patient_id,))
            return cur.fetchall()
    except database.DatabaseError:
        raise
    except MySQLError as e:
        raise database.DatabaseError(f"Failed to fetch bills: {e}")


def db_mark_bill_paid(bill_id):
    """Mark a single bill as paid. Returns True on success."""
    try:
        with database.DBConnection() as (conn, cur):
            cur.execute("UPDATE billing SET paid = 1 WHERE bill_id = %s",
                        (bill_id,))
            conn.commit()
            return cur.rowcount > 0
    except database.DatabaseError:
        raise
    except MySQLError as e:
        raise database.DatabaseError(f"Failed to update bill: {e}")


def db_delete_bill(bill_id):
    """Delete a billing entry. Returns True if a row was removed."""
    try:
        with database.DBConnection() as (conn, cur):
            cur.execute("DELETE FROM billing WHERE bill_id = %s", (bill_id,))
            conn.commit()
            return cur.rowcount > 0
    except database.DatabaseError:
        raise
    except MySQLError as e:
        raise database.DatabaseError(f"Failed to delete bill: {e}")


def build_patient_report(patient_id):
    
    patient = database.db_get_patient_by_id(patient_id)
    if not patient:
        raise database.DatabaseError(f"No patient found with ID {patient_id}.")

    visit_sql = """
        SELECT a.date AS visit_date,
               d.name AS doctor_name, d.specialization
        FROM   appointments a
        JOIN   doctors d ON a.doctor_id = d.doctor_id
        WHERE  a.patient_id = %s
        ORDER  BY a.date DESC
    """
    bill_summary_sql = """
        SELECT
            COALESCE(SUM(amount), 0)                              AS total_amount,
            COALESCE(SUM(CASE WHEN paid = 1 THEN amount ELSE 0 END), 0) AS total_paid
        FROM billing
        WHERE patient_id = %s
    """
    try:
        with database.DBConnection() as (conn, cur):
            cur.execute(visit_sql, (patient_id,))
            visits = cur.fetchall()

            cur.execute(bill_summary_sql, (patient_id,))
            brow = cur.fetchone()

        treatments = db_get_treatments_by_patient(patient_id)
        bills      = db_get_bills_by_patient(patient_id)

        total_amount = float(brow["total_amount"])
        total_paid   = float(brow["total_paid"])

        return {
            "patient": patient.to_dict(),
            "visits": [
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

    except database.DatabaseError:
        raise
    except MySQLError as e:
        raise database.DatabaseError(f"Failed to build patient report: {e}")


def export_patient_report_csv(patient_id, folder="reports"):
    
    report = build_patient_report(patient_id)          # raises on bad ID
    os.makedirs(folder, exist_ok=True)

    safe_name = report["patient"]["name"].replace(" ", "_")
    filepath  = os.path.join(folder,
                             f"patient_{patient_id}_{safe_name}_report.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)

        # ── Section 1: Patient Details ────────────────────────────
        w.writerow(["=== PATIENT DETAILS ==="])
        w.writerow(["Patient ID", "Name", "Age", "Gender", "Disease", "Contact"])
        p = report["patient"]
        w.writerow([p["patient_id"], p["name"], p["age"],
                    p["gender"], p["disease"], p["contact"]])
        w.writerow([])

        # ── Section 2: Visit Dates ────────────────────────────────
        w.writerow(["=== VISIT DATES ==="])
        w.writerow(["Visit Date", "Doctor Name", "Specialization"])
        if report["visits"]:
            for v in report["visits"]:
                w.writerow([v["visit_date"], v["doctor_name"],
                             v["specialization"]])
        else:
            w.writerow(["No visits recorded."])
        w.writerow([])

        # ── Section 3: Treatment History ──────────────────────────
        w.writerow(["=== TREATMENT HISTORY ==="])
        w.writerow(["Treatment ID", "Visit Date", "Diagnosis",
                    "Treatment", "Notes", "Doctor", "Specialization"])
        if report["treatments"]:
            for t in report["treatments"]:
                w.writerow([t["treatment_id"], t["visit_date"],
                             t["diagnosis"], t["treatment_desc"],
                             t["notes"], t["doctor_name"],
                             t["specialization"]])
        else:
            w.writerow(["No treatment records found."])
        w.writerow([])

        # ── Section 4: Billing ────────────────────────────────────
        w.writerow(["=== BILLING ==="])
        w.writerow(["Bill ID", "Date", "Description",
                    "Amount (INR)", "Paid", "Linked Treatment ID"])
        if report["billing"]:
            for b in report["billing"]:
                w.writerow([b["bill_id"], b["bill_date"],
                             b["description"], f"{b['amount']:.2f}",
                             "Yes" if b["paid"] else "No",
                             b["treatment_id"] if b["treatment_id"] else "—"])
        else:
            w.writerow(["No billing records found."])
        w.writerow([])

        # ── Section 5: Billing Summary ────────────────────────────
        w.writerow(["=== BILLING SUMMARY ==="])
        w.writerow(["Total Billed (INR)", "Total Paid (INR)", "Amount Due (INR)"])
        s = report["billing_summary"]
        w.writerow([f"{s['total_amount']:.2f}",
                    f"{s['total_paid']:.2f}",
                    f"{s['total_due']:.2f}"])

    return filepath


def ui_add_treatment():
    divider("Add Treatment Record")
    ui_view_patients()
    try:
        pid = int(prompt("Patient ID"))
    except ValueError:
        print("  Invalid ID.")
        return

    patient = database.db_get_patient_by_id(pid)
    if not patient:
        print(f"  No patient found with ID {pid}.")
        return

    ui_view_doctors()
    try:
        did = int(prompt("Doctor ID"))
    except ValueError:
        print("  Invalid ID.")
        return

    if not database.db_get_doctor_by_id(did):
        print(f"  No doctor found with ID {did}.")
        return

    visit_date     = prompt("Visit Date (YYYY-MM-DD)")
    try:
        datetime.strptime(visit_date, "%Y-%m-%d")
    except ValueError:
        print("  Invalid date format. Use YYYY-MM-DD.")
        return

    diagnosis      = prompt("Diagnosis")
    treatment_desc = prompt("Treatment Description")
    notes          = prompt("Additional Notes (press Enter to skip)")

    try:
        tid = db_add_treatment(pid, did, visit_date,
                               diagnosis, treatment_desc, notes)
        print(f"\n  Treatment record added! (ID: {tid})")
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")


def ui_view_treatments():
    divider("View Treatment History")
    ui_view_patients()
    try:
        pid = int(prompt("Patient ID"))
    except ValueError:
        print("  Invalid ID.")
        return

    patient = database.db_get_patient_by_id(pid)
    if not patient:
        print(f"  No patient found with ID {pid}.")
        return

    try:
        records = db_get_treatments_by_patient(pid)
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")
        return

    divider(f"Treatments — {patient.get_name()}")
    if not records:
        print("  No treatment records found.")
        return
    for t in records:
        print(f"  Treatment ID   : {t['treatment_id']}")
        print(f"  Visit Date     : {t['visit_date']}")
        print(f"  Diagnosis      : {t['diagnosis']}")
        print(f"  Treatment      : {t['treatment_desc']}")
        print(f"  Notes          : {t['notes'] or '—'}")
        print(f"  Doctor         : Dr. {t['doctor_name']} ({t['specialization']})")
        divider()


def ui_delete_treatment():
    divider("Delete Treatment Record")
    ui_view_treatments()
    try:
        tid = int(prompt("Treatment ID to delete"))
    except ValueError:
        print("  Invalid ID.")
        return
    confirm = prompt("Type 'yes' to confirm deletion").lower()
    if confirm != "yes":
        print("  Deletion cancelled.")
        return
    try:
        ok = db_delete_treatment(tid)
        print(f"\n  Treatment deleted." if ok
              else f"\n  Treatment ID {tid} not found.")
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")


def ui_add_bill():
    divider("Add Billing Entry")
    ui_view_patients()
    try:
        pid = int(prompt("Patient ID"))
    except ValueError:
        print("  Invalid ID.")
        return

    if not database.db_get_patient_by_id(pid):
        print(f"  No patient found with ID {pid}.")
        return

    bill_date   = prompt("Bill Date (YYYY-MM-DD)")
    try:
        datetime.strptime(bill_date, "%Y-%m-%d")
    except ValueError:
        print("  Invalid date format. Use YYYY-MM-DD.")
        return

    description = prompt("Description (e.g. Consultation, Lab Test)")
    try:
        amount = float(prompt("Amount (INR)"))
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("  Amount must be a positive number.")
        return

    paid_input   = prompt("Already paid? (yes/no)").lower()
    paid         = paid_input == "yes"
    tid_input    = prompt("Linked Treatment ID (press Enter to skip)")
    treatment_id = int(tid_input) if tid_input.isdigit() else None

    try:
        bid = db_add_bill(pid, bill_date, description,
                          amount, paid, treatment_id)
        print(f"\n  Billing entry added! (Bill ID: {bid})")
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")


def ui_view_bills():
    divider("View Billing Records")
    ui_view_patients()
    try:
        pid = int(prompt("Patient ID"))
    except ValueError:
        print("  Invalid ID.")
        return

    patient = database.db_get_patient_by_id(pid)
    if not patient:
        print(f"  No patient found with ID {pid}.")
        return

    try:
        bills = db_get_bills_by_patient(pid)
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")
        return

    divider(f"Billing — {patient.get_name()}")
    if not bills:
        print("  No billing records found.")
        return

    total = 0.0
    paid_total = 0.0
    for b in bills:
        status = "PAID" if b["paid"] else "UNPAID"
        print(f"  Bill ID      : {b['bill_id']}")
        print(f"  Date         : {b['bill_date']}")
        print(f"  Description  : {b['description']}")
        print(f"  Amount       : ₹{b['amount']:.2f}  [{status}]")
        if b["treatment_id"]:
            print(f"  Treatment ID : {b['treatment_id']}")
        divider()
        total      += float(b["amount"])
        paid_total += float(b["amount"]) if b["paid"] else 0.0

    print(f"  Total Billed : ₹{total:.2f}")
    print(f"  Total Paid   : ₹{paid_total:.2f}")
    print(f"  Amount Due   : ₹{total - paid_total:.2f}")
    divider()


def ui_mark_bill_paid():
    divider("Mark Bill as Paid")
    try:
        bid = int(prompt("Bill ID to mark as paid"))
    except ValueError:
        print("  Invalid ID.")
        return
    try:
        ok = db_mark_bill_paid(bid)
        print(f"\n  Bill {bid} marked as paid." if ok
              else f"\n  Bill ID {bid} not found.")
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")


def ui_delete_bill():
    divider("Delete Billing Entry")
    try:
        bid = int(prompt("Bill ID to delete"))
    except ValueError:
        print("  Invalid ID.")
        return
    confirm = prompt("Type 'yes' to confirm deletion").lower()
    if confirm != "yes":
        print("  Deletion cancelled.")
        return
    try:
        ok = db_delete_bill(bid)
        print(f"\n  Bill deleted." if ok
              else f"\n  Bill ID {bid} not found.")
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")



def ui_view_patient_report():
    """Print the full patient report to the console."""
    divider("Patient Report — View")
    ui_view_patients()
    try:
        pid = int(prompt("Patient ID"))
    except ValueError:
        print("  Invalid ID.")
        return

    try:
        report = build_patient_report(pid)
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")
        return

    p = report["patient"]
    divider(f"Report — {p['name']}")

    # Patient Details
    print(f"  Patient ID  : {p['patient_id']}")
    print(f"  Name        : {p['name']}")
    print(f"  Age         : {p['age']}")
    print(f"  Gender      : {p['gender']}")
    print(f"  Disease     : {p['disease']}")
    print(f"  Contact     : {p['contact']}")
    divider()

    # Visit Dates
    print("  VISIT DATES")
    if report["visits"]:
        for v in report["visits"]:
            print(f"    {v['visit_date']}  —  Dr. {v['doctor_name']}"
                  f" ({v['specialization']})")
    else:
        print("    No visits recorded.")
    divider()

    # Treatment History
    print("  TREATMENT HISTORY")
    if report["treatments"]:
        for t in report["treatments"]:
            print(f"    [{t['treatment_id']}] {t['visit_date']}")
            print(f"      Diagnosis  : {t['diagnosis']}")
            print(f"      Treatment  : {t['treatment_desc']}")
            print(f"      Notes      : {t['notes'] or '—'}")
            print(f"      Doctor     : Dr. {t['doctor_name']}"
                  f" ({t['specialization']})")
            print()
    else:
        print("    No treatment records found.")
    divider()

    # Billing
    print("  BILLING")
    if report["billing"]:
        for b in report["billing"]:
            status = "PAID" if b["paid"] else "UNPAID"
            print(f"    [{b['bill_id']}] {b['bill_date']}  ₹{b['amount']:.2f}"
                  f"  [{status}]  {b['description']}")
    else:
        print("    No billing records found.")

    s = report["billing_summary"]
    divider()
    print(f"  Total Billed : ₹{s['total_amount']:.2f}")
    print(f"  Total Paid   : ₹{s['total_paid']:.2f}")
    print(f"  Amount Due   : ₹{s['total_due']:.2f}")
    divider()

def ui_export_patient_report_csv():
    """Export the full patient report to a CSV file."""
    divider("Patient Report — Export to CSV")
    ui_view_patients()
    try:
        pid = int(prompt("Patient ID"))
    except ValueError:
        print("  Invalid ID.")
        return

    try:
        filepath = export_patient_report_csv(pid)
        print(f"\n  Report saved to: {filepath}")
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")
    except Exception as e:
        print(f"\n  Error writing file: {e}")


def treatment_billing_menu():
    while True:
        divider("Treatment & Billing")
        print("  ── Treatment ──")
        print("  1. Add Treatment Record")
        print("  2. View Treatment History")
        print("  3. Delete Treatment Record")
        print("  ── Billing ──")
        print("  4. Add Billing Entry")
        print("  5. View Billing Records")
        print("  6. Mark Bill as Paid")
        print("  7. Delete Billing Entry")
        print("  0. Back")
        divider()
        choice = prompt("Your choice")
        if   choice == "1": ui_add_treatment()
        elif choice == "2": ui_view_treatments()
        elif choice == "3": ui_delete_treatment()
        elif choice == "4": ui_add_bill()
        elif choice == "5": ui_view_bills()
        elif choice == "6": ui_mark_bill_paid()
        elif choice == "7": ui_delete_bill()
        elif choice == "0": break
        else: print("  Invalid option.")


def report_menu():
    while True:
        divider("Reports & Analytics")
        print("  1. Show Statistics")
        print("  2. Generate Charts")
        print("  3. Patient Report (View on screen)")
        print("  4. Patient Report (Export to CSV)")
        print("  0. Back")
        divider()
        choice = prompt("Your choice")

        if choice == "1":
            show_statistics()
        elif choice == "2":
            generate_charts()
            print("\n  Charts generated in 'static/charts/' folder")
        elif choice == "3":
            ui_view_patient_report()
        elif choice == "4":
            ui_export_patient_report_csv()
        elif choice == "0":
            break
        else:
            print("  Invalid option.")


def main_menu():
    print("\n  Connecting to MySQL …")
    if not database.setup_database():
        print("    Could not initialise the database. Check DB_CONFIG and retry.")
        return
    print("    Connected to hospital_db\n")
   
    if not auth.setup_admin_table():
        print("    Could not initialise admin table. Exiting.")
        return
    auth.bootstrap_default_admin()

    admin = auth.login_prompt()
    if not admin:
        print("  Access denied. Exiting.\n")
        return

    while True:
        divider("Hospital Management System")
        print("  1. Patient Management")
        print("  2. Doctor  Management")
        print("  3. Appointment Booking")
        print("  4. Reports & Analytics")
        print("  5. Treatment & Billing")
        print("  6. Admin Management")
        print("  0. Exit")
        divider()
        choice = prompt("Your choice")
        if   choice == "1": patient_menu()
        elif choice == "2": doctor_menu()
        elif choice == "3": appointment_menu()
        elif choice == "4": report_menu()
        elif choice == "5": treatment_billing_menu()
        elif choice == "6": auth.admin_management_menu(admin)
        elif choice == "0":
            print("\n  Goodbye! Stay healthy.\n")
            break
        else:
            print("   Invalid option.")


#  ENTRY POINT
if __name__ == "__main__":
    print("\n  Setting up admin authentication table …")
    if auth.setup_admin_table():
        print("    admins table ready.")
        main_menu()
    else:
        print("    Setup failed. Check your DB_CONFIG in database.py.")

    

