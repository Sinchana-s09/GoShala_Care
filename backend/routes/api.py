from datetime import date, timedelta
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from backend.database import get_db
from backend.db_models import Cow, VitalsLog, Case
from backend.ml_service import MLService

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/farmer/milk_trend')
@login_required
def farmer_milk_trend():
    """Returns herd milk yield trend over the last 14 days."""
    db = get_db()
    cows = db.query(Cow).filter_by(farmer_id=current_user.id, is_active=True).all()
    cow_ids = [c.id for c in cows]

    days = 14
    start_date = date.today() - timedelta(days=days - 1)
    
    date_labels = []
    total_yields = []

    for d in range(days):
        cur_date = start_date + timedelta(days=d)
        date_str = cur_date.strftime('%b %d')
        date_labels.append(date_str)

        if cow_ids:
            day_logs = db.query(VitalsLog).filter(
                VitalsLog.cow_id.in_(cow_ids),
                VitalsLog.log_date == cur_date
            ).all()
            total = sum(l.milk_yield for l in day_logs)
            total_yields.append(round(total, 1))
        else:
            total_yields.append(0.0)

    return jsonify({
        'labels': date_labels,
        'values': total_yields
    })

@api_bp.route('/farmer/cow/<int:cow_id>/vitals_trend')
@login_required
def cow_vitals_trend(cow_id):
    """Returns temperature and milk yield history for a specific cow."""
    db = get_db()
    cow = db.query(Cow).filter_by(id=cow_id, farmer_id=current_user.id).first()
    if not cow:
        return jsonify({'error': 'Cow not found'}), 404
    logs = db.query(VitalsLog).filter_by(cow_id=cow.id).order_by(VitalsLog.log_date.asc()).limit(20).all()

    labels = [l.log_date.strftime('%b %d') for l in logs]
    temperatures = [float(l.temperature) for l in logs]
    milks = [float(l.milk_yield) for l in logs]

    return jsonify({
        'labels': labels,
        'temperatures': temperatures,
        'milk_yields': milks
    })

@api_bp.route('/admin/pipeline_data')
@login_required
def admin_pipeline_data():
    """Returns pipeline metrics JSON for admin visual rendering."""
    metrics = MLService.get_pipeline_metrics()
    return jsonify(metrics)
