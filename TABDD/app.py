from flask import Flask, render_template, request, redirect, url_for, flash, session
import cx_Oracle
import random

app = Flask(__name__)
app.secret_key = 's3cr3t'  # A chave secreta para sessões

# Função para conectar ao OracleDB
def connect_oracle():
    try:
        dsn = cx_Oracle.makedsn("vsgate-s1.dei.isep.ipp.pt", 10824, service_name="xe")
        oracle_conn = cx_Oracle.connect(user="sys", password="oracle2", dsn=dsn, mode=cx_Oracle.SYSDBA)
        return oracle_conn
    except Exception as e:
        flash(f"Erro ao conectar ao OracleDB: {e}", "error")
        return None

# Rota principal para mostrar todos os produtos e categorias
@app.route('/', methods=['GET'])
def index():
    # Obtém o termo de pesquisa (se existir)
    search_query = request.args.get('search_query', '').lower()

    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()

        # Se houver um termo de pesquisa, ajusta a consulta para filtrar os produtos
        if search_query:
            cursor.execute("""
                SELECT * FROM Product
                WHERE LOWER(productName) LIKE :search_query
            """, {'search_query': f"%{search_query}%"})
        else:
            # Caso contrário, retorna todos os produtos
            cursor.execute("SELECT * FROM Product")

        products = cursor.fetchall()

        cursor.execute("SELECT * FROM Category")  # Selecionando todas as categorias
        categories = cursor.fetchall()

        if 'user_id' in session:
            # Usuário logado, recuperar dados
            user_logged_in = True
            user_name = session.get('user_name')
            user_email = session.get('user_email')
            user_role = session.get('user_role')
            user_dob = session.get('user_dob')

            # Consultar o histórico de encomendas
            cursor.execute("""
                SELECT ordercode, orderdate, totalamount, status, deliveryaddress
                FROM Orders
                WHERE SYSTEMUSERCODE = :user_id
            """, {'user_id': session['user_id']})
            order_history = cursor.fetchall()

            # Consultar encomendas ativas
            cursor.execute("""
                SELECT ordercode, orderdate, totalamount, status, deliveryaddress
                FROM Orders
                WHERE SYSTEMUSERCODE = :user_id AND status = 'pending'
            """, {'user_id': session['user_id']})
            active_orders = cursor.fetchall()

        else:
            # Usuário não logado
            user_logged_in = False
            user_name = None
            user_email = None
            user_role = None
            user_dob = None
            order_history = []
            active_orders = []

        cursor.close()
        oracle_conn.close()

        return render_template('index.html', products=products, categories=categories, user_logged_in=user_logged_in, 
                               user_name=user_name, user_email=user_email, user_role=user_role, 
                               user_dob=user_dob, order_history=order_history, active_orders=active_orders)

    flash("Erro ao conectar ao banco de dados.", "error")
    return redirect(url_for('index'))

# US02: Login de Usuário
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se o usuário já estiver logado, redireciona para a página inicial
    if 'user_id' in session:
        return redirect(url_for('index'))  # Redireciona para a página inicial se já estiver logado

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        oracle_conn = connect_oracle()
        if oracle_conn:
            cursor = oracle_conn.cursor()
            cursor.execute("SELECT * FROM SystemUser WHERE email = :1 AND password = :2", (email, password))
            user = cursor.fetchone()

            if user:
                # Armazenando os dados do usuário na sessão
                session['user_id'] = user[0]  # Código do usuário
                session['user_name'] = user[1]  # Nome do usuário
                session['user_email'] = user[3]  # E-mail do usuário
                session['user_role'] = user[8]  # Role do usuário
                session['user_dob'] = user[7]  # Data de nascimento do usuário
                flash("Login realizado com sucesso!", "success")
                return redirect(url_for('index'))  # Redireciona para a página principal após o login
            else:
                flash("E-mail ou senha incorretos.", "error")
            cursor.close()
            oracle_conn.close()

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Se o usuário já estiver logado, redireciona para a página inicial
    if 'user_id' in session:
        return redirect(url_for('index'))  # Redireciona para a página inicial se já estiver logado

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
                    return redirect(url_for('login'))  # Direciona para a página de login

                cursor.execute("""
                    INSERT INTO SystemUser (systemUserCode, firstName, lastName, email, phone, address, dateOfBirth, password, role)
                    VALUES (:1, :2, :3, :4, :5, :6, TO_DATE(:7, 'YYYY-MM-DD'), :8, :9)
                """, (user_code, first_name, last_name, email, phone, address, dob, password, role))
                
                oracle_conn.commit()  # Confirma a transação

                # Armazenando os dados do usuário na sessão
                session['user_id'] = user_code  # Código do usuário
                session['user_name'] = first_name  # Nome do usuário
                session['user_email'] = email  # E-mail do usuário
                session['user_role'] = role  # Role do usuário
                session['user_dob'] = dob  # Data de nascimento do usuário

                flash('Cadastro realizado com sucesso! Agora você pode fazer login.', 'success')
                return redirect(url_for('index'))  # Redireciona para a página inicial após o registro

            except cx_Oracle.DatabaseError as e:
                flash(f"Erro ao registrar usuário: {e}", 'error')
            finally:
                cursor.close()
                oracle_conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()  # Limpa todas as variáveis da sessão
    flash("Você foi deslogado.", "success")
    return redirect(url_for('index'))  # Redireciona para a página inicial


if __name__ == '__main__':
    app.run(debug=True)
