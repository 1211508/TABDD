import tkinter as tk
from tkinter import messagebox
from cartOperations import shopping_cart

# Function to complete the purchase
def checkout(cart_text):
    if not shopping_cart:
        messagebox.showerror("Checkout Error", "Your cart is empty!")
        return
    
    # Calculate total cost and complete the purchase
    total_cost = sum(item["price"] for item in shopping_cart)
    messagebox.showinfo("Checkout", f"Purchase completed! Total: ${total_cost}")
    
    # Clear the cart after checkout
    shopping_cart.clear()
    cart_text.delete(1.0, tk.END)
    cart_text.insert(tk.END, "Your cart is empty.")
