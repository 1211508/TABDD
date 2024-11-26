import tkinter as tk
from tkinter import messagebox
from mongoDBConn import connect_mongodb
from SQLConn import connect_oracle
from register_user import register_user, login_user
from tkinter import ttk
from product_details import fetch_product_details
from cart import add_to_cart, checkout
from datetime import datetime

# Establish initial database connections
mongo_db = connect_mongodb()
oracle_conn = connect_oracle()

# Ensure connections are valid
if mongo_db is None or oracle_conn is None:
    exit("Failed to connect to databases.")

def show_cart(cart, cart_frame):
    for widget in cart_frame.winfo_children():
        widget.destroy()

    if not cart:
        tk.Label(cart_frame, text="Cart is empty", font=("Helvetica", 12)).pack()
        return

    for item in cart:
        tk.Label(
            cart_frame,
            text=f"{item['product_name']} (x{item['quantity']}): €{item['total']:.2f}",
            font=("Helvetica", 10)
        ).pack(anchor="w")

    tk.Label(cart_frame, text=f"Total: €{sum(item['total'] for item in cart):.2f}", font=("Helvetica", 12, "bold")).pack()

def fetch_orders(SystemUserCode):
    try:
        cursor = oracle_conn.cursor()
        cursor.execute("""
            SELECT orderCode, status, totalAmount
            FROM Orders
            WHERE SystemUserCode = :SystemUserCode
        """, {"SystemUserCode": SystemUserCode})
        orders = cursor.fetchall()
        return orders
    except Exception as e:
        print(f"Error fetching orders: {e}")
        return []
    finally:
        cursor.close()

def show_order_details(order_code):
    try:
        # Buscar itens da coleção OrderItem no MongoDB
        items = mongo_db.OrderItem.find({"orderCode": order_code})

        details_window = tk.Toplevel()
        details_window.title("Order Details")
        details_window.geometry("400x300")

        if not items:
            tk.Label(details_window, text="No items found for this order.", font=("Helvetica", 12)).pack(pady=20)
            return

        for item in items:
            product_name = item.get("productName", "Unknown")
            quantity = item.get("quantity", 0)
            total_amount = item.get("total", 0.0)

            tk.Label(
                details_window,
                text=f"Product: {product_name}\nQuantity: {quantity}\nTotal: €{total_amount:.2f}\n",
                font=("Helvetica", 10),
                justify="left"
            ).pack(anchor="w", padx=10, pady=5)
    except Exception as e:
        print(f"Error fetching order details: {e}")

def show_orders(customer_code, orders_frame):
    for widget in orders_frame.winfo_children():
        widget.destroy()

    orders = fetch_orders(customer_code)

    if not orders:
        tk.Label(orders_frame, text="No orders found.", font=("Helvetica", 12)).pack()
        return

    for order in orders:
        order_code, status, total_amount = order

        frame = tk.Frame(orders_frame, pady=5, padx=10)
        frame.pack(fill="x", anchor="w")

        tk.Label(frame, text=f"Order: {order_code}", font=("Helvetica", 10, "bold")).pack(anchor="w")
        tk.Label(frame, text=f"Status: {status}\nTotal: €{total_amount:.2f}", font=("Helvetica", 10)).pack(anchor="w")
        tk.Button(
            frame, text="View Details", command=lambda o=order_code: show_order_details(o),
            bg="#0984e3", fg="white"
        ).pack(anchor="e", pady=5)

def handle_add_to_cart(product_code_entry, quantity_entry, cart, cart_frame):
    product_code = product_code_entry.get()
    quantity = quantity_entry.get()

    if not product_code or not quantity:
        messagebox.showerror("Error", "Please enter a product quantity.")
        return

    try:
        quantity = int(quantity)
        add_to_cart(product_code, quantity, cart, oracle_conn)
        show_cart(cart, cart_frame)
    except ValueError:
        messagebox.showerror("Error", "Quantity must be an integer.")


def show_product_details(product_code, oracle_conn, mongo_db, details_frame):
    product_details = fetch_product_details(product_code, oracle_conn, mongo_db)

    for widget in details_frame.winfo_children():
        widget.destroy()

    if product_details:
        details_text = (
            f"Product Code: {product_details['productCode']}\n"
            f"Name: {product_details['productName']}\n"
            f"Category: {product_details['category']}\n"
            f"Price: €{product_details['price']}\n"
            f"Stock: {product_details['stockQuantity']}\n"
        )
        tk.Label(details_frame, text=details_text, font=("Helvetica", 10), justify="left", bg="#f5f5f5").pack()
    else:
        tk.Label(details_frame, text="Product details not found.", font=("Helvetica", 12)).pack()

