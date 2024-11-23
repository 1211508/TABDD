import tkinter as tk
from tkinter import messagebox
from mongoDBConn import connect_mongodb
from SQLConn import connect_oracle
from register_user import register_user, login_user
from cartOperations import add_to_cart, remove_from_cart, view_cart
from checkout import checkout
from feedback import feedback
from tkinter import ttk
from product_details import fetch_product_details

# Establish initial database connections
mongo_db = connect_mongodb()
oracle_conn = connect_oracle()

# Ensure connections are valid
if mongo_db is None or oracle_conn is None:
    exit("Failed to connect to databases.")

def show_product_details(product_code, oracle_conn, mongo_db, details_frame):
    # Buscar os detalhes do produto utilizando a função do arquivo separado
    product_details = fetch_product_details(product_code, oracle_conn, mongo_db)
    
    if product_details:
        # Limpar os detalhes existentes na área de detalhes
        for widget in details_frame.winfo_children():
            widget.destroy()
        
        # Exibir os detalhes do produto
        details = (
            f"Product Code: {product_details['productCode']}\n"
            f"Product Name: {product_details['productName']}\n"
            f"Category: {product_details['category']}\n"
            f"Price: {product_details['price']}\n"
            f"Stock Quantity: {product_details['stockQuantity']}\n"
            f"Supplier: {product_details['supplier']}"
        )
        
        tk.Label(details_frame, text=details, font=("Helvetica", 10), justify="left").pack(pady=10)
    else:
        messagebox.showerror("Error", "Product not found.")

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



""" # Fetch categories from the Category table
def fetch_categories():
    cursor = oracle_conn.cursor()
    categories = []

    try:
        # Fetch unique categories from Category table
        cursor.execute("SELECT DISTINCT name FROM Category")
        categories = [row[0] for row in cursor.fetchall()]

    finally:
        cursor.close()

    return categories
 """
# Function to display products in a new window by category
""" def show_category_products(category_name):
    product_window = tk.Toplevel()
    product_window.title(f"Products in Category: {category_name}")
    product_window.geometry("500x400")

    cursor = oracle_conn.cursor()

    try:
        # Retrieve products linked to the selected category
        cursor.execute(
            SELECT p.productCode, p.productName, p.price, p.stockQuantity 
            FROM Product p
            JOIN Category c ON p.productCode = c.productCode
            WHERE c.name = :cat
        , {"cat": category_name})
        products = cursor.fetchall()

        # Display products if they exist
        if products:
            tk.Label(product_window, text="Products", font=("Helvetica", 12, "bold")).pack(pady=5)
            for product in products:
                productCode, productName, price, stockQuantity = product
                product_info = f"Code: {productCode}, Name: {productName}, Price: {price}, Stock: {stockQuantity}"
                product_button = tk.Button(product_window, text=product_info, command=lambda pc=productCode: show_product_details(pc))
                product_button.pack(anchor="w", padx=10, pady=2)
        else:
            tk.Label(product_window, text="No products found in this category.", font=("Helvetica", 10)).pack(pady=20)

    finally:
        cursor.close()

# Function to show detailed information about a selected product
def show_product_details(product_code):
    detail_window = tk.Toplevel()
    detail_window.title(f"Product Details: Code {product_code}")
    detail_window.geometry("400x300")

    cursor = oracle_conn.cursor()
    cursor.execute(
        SELECT productCode, productName, category, price, stockQuantity, supplier 
        FROM Product 
        WHERE productCode = :code
    , {"code": product_code})
    product = cursor.fetchone()

    if product:
        productCode, productName, category, price, stockQuantity, supplier = product
        details = (
            f"Code: {productCode}\n"
            f"Name: {productName}\n"
            f"Category: {category}\n"
            f"Price: {price}\n"
            f"Stock: {stockQuantity}\n"
            f"Supplier: {supplier}"
        )
        tk.Label(detail_window, text=details, font=("Helvetica", 10), justify="left").pack(pady=10)
    else:
        tk.Label(detail_window, text="Product not found.", font=("Helvetica", 10)).pack(pady=20)

    cursor.close()

# Function to search for products by name
def search_product(search_entry, results_text):
    product_name = search_entry.get()
    cursor = oracle_conn.cursor()
    results_text.delete(1.0, tk.END)

    try:
        # Search in Product table with case-insensitive partial match
        cursor.execute(
            SELECT productCode, productName, category, price, stockQuantity 
            FROM Product 
            WHERE LOWER(productName) LIKE LOWER(:name)
        , {"name": f"%{product_name}%"})
        products = cursor.fetchall()

        if products:
            results_text.insert(tk.END, "Products Found:\n")
            for product in products:
                productCode, productName, category, price, stockQuantity = product
                product_info = f"Code: {productCode}, Name: {productName}, Category: {category}, Price: {price}, Stock: {stockQuantity}"
                results_text.insert(tk.END, f"{product_info}\n")
        else:
            results_text.insert(tk.END, "No products found with that name.\n")

    finally:
        cursor.close()
 """
