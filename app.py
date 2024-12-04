from flask import Flask, render_template, request, session, redirect
from models.db import execute_query  # Використовується для роботи з БД

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Обов'язково додайте секретний ключ для сесій

# Логін користувача
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # Рендеринг сторінки без помилок
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    # Перевірка, чи існує користувач
    user = execute_query(
        "SELECT * FROM users WHERE username = %s",
        (username,),
        fetch=True
    )
    if not user:
        # Помилка: користувача не знайдено
        return render_template('login.html', error="Ім'я користувача не знайдено")

    # Перевірка пароля
    if user[0]['password'] != password:
        # Помилка: неправильний пароль
        return render_template('login.html', error="Неправильний пароль")

    # Успішний вхід
    session['user_id'] = user[0]['user_id']
    session['username'] = user[0]['username']
    return redirect('/')





# Фільтрація голосувань користувача
@app.route('/user-polls')
def user_created_polls():
    user_id = session.get('user_id')  # Отримуємо ID користувача з сесії
    if not user_id:
        return redirect('/login')  # Якщо користувач не увійшов, перенаправляємо на логін

    # Запит для отримання створених голосувань
    created_polls = execute_query(
    "SELECT * FROM polls WHERE created_by = %s",
    (session['user_id'],),
    fetch=True
)


    # Запит для отримання голосувань, в яких користувач брав участь
    participated_polls = execute_query(
        """
        SELECT DISTINCT p.poll_id, p.question 
        FROM polls p
        JOIN votes v ON p.poll_id = v.poll_id
        WHERE v.user_id = %s
        """,
        (user_id,),
        fetch=True
    )

    return render_template(
        'user_polls.html', 
        created_polls=created_polls, 
        participated_polls=participated_polls
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Перевірка унікальності email
        existing_user = execute_query(
            "SELECT * FROM users WHERE email = %s",
            (email,),
            fetch=True
        )
        if existing_user:
            return "<h1>Email вже використовується. Спробуйте інший.</h1>"

        # Додати користувача до БД
        execute_query(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, password)
        )
        return redirect('/login')
    return render_template('register.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Очищаємо всі дані сесії
    return redirect('/')  # Повертаємося на головну сторінку



# Головна сторінка
@app.route('/')
def home():
    return render_template('home.html')

# Створення голосування
@app.route('/create')
def create():
    return render_template('create.html')

@app.route('/create_poll', methods=['POST'])
def create_poll():
    if not session.get('user_id'):  # Перевірка, чи користувач авторизований
        return redirect('/login')

    question = request.form['question']
    options = request.form['options'].split(',')

    # Додаємо опитування в БД
    poll_id = execute_query(
        "INSERT INTO polls (question, created_by) VALUES (%s, %s)",
        (question, session['user_id'])
    ).lastrowid

    # Додаємо варіанти відповідей
    for option in options:
        execute_query(
            "INSERT INTO options (poll_id, option_text) VALUES (%s, %s)",
            (poll_id, option.strip())
        )

    return redirect('/user-polls')



# Проведення голосування
@app.route('/vote', methods=['GET'])
def vote():
    try:
        polls = execute_query("SELECT * FROM polls", fetch=True)
        return render_template('vote.html', polls=polls)
    except Exception as e:
        return f'<h1>Помилка:</h1><p>{str(e)}</p>'


@app.route('/vote/<int:poll_id>', methods=['GET', 'POST'])
def vote_poll(poll_id):
    if request.method == 'POST':
        try:
            selected_option = request.form['option']
            voter_ip = request.remote_addr  # Отримуємо IP користувача

            # Отримати ID користувача із сесії
            user_id = session.get('user_id')

            # Перевірити, чи користувач увійшов у систему
            if not user_id:
                return redirect('/login')  # Перенаправлення на сторінку логіну, якщо користувач не авторизований

            # Додати голос у таблицю votes
            execute_query(
                "INSERT INTO votes (poll_id, option_id, voter_ip, user_id) VALUES (%s, %s, %s, %s)",
                (poll_id, selected_option, voter_ip, user_id)
            )
            return render_template('success.html', message="Ваш голос враховано!")
        except Exception as e:
            return f'<h1>Помилка:</h1><p>{str(e)}</p>'

    try:
        # Отримати опитування та варіанти
        poll = execute_query("SELECT * FROM polls WHERE poll_id = %s", (poll_id,), fetch=True)[0]
        options = execute_query("SELECT * FROM options WHERE poll_id = %s", (poll_id,), fetch=True)

        return render_template('poll_detail.html', poll=poll, options=options)
    except Exception as e:
        return f'<h1>Помилка:</h1><p>{str(e)}</p>'






# Сторінка зі списком голосувань для редагування
@app.route('/edit', methods=['GET'])
def edit():
    try:
        polls = execute_query("SELECT poll_id, question FROM polls", fetch=True)
        if not polls:  # Якщо немає опитувань
            return render_template('edit.html', polls=[])
        return render_template('edit.html', polls=polls)
    except Exception as e:
        return f"<h1>Помилка:</h1><p>{str(e)}</p>"



# Сторінка для редагування конкретного голосування
@app.route('/edit/<int:poll_id>', methods=['GET'])
def edit_poll(poll_id):
    try:
        # Fetch poll details
        poll_query = "SELECT poll_id, question FROM polls WHERE poll_id = %s"
        poll = execute_query(poll_query, (poll_id,), fetch=True)

        if not poll:
            return f"<h1>Помилка:</h1><p>Опитування з ID {poll_id} не знайдено.</p>"

        # Fetch options for the poll
        options_query = "SELECT option_id, option_text FROM options WHERE poll_id = %s"
        options = execute_query(options_query, (poll_id,), fetch=True)

        # Prepare data for the template
        poll_data = {
            "id": poll[0]['poll_id'],  # Використовуємо ключі словника, оскільки cursor налаштований як dictionary=True
            "question": poll[0]['question'],
            "options": [{"id": opt['option_id'], "text": opt['option_text']} for opt in options],
        }

        return render_template("edit_poll.html", poll=poll_data)
    except Exception as e:
        return f"<h1>Помилка:</h1><p>{str(e)}</p>"




# Обробка збереження змін
@app.route('/update_poll/<int:poll_id>', methods=['POST'])
def update_poll(poll_id):
    try:
        question = request.form['question']
        options = request.form.getlist('options')

        # Update poll question
        execute_query("UPDATE polls SET question = %s WHERE poll_id = %s", (question, poll_id))

        # Update poll options
        for option_id, option_text in zip(request.form.getlist('option_ids'), options):
            execute_query("UPDATE options SET option_text = %s WHERE option_id = %s", (option_text, option_id))

        return redirect('/edit')
    except Exception as e:
        return f"<h1>Помилка:</h1><p>{str(e)}</p>"





# Перегляд існуючих голосувань
@app.route('/view', methods=['GET'])
def view_polls():
    try:
        # Отримання списку голосувань
        polls_query = "SELECT poll_id, question FROM polls"
        polls = execute_query(polls_query, fetch=True)

        return render_template('view.html', polls=polls)
    except Exception as e:
        return f"<h1>Помилка:</h1><p>{str(e)}</p>"


@app.route('/view/<int:poll_id>', methods=['GET'])
def view_poll_results(poll_id):
    try:
        # Отримання питання опитування
        poll_query = "SELECT question FROM polls WHERE poll_id = %s"
        poll = execute_query(poll_query, (poll_id,), fetch=True)[0]

        # Отримання варіантів відповідей, кількості голосів та списку користувачів
        results_query = """
            SELECT 
                o.option_text, 
                COUNT(v.option_id) AS vote_count, 
                GROUP_CONCAT(u.username SEPARATOR ', ') AS voters 
            FROM 
                options o
            LEFT JOIN 
                votes v ON o.option_id = v.option_id
            LEFT JOIN 
                users u ON v.user_id = u.user_id
            WHERE 
                o.poll_id = %s
            GROUP BY 
                o.option_id, o.option_text;
        """
        results = execute_query(results_query, (poll_id,), fetch=True)

        return render_template('view_poll_results.html', poll=poll, results=results)
    except Exception as e:
        return f"<h1>Помилка:</h1><p>{str(e)}</p>"




@app.route('/user-polls')
def user_polls():
    # Поки що використовуємо статичний текст
    # У реальному випадку тут буде запит до бази даних
    user_polls = [
        {"title": "Опитування 1", "description": "Опис першого опитування"},
        {"title": "Опитування 2", "description": "Опис другого опитування"},
    ]
    return render_template('user_polls.html', polls=user_polls)


if __name__ == '__main__':
    app.run(debug=True)
