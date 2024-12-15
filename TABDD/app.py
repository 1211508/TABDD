from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import cx_Oracle
import random
from datetime import timedelta
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = 's3cr3t'  # A chave secreta para sessões
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

mongo_client = MongoClient("mongodb://mongoadmin:501c74327eb2366e9b961350@vsgate-s1.dei.isep.ipp.pt:10385/")
db = mongo_client['TABDD_NOSQL']
db_2 = mongo_client['TABDD_CART']
product_ratings_collection = db['productRating']


# Função para conectar ao OracleDB
def connect_oracle():
    try:
        dsn = cx_Oracle.makedsn("vsgate-s1.dei.isep.ipp.pt", 10824, service_name="xe")
        oracle_conn = cx_Oracle.connect(user="sys", password="oracle3", dsn=dsn, mode=cx_Oracle.SYSDBA)
        return oracle_conn
    except Exception as e:
        flash(f"Erro ao conectar ao OracleDB: {e}", "error")
        return None

def validate_user_in_db(user_id):
    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()
        cursor.execute("SELECT * FROM SystemUser WHERE systemUserCode = :1", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        oracle_conn.close()
        return user
    return None

def get_product_ratings(product_code):
    product_ratings = product_ratings_collection.find_one({"productCode": product_code})
    return product_ratings.get("ratings", []) if product_ratings else []
# Função para calcular o valor total do carrinho
def calculate_cart_total(cart_items):
    total = 0
    for item in cart_items:
        total += item['price'] * item['quantity']
    return total

@app.route('/')
def index():
    user_logged_in = False
    user_name = None
    user_email = None
    user_dob = None
    user_role = None

    if 'user_id' in session:
        user_id = session['user_id']
        
        user = validate_user_in_db(user_id)
        
        if user: 
            user_logged_in = True
            user_name = session.get('user_name')
            user_email = session.get('user_email')
            user_dob = session.get('user_dob')
            user_role = session.get('user_role')
        else:
            session.clear()  # Limpa todos os dados da sessão
            flash("Seu login não é válido. Por favor, faça login novamente.", "error")
            return redirect(url_for('index'))  # Redireciona para a página inicial imediatamente

    search_query = request.args.get('search_query', '').lower()
    category_id = request.args.get('category_id', None)  # ID da categoria (se houver)
    subcategory_id = request.args.get('subcategory_id', None)  # ID da subcategoria (se houver)
    page_number = request.args.get('page', 1, type=int)
    page_size = 16  # Número de produtos por página

    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()

        search_query = request.args.get('search_query', '').lower()
        query = """
            SELECT productCode, productName, price, stockQuantity, supplierCode
            FROM Product
            WHERE LOWER(productName) LIKE :search_query
            ORDER BY productCode
            OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY
        """

        cursor.execute(query, {
            'search_query': f'%{search_query}%', 
            'offset': (page_number - 1) * page_size, 
            'page_size': page_size
        })
        products = cursor.fetchall()

        cursor.close()
        oracle_conn.close()

        products_data = []
        for product in products:
            products_data.append({
                "productCode": product[0],
                "productName": product[1],
                "price": product[2],
                "stockQuantity": product[3],
                "supplierCode": product[4]
            })

        return render_template('index.html', products=products_data, user_logged_in=user_logged_in,
                               user_name=user_name, user_email=user_email, user_dob=user_dob, user_role=user_role,
                               page_number=page_number, page_size=page_size)

    flash("Erro ao conectar à base de dados.", "error")
    return redirect(url_for('index'))

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        oracle_conn = connect_oracle()
        if oracle_conn:
            cursor = oracle_conn.cursor()
            cursor.execute("SELECT * FROM SystemUser WHERE email = :1 AND password = :2", (email, password))
            user = cursor.fetchone()

            if user:
                session.permanent = False
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['user_email'] = user[3]
                session['user_role'] = user[11]
                session['user_dob'] = user[10] 
                flash("Login realizado com sucesso!", "success")
                return redirect(url_for('index'))  
            else:
                flash("E-mail ou senha incorretos.", "error")
            cursor.close()
            oracle_conn.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Limpa todos os dados da sessão
    flash("Você foi desconectado com sucesso!", "success")
    return redirect(url_for('index'))  # Redireciona para a página principal

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Dados do formulário
        account_id = random.randint(1000, 9999)
        user_code = random.randint(1000, 9999)
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        vat_number = request.form['vatNumber']
        dob = request.form['dob']
        role = request.form['role']
        status = 'active'

        oracle_conn = connect_oracle()
        if oracle_conn:
            cursor = oracle_conn.cursor()
            try:
                # Verificar se o e-mail já existe
                cursor.execute("SELECT * FROM SystemUser WHERE email = :1", (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    flash("Este e-mail já está registrado. Por favor, faça o login.", "error")
                    return redirect(url_for('login'))

                # Inserir o novo usuário no banco de dados
                cursor.execute("""
                    INSERT INTO SystemUser (systemUserCode, firstName, lastName, email, phone, address, VATNumber, status, accountID, dateOfBirth, password, role)
                    VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, TO_DATE(:10, 'YYYY-MM-DD'), :11, :12)
                """, (user_code, first_name, last_name, email, phone, address, vat_number, status, account_id, dob, password, role))

                oracle_conn.commit()

                # Definir os dados na sessão
                session['user_id'] = user_code
                session['user_name'] = first_name
                session['user_email'] = email
                session['user_role'] = role
                session['user_dob'] = dob

                flash('Cadastro realizado com sucesso! Por favor, aceite os termos de GDPR.', 'success')

                # Redirecionar para a página de GDPR
                return redirect(url_for('gdpr_popup'))

            except cx_Oracle.DatabaseError as e:
                flash(f"Erro ao registrar usuário: {e}", 'error')
            finally:
                cursor.close()
                oracle_conn.close()

    return render_template('register.html')


@app.route('/product_details/<int:product_id>', methods=['GET'])
def product_details(product_id):
    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()

        # Recupera os dados do produto
        cursor.execute("""
            SELECT productCode, productName, subcategoryCode, price, stockQuantity, supplierCode
            FROM Product WHERE productCode = :product_id
        """, {'product_id': product_id})
        product = cursor.fetchone()

        if product:
            # Recupera os atributos físicos do produto
            cursor.execute("""
                SELECT color, weight, height, width, depth
                FROM PhysicalAttributes WHERE productCode = :product_id
            """, {'product_id': product_id})
            physical_attributes = cursor.fetchone()

            # Se não houver atributos físicos, define valores padrão
            if not physical_attributes:
                physical_attributes = {
                    'color': 'Não disponível',
                    'weight': 'Não disponível',
                    'height': 'Não disponível',
                    'width': 'Não disponível',
                    'depth': 'Não disponível'
                }

            # Recupera os atributos técnicos do produto
            cursor.execute("""
                SELECT processor, ram, storage, batteryLife, warranty
                FROM TechnicalAttributes WHERE productCode = :product_id
            """, {'product_id': product_id})
            technical_attributes = cursor.fetchone()

            # Se não houver atributos técnicos, define valores padrão
            if not technical_attributes:
                technical_attributes = {
                    'processor': 'Não disponível',
                    'ram': 'Não disponível',
                    'storage': 'Não disponível',
                    'batteryLife': 'Não disponível',
                    'warranty': 'Não disponível'
                }

            # Recupera as avaliações do produto
            ratings = get_product_ratings(product_id)

            cursor.close()
            oracle_conn.close()

            # Organiza os dados do produto para passar ao template
            product_data = {
                'productName': product[1],
                'categoryName': product[2],
                'price': product[3],
                'supplierCode': product[5],
                'stock': product[4],
                'physicalAttributes': physical_attributes,
                'technicalAttributes': technical_attributes,
                'ratings': ratings
            }

            # Passa os dados para o template
            return jsonify(product_data)  # Retorne como JSON

    # Caso o produto não seja encontrado
    return jsonify({'error': 'Produto não encontrado.'}), 404

@app.route('/get_reviews/<int:product_id>', methods=['GET'])
def get_reviews(product_id):
    product_ratings = product_ratings_collection.find_one({"productCode": product_id})
    
    if product_ratings:
        reviews = product_ratings.get("ratings", [])
        return jsonify({'reviews': reviews})
    else:
        return jsonify({'reviews': []}), 404

def add_to_cart(SystemUserCode, productCode, productName, price, quantity):
    print(f"Buscando carrinho para o usuário {SystemUserCode} no MongoDB.")  # Log de início
    cart = db_2.cart.find_one({"SystemUserCode": SystemUserCode})

    if not cart:
        print("Carrinho não encontrado. Criando um novo carrinho.")  # Log
        cart = {
            "SystemUserCode": SystemUserCode,
            "items": [],
            "total_amount": 0
        }
        db_2.cart.insert_one(cart)

    # Certifique-se de que quantity seja um número (int)
    quantity = int(quantity)  # Converte quantity para inteiro

    # Verificar se o produto já está no carrinho
    product_found = False
    for item in cart['items']:
        if item['productCode'] == productCode:
            item['quantity'] += quantity
            item['total_price'] = item['quantity'] * price
            product_found = True
            print(f"Produto encontrado no carrinho. Quantidade atualizada: {item['quantity']}")  # Log
            break

    if not product_found:
        cart['items'].append({
            "productCode": productCode,
            "productName": productName,
            "quantity": quantity,
            "price": price,
            "total_price": price * quantity
        })
        print(f"Produto {productName} adicionado ao carrinho.")  # Log

    cart['total_amount'] = sum(item['total_price'] for item in cart['items'])
    print(f"Carrinho atualizado. Total do carrinho: €{cart['total_amount']}")  # Log

    # Verificar se o total excede €2000
    if cart['total_amount'] > 2000:
        print("Carrinho excede €2000. Não foi adicionado.")  # Log
        return None

    print(f"Atualizando carrinho para o usuário {SystemUserCode}. Carrinho: {cart}")
    result = db_2.cart.update_one(
        {"SystemUserCode": SystemUserCode},
        {"$set": cart},
        upsert=True
    )
    print(f"Resultado da operação de atualização: {result}")
    print("Carrinho atualizado no MongoDB.")  # Log
    return cart


def remove_cart_if_empty(SystemUserCode):
    cart = db_2.cart.find_one({"SystemUserCode": SystemUserCode})

    if cart and len(cart['items']) == 0:
        db_2.cart.delete_one({"SystemUserCode": SystemUserCode})
        return True
    return False

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        flash("Por favor, faça login para alterar o carrinho.", "error")
        return redirect(url_for('login'))

    product_code = request.form['product_code']
    quantity = int(request.form['quantity'])

    cart = db_2.cart.find_one({"SystemUserCode": session['user_id']})

    if cart:
        for item in cart['items']:
            if item['productCode'] == product_code:
                if item['quantity'] <= quantity:
                    cart['items'].remove(item)
                    print(f"Produto {item['productName']} removido completamente do carrinho.")
                else:
                    item['quantity'] -= quantity
                    item['total_price'] = item['quantity'] * item['price']
                    print(f"Quantidade do produto {item['productName']} reduzida em {quantity} unidades.")
                break

        cart['total_amount'] = sum(item['total_price'] for item in cart['items'])
        db_2.cart.update_one({"SystemUserCode": session['user_id']}, {"$set": cart})

        flash("Carrinho atualizado.", "success")
    else:
        flash("Carrinho não encontrado.", "error")

    return redirect(url_for('cart'))

@app.route('/cart', methods=['GET'])
def cart():
    if 'user_id' not in session:
        flash("Por favor, faça login para acessar o carrinho.", "error")
        return redirect(url_for('login'))
 
    cart = db_2.cart.find_one({"SystemUserCode": session['user_id']})
    cart_items = cart['items'] if cart else []
    total_price = cart['total_amount'] if cart else 0
 
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)
@app.route('/cart_data', methods=['GET'])
def cart_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401

    user_id = session['user_id']
    
    cart = db_2.cart.find_one({"SystemUserCode": user_id})
    
    if not cart:
        cart = {"items": [], "total_amount": 0}

    return jsonify({
        'items': cart['items'],
        'total_amount': cart['total_amount']
    })

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart_route():
    if 'user_id' not in session:
        flash("Por favor, faça login para adicionar produtos ao carrinho.", "error")
        return redirect(url_for('login'))

    data = request.get_json()  # Recebe os dados em formato JSON
    print(f"Dados recebidos: {data}")  # Log para ver os dados recebidos no backend

    # Verificar se todos os dados necessários estão presentes
    if 'product_id' not in data or 'quantity' not in data:
        print("Dados ausentes no request.")  # Log
        return jsonify({'success': False, 'message': 'Dados inválidos.'}), 400

    # Conectar ao banco de dados e verificar o produto
    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()
        cursor.execute("SELECT productName, price FROM Product WHERE productCode = :product_id", {'product_id': data['product_id']})
        product = cursor.fetchone()
        if not product:
            print("Produto não encontrado no banco de dados.")  # Log
            return jsonify({'success': False, 'message': 'Produto não encontrado.'}), 404
        cursor.close()
        oracle_conn.close()

        # Adicionar o produto ao carrinho
        cart = add_to_cart(session['user_id'], data['product_id'], product[0], product[1], data['quantity'])
        if not cart:
            return jsonify({'success': False, 'message': 'O valor total do carrinho excede o limite de €2000.'}), 400

        return jsonify({'success': True, 'message': 'Produto adicionado ao carrinho!'}), 200

    return jsonify({'success': False, 'message': 'Erro ao adicionar produto ao carrinho.'}), 500

@app.route('/order_locations', methods=['GET'])
def order_locations():
    if 'user_role' not in session or session['user_role'] != 'delivery order manager':
        return jsonify({'error': 'Você não tem permissão para acessar essa página.'}), 403

    selected_datetime = request.args.get('selected_datetime')
    if not selected_datetime:
        return jsonify({'error': 'Data e hora não fornecidas.'}), 400

    try:
        # Ajuste o formato da data e hora recebida
        selected_datetime = selected_datetime.replace('T', ' ')
        selected_datetime = datetime.strptime(selected_datetime, '%Y-%m-%d %H:%M')
    except ValueError:
        return jsonify({'error': 'Formato de data e hora inválido.'}), 400

    oracle_conn = connect_oracle()
    if not oracle_conn:
        return jsonify({'error': 'Erro ao conectar ao banco de dados.'}), 500

    cursor = oracle_conn.cursor()
    query = """
        SELECT o.orderCode, o.orderDate, ol.location, ol.timestamp
        FROM OrderLocation ol
        JOIN Orders o ON ol.orderCode = o.orderCode
        WHERE TRUNC(ol.timestamp) = TRUNC(:selected_datetime)
    """
    cursor.execute(query, {'selected_datetime': selected_datetime})
    order_locations = cursor.fetchall()

    cursor.close()
    oracle_conn.close()

    if not order_locations:
        return jsonify({'message': 'Nenhuma ordem encontrada para a data e hora selecionadas.'}), 404

    orders_info = [
        {
            'orderCode': order[0],
            'orderDate': order[1],
            'location': order[2],
            'timestamp': order[3].strftime('%Y-%m-%d %H:%M:%S')
        }
        for order in order_locations
    ]

    return jsonify({'orders': orders_info})

def manager_purchases(start_date, end_date, prep_time_comparison, days_diff_comparison):
    # Construa as condições dinamicamente
    prep_time_condition = "< 10" if prep_time_comparison == "less" else ">= 10"
    days_diff_condition = "> 10" if days_diff_comparison == "more" else "<= 10"

    # Query SQL
    query = f"""
        SELECT o.orderCode, o.orderDate, o.totalAmount, o.status, o.deliveryAddress,
               o.deliveryDate, o.preparationTime,
               (o.deliveryDate - o.orderDate) AS daysDifference
        FROM Orders o
        WHERE o.orderDate BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD')
          AND o.preparationTime {prep_time_condition}
          AND (o.deliveryDate - o.orderDate) {days_diff_condition}
    """
    
    # Print da query final (log para depuração)
    print("Query Executada:", query)

    # Conectar ao banco e executar a query
    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()
        try:
            cursor.execute(query)  # Sem parâmetros, pois eles já foram inseridos acima

            # Processar resultados
            purchases = cursor.fetchall()
            print(purchases)
            purchases_data = []
            for purchase in purchases:
                purchases_data.append({
                    'orderCode': purchase[0],
                    'orderDate': purchase[1].strftime('%Y-%m-%d'),
                    'totalAmount': purchase[2],
                    'status': purchase[3],
                    'deliveryAddress': purchase[4],
                    'deliveryDate': purchase[5].strftime('%Y-%m-%d') if purchase[5] else None,
                    'preparationTime': purchase[6],
                    'daysDifference': purchase[7]
                })
            return {"purchases": purchases_data} if purchases_data else {"message": "Nenhuma compra encontrada."}

        finally:
            cursor.close()
            oracle_conn.close()

    return {"error": "Erro ao conectar ao banco de dados."}

@app.route('/manager_purchases', methods=['GET'])
def manager_purchases_route():
    # Obtenha os parâmetros da URL
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    prep_time_comparison = request.args.get('prep_time_comparison')
    days_diff_comparison = request.args.get('days_diff_comparison')

    # Validação dos parâmetros
    if not all([start_date, end_date, prep_time_comparison, days_diff_comparison]):
        return jsonify({'error': 'Parâmetros ausentes ou inválidos.'}), 400

    # Chame a função principal
    result = manager_purchases(
        start_date=start_date,
        end_date=end_date,
        prep_time_comparison=prep_time_comparison,
        days_diff_comparison=days_diff_comparison
    )

    # Log e retorno do resultado
    print("Resultado retornado pela função:", result)  # Log no terminal
    return jsonify(result), 200

@app.route('/gdpr_popup', methods=['GET', 'POST'])
def gdpr_popup():
    if 'user_id' not in session:
        flash("Você precisa fazer login para acessar esta página.", "error")
        return redirect(url_for('login'))  # Verifique a existência da sessão

    if request.method == 'POST':
        user_id = session['user_id']
        try:
            consents = request.json.get('consents', [])
            if not consents:
                return jsonify({'success': False, 'message': 'Nenhum consentimento fornecido.'}), 400

            # Inserir os consentimentos no MongoDB
            db.GDPR.update_one(
                {"SystemUserCode": user_id},
                {
                    "$set": {"SystemUserCode": user_id},
                    "$push": {"consent": {"$each": consents}}
                },
                upsert=True
            )
            flash("Consentimento salvo com sucesso.", "success")
            return jsonify({'success': True, 'message': 'Consentimentos registrados com sucesso.'}), 200

        except Exception as e:
            return jsonify({'success': False, 'message': f"Erro ao salvar consentimentos: {str(e)}"}), 500

    return render_template('gdpr_popup.html')

if __name__ == '__main__':
    app.run(debug=True)