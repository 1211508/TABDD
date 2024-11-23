from tkinter import messagebox, simpledialog

# Function to gather feedback
def feedback(mongo_db):
    satisfaction = simpledialog.askinteger("Feedback", "Rate your satisfaction (1-5):")
    comments = simpledialog.askstring("Feedback", "Leave your comments on usability:")

    if satisfaction and comments:
        # Save feedback to MongoDB
        feedback_collection = mongo_db["Feedback"]
        feedback_collection.insert_one({
            "satisfaction": satisfaction,
            "comments": comments
        })
        messagebox.showinfo("Feedback", "Thank you for your feedback!")
    else:
        messagebox.showwarning("Feedback", "Feedback was not provided.")
