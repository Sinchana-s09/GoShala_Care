from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from backend.database import get_db
from backend.db_models import Case, User, Cow, VitalsLog, PhotoScan
from backend.routes.auth import role_required

vet_bp = Blueprint('vet', __name__, url_prefix='/vet')

@vet_bp.route('/dashboard')
@login_required
@role_required('vet', 'admin')
def dashboard():
    db = get_db()
    status_filter = request.args.get('status', 'pending')
    urgency_filter = request.args.get('urgency', 'all')

    query = db.query(Case)

    if status_filter != 'all':
        query = query.filter(Case.status == status_filter)
    if urgency_filter != 'all':
        query = query.filter(Case.urgency == urgency_filter)

    # Sort: High urgency first, then newest
    cases = query.order_by(
        Case.urgency.desc(),
        Case.created_at.desc()
    ).all()

    # Stat calculations
    pending_count = db.query(Case).filter(Case.status == 'pending').count()
    reviewed_count = db.query(Case).filter(Case.status.in_(['in_review', 'resolved', 'closed'])).count()
    
    handled_cases = db.query(Case).filter(Case.status.in_(['resolved', 'closed'])).all()
    distinct_farmers = len(set(c.farmer_id for c in handled_cases))

    high_urgency_count = db.query(Case).filter(Case.urgency == 'High', Case.status == 'pending').count()

    return render_template(
        'vet/dashboard.html',
        cases=cases,
        pending_count=pending_count,
        reviewed_count=reviewed_count,
        farmers_served=distinct_farmers,
        high_urgency_count=high_urgency_count,
        current_status=status_filter,
        current_urgency=urgency_filter
    )

@vet_bp.route('/cases/<int:case_id>', methods=['GET', 'POST'])
@login_required
@role_required('vet', 'admin')
def case_detail(case_id):
    db = get_db()
    case = db.query(Case).filter_by(id=case_id).first()
    if not case:
        flash("Case not found.", "warning")
        return redirect(url_for('vet.dashboard'))

    if request.method == 'POST':
        status = request.form.get('status', 'in_review')
        vet_notes = request.form.get('vet_notes', '').strip()
        vet_recommendation = request.form.get('vet_recommendation', '').strip()

        case.status = status
        case.vet_notes = vet_notes
        case.vet_recommendation = vet_recommendation
        case.assigned_vet_id = current_user.id
        case.reviewed_at = datetime.utcnow()

        db.commit()
        flash(f"Case #{case.case_number} updated successfully! Advice sent to farmer.", "success")
        return redirect(url_for('vet.case_detail', case_id=case.id))

    # Fetch recent history of the cow for medical context
    cow_history = db.query(VitalsLog).filter_by(cow_id=case.cow_id).order_by(VitalsLog.log_date.desc()).limit(7).all()

    return render_template(
        'vet/case_detail.html',
        case=case,
        cow_history=cow_history
    )
