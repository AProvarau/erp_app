from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import uuid
from datetime import datetime, timedelta

db = SQLAlchemy()

class Client(db.Model):
    __tablename__ = 'clients'
    client_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    users = db.relationship('User', backref='client', lazy=True)
    invitations = db.relationship('Invitation', backref='client', lazy=True)

class Role(db.Model):
    __tablename__ = 'roles'
    role_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    users = db.relationship('User', backref='role', lazy=True)
    invitations = db.relationship('Invitation', backref='role', lazy=True)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.client_id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    def get_id(self):
        return str(self.user_id)

    def is_admin(self):
        return self.role.name == 'Администратор'

class Invitation(db.Model):
    __tablename__ = 'invitations'
    invitation_id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), unique=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.client_id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    def __init__(self, role_id, client_id=None):
        self.token = str(uuid.uuid4())
        self.role_id = role_id
        self.client_id = client_id
        self.expires_at = datetime.utcnow() + timedelta(days=7)  # Приглашение действительно 7 дней