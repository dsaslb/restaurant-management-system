from flask import Blueprint, render_template
from flask_login import login_required, current_user

staff_bp = Blueprint('staff', __name__, url_prefix='/my')

@staff_bp.route('/schedule')
@login_required
def my_schedule():
    return render_template('staff/home.html', user=current_user) 