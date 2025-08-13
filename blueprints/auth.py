from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Invitation, PasswordResetToken
from forms import LoginForm, ForgotPasswordForm, ResetPasswordForm, RegisterForm
from utils import send_reset_email
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Ваш аккаунт неактивен. Обратитесь к администратору.', 'error')
                return redirect(url_for('auth.login'))
            login_user(user)
            flash('Вход выполнен успешно.', 'success')
            return redirect(url_for('main.home'))
        flash('Неверный email или пароль.', 'error')
    return render_template('login.html', form=form)


@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if not user.is_active:
                flash('Ваш аккаунт неактивен. Обратитесь к администратору.', 'error')
                return redirect(url_for('auth.forgot_password'))
            token = PasswordResetToken(user_id=user.user_id)
            db.session.add(token)
            db.session.commit()
            if send_reset_email(user.email, token.token):
                flash('Ссылка для сброса пароля отправлена на ваш email.', 'success')
            else:
                flash('Ошибка при отправке email. Пожалуйста, попробуйте позже.', 'error')
        else:
            flash('Пользователь с таким email не найден.', 'error')
        return redirect(url_for('auth.forgot_password'))
    return render_template('forgot_password.html', form=form)


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    if not reset_token or reset_token.expires_at < datetime.utcnow():
        flash('Недействительная или просроченная ссылка для сброса пароля.', 'error')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = db.session.get(User, reset_token.user_id)
        user.password_hash = generate_password_hash(form.password.data)
        db.session.delete(reset_token)
        db.session.commit()
        flash('Пароль успешно изменён. Пожалуйста, войдите.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', form=form, token=token)


@auth_bp.route('/register/<token>', methods=['GET', 'POST'])
def register(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    invitation = Invitation.query.filter_by(token=token, used=False).first()
    if not invitation or invitation.expires_at < datetime.utcnow():
        flash('Недействительная или просроченная ссылка для регистрации.', 'error')
        return redirect(url_for('auth.login'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role_id=invitation.role_id,
            client_id=invitation.client_id,
            is_active=True
        )
        invitation.used = True
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна. Пожалуйста, войдите.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form, token=token)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('auth.login'))