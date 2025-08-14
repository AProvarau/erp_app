from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, Client, Role, User, Invitation, PasswordResetToken, Gateway, Terminal, ExportContract, Log
from forms import UserForm, ClientForm, InvitationForm, GatewayForm, TerminalForm, ExportContractForm
from utils import send_reset_email
from datetime import datetime
import json

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
        return redirect(url_for('admin.admin_users'))
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

@admin_bp.route('/gateways')
@login_required
def admin_gateways():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    gateways = Gateway.query.all()
    return render_template('admin/gateways.html', gateways=gateways)

@admin_bp.route('/gateway/new', methods=['GET', 'POST'])
@login_required
def admin_gateway_new():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    form = GatewayForm()
    if form.validate_on_submit():
        gateway = Gateway(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(gateway)
        db.session.commit()
        flash('Шлюз успешно создан.', 'success')
        return redirect(url_for('admin.admin_gateways'))
    return render_template('admin/gateway_form.html', form=form)

@admin_bp.route('/gateway/<int:gateway_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_gateway_edit(gateway_id):
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    gateway = db.session.get(Gateway, gateway_id)
    if not gateway:
        flash('Шлюз не найден.', 'error')
        return redirect(url_for('admin.admin_gateways'))
    form = GatewayForm(obj=gateway)
    form.gateway = gateway
    if form.validate_on_submit():
        gateway.name = form.name.data
        gateway.description = form.description.data
        db.session.commit()
        flash('Шлюз успешно обновлен.', 'success')
        return redirect(url_for('admin.admin_gateways'))
    return render_template('admin/gateway_form.html', form=form)

@admin_bp.route('/terminals')
@login_required
def admin_terminals():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    terminals = Terminal.query.all()
    return render_template('admin/terminals.html', terminals=terminals)

@admin_bp.route('/terminal/new', methods=['GET', 'POST'])
@login_required
def admin_terminal_new():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    form = TerminalForm()
    if form.validate_on_submit():
        terminal = Terminal(
            name=form.name.data
        )
        db.session.add(terminal)
        db.session.commit()
        flash('Терминал успешно создан.', 'success')
        return redirect(url_for('admin.admin_terminals'))
    return render_template('admin/terminal_form.html', form=form)

@admin_bp.route('/terminal/<int:terminal_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_terminal_edit(terminal_id):
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    terminal = db.session.get(Terminal, terminal_id)
    if not terminal:
        flash('Терминал не найден.', 'error')
        return redirect(url_for('admin.admin_terminals'))
    form = TerminalForm(obj=terminal)
    form.terminal = terminal
    if form.validate_on_submit():
        terminal.name = form.name.data
        db.session.commit()
        flash('Терминал успешно обновлен.', 'success')
        return redirect(url_for('admin.admin_terminals'))
    return render_template('admin/terminal_form.html', form=form)

@admin_bp.route('/export_contracts')
@login_required
def admin_export_contracts():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    contracts = ExportContract.query.all()
    return render_template('admin/export_contracts.html', contracts=contracts)

@admin_bp.route('/export_contract/new', methods=['GET', 'POST'])
@login_required
def admin_export_contract_new():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    form = ExportContractForm()
    if form.validate_on_submit():
        contract = ExportContract(
            number=form.number.data,
            date=form.date.data,
            client_id=form.client_id.data,
            created_by=current_user.user_id
        )
        db.session.add(contract)
        db.session.flush()  # Получаем ID записи до коммита
        # Логируем создание
        log = Log(
            user_id=current_user.user_id,
            action='create',
            table_name='export_contracts',
            record_id=contract.export_contract_id,
            details=json.dumps({
                'number': contract.number,
                'date': str(contract.date),
                'client_id': contract.client_id
            }, ensure_ascii=False)
        )
        db.session.add(log)
        db.session.commit()
        flash('Экспортный контракт успешно создан.', 'success')
        return redirect(url_for('admin.admin_export_contracts'))
    return render_template('admin/export_contract_form.html', form=form)

@admin_bp.route('/export_contract/<int:export_contract_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_export_contract_edit(export_contract_id):
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    contract = db.session.get(ExportContract, export_contract_id)
    if not contract:
        flash('Контракт не найден.', 'error')
        return redirect(url_for('admin.admin_export_contracts'))
    form = ExportContractForm(obj=contract)
    form.export_contract = contract
    if form.validate_on_submit():
        # Сохраняем старые значения для лога
        old_values = {
            'number': contract.number,
            'date': str(contract.date),
            'client_id': contract.client_id
        }
        # Обновляем контракт
        contract.number = form.number.data
        contract.date = form.date.data
        contract.client_id = form.client_id.data
        # Логируем обновление
        new_values = {
            'number': contract.number,
            'date': str(contract.date),
            'client_id': contract.client_id
        }
        log = Log(
            user_id=current_user.user_id,
            action='update',
            table_name='export_contracts',
            record_id=contract.export_contract_id,
            details=json.dumps({
                'old': old_values,
                'new': new_values
            }, ensure_ascii=False)
        )
        db.session.add(log)
        db.session.commit()
        flash('Контракт успешно обновлен.', 'success')
        return redirect(url_for('admin.admin_export_contracts'))
    return render_template('admin/export_contract_form.html', form=form)

@admin_bp.route('/export_contract/<int:export_contract_id>/delete', methods=['POST'])
@login_required
def admin_export_contract_delete(export_contract_id):
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    contract = db.session.get(ExportContract, export_contract_id)
    if not contract:
        flash('Контракт не найден.', 'error')
        return redirect(url_for('admin.admin_export_contracts'))
    if contract.general_data_entries:
        flash('Контракт не может быть удалён, так как с ним связаны записи в general_data.', 'error')
        return redirect(url_for('admin.admin_export_contracts'))
    # Логируем удаление
    log = Log(
        user_id=current_user.user_id,
        action='delete',
        table_name='export_contracts',
        record_id=contract.export_contract_id,
        details=json.dumps({
            'number': contract.number,
            'date': str(contract.date),
            'client_id': contract.client_id
        }, ensure_ascii=False)
    )
    db.session.add(log)
    db.session.delete(contract)
    db.session.commit()
    flash('Контракт успешно удалён.', 'success')
    return redirect(url_for('admin.admin_export_contracts'))

@admin_bp.route('/logs')
@login_required
def admin_logs():
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    logs = Log.query.order_by(Log.created_at.desc()).all()
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/logs/record/<table_name>/<int:record_id>')
@login_required
def admin_record_logs(table_name, record_id):
    if not current_user.is_admin():
        flash('Доступ запрещен: требуется роль администратора.', 'error')
        return redirect(url_for('main.home'))
    if table_name not in ['general_data', 'export_contracts']:
        flash('Недопустимое имя таблицы.', 'error')
        return redirect(url_for('main.home'))
    logs = Log.query.filter_by(table_name=table_name, record_id=record_id).order_by(Log.created_at.desc()).all()
    return render_template('admin/logs.html', logs=logs, table_name=table_name, record_id=record_id)