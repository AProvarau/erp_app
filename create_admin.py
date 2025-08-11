from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from models import db, Role, User

app = Flask(__name__)

# Конфигурация
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///erp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db.init_app(app)

def create_admin(username, email, password):
    with app.app_context():
        # Проверяем, существует ли роль "Администратор"
        admin_role = Role.query.filter_by(name='Администратор').first()
        if not admin_role:
            admin_role = Role(name='Администратор', description='Полный доступ к системе')
            db.session.add(admin_role)
            db.session.commit()

        # Проверяем, не существует ли пользователь
        if User.query.filter_by(username=username).first():
            print(f"Пользователь с именем {username} уже существует.")
            return
        if User.query.filter_by(email=email).first():
            print(f"Пользователь с email {email} уже существует.")
            return

        # Создаем администратора
        admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role_id=admin_role.role_id,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Администратор {username} успешно создан.")

if __name__ == '__main__':
    # Укажите данные администратора
    create_admin(
        username='admin',
        email='admin@example.com',
        password='securepassword123'
    )