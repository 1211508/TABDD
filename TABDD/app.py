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
                session['user_role'] = user[8]
                session['user_dob'] = user[7] 
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
    # Gerar accountID aleatório
    account_id = random.randint(1000, 9999)  # Gera um ID entre 1000 e 9999

    # Outros dados do usuário
    first_name = request.form['firstName']
    last_name = request.form['lastName']
    email = request.form['email']
    password = request.form['password']
    phone = request.form['phone']
    address = request.form['address']
    vat_number = request.form['vatNumber']  # Incluindo o campo VAT Number
    dob = request.form['dob']
    role = request.form['role']
    status = 'active'  # Status padrão
    # Aqui você pode obter a data atual para o campo 'dateOfBirth' se for necessário

    user_code = random.randint(1000, 9999)  # Gerar um código de usuário aleatório

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
                INSERT INTO SystemUser (systemUserCode, firstName, lastName, email, phone, address, VATNumber, status, accountID, dateOfBirth, password, role)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, TO_DATE(:10, 'YYYY-MM-DD'), :11, :12)
            """, (user_code, first_name, last_name, email, phone, address, vat_number, status, account_id, dob, password, role))

            oracle_conn.commit()  # Confirma a transação

            session['user_id'] = user_code 
            session['user_name'] = first_name  
            session['user_email'] = email
            session['user_role'] = role 
            session['user_dob'] = dob 

            flash('Cadastro realizado com sucesso! Agora você pode fazer login.', 'success')
            return redirect(url_for('index'))  

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

    quantity = int(quantity) 

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

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'user_id' not in session:
        flash("Por favor, faça login para visualizar o carrinho.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    cart = db_2.cart.find_one({"SystemUserCode": user_id})

    if not cart:
        cart = {"items": [], "total_amount": 0}

    total_price = cart['total_amount']

    if total_price > 2000:
        flash("O valor total do carrinho não pode exceder €2000.", "error")
    
    if request.method == 'POST':
        pass
    
    return render_template('cart.html', cart_items=cart['items'], total_price=total_price)

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

    data = request.get_json() 
    print(f"Dados recebidos: {data}")  

    if 'product_id' not in data or 'quantity' not in data:
        print("Dados ausentes no request.")  # Log
        return jsonify({'success': False, 'message': 'Dados inválidos.'}), 400

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

    try:
        # Ajuste para remover o 'T' e garantir o formato correto
        selected_datetime = selected_datetime.replace('T', ' ')  # Trocar T por espaço
        selected_datetime = datetime.strptime(selected_datetime, '%Y-%m-%d %H:%M')  # Converter para datetime
    except ValueError:
        return jsonify({'error': 'Formato de data e hora inválido.'}), 400

    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()

        cursor.execute("""
            SELECT o.orderCode, o.orderDate, ol.location, ol.timestamp
            FROM OrderLocation ol
            JOIN Orders o ON ol.orderCode = o.orderCode
            WHERE TRUNC(ol.timestamp) = TRUNC(:selected_datetime)
        """, {'selected_datetime': selected_datetime})

        order_locations = cursor.fetchall()
        cursor.close()
        oracle_conn.close()

        if not order_locations:
            return jsonify({'message': 'Nenhuma ordem encontrada para a data e hora selecionadas.'}), 404

        orders_info = []
        for order in order_locations:
            order_code, order_date, location, timestamp = order
            orders_info.append({
                'orderCode': order_code,
                'orderDate': order_date,
                'location': location,
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')  # Formatar o timestamp
            })

        return jsonify({'orders': orders_info})

    return jsonify({'error': 'Erro ao conectar ao banco de dados.'}), 500


@app.route('/manager_purchases', methods=['GET'])
def manager_purchases():
    # Obtenção dos parâmetros do formulário
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    prep_time_comparison = request.args.get('prep_time_comparison')
    days_diff_comparison = request.args.get('days_diff_comparison')

    if not start_date or not end_date:
        return jsonify({'error': 'Faltando intervalo de datas.'}), 400  # Erro mais claro

    # Converte as datas de compra para o formato adequado
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # Definir as condições baseadas nos filtros
    prep_condition = "< 10" if prep_time_comparison == 'less' else ">= 10"
    delivery_days_condition = "> 10" if days_diff_comparison == 'more' else "<= 10"

    # A consulta SQL para buscar as ordens com base nos critérios
    query = f"""
        SELECT o.orderCode, o.orderDate, o.totalAmount, o.status, o.deliveryAddress, 
            o.deliveryDate, o.preparationTime, 
            (o.deliveryDate - o.orderDate) AS daysDifference
        FROM Orders o
        WHERE o.orderDate BETWEEN TO_DATE(:start_date, 'YYYY-MM-DD') AND TO_DATE(:end_date, 'YYYY-MM-DD')
        AND o.preparationTime {prep_condition} 
        AND (o.deliveryDate - o.orderDate) {delivery_days_condition}
    """



    # Conectar ao banco de dados
    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()
        cursor.execute(query, {'start_date': start_date, 'end_date': end_date})
        purchases = cursor.fetchall()

        # Verificar se existem compras que correspondem aos critérios
        if not purchases:
            return jsonify({'message': 'Nenhuma compra encontrada para os critérios selecionados.'}), 200

        # Processar os resultados
        purchases_data = []
        for purchase in purchases:
            purchases_data.append({
                'orderCode': purchase[0],
                'orderDate': purchase[1].strftime('%Y-%m-%d'),
                'totalAmount': purchase[2],
                'status': purchase[3],
                'deliveryAddress': purchase[4],
                'deliveryDate': purchase[5].strftime('%Y-%m-%d') if purchase[5] else None,
                'preparationTime': purchase[6]
            })

        cursor.close()
        oracle_conn.close()

        # Retorna os resultados para o front-end
        return jsonify({'purchases': purchases_data})

    else:
        return jsonify({'error': 'Erro ao conectar ao banco de dados.'}), 500

if __name__ == '__main__':
    app.run(debug=True)