def load_all_products(oracle_conn, mongo_db):
    products = []
    try:
        # Buscar produtos no Oracle
        cursor = oracle_conn.cursor()
        cursor.execute("""
            SELECT productCode, productName
            FROM Product
        """)
        oracle_products = cursor.fetchall()
        products.extend(oracle_products)
        
        # Buscar produtos no MongoDB
        mongo_products = mongo_db.products.find()  # Supondo que você tenha uma coleção "products"
        for product in mongo_products:
            products.append((product["productCode"], product["productName"]))
        
        return products  # Lista combinada de produtos de ambos os bancos
    
    except Exception as e:
        print(f"Error loading products: {e}")
        return []
    finally:
        cursor.close()

def on_product_select(event, product_dropdown, oracle_conn, mongo_db, details_frame):
    # Quando o usuário selecionar um produto no dropdown, exibir os detalhes
    selected_name = product_dropdown.get()
    if selected_name:
        # Encontrar o productCode correspondente ao nome selecionado
        for product in product_dropdown.product_list:
            if product[1] == selected_name:
                show_product_details(product[0], oracle_conn, mongo_db, details_frame)
                break

def show_product_ratings(product_code):
    try:
        ratings = mongo_db.productRating.find_one({"productCode": product_code}).get("ratings", [])

        ratings_window = tk.Toplevel()
        ratings_window.title("Product Ratings and Comments")
        ratings_window.geometry("400x300")

        if not ratings:
            tk.Label(ratings_window, text="No ratings or comments available.", font=("Helvetica", 12)).pack(pady=20)
            return

        for rating in ratings:
            tk.Label(
                ratings_window,
                text=f"Rating: {rating['rating']}\nComment: {rating['comment']}\n",
                font=("Helvetica", 10),
                justify="left"
            ).pack(anchor="w", padx=10, pady=5)
    except Exception as e:
        print(f"Error fetching ratings: {e}")

def create_order(SystemUserCode, cart, delivery_address):
    try:
        cursor = oracle_conn.cursor()

        # Generate a new orderCode
        cursor.execute("SELECT MAX(orderCode) FROM Orders")
        max_order_code = cursor.fetchone()[0] or 0
        order_code = max_order_code + 1

        # Calculate total amount
        total_amount = sum(item['total'] for item in cart)

        # Insert the order into the Orders table
        order_date = datetime.now().strftime('%Y-%m-%d')
        status = "in transit"
        cursor.execute(
            """
            INSERT INTO Orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress)
            VALUES (:orderCode, TO_DATE(:orderDate, 'YYYY-MM-DD'), :totalAmount, :status, :SystemUserCode, :deliveryAddress)
            """,
            {
                "orderCode": order_code,
                "orderDate": order_date,
                "totalAmount": total_amount,
                "status": status,
                "SystemUserCode": SystemUserCode,
                "deliveryAddress": delivery_address
            }
        )

        # Insert items into MongoDB's OrderItem collection
        order_items = [
            {
                "orderCode": order_code,
                "productCode": item["product_code"],
                "productName": item["product_name"],
                "quantity": item["quantity"],
                "total": item["total"]
            }
            for item in cart
        ]
        mongo_db.OrderItem.insert_many(order_items)

        oracle_conn.commit()
        print(f"Order {order_code} created successfully.")
        return order_code
    except Exception as e:
        oracle_conn.rollback()
        print(f"Error creating order: {e}")
        return None
    finally:
        cursor.close()


def handle_checkout(SystemUserCode, cart, refresh_orders):
    if not cart:
        messagebox.showerror("Error", "Cart is empty.")
        return

    # Get delivery address from user
    checkout_window = tk.Toplevel()
    checkout_window.title("Checkout")
    checkout_window.geometry("400x250")

    tk.Label(checkout_window, text="Enter Delivery Address", font=("Helvetica", 12)).pack(pady=10)
    delivery_address_entry = tk.Entry(checkout_window, width=50)
    delivery_address_entry.pack(pady=5)

    def confirm_checkout():
        delivery_address = delivery_address_entry.get()
        if not delivery_address:
            messagebox.showerror("Error", "Delivery address is required.")
            return

        print(f"Attempting to create order for user: {SystemUserCode}")
        print(f"Cart contents: {cart}")
        print(f"Delivery Address: {delivery_address}")

        order_code = create_order(SystemUserCode, cart, delivery_address)
        if order_code:
            messagebox.showinfo("Success", f"Order {order_code} created successfully.")
            cart.clear()
            refresh_orders()
            checkout_window.destroy()
        else:
            messagebox.showerror("Error", "Failed to create order. Check logs for details.")

    tk.Button(checkout_window, text="Confirm", command=confirm_checkout, bg="#27ae60", fg="white").pack(pady=10)

