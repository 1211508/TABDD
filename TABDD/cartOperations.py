import tkinter as tk
from tkinter import messagebox, simpledialog

# Initialize a shopping cart as a global list
shopping_cart = []

# Function to add an item to the cart
def add_to_cart(mongo_db):
    item_id = simpledialog.askstring("Add to Cart", "Enter the Item ID to add:")
    item_collection = mongo_db["Product"]
    item = item_collection.find_one({"_id": int(item_id)})

    if item:
        shopping_cart.append(item)
        messagebox.showinfo("Cart", f"Added {item['name']} to the cart.")
    else:
        messagebox.showerror("Error", "Item not found.")

# Function to remove an item from the cart
def remove_from_cart():
    item_id = simpledialog.askstring("Remove from Cart", "Enter the Item ID to remove:")
    item_id = int(item_id)

    for item in shopping_cart:
        if item["_id"] == item_id:
            shopping_cart.remove(item)
            messagebox.showinfo("Cart", f"Removed {item['name']} from the cart.")
            return
    messagebox.showerror("Error", "Item not found in the cart.")

# Function to view the cart
def view_cart(cart_text):
    cart_text.delete(1.0, tk.END)
    if shopping_cart:
        total_cost = sum(item["price"] for item in shopping_cart)
        cart_text.insert(tk.END, "Items in Cart:\n")
        for item in shopping_cart:
            cart_text.insert(tk.END, f"ID: {item['_id']}, Name: {item['name']}, Price: {item['price']}\n")
        cart_text.insert(tk.END, f"\nTotal Cost: ${total_cost}")
    else:
        cart_text.insert(tk.END, "Your cart is empty.")
