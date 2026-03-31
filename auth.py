import re
import bcrypt
import mysql.connector
from mysql.connector import Error as MySQLError


DB_CONFIG = {
    "host":     "localhost",
    "user":     "TusharAdelkar",
    "password": "SUNshine21#",
    "database": "hospital_db",
}


# exceptions
class AuthError(Exception):
    """Raised when login credentials are incorrect."""
    pass

class AdminExistsError(Exception):
    """Raised when trying to create a duplicate admin username."""
    pass


class _AuthDBConnection:

    def __enter__(self):
        self.conn   = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(dictionary=True)
        return self.conn, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and self.conn.is_connected():
            self.conn.rollback()
        if hasattr(self, "cursor") and self.cursor:
            self.cursor.close()
        if hasattr(self, "conn") and self.conn.is_connected():
            self.conn.close()
        return False


# validation
def validate_username(username):
    username = username.strip()
    if not re.fullmatch(r"[A-Za-z0-9_]{4,30}", username):
        raise ValueError(
            "Username contain 4–30 characters: letters, numbers, underscores only."
        )
    return username.lower()


def validate_password(password):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        raise ValueError("Password must contain at least one special character.")
    return password


def setup_admin_table():
    init_cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    try:
        conn = mysql.connector.connect(**init_cfg)
        cur  = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS hospital_db "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.execute("USE hospital_db")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                admin_id    INT          AUTO_INCREMENT PRIMARY KEY,
                username    VARCHAR(30)  NOT NULL UNIQUE,
                password    VARCHAR(255) NOT NULL,
                created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except MySQLError as e:
        print(f"\n  Admin table setup failed: {e}")
        return False



def db_create_admin(username, plain_password):
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    sql = "INSERT INTO admins (username, password) VALUES (%s, %s)"
    try:
        with _AuthDBConnection() as (conn, cur):
            cur.execute(sql, (username, hashed.decode("utf-8")))
            conn.commit()
            return cur.lastrowid
    except MySQLError as e:
        if e.errno == 1062:
            raise AdminExistsError(f"Username '{username}' is already taken.")
        raise Exception(f"Failed to create admin: {e}")


def db_get_admin_by_username(username):
    try:
        with _AuthDBConnection() as (_, cur):
            cur.execute(
                "SELECT admin_id, username, password FROM admins WHERE username = %s",
                (username,)
            )
            return cur.fetchone()
    except MySQLError as e:
        raise Exception(f"Failed to fetch admin: {e}")


def db_list_admins():
    try:
        with _AuthDBConnection() as (_, cur):
            cur.execute(
                "SELECT admin_id, username, created_at FROM admins ORDER BY admin_id"
            )
            return cur.fetchall()
    except MySQLError as e:
        raise Exception(f"Failed to list admins: {e}")


def db_delete_admin(admin_id):
    try:
        with _AuthDBConnection() as (conn, cur):
            cur.execute("SELECT COUNT(*) AS cnt FROM admins")
            row = cur.fetchone()
            if row["cnt"] <= 1:
                raise AuthError("Cannot delete the last admin account.")
            cur.execute("DELETE FROM admins WHERE admin_id = %s", (admin_id,))
            conn.commit()
            return cur.rowcount > 0
    except AuthError:
        raise
    except MySQLError as e:
        raise Exception(f"Failed to delete admin: {e}")


