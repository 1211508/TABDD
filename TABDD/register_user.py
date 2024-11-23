import cx_Oracle
from tkinter import messagebox
import random

def register_user(first_name, last_name, email, phone, address, dob, password, role, oracle_conn):
    try:
        # Generate a random user code
        user_code = random.randint(1000, 9999)
        
        # Insert the user into the User table with a role
        cursor = oracle_conn.cursor()
        cursor.execute("""
            INSERT INTO SystemUser (systemUserCode, firstName, lastName, email, phone, address, dateOfBirth, password, role)
            VALUES (:1, :2, :3, :4, :5, :6, TO_DATE(:7, 'YYYY-MM-DD'), :8, :9)
        """, (user_code, first_name, last_name, email, phone, address, dob, password, role))
        
        oracle_conn.commit()
        cursor.close()

        messagebox.showinfo("Registration", f"User registered successfully!\nUser Code: {user_code}")
        return True
    except cx_Oracle.IntegrityError:
        messagebox.showerror("Registration Error", "An account with this email already exists.")
        return False
    except Exception as e:
        messagebox.showerror("Registration Error", f"Failed to register user: {e}")
        return False


def login_user(email, password, oracle_conn):
    try:
        cursor = oracle_conn.cursor()
        cursor.execute("SELECT systemUserCode FROM SystemUser WHERE email = :1 AND password = :2", (email, password))
        result = cursor.fetchone()
        cursor.close()

        if result:
            return result[0]  # Return customer code if login is successful
        else:
            messagebox.showerror("Login Error", "Invalid email or password.")
            return None
    except Exception as e:
        messagebox.showerror("Login Error", f"Failed to login: {e}")
        return None


