from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import cx_Oracle
import random
from datetime import timedelta
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 's3cr3t'  # A chave secreta para sessões
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client['shop']
product_ratings_collection = db['product_rating']

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

# Rota para visualizar o carrinho de compras
@app.route('/cart', methods=['GET', 'POST'])
def cart():
    # Aqui vamos pegar os itens do carrinho, que podem estar na sessão
    cart_items = session.get('cart', [])
    total_price = calculate_cart_total(cart_items)

    # Se o carrinho ultrapassar €2000, não permitimos adicionar mais itens
    if total_price > 2000:
        flash("O valor total do carrinho não pode exceder €2000.", "error")
    
    # Se o usuário tentar adicionar um produto
    if request.method == 'POST':
        product_code = request.form['product_code']
        product_name = request.form['product_name']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        
        # Verificando o valor total do carrinho após adicionar este item
        new_total_price = total_price + (price * quantity)
        if new_total_price <= 2000:
            cart_items.append({
                'product_code': product_code,
                'product_name': product_name,
                'price': price,
                'quantity': quantity
            })
            session['cart'] = cart_items
        else:
            flash("O carrinho ultrapassa o limite de €2000.", "error")
    
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

# Rota principal para mostrar todos os produtos e categorias
@app.route('/', methods=['GET'])
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

        # Consulta para pegar todas as categorias
        cursor.execute("SELECT * FROM Category")
        categories = cursor.fetchall()

        # Pegar as subcategorias
        cursor.execute("SELECT * FROM Subcategory")
        subcategories = cursor.fetchall()

        # Paginando os resultados de produtos
        if search_query:
            cursor.execute("""
                SELECT p.productCode, p.productName, p.subcategory, p.price, p.stockQuantity, p.supplier
                FROM Product p
                WHERE LOWER(p.productName) LIKE :search_query
                ORDER BY p.productCode
                OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY
            """, {'search_query': f"%{search_query}%", 'offset': (page_number - 1) * page_size, 'page_size': page_size})
        elif category_id:
            cursor.execute("""
                SELECT p.productCode, p.productName, p.subcategory, p.price, p.stockQuantity, p.supplier
                FROM Product p
                JOIN Subcategory s ON p.productCode = s.productCode
                WHERE s.categoryCode = :category_id
                ORDER BY p.productCode
                OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY
            """, {'category_id': category_id, 'offset': (page_number - 1) * page_size, 'page_size': page_size})
        elif subcategory_id:
            cursor.execute("""
                SELECT p.productCode, p.productName, p.subcategory, p.price, p.stockQuantity, p.supplier
                FROM Product p
                JOIN Subcategory s ON p.productCode = s.productCode
                WHERE s.subcategoryCode = :subcategory_id
                ORDER BY p.productCode
                OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY
            """, {'subcategory_id': subcategory_id, 'offset': (page_number - 1) * page_size, 'page_size': page_size})
        else:
            cursor.execute("""
                SELECT p.productCode, p.productName, p.subcategory, p.price, p.stockQuantity, p.supplier
                FROM Product p
                ORDER BY p.productCode
                OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY
            """, {'offset': (page_number - 1) * page_size, 'page_size': page_size})

        products = cursor.fetchall()

        # Agora, pegar os atributos físicos e técnicos para cada produto
        physical_attributes = {}
        technical_attributes = {}

        for product in products:
            product_code = product[0]

            # Atributos Físicos
            cursor.execute("""
                SELECT * FROM PhysicalAttributes WHERE productCode = :product_code
            """, {'product_code': product_code})
            physical_attributes[product_code] = cursor.fetchone()

            # Atributos Técnicos
            cursor.execute("""
                SELECT * FROM TechnicalAttributes WHERE productCode = :product_code
            """, {'product_code': product_code})
            technical_attributes[product_code] = cursor.fetchone()

        cursor.close()
        oracle_conn.close()

        return render_template('index.html', products=products, categories=categories, subcategories=subcategories,
                               physical_attributes=physical_attributes, technical_attributes=technical_attributes,
                               user_logged_in=user_logged_in, user_name=user_name, user_email=user_email, 
                               user_dob=user_dob, user_role=user_role, page_number=page_number, page_size=page_size)

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

            cursor.close()
            oracle_conn.close()

            # Passa os dados como JSON para o modal
            return jsonify({
                'productName': product[1],
                'price': product[3],
                'supplier': product[5],
                'stock': product[4],
                'categoryName': product[2],
                'physicalAttributes': physical_attributes,
                'technicalAttributes': technical_attributes
            })

    return jsonify({'error': 'Produto não encontrado.'}), 404

if __name__ == '__main__':
    app.run(debug=True)
