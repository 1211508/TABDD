from pymongo import MongoClient
import tkinter as tk
from tkinter import messagebox

def connect_mongodb():
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://mongoadmin:501c74327eb2366e9b961350@vsgate-s1.dei.isep.ipp.pt:10385")
        db = client["TABDD_NOSQL"]
        return db  # Return the database connection object
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect to MongoDB: {e}")
        return None

