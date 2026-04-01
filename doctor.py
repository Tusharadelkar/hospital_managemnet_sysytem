#  DOCTOR UI
import database
from utility import InvalidAgeError, InvalidNameError, divider, prompt, validate_age, validate_name


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
    except database.DatabaseError as e:
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
    except database.DatabaseError as e:
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
            print(f"\n Doctor '{doctor.get_name()}' deleted.")
        else:
            print("  Deletion cancelled.")
    except database.DatabaseError as e:
        print(f"\n DB Error: {e}")



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