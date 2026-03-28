import re
from datetime import datetime
import mysql.connector
from mysql.connector import Error as MySQLError
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import database 


#  Custom eception
class InvalidNameError(Exception):
    pass

class InvalidAgeError(Exception):
    pass

class InvalidContactError(Exception):
    pass

class DatabaseError(Exception):
    pass


#  VALIDATION FUNCTIONS

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
class Person:
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

    def to_dict(self) -> dict:
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

    def to_dict(self) -> dict:
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

def report_menu():
    while True:
        divider("Reports & Analytics")

        print("  1. Show Statistics")
        print("  2. Generate Charts")
        print("  0. Back")

        divider()
        choice = prompt("Your choice")

        if choice == "1":
            show_statistics()

        elif choice == "2":
            generate_charts()
            print("\n Charts generated in 'static/charts/' folder")

        elif choice == "0":
            break

        else:
            print(" Invalid option.")


def main_menu():
    print("\n  Connecting to MySQL …")
    if not database.setup_database():
        print("  Could not initialise the database. Check DB_CONFIG and retry.")
        return
    print("  Connected to hospital_db\n")

    while True:
        divider("Hospital Management System")
        print("1. Patient Management")
        print("2. Doctor  Management")
        print("3. Appointment Booking")
        print("4. Reports & Analytics")
        print("0. Exit")
        divider()
        choice = prompt("Your choice")
        if   choice == "1": patient_menu()
        elif choice == "2": doctor_menu()
        elif choice == "3": appointment_menu()
        elif choice == "4": report_menu()
        elif choice == "0":
            print("\n  Goodbye! Stay healthy.\n")
            break
        else:
            print("   Invalid option.")



#  ENTRY POINT
if __name__ == "__main__":
    main_menu()

