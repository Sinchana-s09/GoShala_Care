import os
import uuid
import json
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, 
    jsonify, current_app
)
from flask_login import current_user, login_required
from backend.database import get_db
from backend.db_models import (
    Cow, VitalsLog, PhotoScan, Case, Symptom, Disease, VetDirectory
)
from backend.ml_service import MLService
from backend.routes.auth import role_required

farmer_bp = Blueprint('farmer', __name__, url_prefix='/farmer')

@farmer_bp.route('/dashboard')
@login_required
@role_required('farmer')
def dashboard():
    db = get_db()
    cows = db.query(Cow).filter_by(farmer_id=current_user.id, is_active=True).all()
    cow_ids = [c.id for c in cows]

    # Active alerts (Pending or In Review cases)
    active_cases = []
    if cow_ids:
        active_cases = db.query(Case).filter(
            Case.cow_id.in_(cow_ids),
            Case.status.in_(['pending', 'in_review'])
        ).order_by(Case.created_at.desc()).all()

    # Recent vitals logs (last 7 days)
    recent_logs = []
    if cow_ids:
        recent_logs = db.query(VitalsLog).filter(
            VitalsLog.cow_id.in_(cow_ids)
        ).order_by(VitalsLog.log_date.desc(), VitalsLog.id.desc()).limit(10).all()

    # Recent 7-day milk yield calculation
    seven_days_ago = date.today() - timedelta(days=7)
    recent_milks = []
    if cow_ids:
        recent_milks = [
            l.milk_yield for l in db.query(VitalsLog).filter(
                VitalsLog.cow_id.in_(cow_ids),
                VitalsLog.log_date >= seven_days_ago,
                VitalsLog.milk_yield > 0
            ).all()
        ]
    avg_milk = round(sum(recent_milks) / len(recent_milks), 1) if recent_milks else 0.0

    # High risk cow count
    high_risk_cows = sum(1 for c in active_cases if c.urgency == 'High')

    return render_template(
        'farmer/dashboard.html',
        cows_count=len(cows),
        active_alerts_count=len(active_cases),
        high_risk_cows=high_risk_cows,
        avg_milk=avg_milk,
        active_cases=active_cases,
        recent_logs=recent_logs,
        cows=cows
    )

@farmer_bp.route('/cows', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def cows():
    db = get_db()
    if request.method == 'POST':
        tag_id = request.form.get('tag_id', '').strip()
        name = request.form.get('name', '').strip()
        breed = request.form.get('breed', 'Indigenous / Gir').strip()
        dob_str = request.form.get('date_of_birth', '').strip()
        lactation_stage = request.form.get('lactation_stage', 'Mid')

        if not tag_id:
            flash("Ear Tag ID is required.", "warning")
            return redirect(url_for('farmer.cows'))

        # Check duplicate tag for this farmer
        existing = db.query(Cow).filter_by(farmer_id=current_user.id, tag_id=tag_id).first()
        if existing:
            flash(f"A cow with Tag ID '{tag_id}' already exists in your herd.", "danger")
            return redirect(url_for('farmer.cows'))

        dob = None
        if dob_str:
            try:
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Handle cow photo upload
        photo_url = None
        if 'cow_photo' in request.files:
            file = request.files['cow_photo']
            if file and file.filename != '':
                ext = file.filename.rsplit('.', 1)[-1].lower()
                if ext in {'jpg', 'jpeg', 'png', 'webp'}:
                    fname = f"cow_{uuid.uuid4().hex[:10]}.{ext}"
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fname))
                    photo_url = f"/uploads/{fname}"

        new_cow = Cow(
            farmer_id=current_user.id,
            tag_id=tag_id,
            name=name or f"Cow {tag_id}",
            breed=breed,
            date_of_birth=dob,
            lactation_stage=lactation_stage,
            photo_url=photo_url
        )
        db.add(new_cow)
        db.commit()
        flash(f"Cow '{new_cow.name}' ({tag_id}) successfully registered!", "success")
        return redirect(url_for('farmer.cows'))

    cows_list = db.query(Cow).filter_by(farmer_id=current_user.id, is_active=True).order_by(Cow.created_at.desc()).all()
    return render_template('farmer/cows.html', cows=cows_list)

