from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, GeneralData
from forms import GeneralDataForm

general_bp = Blueprint('general', __name__, template_folder='templates/general')

@general_bp.route('/general')
@login_required
def index():
    entries = GeneralData.query.all()
    return render_template('general/index.html', entries=entries)

@general_bp.route('/general/new', methods=['GET', 'POST'])
@login_required
def new_entry():
    form = GeneralDataForm()
    if form.validate_on_submit():
        entry = GeneralData(
            client_id=form.client_id.data,
            gateway_id=form.gateway_id.data,
            terminal_id=form.terminal_id.data,
            vehicle=form.vehicle.data,
            invoice_number=form.invoice_number.data,
            user_id=current_user.user_id
        )
        db.session.add(entry)
        db.session.commit()
        flash('Запись успешно создана.', 'success')
        return redirect(url_for('general.index'))
    return render_template('general/form.html', form=form)