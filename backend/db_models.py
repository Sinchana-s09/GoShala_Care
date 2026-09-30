from datetime import datetime
import json
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, Date, DateTime, 
    ForeignKey, Enum, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(60), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum('farmer', 'vet', 'admin', name='user_roles'), nullable=False, default='farmer', index=True)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    location = Column(String(150), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cows = relationship('Cow', back_populates='farmer', cascade='all, delete-orphan')
    vitals_logs = relationship('VitalsLog', back_populates='farmer', foreign_keys='VitalsLog.farmer_id')
    photo_scans = relationship('PhotoScan', back_populates='farmer', foreign_keys='PhotoScan.farmer_id')
    farmer_cases = relationship('Case', back_populates='farmer', foreign_keys='Case.farmer_id')
    assigned_cases = relationship('Case', back_populates='vet', foreign_keys='Case.assigned_vet_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_farmer(self):
        return self.role == 'farmer'

    @property
    def is_vet(self):
        return self.role == 'vet'

    @property
    def is_admin(self):
        return self.role == 'admin'


class Cow(Base):
    __tablename__ = 'cows'

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    tag_id = Column(String(50), nullable=False)
    name = Column(String(100), nullable=True)
    breed = Column(String(80), nullable=False, default='Indigenous / Gir')
    date_of_birth = Column(Date, nullable=True)
    lactation_stage = Column(Enum('Early', 'Mid', 'Late', 'Dry', 'Heifer', 'Calf', name='lactation_stages'), nullable=False, default='Mid')
    photo_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    farmer = relationship('User', back_populates='cows')
    vitals_logs = relationship('VitalsLog', back_populates='cow', cascade='all, delete-orphan', order_by='desc(VitalsLog.log_date)')
    photo_scans = relationship('PhotoScan', back_populates='cow', cascade='all, delete-orphan')
    cases = relationship('Case', back_populates='cow', cascade='all, delete-orphan')

    @property
    def latest_vitals(self):
        if self.vitals_logs:
            return self.vitals_logs[0]
        return None


class Disease(Base):
    __tablename__ = 'diseases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), unique=True, nullable=False)
    scientific_name = Column(String(150), nullable=True)
    urgency_level = Column(Enum('Low', 'Moderate', 'High', name='urgency_levels'), nullable=False, default='Moderate')
    description = Column(Text, nullable=False)
    key_indicators = Column(Text, nullable=True)
    prevention_guidance = Column(Text, nullable=False)
    first_aid = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    symptoms = relationship('DiseaseSymptom', back_populates='disease', cascade='all, delete-orphan')


class Symptom(Base):
    __tablename__ = 'symptoms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(120), nullable=False)
    category = Column(String(50), nullable=False, default='General')
    severity_weight = Column(Float, nullable=False, default=1.0)


class DiseaseSymptom(Base):
    __tablename__ = 'disease_symptoms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    disease_id = Column(Integer, ForeignKey('diseases.id', ondelete='CASCADE'), nullable=False)
    symptom_code = Column(String(50), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=True)
    weight = Column(Float, nullable=False, default=1.0)

    disease = relationship('Disease', back_populates='symptoms')


class VitalsLog(Base):
    __tablename__ = 'vitals_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cow_id = Column(Integer, ForeignKey('cows.id', ondelete='CASCADE'), nullable=False)
    farmer_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    log_date = Column(Date, nullable=False)
    temperature = Column(Float, nullable=False) # °C e.g., 38.6
    feed_intake = Column(Enum('normal', 'reduced', 'none', name='feed_intakes'), nullable=False, default='normal')
    water_intake = Column(Enum('normal', 'reduced', 'none', name='water_intakes'), nullable=False, default='normal')
    milk_yield = Column(Float, nullable=False, default=0.0) # Litres
    symptoms_json = Column(Text, nullable=True) # JSON list of string codes
    other_symptoms = Column(String(255), nullable=True)
    calculated_risk = Column(Enum('Low', 'Moderate', 'High', name='risk_levels'), nullable=False, default='Low')
    risk_score = Column(Float, nullable=False, default=0.0) # 0.0 - 1.0
    explanation = Column(Text, nullable=True)
    # Everyday Tracking & Physical Activity Requirements
    feed_quantity_kg = Column(Float, nullable=True, default=15.0) # kg food intake
    water_intake_litres = Column(Float, nullable=True, default=50.0) # litres water intake
    walking_distance_km = Column(Float, nullable=True, default=4.0) # km daily physical activity
    rumination_time_hrs = Column(Float, nullable=True, default=7.5) # daily rumination hours
    resting_hours = Column(Float, nullable=True, default=10.0) # daily resting hours
    heart_rate_bpm = Column(Float, nullable=True, default=65.0) # heart rate beats per min
    respiratory_rate = Column(Float, nullable=True, default=26.0) # breaths per min
    predicted_disease = Column(String(100), nullable=True) # classified disease e.g. Healthy, Mastitis
    comparison_data_json = Column(Text, nullable=True) # JSON storing comparison against normal & disease datasets
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    cow = relationship('Cow', back_populates='vitals_logs')
    farmer = relationship('User', back_populates='vitals_logs', foreign_keys=[farmer_id])

    @property
    def symptoms_list(self):
        if not self.symptoms_json:
            return []
        try:
            return json.loads(self.symptoms_json)
        except Exception:
            return []

    @symptoms_list.setter
    def symptoms_list(self, value):
        self.symptoms_json = json.dumps(value if isinstance(value, list) else [])

    @property
    def comparison_data(self):
        if not self.comparison_data_json:
            return {}
        try:
            return json.loads(self.comparison_data_json)
        except Exception:
            return {}


class PhotoScan(Base):
    __tablename__ = 'photo_scans'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cow_id = Column(Integer, ForeignKey('cows.id', ondelete='CASCADE'), nullable=False)
    farmer_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    image_path = Column(String(255), nullable=False)
    body_part = Column(Enum('skin', 'udder', 'hooves', 'general', name='body_parts'), nullable=False, default='general')
    predicted_label = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    detected_risk = Column(Enum('Low', 'Moderate', 'High', name='photo_risk_levels'), nullable=False, default='Low')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    cow = relationship('Cow', back_populates='photo_scans')
    farmer = relationship('User', back_populates='photo_scans', foreign_keys=[farmer_id])


class Case(Base):
    __tablename__ = 'cases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String(30), unique=True, nullable=False, index=True)
    cow_id = Column(Integer, ForeignKey('cows.id', ondelete='CASCADE'), nullable=False)
    farmer_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    source = Column(Enum('vitals', 'photo', 'combined', name='case_sources'), nullable=False, default='vitals')
    vitals_log_id = Column(Integer, ForeignKey('vitals_logs.id', ondelete='SET NULL'), nullable=True)
    photo_scan_id = Column(Integer, ForeignKey('photo_scans.id', ondelete='SET NULL'), nullable=True)
    suspected_disease = Column(String(120), nullable=True)
    urgency = Column(Enum('Low', 'Moderate', 'High', name='case_urgencies'), nullable=False, default='Moderate', index=True)
    status = Column(Enum('pending', 'in_review', 'resolved', 'closed', name='case_statuses'), nullable=False, default='pending', index=True)
    rule_explanation = Column(Text, nullable=True)
    ml_prediction_summary = Column(Text, nullable=True)
    assigned_vet_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    vet_notes = Column(Text, nullable=True)
    vet_recommendation = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cow = relationship('Cow', back_populates='cases')
    farmer = relationship('User', back_populates='farmer_cases', foreign_keys=[farmer_id])
    vet = relationship('User', back_populates='assigned_cases', foreign_keys=[assigned_vet_id])
    vitals_log = relationship('VitalsLog')
    photo_scan = relationship('PhotoScan')


class VetDirectory(Base):
    __tablename__ = 'vet_directory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    name = Column(String(120), nullable=False)
    clinic_name = Column(String(150), nullable=False)
    specialty = Column(String(100), nullable=False, default='Bovine Medicine & Surgery')
    phone = Column(String(30), nullable=False)
    email = Column(String(120), nullable=True)
    address = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    emergency_available = Column(Boolean, nullable=False, default=True)
    operating_hours = Column(String(100), default='8:00 AM - 8:00 PM')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
