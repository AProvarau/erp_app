from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, Client, Role, User, Invitation, PasswordResetToken
from utils import send_reset_email
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/new', methods=['GET', 'POST'])
@login_required
def admin_user_new():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role_id = request.form['role_id']
        client_id = request.form.get('client_id')
        is_active = 'is_active' in request.form

        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято.', 'error')
            return redirect(url_for('admin.admin_user_new'))
        if User.query.filter_by(email=email).first():
            flash('Email уже используется.', 'error')
            return redirect(url_for('admin.admin_user_new'))

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
        return redirect(url_for('admin.admin_users'))

    roles = Role.query.all()
    clients = Client.query.all()
    return render_template('admin/user_form.html', roles=roles, clients=clients, user=None)

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_user_edit(user_id):
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    user = db.session.get(User, user_id)
    if not user:
        flash('Пользователь не найден.', 'error')
        return redirect(url_for('admin.admin_users'))
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        password = request.form['password']
        user.role_id = request.form['role_id']
        user.client_id = request.form.get('client_id') or None
        user.is_active = 'is_active' in request.form

        if User.query.filter_by(username=user.username).filter(User.user_id != user_id).first():
            flash('Имя пользователя уже занято.', 'error')
            return redirect(url_for('admin.admin_user_edit', user_id=user_id))
        if User.query.filter_by(email=user.email).filter(User.user_id != user_id).first():
            flash('Email уже используется.', 'error')
            return redirect(url_for('admin.admin_user_edit', user_id=user_id))

        if password:
            user.password_hash = generate_password_hash(password)

        db.session.commit()
        flash('Пользователь успешно обновлен.', 'success')
        return redirect(url_for('admin.admin_users'))

    roles = Role.query.all()
    clients = Client.query.all()
    return render_template('admin/user_form.html', user=user, roles=roles, clients=clients)

@admin_bp.route('/user/<int:user_id>/reset_password', methods=['POST'])
@login_required
def admin_user_reset_password(user_id):
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    user = db.session.get(User, user_id)
    if not user:
        flash('Пользователь не найден.', 'error')
        return redirect(url_for('admin.admin_users'))
    if not user.is_active:
        flash('Нельзя сбросить пароль для неактивного пользователя.', 'error')
        return redirect(url_for('admin.admin_users'))
    token = PasswordResetToken(user_id=user.user_id)
    db.session.add(token)
    db.session.commit()
    if send_reset_email(user.email, token.token):
        flash(f'Ссылка для сброса пароля отправлена на {user.email}.', 'success')
    else:
        flash('Ошибка при отправке email. Пожалуйста, попробуйте позже.', 'error')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/clients')
@login_required
def admin_clients():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    clients = Client.query.all()
    return render_template('admin/clients.html', clients=clients)

@admin_bp.route('/client/new', methods=['GET', 'POST'])
@login_required
def admin_client_new():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')

        if Client.query.filter_by(name=name).first():
            flash('Клиент с таким именем уже существует.', 'error')
            return redirect(url_for('admin.admin_client_new'))

        client = Client(
            name=name,
            description=description
        )
        db.session.add(client)
        db.session.commit()
        flash('Клиент успешно создан.', 'success')
        return redirect(url_for('admin.admin_clients'))

    return render_template('admin/client_form.html', client=None)

@admin_bp.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_client_edit(client_id):
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    client = db.session.get(Client, client_id)
    if not client:
        flash('Клиент не найден.', 'error')
        return redirect(url_for('admin.admin_clients'))
    if request.method == 'POST':
        client.name = request.form['name']
        client.description = request.form.get('description')

        if Client.query.filter_by(name=client.name).filter(Client.client_id != client_id).first():
            flash('Клиент с таким именем уже существует.', 'error')
            return redirect(url_for('admin.admin_client_edit', client_id=client_id))

        db.session.commit()
        flash('Клиент успешно обновлен.', 'success')
        return redirect(url_for('admin.admin_clients'))

    return render_template('admin/client_form.html', client=client)

@admin_bp.route('/invitation/new', methods=['GET', 'POST'])
@login_required
def admin_invitation_new():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуетс я роль администратора.', 'error')
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        role_id = request.form['role_id']
        client_id = request.form.get('client_id')

        invitation = Invitation(role_id=role_id, client_id=client_id if client_id else None)
        db.session.add(invitation)
        db.session.commit()
        invitation_url = url_for('auth.register', token=invitation.token, _external=True)
        flash(f'Приглашение создано. Ссылка: {invitation_url}', 'success')
        return redirect(url_for('admin.admin_users'))

    roles = Role.query.all()
    clients = Client.query.all()
    return render_template('admin/invitation_form.html', roles=roles, clients=clients)

@admin_bp.route('/invitations')
@login_required
def admin_invitations():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    invitations = Invitation.query.filter_by(used=False).filter(Invitation.expires_at > datetime.utcnow()).all()
    return render_template('admin/invitations.html', invitations=invitations)

@admin_bp.route('/invitation/<int:invitation_id>/delete', methods=['POST'])
@login_required
def admin_invitation_delete(invitation_id):
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    invitation = db.session.get(Invitation, invitation_id)
    if not invitation:
        flash('Приглашение не найдено.', 'error')
        return redirect(url_for('admin.admin_invitations'))
    db.session.delete(invitation)
    db.session.commit()
    flash('Приглашение успешно удалено.', 'success')
    return redirect(url_for('admin.admin_invitations'))