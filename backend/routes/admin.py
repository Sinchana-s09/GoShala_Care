import os
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from backend.database import get_db
from backend.db_models import (
    User, Cow, Case, Disease, Symptom, DiseaseSymptom, 
    VetDirectory, VitalsLog, PhotoScan
)
from backend.routes.auth import role_required
from backend.ml_service import MLService
from backend.ml_pipeline.train_tabular import train_tabular_pipeline
from backend.ml_pipeline.train_image import train_image_pipeline

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    db = get_db()
    cows_count = db.query(Cow).count()
    farmers_count = db.query(User).filter_by(role='farmer').count()
    vets_count = db.query(User).filter_by(role='vet').count()
    total_cases = db.query(Case).count()
    pending_cases = db.query(Case).filter_by(status='pending').count()
    diseases_count = db.query(Disease).count()
    clinics_count = db.query(VetDirectory).count()

    metrics = MLService.get_pipeline_metrics()
    tabular_acc = metrics.get('tabular_model', {}).get('accuracy', 'N/A')
    if isinstance(tabular_acc, float):
        tabular_acc = f"{tabular_acc * 100:.1f}%"

    image_acc = metrics.get('image_model', {}).get('accuracy', 'N/A')
    if isinstance(image_acc, float):
        image_acc = f"{image_acc * 100:.1f}%"

    recent_cases = db.query(Case).order_by(Case.created_at.desc()).limit(6).all()

    return render_template(
        'admin/dashboard.html',
        cows_count=cows_count,
        farmers_count=farmers_count,
        vets_count=vets_count,
        total_cases=total_cases,
        pending_cases=pending_cases,
        diseases_count=diseases_count,
        clinics_count=clinics_count,
        tabular_acc=tabular_acc,
        image_acc=image_acc,
        recent_cases=recent_cases
    )

# ----------------- User Management -----------------
@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def users():
    db = get_db()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'vet')
        phone = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()

        if not username or not email or not password or not full_name:
            flash("All mandatory fields must be completed.", "warning")
            return redirect(url_for('admin.users'))

        existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing:
            flash("Username or email already in use.", "danger")
            return redirect(url_for('admin.users'))

        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            phone=phone,
            location=location
        )
        new_user.set_password(password)
        db.add(new_user)
        db.commit()

        flash(f"New {role.upper()} account '{username}' created successfully.", "success")
        return redirect(url_for('admin.users'))

    all_users = db.query(User).order_by(User.role, User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user(user_id):
    db = get_db()
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for('admin.users'))
    if user.id == current_user.id:
        flash("You cannot deactivate your own administrative account.", "danger")
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.commit()
    status_str = "activated" if user.is_active else "deactivated"
    flash(f"User '{user.username}' has been {status_str}.", "info")
    return redirect(url_for('admin.users'))

# ----------------- Vet Directory Management -----------------
@admin_bp.route('/vets', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def vets():
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        clinic_name = request.form.get('clinic_name', '').strip()
        specialty = request.form.get('specialty', 'Bovine Medicine').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        emergency_available = bool(request.form.get('emergency_available'))
        operating_hours = request.form.get('operating_hours', '8:00 AM - 8:00 PM').strip()

        if not name or not clinic_name or not phone or latitude is None or longitude is None:
            flash("Name, Clinic Name, Phone, and Coordinates are required.", "warning")
            return redirect(url_for('admin.vets'))

        entry = VetDirectory(
            name=name,
            clinic_name=clinic_name,
            specialty=specialty,
            phone=phone,
            email=email,
            address=address,
            latitude=latitude,
            longitude=longitude,
            emergency_available=emergency_available,
            operating_hours=operating_hours
        )
        db.add(entry)
        db.commit()
        flash(f"Vet clinic '{clinic_name}' added to map directory.", "success")
        return redirect(url_for('admin.vets'))

    vets_list = db.query(VetDirectory).order_by(VetDirectory.id.desc()).all()
    return render_template('admin/vets.html', vets=vets_list)

@admin_bp.route('/vets/<int:vet_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_vet(vet_id):
    db = get_db()
    vet = db.query(VetDirectory).filter_by(id=vet_id).first()
    if not vet:
        flash("Vet clinic not found.", "warning")
        return redirect(url_for('admin.vets'))
    cname = vet.clinic_name
    db.delete(vet)
    db.commit()
    flash(f"Clinic '{cname}' removed from directory.", "info")
    return redirect(url_for('admin.vets'))

# ----------------- Disease & Symptom Reference Library -----------------
@admin_bp.route('/diseases', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def diseases():
    db = get_db()
    all_symptoms = db.query(Symptom).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        scientific_name = request.form.get('scientific_name', '').strip()
        urgency_level = request.form.get('urgency_level', 'Moderate')
        description = request.form.get('description', '').strip()
        key_indicators = request.form.get('key_indicators', '').strip()
        prevention_guidance = request.form.get('prevention_guidance', '').strip()
        first_aid = request.form.get('first_aid', '').strip()
        selected_symptoms = request.form.getlist('symptoms')

        if not name or not description or not prevention_guidance:
            flash("Disease Name, Description, and Prevention Guidance are required.", "warning")
            return redirect(url_for('admin.diseases'))

        existing = db.query(Disease).filter_by(name=name).first()
        if existing:
            flash(f"Disease '{name}' already exists in library.", "danger")
            return redirect(url_for('admin.diseases'))

        new_disease = Disease(
            name=name,
            scientific_name=scientific_name,
            urgency_level=urgency_level,
            description=description,
            key_indicators=key_indicators,
            prevention_guidance=prevention_guidance,
            first_aid=first_aid
        )
        db.add(new_disease)
        db.commit()

        for s_code in selected_symptoms:
            db.add(DiseaseSymptom(
                disease_id=new_disease.id,
                symptom_code=s_code,
                is_primary=True,
                weight=2.0
            ))
        db.commit()

        flash(f"Disease '{name}' successfully added to Clinical Knowledge Base & Rule Classifier!", "success")
        return redirect(url_for('admin.diseases'))

    diseases_list = db.query(Disease).order_by(Disease.name).all()
    return render_template('admin/diseases.html', diseases=diseases_list, symptoms=all_symptoms)

@admin_bp.route('/diseases/<int:disease_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_disease(disease_id):
    db = get_db()
    disease = db.query(Disease).filter_by(id=disease_id).first()
    if not disease:
        flash("Disease record not found.", "warning")
        return redirect(url_for('admin.diseases'))
    dname = disease.name
    db.delete(disease)
    db.commit()
    flash(f"Disease '{dname}' deleted from reference library and rule engine.", "info")
    return redirect(url_for('admin.diseases'))

# ----------------- Data Science Pipeline & Status -----------------
@admin_bp.route('/pipeline_status')
@login_required
@role_required('admin')
def pipeline_status():
    metrics = MLService.get_pipeline_metrics()
    tabular = metrics.get('tabular_model', {})
    image = metrics.get('image_model', {})
    
    return render_template(
        'admin/pipeline_status.html',
        tabular=tabular,
        image=image
    )

@admin_bp.route('/pipeline/retrain', methods=['POST'])
@login_required
@role_required('admin')
def retrain_models():
    """Trigger retrain of Tabular and Image models from datasets."""
    try:
        train_tabular_pipeline()
        train_image_pipeline()
        MLService.load_models()
        flash("ML Pipeline successfully re-trained on latest datasets! Models and metrics updated.", "success")
    except Exception as e:
        flash(f"Retraining encountered an error: {e}", "danger")
    return redirect(url_for('admin.pipeline_status'))
