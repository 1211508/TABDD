import cx_Oracle
from tkinter import messagebox

def connect_oracle():
    try:
        # Establish Oracle connection
        dsn = cx_Oracle.makedsn("vsgate-s1.dei.isep.ipp.pt", 10824, service_name="xe")
        oracle_conn = cx_Oracle.connect(user="sys", password="oracle2", dsn=dsn, mode=cx_Oracle.SYSDBA)
        return oracle_conn  # Return the Oracle connection object
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect to OracleSQL: {e}")
        return None

