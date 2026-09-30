from flask import Blueprint, render_template, request
from backend.database import get_db
from backend.db_models import Disease, DiseaseSymptom, Symptom

library_bp = Blueprint('library', __name__)

@library_bp.route('/diseases')
def diseases_library():
    db = get_db()
    search = request.args.get('q', '').strip()
    urgency_filter = request.args.get('urgency', 'all')

    query = db.query(Disease)
    if search:
        query = query.filter(
            (Disease.name.ilike(f"%{search}%")) |
            (Disease.description.ilike(f"%{search}%")) |
            (Disease.key_indicators.ilike(f"%{search}%"))
        )
    if urgency_filter != 'all':
        query = query.filter(Disease.urgency_level == urgency_filter)

    diseases = query.order_by(Disease.name).all()
    symptoms = {s.code: s.display_name for s in db.query(Symptom).all()}

    return render_template(
        'library/diseases.html',
        diseases=diseases,
        symptoms=symptoms,
        search=search,
        urgency_filter=urgency_filter
    )
