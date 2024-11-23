# product_details.py

import cx_Oracle

def fetch_product_details(product_code, oracle_conn, mongo_db):
    try:
        cursor = oracle_conn.cursor()
        cursor.execute("""
            SELECT productCode, productName, category, price, stockQuantity, supplier
            FROM Product
            WHERE productCode = :code
        """, {"code": product_code})
        
        product = cursor.fetchone()
        
        if product:
            # Return product details as a dictionary
            product_details = {
                "productCode": product[0],
                "productName": product[1],
                "category": product[2],
                "price": product[3],
                "stockQuantity": product[4],
                "supplier": product[5]
            }
            return product_details
        else:
            return None
        
    except Exception as e:
        print(f"Error fetching product details: {e}")
        return None
    finally:
        cursor.close()
