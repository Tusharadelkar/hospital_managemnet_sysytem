from datetime import datetime
import mysql.connector
from mysql.connector import Error as MySQLError
import Hospital_management_system

class DatabaseError(Exception):
    """Raised for any database-level problem."""
    pass

DB_CONFIG = {
    "host":     "localhost",
    "user":     "TusharAdelkar",   
    "password": "SUNshine21#", 
    "database": "hospital_db",
}

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

        conn.commit()
        cur.close()
        conn.close()
        return True

    except MySQLError as e:
        print(f"\n  ✖  Database setup failed: {e}")
        return False


#  DATABASE CONNECTION MANAGER
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



#  DATABASE OPERATIONS  ── Patient
def db_add_patient(name: str, age: int, gender: str,
                   disease: str, contact: str) -> int:
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


def db_get_patients(search: str = "") -> list:
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
        return [Hospital_management_system.Patient(r["patient_id"], r["name"], r["age"],
                        r["gender"], r["disease"], r["contact"])
                for r in rows]
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch patients: {e}")


def db_get_patient_by_id(patient_id: int):
    try:
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM patients WHERE patient_id = %s",
                        (patient_id,))
            row = cur.fetchone()
        if not row:
            return None
        return Hospital_management_system.Patient(row["patient_id"], row["name"], row["age"],
                       row["gender"], row["disease"], row["contact"])
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch patient: {e}")


def db_update_patient(patient_id: int, name: str, age: int,
                      gender: str, disease: str, contact: str) -> bool:
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


def db_delete_patient(patient_id: int) -> bool:
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

#  DATABASE OPERATIONS  ── Doctor
def db_add_doctor(name: str, age: int,
                  specialization: str, experience: int) -> int:
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

def db_get_doctors() -> list:
    try:
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM doctors ORDER BY doctor_id")
            rows = cur.fetchall()
        return [Hospital_management_system.Doctor(r["doctor_id"], r["name"], r["age"],
                       r["specialization"], r["experience"])
                for r in rows]
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch doctors: {e}")

def db_get_doctor_by_id(doctor_id: int):
    try:
        with DBConnection() as (conn, cur):
            cur.execute("SELECT * FROM doctors WHERE doctor_id = %s",
                        (doctor_id,))
            row = cur.fetchone()
        if not row:
            return None
        return Hospital_management_system.Doctor(row["doctor_id"], row["name"], row["age"],
                      row["specialization"], row["experience"])
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch doctor: {e}")

#  DATABASE OPERATIONS  ── Appointment
def db_book_appointment(patient_id: int,
                        doctor_id: int, date: str) -> int:
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


def db_get_appointments() -> list:
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
        return [Hospital_management_system.Appointment(r["appointment_id"], r["patient_id"],
                            r["doctor_id"],      r["date"],
                            r["patient_name"],   r["doctor_name"])
                for r in rows]
    except DatabaseError:
        raise
    except MySQLError as e:
        raise DatabaseError(f"Failed to fetch appointments: {e}")