def open_main_window(SystemUserCode):
    cart = []
    main_window = tk.Tk()
    main_window.title("Main Page")
    main_window.geometry("1200x600")
    main_window.configure(bg="#f5f5f5")

    # Orders Section
    orders_frame = tk.Frame(main_window, bg="#f5f5f5", width=400)
    orders_frame.pack(side="left", fill="y", padx=10, pady=10)

    tk.Label(orders_frame, text="My Orders", font=("Helvetica", 14, "bold"), bg="#f5f5f5").pack(pady=10)

    def refresh_orders():
        show_orders(SystemUserCode, orders_frame)

    refresh_orders()

    # Cart and Product Section
    right_frame = tk.Frame(main_window, bg="#f5f5f5")
    right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    # Cart Frame
    cart_frame = tk.Frame(right_frame, bg="#f5f5f5")
    cart_frame.pack(fill="x", pady=10)

    tk.Label(cart_frame, text="Cart", font=("Helvetica", 14, "bold"), bg="#f5f5f5").pack(pady=10)

    def refresh_cart():
        show_cart(cart, cart_frame)

    # Product Selection Frame
    product_frame = tk.Frame(right_frame, bg="#f5f5f5")
    product_frame.pack(fill="both", expand=True, pady=10)

    tk.Label(product_frame, text="Select a Product", font=("Helvetica", 12), bg="#f5f5f5").grid(row=0, column=0, padx=5, pady=5)

    product_dropdown = ttk.Combobox(product_frame, width=40)
    product_dropdown.grid(row=1, column=0, padx=5, pady=5)

    products = load_all_products(oracle_conn, mongo_db)
    product_dropdown["values"] = [product[1] for product in products]
    product_dropdown.set("")

    details_frame = tk.Frame(product_frame, bg="#f5f5f5")
    details_frame.grid(row=2, column=0, padx=5, pady=10)

    view_ratings_button = None  # Placeholder for the button

    def handle_dropdown_selection(event=None):
        nonlocal view_ratings_button

        selected_product_name = product_dropdown.get()
        product_code = None

        # Clear details frame
        for widget in details_frame.winfo_children():
            widget.destroy()

        # Display product details
        for product in products:
            if product[1] == selected_product_name:
                product_code = product[0]
                show_product_details(product_code, oracle_conn, mongo_db, details_frame)
                break

        # Update the View Ratings button
        if product_code:
            if not view_ratings_button:
                view_ratings_button = tk.Button(
                    product_frame,
                    text="View Ratings",
                    bg="#0984e3",
                    fg="white",
                    font=("Helvetica", 10, "bold")
                )
                view_ratings_button.grid(row=3, column=0, pady=10)

            # Update the command to use the correct product_code
            view_ratings_button.config(command=lambda: show_product_ratings(product_code))
        else:
            if view_ratings_button:
                view_ratings_button.destroy()
                view_ratings_button = None

    product_dropdown.bind("<<ComboboxSelected>>", handle_dropdown_selection)

    # Input for Cart
    tk.Label(product_frame, text="Quantity:", bg="#f5f5f5").grid(row=4, column=0, padx=5, pady=5)
    quantity_entry = tk.Entry(product_frame)
    quantity_entry.grid(row=5, column=0, padx=5, pady=5)

    def handle_add():
        selected_product_name = product_dropdown.get()
        for product in products:
            if product[1] == selected_product_name:
                product_code = product[0]
                quantity = quantity_entry.get()
                try:
                    quantity = int(quantity)
                    add_to_cart(product_code, quantity, cart, oracle_conn)
                    refresh_cart()
                except ValueError:
                    messagebox.showerror("Error", "Quantity must be a number.")
                break

    tk.Button(
        product_frame,
        text="Add to Cart",
        command=handle_add,
        bg="#27ae60",
        fg="white",
        font=("Helvetica", 10, "bold")
    ).grid(row=6, column=0, pady=10)

    refresh_cart()
    main_window.mainloop()


# Function to open the login window
def open_login_window(root):
    root.withdraw()  # Hide the root window when opening login

    login_window = tk.Toplevel()
    login_window.title("Login")
    login_window.geometry("400x250")
    login_window.configure(bg="#dfe6e9")

    tk.Label(login_window, text="Email", font=("Helvetica", 10), bg="#dfe6e9").pack(pady=5)
    login_email_entry = tk.Entry(login_window)
    login_email_entry.pack()

    tk.Label(login_window, text="Password", font=("Helvetica", 10), bg="#dfe6e9").pack(pady=5)
    login_password_entry = tk.Entry(login_window, show="*")
    login_password_entry.pack()

    login_button = tk.Button(
        login_window, text="Login",
        command=lambda: handle_login(login_email_entry, login_password_entry, login_window, root),
        width=15, bg="#0984e3", fg="white", font=("Helvetica", 10, "bold")
    )
    login_button.pack(pady=10)