# Main window setup with category buttons and search functionality
def open_main_window():
    # Conectar ao MongoDB e Oracle
    mongo_db = connect_mongodb()
    oracle_conn = connect_oracle()

    if mongo_db is None or oracle_conn is None:
        exit("Failed to connect to databases.")
    
    main_window = tk.Tk()
    main_window.title("Main Page")
    main_window.geometry("800x600")  # Ajuste o tamanho da janela
    main_window.configure(bg="#f5f5f5")
    
    # Carregar todos os produtos de ambos os bancos de dados
    products = load_all_products(oracle_conn, mongo_db)

    # Barra com o dropdown que exibe todos os produtos disponíveis
    product_dropdown_frame = tk.Frame(main_window, bg="#f5f5f5")
    product_dropdown_frame.pack(pady=20)

    tk.Label(product_dropdown_frame, text="Select a Product", font=("Helvetica", 14, "bold"), bg="#f5f5f5").grid(row=0, column=0, padx=5, pady=5)

    # Dropdown para exibir todos os produtos
    product_dropdown = ttk.Combobox(product_dropdown_frame, width=40)
    product_dropdown.grid(row=1, column=0, padx=5, pady=5)

    # Preencher o dropdown com os produtos encontrados
    product_dropdown['values'] = [product[1] for product in products]
    product_dropdown.set('')  # Limpar seleção anterior
    product_dropdown.product_list = products  # Armazenar lista de produtos no widget

    # Frame para exibir os detalhes do produto abaixo do dropdown
    details_frame = tk.Frame(main_window, bg="#f5f5f5")
    details_frame.pack(pady=10)
    
    # Vincular evento de seleção do produto no dropdown
    product_dropdown.bind("<<ComboboxSelected>>", lambda event: on_product_select(event, product_dropdown, oracle_conn, mongo_db, details_frame))
    
    """ # Sidebar with categories
    tk.Label(main_window, text="Categories", font=("Helvetica", 14, "bold"), bg="#f5f5f5").pack(pady=10, anchor="w")
    sidebar = tk.Frame(main_window, bg="#dfe6e9", width=200, height=400)
    sidebar.pack(side="left", fill="y") """

    # Get categories and add buttons for each category in the sidebar
    """  categories = fetch_categories()
    for category in categories:
        category_button = tk.Button(sidebar, text=category, width=20, command=lambda cat=category: show_category_products(cat))
        category_button.pack(pady=2, padx=5, anchor="w")
    """
    """ # Search Section in main area
    search_frame = tk.Frame(main_window, bg="#f5f5f5")
    search_frame.pack(pady=10)
    
    tk.Label(search_frame, text="Search Products", font=("Helvetica", 14, "bold"), bg="#f5f5f5").grid(row=0, column=0, columnspan=2, pady=5)

    search_entry = tk.Entry(search_frame, width=30)
    search_entry.grid(row=1, column=0, padx=5)

    results_text = tk.Text(main_window, height=10, width=60, bg="#ffffff", font=("Helvetica", 10))
    results_text.pack(pady=10) """

    """ search_button = tk.Button(
        search_frame, text="Search",
        command=lambda: search_product(search_entry, results_text),
        bg="#0984e3", fg="white", font=("Helvetica", 10, "bold")
    )
    search_button.grid(row=1, column=1, padx=5)

    # Cart Management Section
    cart_frame = tk.Frame(main_window, bg="#f5f5f5")
    cart_frame.pack(side="right", expand=True, fill="both")

    tk.Label(cart_frame, text="Shopping Cart", font=("Helvetica", 14, "bold"), bg="#f5f5f5").pack(pady=10)
    
    add_button = tk.Button(cart_frame, text="Add to Cart", command=lambda: add_to_cart(mongo_db), bg="#0984e3", fg="white", font=("Helvetica", 10, "bold"))
    add_button.pack(pady=5)

    remove_button = tk.Button(cart_frame, text="Remove from Cart", command=lambda: remove_from_cart(mongo_db), bg="#d63031", fg="white", font=("Helvetica", 10, "bold"))
    remove_button.pack(pady=5)

    view_cart_button = tk.Button(cart_frame, text="View Cart", command=lambda: view_cart(mongo_db), bg="#74b9ff", fg="white", font=("Helvetica", 10, "bold"))
    view_cart_button.pack(pady=5)

    checkout_button = tk.Button(cart_frame, text="Checkout", command=lambda: checkout(mongo_db), bg="#00b894", fg="white", font=("Helvetica", 10, "bold"))
    checkout_button.pack(pady=5)
 """
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
    first_name = first_name_entry.get()
    last_name = last_name_entry.get()
    email = email_entry.get()
    phone = phone_entry.get()  # Capture the phone number
    address = address_entry.get()  # Capture the address
    dob = dob_entry.get()  # Capture the date of birth
    password = password_entry.get()  # Capture the password

    # Ensure oracle_conn is passed here
    success = register_user(first_name, last_name, email, phone, address, dob, password, role, oracle_conn)  # Pass role as argument
    if success:
        registration_window.destroy()
        open_main_window()


# Handle login, then open the main window
def handle_login(email_entry, password_entry, login_window, root):
    email = email_entry.get()
    password = password_entry.get()

    customer_code = login_user(email, password, oracle_conn)
    if customer_code:
        login_window.destroy()
        open_main_window()

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
