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
from models import Patient, Doctor, Appointment
import utility

def show_statistics():
    from utility import divider,prompt
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

        treatments = database.db_get_treatments_by_patient(patient_id)
        bills      = database.db_get_bills_by_patient(patient_id)

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

        
        w.writerow(["=== PATIENT DETAILS ==="])
        w.writerow(["Patient ID", "Name", "Age", "Gender", "Disease", "Contact"])
        p = report["patient"]
        w.writerow([p["patient_id"], p["name"], p["age"],
                    p["gender"], p["disease"], p["contact"]])
        w.writerow([])

        
        w.writerow(["=== VISIT DATES ==="])
        w.writerow(["Visit Date", "Doctor Name", "Specialization"])
        if report["visits"]:
            for v in report["visits"]:
                w.writerow([v["visit_date"], v["doctor_name"],
                             v["specialization"]])
        else:
            w.writerow(["No visits recorded."])
        w.writerow([])

        
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

        w.writerow(["=== BILLING SUMMARY ==="])
        w.writerow(["Total Billed (INR)", "Total Paid (INR)", "Amount Due (INR)"])
        s = report["billing_summary"]
        w.writerow([f"{s['total_amount']:.2f}",
                    f"{s['total_paid']:.2f}",
                    f"{s['total_due']:.2f}"])

    return filepath


def ui_add_treatment():
    from utility import divider,prompt
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

def ui_view_treatments():
    from utility import divider,prompt
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
        records = database.db_get_treatments_by_patient(pid)
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
    from utility import divider,prompt
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
        ok = database.db_delete_treatment(tid)
        print(f"\n  Treatment deleted." if ok
              else f"\n  Treatment ID {tid} not found.")
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")


def ui_add_bill():
    from utility import divider,prompt
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
        bid = database.db_add_bill(pid, bill_date, description,
                          amount, paid, treatment_id)
        print(f"\n  Billing entry added! (Bill ID: {bid})")
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")


def ui_view_bills():
    from utility import divider,prompt
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
        bills = database.db_get_bills_by_patient(pid)
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
    from utility import divider,prompt
    divider("Mark Bill as Paid")
    try:
        bid = int(prompt("Bill ID to mark as paid"))
    except ValueError:
        print("  Invalid ID.")
        return
    try:
        ok = database.db_mark_bill_paid(bid)
        print(f"\n  Bill {bid} marked as paid." if ok
              else f"\n  Bill ID {bid} not found.")
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")

def ui_delete_bill():
    from utility import divider,prompt
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
        ok = database.db_delete_bill(bid)
        print(f"\n  Bill deleted." if ok
              else f"\n  Bill ID {bid} not found.")
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")

def ui_view_patient_report():
    from utility import divider,prompt
    
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
    from utility import divider,prompt
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
    from utility import divider,prompt
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
        utility.divider("Reports & Analytics")
        print("  1. Show Statistics")
        print("  2. Generate Charts")
        print("  3. Patient Report (View on screen)")
        print("  4. Patient Report (Export to CSV)")
        print("  0. Back")
        utility.divider()
        choice = utility.prompt("Your choice")

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
    from utility import divider, prompt
    from doctor import doctor_menu
    from patients import patient_menu
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
        elif choice == "3":
            import apointment as ap
            ap.appointment_menu()
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

    

