#  PATIENT UI
import database
import utility


def ui_add_patient():
    from utility import divider,prompt
    divider("Add Patient")
    try:
        name    = utility.validate_name(prompt("Name"))
        age     = utility.validate_age(prompt("Age"))
        gender  = prompt("Gender (Male/Female/Other)").capitalize()
        disease = prompt("Disease / Condition")
        contact = utility.validate_contact(prompt("Contact (10 digits)"))
        new_id  = database.db_add_patient(name, age, gender, disease, contact)
        print(f"\n  Patient '{name}' added! (ID: {new_id})")
    except (utility.InvalidNameError, utility.InvalidAgeError, utility.InvalidContactError) as e:
        print(f"\n  Validation Error: {e}")
    except database.DatabaseError as e:
        print(f"\n DB Error: {e}")

def ui_view_patients():
    from utility import divider,prompt
    divider("All Patients")
    try:
        patients = database.db_get_patients()
        if not patients:
            print("  No patients found.")
            return
        for p in patients:
            p.display()
            divider()
    except database.DatabaseError as e:
        print(f"\n DB Error: {e}")

def ui_update_patient():
    from utility import divider,prompt
    divider("Update Patient")
    ui_view_patients()
    try:
        pid = int(prompt("Enter Patient ID to update"))
    except ValueError:
        print(" Invalid ID.")
        return

    try:
        patient = database.db_get_patient_by_id(pid)
    except database.DatabaseError as e:
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

        name    = utility.validate_name(n)    if n  else patient.get_name()
        age     = utility.validate_age(a)     if a  else patient.get_age()
        gender  = g.capitalize()      if g  else patient.get_gender()
        disease = di                  if di else patient.get_disease()
        contact = utility.validate_contact(c) if c  else patient.get_contact()

        ok = database.db_update_patient(pid, name, age, gender, disease, contact)
        print(f"\n Patient ID {pid} updated!" if ok
              else f"\n  No changes saved.")
    except (utility.InvalidNameError, utility.InvalidAgeError, utility.InvalidContactError) as e:
        print(f"\n Validation Error: {e}")
    except database.DatabaseError as e:
        print(f"\n DB Error: {e}")

def ui_delete_patient():
    from utility import divider,prompt
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
    except database.DatabaseError as e:
        print(f"\n DB Error: {e}")

def ui_search_patient():
    from utility import divider,prompt
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
    except database.DatabaseError as e:
        print(f"\n DB Error: {e}")

def patient_menu():
    from utility import divider,prompt
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