# Function to open the registration window
# Function to open the registration window
def open_registration_window(root):
    root.withdraw()  # Hide the root window when opening registration

    registration_window = tk.Toplevel()
    registration_window.title("User Registration")
    registration_window.geometry("400x600")
    registration_window.configure(bg="#dfe6e9")

    tk.Label(registration_window, text="First Name", font=("Helvetica", 10), bg="#dfe6e9").pack()
    first_name_entry = tk.Entry(registration_window)
    first_name_entry.pack()

    tk.Label(registration_window, text="Last Name", font=("Helvetica", 10), bg="#dfe6e9").pack()
    last_name_entry = tk.Entry(registration_window)
    last_name_entry.pack()

    tk.Label(registration_window, text="Email", font=("Helvetica", 10), bg="#dfe6e9").pack()
    email_entry = tk.Entry(registration_window)
    email_entry.pack()

    tk.Label(registration_window, text="Phone", font=("Helvetica", 10), bg="#dfe6e9").pack()
    phone_entry = tk.Entry(registration_window)
    phone_entry.pack()

    tk.Label(registration_window, text="Address", font=("Helvetica", 10), bg="#dfe6e9").pack()
    address_entry = tk.Entry(registration_window)
    address_entry.pack()

    tk.Label(registration_window, text="Date of Birth (YYYY-MM-DD)", font=("Helvetica", 10), bg="#dfe6e9").pack()
    dob_entry = tk.Entry(registration_window)
    dob_entry.pack()

    tk.Label(registration_window, text="Password", font=("Helvetica", 10), bg="#dfe6e9").pack()
    password_entry = tk.Entry(registration_window, show="*")
    password_entry.pack()

    tk.Label(registration_window, text="Role", font=("Helvetica", 10), bg="#dfe6e9").pack()
    role_var = tk.StringVar()
    role_var.set('customer')  # default role
    role_menu = tk.OptionMenu(registration_window, role_var, 'customer', 'warehouse manager', 'delivery order manager', 'manager')
    role_menu.pack()

    register_button = tk.Button(
        registration_window, text="Register",
        command=lambda: handle_register(first_name_entry, last_name_entry, email_entry, phone_entry, address_entry, dob_entry, password_entry, role_var.get(), registration_window, root),
        width=15, bg="#0984e3", fg="white", font=("Helvetica", 10, "bold")
    )
    register_button.pack(pady=20)

# Handle registration, then open the main window
# Handle registration, then open the main window
def handle_register(first_name_entry, last_name_entry, email_entry, phone_entry, address_entry, dob_entry, password_entry, role, registration_window, root):
    first_name = first_name_entry.get().strip()
    last_name = last_name_entry.get().strip()
    email = email_entry.get().strip()
    phone = phone_entry.get().strip()
    address = address_entry.get().strip()
    dob = dob_entry.get().strip()
    password = password_entry.get().strip()

    if not (first_name and last_name and email and password and dob):
        messagebox.showerror("Error", "Please fill in all required fields.")
        return

    # Ensure oracle_conn is passed here
    success = register_user(first_name, last_name, email, phone, address, dob, password, role, oracle_conn)  # Pass role as argument
    if success:
        messagebox.showinfo("Success", "Registration successful. You can now log in.")
        registration_window.destroy()
        root.deiconify()
    else:
        messagebox.showerror("Error", "Registration failed. Please try again.")

# Handle login, then open the main window
def handle_login(email_entry, password_entry, login_window, root):
    email = email_entry.get().strip()
    password = password_entry.get().strip()

    if not (email and password):
        messagebox.showerror("Error", "Email and Password are required.")
        return

    SystemUserCode = login_user(email, password, oracle_conn)
    if SystemUserCode:
        login_window.destroy()
        open_main_window(SystemUserCode)
    else:
        messagebox.showerror("Error", "Invalid credentials. Please try again.")

# Root window with options to go to login or registration
root = tk.Tk()
root.title("Welcome")
root.geometry("400x200")
root.configure(bg="#dfe6e9")

tk.Label(root, text="Welcome to the Shopping System", font=("Helvetica", 14, "bold"), bg="#dfe6e9").pack(pady=20)
login_button = tk.Button(root, text="Login", command=lambda: open_login_window(root), width=15, bg="#74b9ff", fg="white", font=("Helvetica", 10, "bold"))
login_button.pack(pady=10)

register_button = tk.Button(root, text="Register", command=lambda: open_registration_window(root), width=15, bg="#0984e3", fg="white", font=("Helvetica", 10, "bold"))
register_button.pack(pady=10)

root.mainloop()
