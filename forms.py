from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import re
from models import User, Role, Client

def validate_password_strength(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError("Пароль должен содержать минимум 8 символов.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Пароль должен содержать хотя бы одну заглавную букву.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Пароль должен содержать хотя бы одну строчную букву.")
    if not re.search(r"\d", password):
        raise ValidationError("Пароль должен содержать хотя бы одну цифру.")
    if not re.search(r"[!@#$%^&*]", password):
        raise ValidationError("Пароль должен содержать хотя бы один специальный символ (!@#$%^&*).")

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Отправить ссылку для сброса')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Новый пароль', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')])
    submit = SubmitField('Сохранить новый пароль')

class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Имя пользователя уже занято.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Email уже используется.')

class UserForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[validate_password_strength])
    confirm_password = PasswordField('Подтвердите пароль', validators=[EqualTo('password', message='Пароли должны совпадать')])
    role_id = SelectField('Роль', coerce=int, validators=[DataRequired()])
    client_id = SelectField('Клиент', coerce=int, choices=[(0, 'Нет')], validate_choice=False)
    is_active = BooleanField('Активен')
    submit = SubmitField('Сохранить')

    def __init__(self, user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = user
        self.role_id.choices = [(role.role_id, role.name) for role in Role.query.all()]
        self.client_id.choices = [(0, 'Нет')] + [(client.client_id, client.name) for client in Client.query.all()]

    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user and (not self.user or existing_user.user_id != self.user.user_id):
            raise ValidationError('Имя пользователя уже занято.')

    def validate_email(self, email):
        existing_user = User.query.filter_by(email=email.data).first()
        if existing_user and (not self.user or existing_user.user_id != self.user.user_id):
            raise ValidationError('Email уже используется.')

class ClientForm(FlaskForm):
    name = StringField('Название клиента', validators=[DataRequired(), Length(min=2, max=100)])
    description = StringField('Описание')
    submit = SubmitField('Сохранить')

    def validate_name(self, name):
        existing_client = Client.query.filter_by(name=name.data).first()
        if existing_client and (not hasattr(self, 'client') or existing_client.client_id != self.client.client_id):
            raise ValidationError('Клиент с таким именем уже существует.')

class InvitationForm(FlaskForm):
    role_id = SelectField('Роль', coerce=int, validators=[DataRequired()])
    client_id = SelectField('Клиент', coerce=int, choices=[(0, 'Нет')], validate_choice=False)
    submit = SubmitField('Создать приглашение')

    def __init__(self, *args, **kwargs):
        super(InvitationForm, self).__init__(*args, **kwargs)
        self.role_id.choices = [(role.role_id, role.name) for role in Role.query.all()]
        self.client_id.choices = [(0, 'Нет')] + [(client.client_id, client.name) for client in Client.query.all()]