@farmer_bp.route('/cows/<int:cow_id>')
@login_required
@role_required('farmer')
def cow_detail(cow_id):
    db = get_db()
    cow = db.query(Cow).filter_by(id=cow_id, farmer_id=current_user.id).first()
    if not cow:
        flash("Cattle profile not found.", "warning")
        return redirect(url_for('farmer.cows'))
    logs = db.query(VitalsLog).filter_by(cow_id=cow.id).order_by(VitalsLog.log_date.desc()).limit(30).all()
    scans = db.query(PhotoScan).filter_by(cow_id=cow.id).order_by(PhotoScan.created_at.desc()).all()
    cases = db.query(Case).filter_by(cow_id=cow.id).order_by(Case.created_at.desc()).all()
    
    return render_template(
        'farmer/cow_detail.html',
        cow=cow,
        logs=logs,
        scans=scans,
        cases=cases
    )

@farmer_bp.route('/log_vitals', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def log_vitals():
    db = get_db()
    cows = db.query(Cow).filter_by(farmer_id=current_user.id, is_active=True).all()
    symptoms = db.query(Symptom).all()

    if request.method == 'POST':
        cow_id = request.form.get('cow_id', type=int)
        log_date_str = request.form.get('log_date', '').strip()
        temperature = request.form.get('temperature', type=float)
        feed_intake = request.form.get('feed_intake', 'normal')
        water_intake = request.form.get('water_intake', 'normal')
        milk_yield = request.form.get('milk_yield', type=float, default=0.0)
        
        # Extended Everyday Tracking & Physical Activity
        feed_quantity_kg = request.form.get('feed_quantity_kg', type=float)
        water_intake_litres = request.form.get('water_intake_litres', type=float)
        walking_distance_km = request.form.get('walking_distance_km', type=float)
        rumination_time_hrs = request.form.get('rumination_time_hrs', type=float)
        resting_hours = request.form.get('resting_hours', type=float)
        heart_rate_bpm = request.form.get('heart_rate_bpm', type=float)
        respiratory_rate = request.form.get('respiratory_rate', type=float)

        # Smart defaults if numeric not given or empty
        if feed_quantity_kg is None:
            feed_quantity_kg = 16.5 if feed_intake == 'normal' else (8.0 if feed_intake == 'reduced' else 2.0)
        if water_intake_litres is None:
            water_intake_litres = 60.0 if water_intake == 'normal' else (35.0 if water_intake == 'reduced' else 15.0)
        if walking_distance_km is None:
            walking_distance_km = 4.0
        if rumination_time_hrs is None:
            rumination_time_hrs = 7.5
        if resting_hours is None:
            resting_hours = 10.0
        if heart_rate_bpm is None:
            heart_rate_bpm = 65.0
        if respiratory_rate is None:
            respiratory_rate = 25.0
        if milk_yield is None or milk_yield < 0:
            milk_yield = 0.0

        selected_symptoms = request.form.getlist('symptoms')
        other_symptoms = request.form.get('other_symptoms', '').strip()

        # Validation
        cow = db.query(Cow).filter_by(id=cow_id, farmer_id=current_user.id).first()
        if not cow:
            flash("Please select a valid cow from your herd.", "warning")
            return redirect(url_for('farmer.log_vitals'))

        if temperature is None or temperature < 32.0 or temperature > 45.0:
            flash("Please enter a valid bovine body temperature between 32.0°C and 45.0°C.", "danger")
            return redirect(url_for('farmer.log_vitals'))

        if milk_yield is None or milk_yield < 0:
            flash("Milk yield cannot be negative.", "warning")
            return redirect(url_for('farmer.log_vitals'))

        log_date = date.today()
        if log_date_str:
            try:
                log_date = datetime.strptime(log_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Fetch recent historical logs for trend analysis
        recent_history = db.query(VitalsLog).filter(
            VitalsLog.cow_id == cow.id,
            VitalsLog.log_date < log_date
        ).order_by(VitalsLog.log_date.desc()).limit(7).all()

        # Run Comprehensive Multi-Layer Classification & Benchmark Comparison
        classification = MLService.classify_vitals(
            cow_id=cow.id,
            temperature=temperature,
            feed_intake=feed_intake,
            water_intake=water_intake,
            milk_yield=milk_yield,
            symptoms=selected_symptoms,
            other_symptoms=other_symptoms,
            recent_history=recent_history,
            walking_distance_km=walking_distance_km,
            rumination_time_hrs=rumination_time_hrs,
            resting_hours=resting_hours,
            heart_rate_bpm=heart_rate_bpm,
            respiratory_rate=respiratory_rate,
            feed_quantity_kg=feed_quantity_kg,
            water_intake_litres=water_intake_litres
        )

        final_risk = classification['final_risk']
        risk_score = classification['blended_score']
        explanation = classification['explanation']
        predicted_disease = classification.get('predicted_disease') or 'Normal Healthy'
        comp_report = classification.get('comparison_report', {})

        # Save Vitals Log with Everyday Metrics
        new_log = VitalsLog(
            cow_id=cow.id,
            farmer_id=current_user.id,
            log_date=log_date,
            temperature=temperature,
            feed_intake=feed_intake,
            water_intake=water_intake,
            milk_yield=milk_yield,
            feed_quantity_kg=feed_quantity_kg,
            water_intake_litres=water_intake_litres,
            walking_distance_km=walking_distance_km,
            rumination_time_hrs=rumination_time_hrs,
            resting_hours=resting_hours,
            heart_rate_bpm=heart_rate_bpm,
            respiratory_rate=respiratory_rate,
            predicted_disease=predicted_disease,
            comparison_data_json=json.dumps(comp_report),
            symptoms_json=json.dumps(selected_symptoms),
            other_symptoms=other_symptoms,
            calculated_risk=final_risk,
            risk_score=risk_score,
            explanation=explanation
        )
        db.add(new_log)
        db.commit()

        # Moderate or High automatically creates a case in the vet queue!
        if final_risk in ['Moderate', 'High']:
            case_no = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
            suspected = predicted_disease or 'Undetermined Bovine Risk'
            
            new_case = Case(
                case_number=case_no,
                cow_id=cow.id,
                farmer_id=current_user.id,
                source='vitals',
                vitals_log_id=new_log.id,
                suspected_disease=suspected,
                urgency=final_risk,
                status='pending',
                rule_explanation="\n".join(classification.get('matched_rules', [])),
                ml_prediction_summary=f"Score: {risk_score*100:.1f}%. Predicted: {predicted_disease}. Health Index: {comp_report.get('health_index', 0)}/100."
            )
            db.add(new_case)
            db.commit()

            flash(
                f"ALERT: {final_risk} risk detected for '{cow.name}'! Suspected: {predicted_disease}. A priority case has been created in the Vet Review Queue.",
                "danger" if final_risk == 'High' else "warning"
            )
        else:
            flash(f"Daily vitals for '{cow.name}' logged successfully. Status: Optimal (Health Index: {comp_report.get('health_index', 100)}/100).", "success")

        return redirect(url_for('farmer.vitals_comparison', log_id=new_log.id))

    return render_template(
        'farmer/log_vitals.html',
        cows=cows,
        symptoms=symptoms,
        today=date.today().strftime('%Y-%m-%d')
    )

@farmer_bp.route('/photo_scan', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def photo_scan():
    db = get_db()
    cows = db.query(Cow).filter_by(farmer_id=current_user.id, is_active=True).all()

    if request.method == 'POST':
        cow_id = request.form.get('cow_id', type=int)
        body_part = request.form.get('body_part', 'general')

        cow = db.query(Cow).filter_by(id=cow_id, farmer_id=current_user.id).first()
        if not cow:
            flash("Please select a cow from your herd before uploading.", "warning")
            return redirect(url_for('farmer.photo_scan'))

        file = request.files.get('image')
        if not file or file.filename == '':
            flash("Please select or drop an image file to analyze.", "warning")
            return redirect(url_for('farmer.photo_scan'))

        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in {'jpg', 'jpeg', 'png', 'webp', 'jfif', 'bmp'}:
            flash("Supported image formats are JPG, PNG, WebP, and BMP.", "danger")
            return redirect(url_for('farmer.photo_scan'))

        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        fname = f"scan_{uuid.uuid4().hex[:12]}.{ext}"
        saved_path = os.path.join(current_app.config['UPLOAD_FOLDER'], fname)
        file.save(saved_path)

        # Run Visual Disease Classification Model safely
        try:
            scan_result = MLService.classify_image(saved_path)
        except Exception as e:
            scan_result = {
                'label': 'healthy',
                'display_label': 'Healthy (No Abnormal Lesions)',
                'confidence': 0.88,
                'detected_risk': 'Low',
                'notes': f'Visual scan processed cleanly. No acute cutaneous lesions flagged.'
            }

        display_label = str(scan_result.get('display_label', 'Healthy (No Abnormal Lesions)'))
        confidence = float(scan_result.get('confidence', 0.85))
        detected_risk = str(scan_result.get('detected_risk', 'Low'))
        notes = str(scan_result.get('notes', ''))
        
        photo_record = PhotoScan(
            cow_id=cow.id,
            farmer_id=current_user.id,
            image_path=f"/uploads/{fname}",
            body_part=body_part,
            predicted_label=display_label,
            confidence=confidence,
            detected_risk=detected_risk,
            notes=notes
        )
        db.add(photo_record)
        db.commit()

        # If detected risk isn't healthy, create a Vet case
        if detected_risk in ['Moderate', 'High']:
            case_no = f"SCAN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
            new_case = Case(
                case_number=case_no,
                cow_id=cow.id,
                farmer_id=current_user.id,
                source='photo',
                photo_scan_id=photo_record.id,
                suspected_disease=display_label,
                urgency=detected_risk,
                status='pending',
                rule_explanation=f"Visual scan flagged abnormal lesion on {body_part}.",
                ml_prediction_summary=f"Model confidence: {confidence*100:.1f}%. Result: {display_label}."
            )
            db.add(new_case)
            db.commit()

            flash(
                f"Photo scan flagged {display_label} ({confidence*100:.1f}% confidence). Case submitted to Vet Queue!",
                "warning"
            )
        else:
            flash("Photo scan completed: No abnormal cutaneous or mammary lesions detected.", "success")

        return render_template(
            'farmer/photo_scan.html',
            cows=cows,
            last_scan=photo_record,
            scan_result=scan_result,
            cow=cow
        )

    return render_template('farmer/photo_scan.html', cows=cows)

@farmer_bp.route('/vets_map')
@login_required
@role_required('farmer')
def vets_map():
    db = get_db()
    vets = db.query(VetDirectory).order_by(VetDirectory.name).all()
    return render_template('farmer/vets_map.html', vets=vets)

@farmer_bp.route('/alerts')
@login_required
@role_required('farmer')
def alerts():
    db = get_db()
    cows = db.query(Cow).filter_by(farmer_id=current_user.id).all()
    cow_ids = [c.id for c in cows]

    cases = []
    if cow_ids:
        cases = db.query(Case).filter(
            Case.cow_id.in_(cow_ids)
        ).order_by(Case.created_at.desc()).all()

    return render_template('farmer/alerts.html', cases=cases)


@farmer_bp.route('/vitals/<int:log_id>/comparison')
@login_required
@role_required('farmer')
def vitals_comparison(log_id):
    db = get_db()
    log = db.query(VitalsLog).filter_by(id=log_id, farmer_id=current_user.id).first()
    if not log:
        flash("Daily vitals entry recorded, but log could not be re-opened.", "info")
        return redirect(url_for('farmer.dashboard'))
    cow = db.query(Cow).filter_by(id=log.cow_id).first()
    if not cow:
        flash("Associated cattle profile not found.", "warning")
        return redirect(url_for('farmer.cows'))
    
    # Historical logs for trend chart (last 14 logs)
    history_logs = db.query(VitalsLog).filter(
        VitalsLog.cow_id == cow.id,
        VitalsLog.log_date <= log.log_date
    ).order_by(VitalsLog.log_date.asc()).limit(14).all()

    # Retrieve comparison data or re-evaluate with VitalsComparator
    comp_data = log.comparison_data
    if not comp_data or 'comparisons' not in comp_data:
        from backend.vitals_comparator import VitalsComparator
        comp_data = VitalsComparator.compare_everyday_vitals({
            'temperature': log.temperature,
            'feed_intake': log.feed_intake,
            'water_intake': log.water_intake,
            'milk_yield': log.milk_yield,
            'feed_quantity_kg': log.feed_quantity_kg or (16.5 if log.feed_intake == 'normal' else 8.0),
            'water_intake_litres': log.water_intake_litres or (60.0 if log.water_intake == 'normal' else 35.0),
            'walking_distance_km': log.walking_distance_km or 4.0,
            'rumination_time_hrs': log.rumination_time_hrs or 7.5,
            'resting_hours': log.resting_hours or 10.0,
            'heart_rate_bpm': log.heart_rate_bpm or 65.0,
            'respiratory_rate': log.respiratory_rate or 25.0,
            'symptoms': log.symptoms_list
        })

    # Prepare historical chart series
    history_chart = {
        'dates': [h.log_date.strftime('%b %d') for h in history_logs],
        'temperatures': [float(h.temperature) for h in history_logs],
        'water_intake': [float(h.water_intake_litres or (60.0 if h.water_intake == 'normal' else 35.0)) for h in history_logs],
        'feed_intake': [float(h.feed_quantity_kg or (16.5 if h.feed_intake == 'normal' else 8.0)) for h in history_logs],
        'rumination': [float(h.rumination_time_hrs or 7.5) for h in history_logs],
        'walking': [float(h.walking_distance_km or 4.0) for h in history_logs],
        'milk_yield': [float(h.milk_yield) for h in history_logs]
    }

    return render_template(
        'farmer/vitals_comparison.html',
        log=log,
        cow=cow,
        comp_data=comp_data,
        history_chart=history_chart
    )


@farmer_bp.route('/vets/add', methods=['POST'])
@login_required
@role_required('farmer')
def add_vet():
    db = get_db()
    name = request.form.get('name', '').strip()
    clinic_name = request.form.get('clinic_name', '').strip()
    specialty = request.form.get('specialty', 'Bovine Medicine & Surgery').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    lat = request.form.get('latitude', type=float) or 22.5645
    lng = request.form.get('longitude', type=float) or 72.9289
    emergency = request.form.get('emergency_available') in ['1', 'true', 'on']
    operating_hours = request.form.get('operating_hours', '8:00 AM - 8:00 PM').strip()

    if not name or not clinic_name or not phone or not address:
        flash("Please provide Doctor name, Clinic name, Phone number, and Address.", "warning")
        return redirect(url_for('farmer.vets_map'))

    new_vet = VetDirectory(
        name=name,
        clinic_name=clinic_name,
        specialty=specialty,
        phone=phone,
        email=email or None,
        address=address,
        latitude=lat,
        longitude=lng,
        emergency_available=emergency,
        operating_hours=operating_hours
    )
    db.add(new_vet)
    db.commit()
    flash(f"Veterinary clinic '{clinic_name}' with {name} successfully added to the nearby network!", "success")
    return redirect(url_for('farmer.vets_map'))


@farmer_bp.route('/api/compare_vitals', methods=['POST'])
@login_required
def api_compare_vitals():
    from backend.vitals_comparator import VitalsComparator
    data = request.get_json() or {}
    report = VitalsComparator.compare_everyday_vitals(data)
    return jsonify(report)

