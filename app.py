from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from models import db, User, Role
from config import Config
from blueprints.auth import auth_bp
from blueprints.admin import admin_bp
from blueprints.main import main_bp

app = Flask(__name__)
app.config.from_object(Config)

# Инициализация базы данных
db.init_app(app)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Регистрация Blueprint'ов
app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(main_bp, url_prefix='/')

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