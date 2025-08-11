from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from models import db, Role, User
from admin_config import ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD

app = Flask(__name__)

# Конфигурация
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///erp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db.init_app(app)

def create_admin():
    with app.app_context():
        # Проверяем, существует ли роль "Администратор"
        admin_role = Role.query.filter_by(name='Администратор').first()
        if not admin_role:
            admin_role = Role(name='Администратор', description='Полный доступ к системе')
            db.session.add(admin_role)
            db.session.commit()

        # Проверяем, не существует ли пользователь
        if User.query.filter_by(username=ADMIN_USERNAME).first():
            print(f"Пользователь с именем {ADMIN_USERNAME} уже существует.")
            return
        if User.query.filter_by(email=ADMIN_EMAIL).first():
            print(f"Пользователь с email {ADMIN_EMAIL} уже существует.")
            return

        # Создаем администратора
        admin = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(ADMIN_PASSWORD),
            role_id=admin_role.role_id,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Администратор {ADMIN_USERNAME} успешно создан.")

if __name__ == '__main__':
    create_admin()