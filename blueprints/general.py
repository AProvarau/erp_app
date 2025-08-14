from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from models import db, GeneralData, ExportContract, Log
from forms import GeneralDataForm
import json

general_bp = Blueprint('general', __name__, template_folder='templates/general')

@general_bp.route('/general')
@login_required
def index():
    # Получаем per_page из запроса или сессии, по умолчанию 10
    per_page = request.args.get('per_page', session.get('per_page', 10), type=int)
    # Ограничиваем допустимые значения per_page
    if per_page not in [10, 25, 50]:
        per_page = 10
    session['per_page'] = per_page
    page = request.args.get('page', 1, type=int)
    if current_user.is_admin() or current_user.client_id is None:
        # Администраторы и пользователи без client_id видят все записи
        pagination = GeneralData.query.paginate(page=page, per_page=per_page, error_out=False)
    else:
        # Пользователи с client_id видят только свои записи
        pagination = GeneralData.query.filter_by(client_id=current_user.client_id).paginate(page=page, per_page=per_page, error_out=False)
    entries = pagination.items
    return render_template('general/index.html', entries=entries, pagination=pagination, per_page=per_page)

@general_bp.route('/general/new', methods=['GET', 'POST'])
@login_required
def new_entry():
    form = GeneralDataForm()
    # Ограничиваем выбор client_id для пользователей с client_id
    if current_user.client_id is not None and not current_user.is_admin():
        form.client_id.choices = [(current_user.client_id, current_user.client.name)]
        form.export_contract_id.choices = [(contract.export_contract_id, contract.number) for contract in ExportContract.query.filter_by(client_id=current_user.client_id).all()]
    if form.validate_on_submit():
        entry = GeneralData(
            client_id=form.client_id.data,
            gateway_id=form.gateway_id.data,
            terminal_id=form.terminal_id.data,
            export_contract_id=form.export_contract_id.data,
            vehicle=form.vehicle.data or None,
            invoice_number=form.invoice_number.data,
            delivery_address=form.delivery_address.data or None,
            user_id=current_user.user_id
        )
        db.session.add(entry)
        db.session.flush()  # Получаем ID записи до коммита
        # Логируем создание
        log = Log(
            user_id=current_user.user_id,
            action='create',
            table_name='general_data',
            record_id=entry.id,
            details=json.dumps({
                'client_id': entry.client_id,
                'gateway_id': entry.gateway_id,
                'terminal_id': entry.terminal_id,
                'export_contract_id': entry.export_contract_id,
                'vehicle': entry.vehicle,
                'invoice_number': entry.invoice_number,
                'delivery_address': entry.delivery_address
            }, ensure_ascii=False)
        )
        db.session.add(log)
        db.session.commit()
        flash('Запись успешно создана.', 'success')
        return redirect(url_for('general.index'))
    return render_template('general/form.html', form=form)

@general_bp.route('/general/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_entry(id):
    entry = db.session.get(GeneralData, id)
    if not entry:
        flash('Запись не найдена.', 'error')
        return redirect(url_for('general.index'))
    # Проверяем, имеет ли пользователь доступ к записи
    if not current_user.is_admin() and current_user.client_id is not None and entry.client_id != current_user.client_id:
        flash('Доступ к редактированию этой записи запрещён.', 'error')
        return redirect(url_for('general.index'))
    form = GeneralDataForm(obj=entry)
    # Ограничиваем выбор client_id и export_contract_id для пользователей с client_id
    if current_user.client_id is not None and not current_user.is_admin():
        form.client_id.choices = [(current_user.client_id, current_user.client.name)]
        form.export_contract_id.choices = [(contract.export_contract_id, contract.number) for contract in ExportContract.query.filter_by(client_id=current_user.client_id).all()]
    if form.validate_on_submit():
        # Сохраняем старые значения для лога
        old_values = {
            'client_id': entry.client_id,
            'gateway_id': entry.gateway_id,
            'terminal_id': entry.terminal_id,
            'export_contract_id': entry.export_contract_id,
            'vehicle': entry.vehicle,
            'invoice_number': entry.invoice_number,
            'delivery_address': entry.delivery_address
        }
        # Обновляем запись
        entry.client_id = form.client_id.data
        entry.gateway_id = form.gateway_id.data
        entry.terminal_id = form.terminal_id.data
        entry.export_contract_id = form.export_contract_id.data
        entry.vehicle = form.vehicle.data or None
        entry.invoice_number = form.invoice_number.data
        entry.delivery_address = form.delivery_address.data or None
        # Логируем обновление
        new_values = {
            'client_id': entry.client_id,
            'gateway_id': entry.gateway_id,
            'terminal_id': entry.terminal_id,
            'export_contract_id': entry.export_contract_id,
            'vehicle': entry.vehicle,
            'invoice_number': entry.invoice_number,
            'delivery_address': entry.delivery_address
        }
        log = Log(
            user_id=current_user.user_id,
            action='update',
            table_name='general_data',
            record_id=entry.id,
            details=json.dumps({
                'old': old_values,
                'new': new_values
            }, ensure_ascii=False)
        )
        db.session.add(log)
        db.session.commit()
        flash('Запись успешно обновлена.', 'success')
        return redirect(url_for('general.index'))
    return render_template('general/form.html', form=form, entry=entry)

@general_bp.route('/general/<int:id>/delete', methods=['POST'])
@login_required
def delete_entry(id):
    entry = db.session.get(GeneralData, id)
    if not entry:
        flash('Запись не найдена.', 'error')
        return redirect(url_for('general.index'))
    # Проверяем, имеет ли пользователь доступ к записи
    if not current_user.is_admin() and current_user.client_id is not None and entry.client_id != current_user.client_id:
        flash('Доступ к удалению этой записи запрещён.', 'error')
        return redirect(url_for('general.index'))
    # Логируем удаление
    log = Log(
        user_id=current_user.user_id,
        action='delete',
        table_name='general_data',
        record_id=entry.id,
        details=json.dumps({
            'client_id': entry.client_id,
            'gateway_id': entry.gateway_id,
            'terminal_id': entry.terminal_id,
            'export_contract_id': entry.export_contract_id,
            'vehicle': entry.vehicle,
            'invoice_number': entry.invoice_number,
            'delivery_address': entry.delivery_address
        }, ensure_ascii=False)
    )
    db.session.add(log)
    db.session.delete(entry)
    db.session.commit()
    flash('Запись успешно удалена.', 'success')
    return redirect(url_for('general.index'))