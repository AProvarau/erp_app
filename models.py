from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()

class Client(db.Model):
    __tablename__ = 'clients'
    client_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)

class Role(db.Model):
    __tablename__ = 'roles'
    role_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.client_id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    role = db.relationship('Role', backref='users', lazy=True)
    client = db.relationship('Client', backref='users', lazy=True)

    def get_id(self):
        return str(self.user_id)

    def is_admin(self):
        return self.role.name == 'Администратор'

class Invitation(db.Model):
    __tablename__ = 'invitations'
    invitation_id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.client_id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, server_default=db.text("(datetime('now', '+1 day'))"))
    used = db.Column(db.Boolean, default=False)

    role = db.relationship('Role', backref='invitations', lazy=True)
    client = db.relationship('Client', backref='invitations', lazy=True)

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    token_id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, server_default=db.text("(datetime('now', '+1 hour'))"))

    user = db.relationship('User', backref='reset_tokens', lazy=True)

class Gateway(db.Model):
    __tablename__ = 'gateways'
    gateway_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)

class Terminal(db.Model):
    __tablename__ = 'terminals'
    terminal_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

class GeneralData(db.Model):
    __tablename__ = 'general_data'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.client_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    gateway_id = db.Column(db.Integer, db.ForeignKey('gateways.gateway_id'), nullable=False)
    terminal_id = db.Column(db.Integer, db.ForeignKey('terminals.terminal_id'), nullable=False)
    vehicle = db.Column(db.String(100), nullable=False)
    invoice_number = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    client = db.relationship('Client', backref='general_data_entries', lazy=True)
    user = db.relationship('User', backref='general_data_entries', lazy=True)
    gateway = db.relationship('Gateway', backref='general_data_entries', lazy=True)
    terminal = db.relationship('Terminal', backref='general_data_entries', lazy=True)