def db_change_password(admin_id, old_password, new_password):
    try:
        with _AuthDBConnection() as (conn, cur):
            cur.execute(
                "SELECT password FROM admins WHERE admin_id = %s", (admin_id,)
            )
            row = cur.fetchone()
            if not row:
                raise AuthError("Admin not found.")
            if not bcrypt.checkpw(old_password.encode("utf-8"),
                                  row["password"].encode("utf-8")):
                raise AuthError("Current password is incorrect.")
            new_hash = bcrypt.hashpw(
                new_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            cur.execute(
                "UPDATE admins SET password = %s WHERE admin_id = %s",
                (new_hash, admin_id)
            )
            conn.commit()
            return True
    except AuthError:
        raise
    except MySQLError as e:
        raise Exception(f"Failed to change password: {e}")



def login(username, plain_password):
    username = username.strip().lower()
    admin = db_get_admin_by_username(username)
    if not admin:
        raise AuthError("Invalid username or password.")
    if not bcrypt.checkpw(plain_password.encode("utf-8"),
                          admin["password"].encode("utf-8")):
        raise AuthError("Invalid username or password.")
    return admin


MAX_LOGIN_ATTEMPTS = 3

def login_prompt():
    import msvcrt

    def input_password(prompt_text: str) -> str:
        print(prompt_text, end="", flush=True)
        password = ""
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                print()
                break
            elif ch == "\x08":
                if password:
                    password = password[:-1]
                    print("\b \b", end="", flush=True)
            elif ch == "\x03":
                raise KeyboardInterrupt
            else:
                password += ch
                print("*", end="", flush=True)
        return password

    print("\n" + "═" * 54)
    print("       HOSPITAL MANAGEMENT SYSTEM — Admin Login")
    print("═" * 54)

    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
        remaining = MAX_LOGIN_ATTEMPTS - attempt
        username  = input("  Username : ").strip()
        password  = input_password("  Password : ")

        try:
            admin = login(username, password)
            print(f"\n    Welcome, {admin['username']}!\n")
            return admin
        except AuthError as e:
            if remaining > 0:
                print(f"\n    {e}  ({remaining} attempt(s) remaining)\n")
            else:
                print(f"\n    {e}  No attempts remaining. Exiting.\n")

    return None


# ─────────────────────────────────────────
#  ADMIN MANAGEMENT UI  (console)
# ─────────────────────────────────────────

def _divider(title: str = ""):
    width = 54
    if title:
        pad = (width - len(title) - 2) // 2
        print("\n" + "─" * pad + f" {title} " + "─" * pad)
    else:
        print("─" * width)


def _prompt(text: str) -> str:
    return input(f"  {text}: ").strip()


def ui_add_admin():
    import msvcrt

    def input_password(prompt_text):
        print(prompt_text, end="", flush=True)
        pw = ""
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"): print(); break
            elif ch == "\x08":
                if pw: pw = pw[:-1]; print("\b \b", end="", flush=True)
            elif ch == "\x03": raise KeyboardInterrupt
            else: pw += ch; print("*", end="", flush=True)
        return pw

    _divider("Add New Admin")
    try:
        username = validate_username(_prompt("New username"))
        password = input_password("  Password      : ")
        validate_password(password)
        confirm  = input_password("  Confirm pass  : ")
        if password != confirm:
            print("\n  ✖  Passwords do not match.")
            return
        new_id = db_create_admin(username, password)
        print(f"\n  ✔  Admin '{username}' created! (ID: {new_id})")
    except (ValueError, AdminExistsError) as e:
        print(f"\n  ✖  {e}")
    except Exception as e:
        print(f"\n  ✖  DB Error: {e}")


def ui_list_admins():
    _divider("All Admins")
    try:
        admins = db_list_admins()
        if not admins:
            print("  No admins found.")
            return
        for a in admins:
            print(f"  [{a['admin_id']}]  {a['username']}  "
                  f"(created: {a['created_at']})")
    except Exception as e:
        print(f"\n  ✖  DB Error: {e}")


def ui_delete_admin():
    _divider("Delete Admin")
    ui_list_admins()
    try:
        aid = int(_prompt("Admin ID to delete"))
    except ValueError:
        print("  ✖  Invalid ID.")
        return
    confirm = _prompt("Type 'yes' to confirm deletion").lower()
    if confirm != "yes":
        print("  Deletion cancelled.")
        return
    try:
        ok = db_delete_admin(aid)
        print(f"\n  ✔  Admin deleted." if ok
              else f"\n  ✖  Admin ID {aid} not found.")
    except (Exception, AuthError) as e:
        print(f"\n  ✖  {e}")


def ui_change_password(current_admin: dict):
    import msvcrt

    def input_password(prompt_text):
        print(prompt_text, end="", flush=True)
        pw = ""
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"): print(); break
            elif ch == "\x08":
                if pw: pw = pw[:-1]; print("\b \b", end="", flush=True)
            elif ch == "\x03": raise KeyboardInterrupt
            else: pw += ch; print("*", end="", flush=True)
        return pw

    _divider("Change Password")
    try:
        old     = input_password("  Current password : ")
        new     = input_password("  New password     : ")
        validate_password(new)
        confirm = input_password("  Confirm new      : ")
        if new != confirm:
            print("\n    Passwords do not match.")
            return
        db_change_password(current_admin["admin_id"], old, new)
        print("\n    Password changed successfully!")
    except (ValueError, AuthError) as e:
        print(f"\n    {e}")
    except Exception as e:
        print(f"\n    DB Error: {e}")


def admin_management_menu(current_admin: dict):
    while True:
        _divider("Admin Management")
        print("  1. List all admins")
        print("  2. Add new admin")
        print("  3. Delete an admin")
        print("  4. Change my password")
        print("  0. Back")
        _divider()
        choice = _prompt("Your choice")
        if   choice == "1": ui_list_admins()
        elif choice == "2": ui_add_admin()
        elif choice == "3": ui_delete_admin()
        elif choice == "4": ui_change_password(current_admin)
        elif choice == "0": break
        else: print("    Invalid option.")


# ─────────────────────────────────────────
#  FIRST-RUN BOOTSTRAP
# ─────────────────────────────────────────

def bootstrap_default_admin():
    try:
        admins = db_list_admins()
        if not admins:
            db_create_admin("admin", "Admin@123")
            print("     Default admin created.")
            print("     Username : admin")
            print("     Password : Admin@123")
            print("     Please change the password after first login!\n")
    except Exception as e:
        print(f"    Could not create default admin: {e}")
