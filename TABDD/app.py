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

# Função para validar se o usuário ainda existe na base de dados
def validate_user_in_db(user_id):
    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()
        cursor.execute("SELECT * FROM SystemUser WHERE SystemUserCode = :1", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        oracle_conn.close()
        return user
    return None

def get_product_ratings(product_code):
    # Buscar as classificações dos produtos
    product_ratings = product_ratings_collection.find_one({"productCode": product_code})
    return product_ratings.get("ratings", []) if product_ratings else []

# Função para calcular o valor total do carrinho
def calculate_cart_total(cart_items):
    total = 0
    for item in cart_items:
        total += item['price'] * item['quantity']
    return total

# Verifique se os produtos estão sendo passados corretamente
@app.route('/')
def index():
    user_logged_in = False
    user_name = None
    user_email = None
    user_dob = None
    user_role = None

    # Verifica se o usuário está logado
    if 'user_id' in session:
        user_id = session['user_id']
        
        # Verifica se o usuário ainda existe na base de dados
        user = validate_user_in_db(user_id)
        
        if user:  # Se o usuário existe, mantém a sessão
            user_logged_in = True
            user_name = session.get('user_name')
            user_email = session.get('user_email')
            user_dob = session.get('user_dob')
            user_role = session.get('user_role')
        else:
            # Se o usuário não existe, limpa a sessão
            session.clear()  # Limpa todos os dados da sessão
            flash("Seu login não é válido. Por favor, faça login novamente.", "error")
            return redirect(url_for('index'))  # Redireciona para a página inicial imediatamente

    # Obtém o termo de pesquisa (se existir)
    search_query = request.args.get('search_query', '').lower()
    category_id = request.args.get('category_id', None)  # ID da categoria (se houver)
    subcategory_id = request.args.get('subcategory_id', None)  # ID da subcategoria (se houver)
    page_number = request.args.get('page', 1, type=int)
    page_size = 10  # Número de produtos por página

    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()

        # Consulta para pegar todos os produtos
        query = """
            SELECT productCode, productName, price, stockQuantity, supplier
            FROM Product
            ORDER BY productCode
            OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY
        """
        
        cursor.execute(query, {'offset': (page_number - 1) * page_size, 'page_size': page_size})
        products = cursor.fetchall()

        cursor.close()
        oracle_conn.close()

        # Converter a lista de tuplas em uma lista de dicionários
        products_data = []
        for product in products:
            products_data.append({
                "productCode": product[0],
                "productName": product[1],
                "price": product[2],
                "stockQuantity": product[3],
                "supplier": product[4]
            })

        # Agora, passando corretamente a variável 'products_data' para o template
        return render_template('index.html', products=products_data, user_logged_in=user_logged_in,
                               user_name=user_name, user_email=user_email, user_dob=user_dob, user_role=user_role,
                               page_number=page_number, page_size=page_size)

    flash("Erro ao conectar ao banco de dados.", "error")
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
                session['user_id'] = user[0]  # Código do usuário
                session['user_name'] = user[1]  # Nome do usuário
                session['user_email'] = user[3]  # E-mail do usuário
                session['user_role'] = user[8]  # Role do usuário
                session['user_dob'] = user[7]  # Data de nascimento do usuário
                flash("Login realizado com sucesso!", "success")
                return redirect(url_for('index'))  # Redireciona para a página principal
            else:
                flash("E-mail ou senha incorretos.", "error")
            cursor.close()
            oracle_conn.close()
    return render_template('login.html')

# Rota de logout
@app.route('/logout')
def logout():
    session.clear()  # Limpa todos os dados da sessão
    flash("Você foi desconectado com sucesso!", "success")
    return redirect(url_for('index'))  # Redireciona para a página principal

# Rota de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        dob = request.form['dob']
        role = request.form['role']

        user_code = random.randint(1000, 9999)

        oracle_conn = connect_oracle()
        if oracle_conn:
            cursor = oracle_conn.cursor()
            try:
                cursor.execute("SELECT * FROM SystemUser WHERE email = :1", (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    flash("Este e-mail já está registrado. Por favor, faça o login.", "error")
                    return redirect(url_for('login'))

                cursor.execute("""
                    INSERT INTO SystemUser (SystemUserCode, firstName, lastName, email, phone, address, dateOfBirth, password, role)
                    VALUES (:1, :2, :3, :4, :5, :6, TO_DATE(:7, 'YYYY-MM-DD'), :8, :9)
                """, (user_code, first_name, last_name, email, phone, address, dob, password, role))
                
                oracle_conn.commit()  # Confirma a transação

                session['user_id'] = user_code  # Código do usuário
                session['user_name'] = first_name  # Nome do usuário
                session['user_email'] = email  # E-mail do usuário
                session['user_role'] = role  # Role do usuário
                session['user_dob'] = dob  # Data de nascimento do usuário

                flash('Cadastro realizado com sucesso! Agora você pode fazer login.', 'success')
                return redirect(url_for('index'))  # Redireciona para a página inicial

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

        # Buscar os dados do produto
        cursor.execute("""
            SELECT productCode, productName, subcategory, price, stockQuantity, supplier
            FROM Product WHERE productCode = :product_id
        """, {'product_id': product_id})
        product = cursor.fetchone()

        if product:
            # Buscar os atributos físicos
            cursor.execute("""
                SELECT color, weight, height, width, depth
                FROM PhysicalAttributes WHERE productCode = :product_id
            """, {'product_id': product_id})
            physical_attributes = cursor.fetchone()

            # Se não encontrar, atribuir valores padrão
            if not physical_attributes:
                physical_attributes = {
                    'color': 'Não disponível',
                    'weight': 'Não disponível',
                    'height': 'Não disponível',
                    'width': 'Não disponível',
                    'depth': 'Não disponível'
                }

            # Buscar os atributos técnicos
            cursor.execute("""
                SELECT processor, ram, storage, batteryLife, warranty
                FROM TechnicalAttributes WHERE productCode = :product_id
            """, {'product_id': product_id})
            technical_attributes = cursor.fetchone()

            # Se não encontrar, atribuir valores padrão
            if not technical_attributes:
                technical_attributes = {
                    'processor': 'Não disponível',
                    'ram': 'Não disponível',
                    'storage': 'Não disponível',
                    'batteryLife': 'Não disponível',
                    'warranty': 'Não disponível'
                }

            # Obter as avaliações do produto
            ratings = get_product_ratings(product_id)

            cursor.close()
            oracle_conn.close()

            # Passa os dados para o frontend
            return jsonify({
                'productName': product[1],
                'price': product[3],
                'supplier': product[5],
                'stock': product[4],
                'categoryName': product[2],
                'physicalAttributes': physical_attributes,
                'technicalAttributes': technical_attributes,
                'ratings': ratings
            })

    return jsonify({'error': 'Produto não encontrado.'}), 404

# Rota para recuperar as avaliações de um produto
@app.route('/get_reviews/<int:product_id>', methods=['GET'])
def get_reviews(product_id):
    # Buscar as classificações dos produtos no MongoDB
    product_ratings = product_ratings_collection.find_one({"productCode": product_id})
    
    # Se o produto tiver avaliações
    if product_ratings:
        reviews = product_ratings.get("ratings", [])
        return jsonify({'reviews': reviews})
    else:
        return jsonify({'reviews': []}), 404

# Função para adicionar produto ao carrinho no MongoDB
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


# Função para remover o carrinho se estiver vazio
def remove_cart_if_empty(SystemUserCode):
    # Buscar o carrinho do usuário
    cart = db_2.cart.find_one({"SystemUserCode": SystemUserCode})

    if cart and len(cart['items']) == 0:
        # Se o carrinho estiver vazio, removemos
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

    # Recuperar o carrinho do MongoDB
    cart = db_2.cart.find_one({"SystemUserCode": session['user_id']})

    if cart:
        # Procurar o item no carrinho
        for item in cart['items']:
            if item['productCode'] == product_code:
                # Se o item foi encontrado
                if item['quantity'] <= quantity:
                    # Remover o item completamente
                    cart['items'].remove(item)
                    print(f"Produto {item['productName']} removido completamente do carrinho.")
                else:
                    # Remover a quantidade específica
                    item['quantity'] -= quantity
                    item['total_price'] = item['quantity'] * item['price']
                    print(f"Quantidade do produto {item['productName']} reduzida em {quantity} unidades.")
                break

        # Atualizar o carrinho no MongoDB
        cart['total_amount'] = sum(item['total_price'] for item in cart['items'])
        db_2.cart.update_one({"SystemUserCode": session['user_id']}, {"$set": cart})

        flash("Carrinho atualizado.", "success")
    else:
        flash("Carrinho não encontrado.", "error")

    return redirect(url_for('cart'))

# Rota para visualizar o carrinho de compras
@app.route('/cart', methods=['GET', 'POST'])
def cart():
    # Verifica se o usuário está logado
    if 'user_id' not in session:
        flash("Por favor, faça login para visualizar o carrinho.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    # Buscar o carrinho no MongoDB
    cart = db_2.cart.find_one({"SystemUserCode": user_id})

    # Se o carrinho não existir
    if not cart:
        cart = {"items": [], "total_amount": 0}

    # Calcula o total do carrinho
    total_price = cart['total_amount']

    # Se o carrinho ultrapassar €2000, não permitimos adicionar mais itens
    if total_price > 2000:
        flash("O valor total do carrinho não pode exceder €2000.", "error")
    
    if request.method == 'POST':
        # Aqui você pode adicionar um produto no carrinho, similar ao add_to_cart_route
        pass
    
    return render_template('cart.html', cart_items=cart['items'], total_price=total_price)

@app.route('/cart_data', methods=['GET'])
def cart_data():
    # Verificar se o usuário está logado
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401

    user_id = session['user_id']
    
    # Recuperar o carrinho do banco de dados ou sessão
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
        flash("Você não tem permissão para acessar essa página.", "error")
        return redirect(url_for('index'))

    selected_datetime = request.args.get('selected_datetime')

    # Converte para o formato datetime
    try:
        selected_datetime = datetime.strptime(selected_datetime, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'error': 'Formato de data e hora inválido.'}), 400

    # Conectar ao banco de dados Oracle
    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()

        # Buscar as ordens e localizações para a data e hora fornecida
        cursor.execute("""
            SELECT o.orderCode, o.orderDate, ol.location, ol.timestamp
            FROM Orders o
            JOIN OrderLocation ol ON o.orderCode = ol.orderCode
            WHERE ol.timestamp = :selected_datetime
        """, {'selected_datetime': selected_datetime})

        order_locations = cursor.fetchall()

        cursor.close()
        oracle_conn.close()

        # Preparar os dados para o frontend
        orders = []
        for order in order_locations:
            orders.append({
                'orderCode': order[0],
                'orderDate': order[1].strftime('%Y-%m-%d %H:%M:%S'),
                'location': order[2],
                'timestamp': order[3].strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify({'orders': orders})

    return jsonify({'error': 'Erro ao conectar ao banco de dados.'}), 500

if __name__ == '__main__':
    app.run(debug=True)