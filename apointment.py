from datetime import datetime

import database
from utility import divider, prompt


def ui_book_appointment():
    divider("Book Appointment")
    try:
        patients = database.db_get_patients()
        doctors  = database.db_get_doctors()
    except database.DatabaseError as e:
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
    except database.DatabaseError as e:
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
    except database.DatabaseError as e:
        print(f"\n  DB Error: {e}")

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
        else: print("  Invalid option.")

