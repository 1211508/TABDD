from tkinter import messagebox

def add_to_cart(product_code, quantity, cart, oracle_conn):
    try:
        cursor = oracle_conn.cursor()
        cursor.execute("""
            SELECT productCode, productName, price, stockQuantity
            FROM Product
            WHERE productCode = :product_code
        """, {"product_code": product_code})
        product = cursor.fetchone()

        if not product:
            messagebox.showerror("Error", "Product not found.")
            return

        product_code, product_name, price, stock_quantity = product

        if quantity > stock_quantity:
            messagebox.showerror("Error", f"Only {stock_quantity} items in stock.")
            return

        total_price = price * quantity
        current_total = sum(item['total'] for item in cart)

        if current_total + total_price > 2000:
            messagebox.showerror("Error", "Cart total exceeds €2000 limit.")
            return

        cart.append({
            'product_code': product_code,
            'product_name': product_name,
            'quantity': quantity,
            'total': total_price
        })

        messagebox.showinfo("Success", f"Added {quantity} of {product_name} to cart.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        cursor.close()

def checkout(cart, oracle_conn):
    if not cart:
        messagebox.showerror("Error", "Cart is empty.")
        return

    try:
        cursor = oracle_conn.cursor()
        for item in cart:
            cursor.execute("""
                UPDATE Product
                SET stockQuantity = stockQuantity - :quantity
                WHERE productCode = :product_code
            """, {"quantity": item['quantity'], "product_code": item['product_code']})

        oracle_conn.commit()
        cart.clear()
        messagebox.showinfo("Success", "Purchase completed successfully.")
    except Exception as e:
        oracle_conn.rollback()
        messagebox.showerror("Error", str(e))
    finally:
        cursor.close()