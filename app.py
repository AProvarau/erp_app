from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Client, Role, User, Invitation
from datetime import datetime

app = Flask(__name__)

# Конфигурация
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///erp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db.init_app(app)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Маршрут для логина
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            if not user.is_active:
                flash('Ваш аккаунт неактивен. Обратитесь к администратору.', 'error')
                return redirect(url_for('login'))
            if check_password_hash(user.password_hash, password):
                login_user(user)
                flash('Вход выполнен успешно.', 'success')
                return redirect(url_for('home'))
        flash('Неверный email или пароль.', 'error')
    return render_template('login.html')


# Маршрут для регистрации по приглашению
@app.route('/register/<token>', methods=['GET', 'POST'])
def register(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    # Проверка токена приглашения
    invitation = Invitation.query.filter_by(token=token, used=False).first()
    if not invitation or invitation.expires_at < datetime.utcnow():
        flash('Недействительная или просроченная ссылка для регистрации.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято.', 'error')
            return redirect(url_for('register', token=token))
        if User.query.filter_by(email=email).first():
            flash('Email уже используется.', 'error')
            return redirect(url_for('register', token=token))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role_id=invitation.role_id,
            client_id=invitation.client_id,
            is_active=True
        )
        invitation.used = True
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна. Пожалуйста, войдите.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', token=token)


# Маршрут для выхода
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('login'))


# Главная страница
@app.route('/')
def home():
    return render_template('home.html')


# Маршруты админской части: пользователи
@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('home'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/user/new', methods=['GET', 'POST'])
@login_required
def admin_user_new():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role_id = request.form['role_id']
        client_id = request.form.get('client_id')
        is_active = 'is_active' in request.form

        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято.', 'error')
            return redirect(url_for('admin_user_new'))
        if User.query.filter_by(email=email).first():
            flash('Email уже используется.', 'error')
            return redirect(url_for('admin_user_new'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role_id=role_id,
            client_id=client_id if client_id else None,
            is_active=is_active
        )
        db.session.add(user)
        db.session.commit()
        flash('Пользователь успешно создан.', 'success')
        return redirect(url_for('admin_users'))

    roles = Role.query.all()
    clients = Client.query.all()
    return render_template('admin/user_form.html', roles=roles, clients=clients, user=None)


@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_user_edit(user_id):
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        password = request.form['password']
        user.role_id = request.form['role_id']
        user.client_id = request.form.get('client_id') or None
        user.is_active = 'is_active' in request.form

        if User.query.filter_by(username=user.username).filter(User.user_id != user_id).first():
            flash('Имя пользователя уже занято.', 'error')
            return redirect(url_for('admin_user_edit', user_id=user_id))
        if User.query.filter_by(email=user.email).filter(User.user_id != user_id).first():
            flash('Email уже используется.', 'error')
            return redirect(url_for('admin_user_edit', user_id=user_id))

        if password:
            user.password_hash = generate_password_hash(password)

        db.session.commit()
        flash('Пользователь успешно обновлен.', 'success')
        return redirect(url_for('admin_users'))

    roles = Role.query.all()
    clients = Client.query.all()
    return render_template('admin/user_form.html', user=user, roles=roles, clients=clients)


# Маршруты админской части: клиенты
@app.route('/admin/clients')
@login_required
def admin_clients():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('home'))
    clients = Client.query.all()
    return render_template('admin/clients.html', clients=clients)


@app.route('/admin/client/new', methods=['GET', 'POST'])
@login_required
def admin_client_new():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')

        if Client.query.filter_by(name=name).first():
            flash('Клиент с таким именем уже существует.', 'error')
            return redirect(url_for('admin_client_new'))

        client = Client(
            name=name,
            description=description
        )
        db.session.add(client)
        db.session.commit()
        flash('Клиент успешно создан.', 'success')
        return redirect(url_for('admin_clients'))

    return render_template('admin/client_form.html', client=None)


@app.route('/admin/client/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_client_edit(client_id):
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('home'))
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        client.name = request.form['name']
        client.description = request.form.get('description')

        if Client.query.filter_by(name=client.name).filter(Client.client_id != client_id).first():
            flash('Клиент с таким именем уже существует.', 'error')
            return redirect(url_for('admin_client_edit', client_id=client_id))

        db.session.commit()
        flash('Клиент успешно обновлен.', 'success')
        return redirect(url_for('admin_clients'))

    return render_template('admin/client_form.html', client=client)


# Маршрут для создания приглашения
@app.route('/admin/invitation/new', methods=['GET', 'POST'])
@login_required
def admin_invitation_new():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('home'))
    if request.method == 'POST':
        role_id = request.form['role_id']
        client_id = request.form.get('client_id')

        invitation = Invitation(role_id=role_id, client_id=client_id if client_id else None)
        db.session.add(invitation)
        db.session.commit()
        invitation_url = url_for('register', token=invitation.token, _external=True)
        flash(f'Приглашение создано. Ссылка: {invitation_url}', 'success')
        return redirect(url_for('admin_users'))

    roles = Role.query.all()
    clients = Client.query.all()
    return render_template('admin/invitation_form.html', roles=roles, clients=clients)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Добавим тестовые роли, если их нет
        if not Role.query.filter_by(name='Администратор').first():
            admin_role = Role(name='Администратор', description='Полный доступ к системе')
            db.session.add(admin_role)
            db.session.commit()
        if not Role.query.filter_by(name='Менеджер').first():
            manager_role = Role(name='Менеджер', description='Управление клиентами')
            db.session.add(manager_role)
            db.session.commit()
        if not Role.query.filter_by(name='Декларант').first():
            employee_role = Role(name='Декларант', description='Ограниченный доступ')
            db.session.add(employee_role)
            db.session.commit()
    app.run(host='0.0.0.0', port=5000)