from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, Client, Role, User, Invitation, PasswordResetToken
from forms import UserForm, ClientForm, InvitationForm
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
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role_id=form.role_id.data,
            client_id=form.client_id.data if form.client_id.data != 0 else None,
            is_active=form.is_active.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Пользователь успешно создан.', 'success')
        return redirect(url_for('admin.admin_users'))
    return render_template('admin/user_form.html', form=form)

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
    form = UserForm(user=user, obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role_id = form.role_id.data
        user.client_id = form.client_id.data if form.client_id.data != 0 else None
        user.is_active = form.is_active.data
        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Пользователь успешно обновлен.', 'success')
        return redirect(url_for('admin.admin_users'))
    return render_template('admin/user_form.html', form=form, user=user)

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
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(client)
        db.session.commit()
        flash('Клиент успешно создан.', 'success')
        return redirect(url_for('admin.admin_clients'))
    return render_template('admin/client_form.html', form=form)

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
    form = ClientForm(obj=client)
    form.client = client
    if form.validate_on_submit():
        client.name = form.name.data
        client.description = form.description.data
        db.session.commit()
        flash('Клиент успешно обновлен.', 'success')
        return redirect(url_for('admin.admin_clients'))
    return render_template('admin/client_form.html', form=form)

@admin_bp.route('/invitation/new', methods=['GET', 'POST'])
@login_required
def admin_invitation_new():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    form = InvitationForm()
    if form.validate_on_submit():
        invitation = Invitation(
            role_id=form.role_id.data,
            client_id=form.client_id.data if form.client_id.data != 0 else None
        )
        db.session.add(invitation)
        db.session.commit()
        invitation_url = url_for('auth.register', token=invitation.token, _external=True)
        flash(f'Приглашение создано. Ссылка: {invitation_url}', 'success')
        return redirect(url_for('admin.admin_users'))
    return render_template('admin/invitation_form.html', form=form)

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