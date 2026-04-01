
#  Custom eception
import re



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