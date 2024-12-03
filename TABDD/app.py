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
    # Verifica se o usuário está logado verificando a chave 'user_id' na sessão
    user_logged_in = False
    user_name = None
    user_email = None
    user_dob = None
    user_role = None

    if 'user_id' in session:  # Se a sessão estiver preenchida com os dados do usuário
        user_logged_in = True
        user_name = session.get('user_name')
        user_email = session.get('user_email')
        user_dob = session.get('user_dob')
        user_role = session.get('user_role')

    # Obtém o termo de pesquisa (se existir)
    search_query = request.args.get('search_query', '').lower()
    category_id = request.args.get('category_id', None)  # ID da categoria (se houver)

    oracle_conn = connect_oracle()
    if oracle_conn:
        cursor = oracle_conn.cursor()

        # Consulta para pegar todas as categorias
        cursor.execute("SELECT * FROM Category")
        categories = cursor.fetchall()

        # Se houver um termo de pesquisa, ajusta a consulta para filtrar os produtos
        if search_query:
            cursor.execute("""
                SELECT * FROM Product
                WHERE LOWER(productName) LIKE :search_query
            """, {'search_query': f"%{search_query}%"})
        elif category_id:
            # Se o usuário clicar em uma categoria, filtra os produtos dessa categoria
            cursor.execute("""
                SELECT * FROM Product
                WHERE categoryCode = :category_id
            """, {'category_id': category_id})
        else:
            # Caso contrário, retorna todos os produtos
            cursor.execute("SELECT * FROM Product")

        products = cursor.fetchall()

        cursor.close()
        oracle_conn.close()

        # Passar os dados para o template
        return render_template('index.html', products=products, categories=categories, user_logged_in=user_logged_in, 
                               user_name=user_name, user_email=user_email, user_dob=user_dob, user_role=user_role)

    flash("Erro ao conectar ao banco de dados.", "error")
    return redirect(url_for('index'))



# US02: Login de Usuário
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
                # Armazenando os dados do usuário na sessão
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
                    INSERT INTO SystemUser (systemUserCode, firstName, lastName, email, phone, address, dateOfBirth, password, role)
                    VALUES (:1, :2, :3, :4, :5, :6, TO_DATE(:7, 'YYYY-MM-DD'), :8, :9)
                """, (user_code, first_name, last_name, email, phone, address, dob, password, role))
                
                oracle_conn.commit()  # Confirma a transação

                # Armazenando os dados na sessão
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

@app.route('/logout')
def logout():
    # Limpar os dados da sessão
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('user_role', None)
    session.pop('user_dob', None)
    flash("Você foi desconectado com sucesso!", "success")
    return redirect(url_for('index'))  # Redireciona para a página principal

if __name__ == '__main__':
    app.run(debug=True)