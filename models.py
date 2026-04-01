from abc import ABC, abstractmethod


# ── BASE CLASS ────────────────────────────────────────────────────────────────
class Person(ABC):
    def __init__(self, name: str, age: int):
        self.__name = name
        self.__age  = age

    def get_name(self):  return self.__name
    def get_age(self):   return self.__age
    def set_name(self, n): self.__name = n
    def set_age(self,  a): self.__age  = a

    @abstractmethod
    def display(self):
        print(f"  Name : {self.__name}")
        print(f"  Age  : {self.__age}")


# ── PATIENT ───────────────────────────────────────────────────────────────────
class Patient(Person):
    def __init__(self, patient_id: int, name: str, age: int,
                 gender: str, disease: str, contact: str):
        super().__init__(name, age)
        self.__patient_id = patient_id
        self.__gender     = gender
        self.__disease    = disease
        self.__contact    = contact

    def get_patient_id(self): return self.__patient_id
    def get_gender(self):     return self.__gender
    def get_disease(self):    return self.__disease
    def get_contact(self):    return self.__contact
    def set_gender(self, g):  self.__gender  = g
    def set_disease(self, d): self.__disease = d
    def set_contact(self, c): self.__contact = c

    def display(self):
        print(f"  Patient ID : {self.__patient_id}")
        super().display()
        print(f"  Gender     : {self.__gender}")
        print(f"  Disease    : {self.__disease}")
        print(f"  Contact    : {self.__contact}")

    def to_dict(self):
        return {
            "patient_id": self.__patient_id,
            "name":       self.get_name(),
            "age":        self.get_age(),
            "gender":     self.__gender,
            "disease":    self.__disease,
            "contact":    self.__contact,
        }


# ── DOCTOR ────────────────────────────────────────────────────────────────────
class Doctor(Person):
    def __init__(self, doctor_id: int, name: str, age: int,
                 specialization: str, experience: int):
        super().__init__(name, age)
        self.__doctor_id      = doctor_id
        self.__specialization = specialization
        self.__experience     = experience

    def get_doctor_id(self):      return self.__doctor_id
    def get_specialization(self): return self.__specialization
    def get_experience(self):     return self.__experience

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


# ── APPOINTMENT ───────────────────────────────────────────────────────────────
class Appointment:
    def __init__(self, appointment_id, patient_id, doctor_id, date,
                 patient_name: str = "", doctor_name: str = ""):
        self.__appt_id      = appointment_id
        self.__patient_id   = patient_id
        self.__doctor_id    = doctor_id
        self.__date         = date
        self.__patient_name = patient_name
        self.__doctor_name  = doctor_name

    def get_appt_id(self):    return self.__appt_id
    def get_patient_id(self): return self.__patient_id
    def get_doctor_id(self):  return self.__doctor_id
    def get_date(self):       return str(self.__date)

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
