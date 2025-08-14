from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, GeneralData, ExportContract
from forms import GeneralDataForm

general_bp = Blueprint('general', __name__, template_folder='templates/general')

@general_bp.route('/general')
@login_required
def index():
    if current_user.is_admin() or current_user.client_id is None:
        # Администраторы и пользователи без client_id видят все записи
        entries = GeneralData.query.all()
    else:
        # Пользователи с client_id видят только свои записи
        entries = GeneralData.query.filter_by(client_id=current_user.client_id).all()
    return render_template('general/index.html', entries=entries)

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
        entry.client_id = form.client_id.data
        entry.gateway_id = form.gateway_id.data
        entry.terminal_id = form.terminal_id.data
        entry.export_contract_id = form.export_contract_id.data
        entry.vehicle = form.vehicle.data or None
        entry.invoice_number = form.invoice_number.data
        entry.delivery_address = form.delivery_address.data or None
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
    db.session.delete(entry)
    db.session.commit()
    flash('Запись успешно удалена.', 'success')
    return redirect(url_for('general.index'))