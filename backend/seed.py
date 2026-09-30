from datetime import datetime, date, timedelta
import json
from backend.database import get_db, create_all_tables
from backend.db_models import (
    User, Cow, Disease, Symptom, DiseaseSymptom, 
    VitalsLog, Case, VetDirectory
)

def run_seed():
    create_all_tables()
    db = get_db()

    print("[GoShala Seed] Checking existing data...")

    # 1. Default Users
    admin_user = db.query(User).filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@goshala.org',
            full_name='System Administrator',
            role='admin',
            phone='+91 99000 11223',
            location='Central Command, Anand'
        )
        admin_user.set_password('Admin@123')
        db.add(admin_user)
        print("  -> Created Admin user: admin / Admin@123")

    vet_user = db.query(User).filter_by(username='dr_ramesh').first()
    if not vet_user:
        vet_user = User(
            username='dr_ramesh',
            email='dr.ramesh@kamdhenuvet.in',
            full_name='Dr. Ramesh Patel, MVSc',
            role='vet',
            phone='+91 98250 12345',
            location='Kamdhenu Bovine Care, Anand'
        )
        vet_user.set_password('Vet@123')
        db.add(vet_user)
        print("  -> Created Vet user: dr_ramesh / Vet@123")

    farmer_user = db.query(User).filter_by(username='ramesh_farmer').first()
    if not farmer_user:
        farmer_user = User(
            username='ramesh_farmer',
            email='farmer.ramesh@gmail.com',
            full_name='Ramesh Bhai Patel',
            role='farmer',
            phone='+91 98980 54321',
            location='Mogri Village, Anand'
        )
        farmer_user.set_password('Farmer@123')
        db.add(farmer_user)
        print("  -> Created Farmer user: ramesh_farmer / Farmer@123")

    db.commit()

    # 2. Symptoms
    symptoms_data = [
        ('fever', 'High Fever (>39.5°C)', 'Systemic', 1.8),
        ('milk_drop', 'Sudden Sharp Milk Drop (>30%)', 'Production', 1.6),
        ('mouth_blisters', 'Drooling / Mouth Blisters & Erosions', 'Oral/Head', 2.0),
        ('skin_lumps', 'Skin Lumps, Nodules or Scabs', 'Dermatological', 1.9),
        ('limping', 'Limping / Hoof Sores / Foot Lesions', 'Locomotive', 1.5),
        ('not_eating', 'Not Eating / No Cudding / Off Feed', 'Digestive', 1.7),
        ('swollen_udder', 'Hot, Hard or Swollen Udder / Clots in Milk', 'Mammary', 2.0),
        ('bloat', 'Swollen Left Belly / Severe Bloat', 'Digestive', 2.0),
        ('downer_cow', 'Unable to Stand / Downer Cow After Calving', 'Metabolic', 2.0),
        ('abortion', 'Abortion / Retained Placenta / Discharge', 'Reproductive', 1.8),
        ('leg_swelling', 'Crackling Leg/Shoulder Swelling (Crepitus)', 'Musculoskeletal', 2.0),
        ('breathing_difficulty', 'Rapid Grunting Breathing / Froth from Nostrils', 'Respiratory', 1.9),
        ('sweet_breath', 'Sweet Acetone Smell in Breath or Milk', 'Metabolic', 1.5),
        ('tremor_cold_ears', 'Muscle Tremors, Staggering, Cold Ears', 'Metabolic', 1.8)
    ]
    for code, name, cat, weight in symptoms_data:
        if not db.query(Symptom).filter_by(code=code).first():
            db.add(Symptom(code=code, display_name=name, category=cat, severity_weight=weight))
    db.commit()

    # 3. Diseases & Mappings
    diseases_data = [
        {
            'name': 'Mastitis',
            'scientific_name': 'Bovine Mastitis (Streptococcus / Staph aureus)',
            'urgency_level': 'High',
            'description': 'Inflammation of the mammary gland caused by bacterial infection through teat canals. Causes severe economic loss and milk spoilage.',
            'key_indicators': 'Hot, hard, painful swollen udder, watery or clotted milk, abrupt reduction in milk yield, fever.',
            'prevention_guidance': 'Dip teats in antiseptic iodine post-milking, maintain clean dry bedding, disinfect milking equipment, practice good hand hygiene.',
            'first_aid': 'Isolate affected quarter, milk out gently, apply cold compress if acute inflammation, administer vet-prescribed intramammary antibiotics.',
            'symptoms': [('swollen_udder', True, 2.5), ('milk_drop', True, 2.0), ('fever', False, 1.2)]
        },
        {
            'name': 'Foot-and-Mouth Disease (FMD)',
            'scientific_name': 'Aphthovirus',
            'urgency_level': 'High',
            'description': 'Highly contagious viral disease affecting cloven-hoofed animals. Rapidly spreads through aerosol, direct contact, and contaminated feed.',
            'key_indicators': 'Excessive frothy salivation, blister-like vesicles on tongue, lips, and interdigital clefts of hooves, severe lameness, high fever.',
            'prevention_guidance': 'Strict biosecurity, mandatory 6-month vaccination, quarantine new stock for 21 days, disinfect farm gate with 4% sodium carbonate.',
            'first_aid': 'Isolate cow immediately. Wash mouth with 1% potassium permanganate or mild alum solution, treat foot lesions with antiseptic fly-repellent paste. Contact veterinary authority.',
            'symptoms': [('mouth_blisters', True, 3.0), ('limping', True, 2.2), ('fever', True, 1.8), ('not_eating', False, 1.5)]
        },
        {
            'name': 'Lumpy Skin Disease (LSD)',
            'scientific_name': 'Capripoxvirus',
            'urgency_level': 'High',
            'description': 'Vector-borne viral disease characterized by firm round skin nodules, enlarged lymph nodes, and edema.',
            'key_indicators': 'Round, raised cutaneous nodules (2-5 cm) all over body, fever, watery eye discharge, swelling in dewlap and limbs.',
            'prevention_guidance': 'Annual homologous goat pox / LSD vaccine, control biting flies, ticks, and mosquitoes using neem/permethrin repellents.',
            'first_aid': 'Isolate animal in vector-proof enclosure. Clean open nodules with antiseptic solution (povidone-iodine), provide soft palatable feed and fresh water.',
            'symptoms': [('skin_lumps', True, 3.5), ('fever', True, 1.8), ('milk_drop', False, 1.3)]
        },
        {
            'name': 'Milk Fever (Hypocalcemia)',
            'scientific_name': 'Parturient Paresis',
            'urgency_level': 'High',
            'description': 'Acute metabolic disorder occurring around calving due to sudden calcium demand for colostrum production.',
            'key_indicators': 'Unable to stand (downer cow), S-shaped curve of neck, muscle tremors, cold ears and extremities, dilated pupils.',
            'prevention_guidance': 'Feed low-calcium diet during dry period to prime parathyroid hormone, provide oral calcium gel immediately before and after calving.',
            'first_aid': 'Do NOT drench liquid medications (high aspiration risk). Keep cow propped in sternal position with straw bales. Vet must urgently administer IV Calcium Borogluconate slowly.',
            'symptoms': [('downer_cow', True, 3.5), ('tremor_cold_ears', True, 2.5), ('not_eating', False, 1.2)]
        },
        {
            'name': 'Bloat (Tympanites)',
            'scientific_name': 'Ruminal Tympany',
            'urgency_level': 'High',
            'description': 'Excessive gas accumulation in rumen, either frothy (due to lush legumes) or free gas (esophageal obstruction). Can cause fatal asphyxiation.',
            'key_indicators': 'Distended left flank drum-tight, grunting, kicking at belly, labored mouth breathing, restlessness.',
            'prevention_guidance': 'Avoid sudden turnout onto lush wet clover/alfalfa pastures; feed dry hay before grazing green fodder.',
            'first_aid': 'For urgent relief, keep head elevated. Administer antifoaming agents (vegetable oil 500ml or dimethicone). In extreme life-threatening distress, veterinary emergency trocharization of left paralumbar fossa.',
            'symptoms': [('bloat', True, 3.5), ('breathing_difficulty', True, 2.0), ('not_eating', False, 1.5)]
        },
        {
            'name': 'Ketosis (Acetonemia)',
            'scientific_name': 'Bovine Ketosis',
            'urgency_level': 'Moderate',
            'description': 'Metabolic state of severe negative energy balance in high-yielding dairy cows during early lactation.',
            'key_indicators': 'Rapid loss of body condition, sweet acetone odor in breath/urine/milk, sudden drop in milk, partial anorexia (refusing grain but eating straw).',
            'prevention_guidance': 'Balanced transition diet with adequate non-fiber carbohydrates, avoid overconditioning before calving, feed propylene glycol or niacin.',
            'first_aid': 'Administer oral propylene glycol (250-400ml twice daily), intravenous dextrose 50%, and corticosteroids under vet supervision.',
            'symptoms': [('sweet_breath', True, 3.0), ('milk_drop', True, 2.0), ('not_eating', False, 1.6)]
        },
        {
            'name': 'Brucellosis',
            'scientific_name': 'Brucella abortus',
            'urgency_level': 'High',
            'description': 'Bacterial zoonotic disease causing reproductive failure, contagious abortion, and infertility. Poses high human transmission risk (undulant fever).',
            'key_indicators': 'Late-term abortion (between 5th and 8th months), retained placenta, uterine infection, testicular swelling in bulls.',
            'prevention_guidance': 'Vaccinate female calves at 4-8 months with Strain 19 or RB51. Never drink unpasteurized milk. Test and screen all new breeding stock.',
            'first_aid': 'Burn or deeply bury aborted fetus and placenta with quicklime. Disinfect area thoroughly with bleaching powder. Wear gloves. Consult veterinary authority.',
            'symptoms': [('abortion', True, 3.5), ('fever', False, 1.2)]
        },
        {
            'name': 'Black Quarter (BQ)',
            'scientific_name': 'Clostridium chauvoei',
            'urgency_level': 'High',
            'description': 'Acute bacterial soil-borne infection characterized by severe toxemia and gas-filled muscular necrosis, especially in young cattle (6-24 months).',
            'key_indicators': 'Crepitant (crackling sound on touch) swelling over hip, shoulder or chest, high fever, acute lameness, depression, dark dry skin over swelling.',
            'prevention_guidance': 'Annual vaccination before monsoon onset. Do not graze on newly excavated pastures.',
            'first_aid': 'Extremely urgent veterinary intervention required. High doses of crystalline penicillin if detected early; drain and oxygenate local wound tissue.',
            'symptoms': [('leg_swelling', True, 3.5), ('limping', True, 2.0), ('fever', True, 1.8)]
        }
    ]

    for d_info in diseases_data:
        d_obj = db.query(Disease).filter_by(name=d_info['name']).first()
        if not d_obj:
            d_obj = Disease(
                name=d_info['name'],
                scientific_name=d_info['scientific_name'],
                urgency_level=d_info['urgency_level'],
                description=d_info['description'],
                key_indicators=d_info['key_indicators'],
                prevention_guidance=d_info['prevention_guidance'],
                first_aid=d_info['first_aid']
            )
            db.add(d_obj)
            db.commit()
            for sym_code, is_prim, wt in d_info['symptoms']:
                db.add(DiseaseSymptom(disease_id=d_obj.id, symptom_code=sym_code, is_primary=is_prim, weight=wt))
            db.commit()

    # 4. Vet Directory
    vets_data = [
        ('Dr. Ramesh Patel, MVSc', 'Kamdhenu Bovine Care & Research Center', 'Bovine Surgery & Udder Health', '+91 98250 12345', 'dr.ramesh@kamdhenuvet.in', 'Near Dairy Circle, Anand, Gujarat 388001', 22.5645, 72.9289, True, '24/7 Emergency Service', vet_user.id),
        ('Dr. Sunita Sharma, Ph.D', 'Pashu Seva Kendra Veterinary Hospital', 'Epidemiology & Infectious Diseases', '+91 98765 43210', 'sunita.sharma@pashuseva.org', 'Station Road, Nadiad, Gujarat 387001', 22.6916, 72.8634, True, '8:00 AM - 9:00 PM', None),
        ('Dr. Arvind Joshi, MVSc', 'Amul Zone Mobile Cattle Dispensary', 'Reproductive Care & Nutrition', '+91 94270 56789', 'arvind.joshi@amulcare.in', 'Mogri Crossing, Vidyanagar, Gujarat 388120', 22.5510, 72.9150, False, '9:00 AM - 6:00 PM', None),
        ('Dr. Meera Kulkarni, BVSc', 'Surabhi Livestock Emergency Clinic', 'Metabolic Disorders & Calf Care', '+91 91234 56780', 'meera.vet@surabhicattle.com', 'Borsad Highway, Anand Rural, Gujarat 388540', 22.5200, 72.9000, True, '24/7 On-Call Support', None)
    ]
    for name, cname, spec, phone, email, addr, lat, lng, emerg, hrs, uid in vets_data:
        if not db.query(VetDirectory).filter_by(name=name).first():
            db.add(VetDirectory(
                name=name, clinic_name=cname, specialty=spec, phone=phone, email=email,
                address=addr, latitude=lat, longitude=lng, emergency_available=emerg,
                operating_hours=hrs, user_id=uid
            ))
    db.commit()

    # 5. Demo Cows for Farmer
    cows_data = [
        ('IN-GJ-001', 'Gauri', 'Gir', date(2021, 3, 15), 'Mid', None),
        ('IN-GJ-002', 'Lakshmi', 'Sahiwal', date(2020, 8, 20), 'Early', None),
        ('IN-GJ-003', 'Surabhi', 'Kankrej', date(2022, 1, 10), 'Late', None),
        ('IN-GJ-004', 'Nandi', 'Rathi', date(2019, 11, 5), 'Mid', None)
    ]
    created_cows = {}
    for tag, name, breed, dob, stage, photo in cows_data:
        cow = db.query(Cow).filter_by(farmer_id=farmer_user.id, tag_id=tag).first()
        if not cow:
            cow = Cow(
                farmer_id=farmer_user.id,
                tag_id=tag,
                name=name,
                breed=breed,
                date_of_birth=dob,
                lactation_stage=stage,
                photo_url=photo
            )
            db.add(cow)
            db.commit()
        created_cows[tag] = cow

    # 6. Historical Vitals Logs (Last 7 Days) for Gauri (Normal -> Symptoms Developing)
    today = date.today()
    gauri = created_cows['IN-GJ-001']
    if not db.query(VitalsLog).filter_by(cow_id=gauri.id).first():
        vitals_history = [
            (-6, 38.5, 'normal', 'normal', 14.5, [], 'Low', 0.05, 'Normal baseline vitals.'),
            (-5, 38.6, 'normal', 'normal', 14.2, [], 'Low', 0.06, 'Normal baseline vitals.'),
            (-4, 38.5, 'normal', 'normal', 14.0, [], 'Low', 0.08, 'Normal baseline vitals.'),
            (-3, 38.7, 'normal', 'normal', 13.8, [], 'Low', 0.12, 'Normal vitals.'),
            (-2, 39.1, 'reduced', 'normal', 12.0, ['fever'], 'Moderate', 0.45, 'Elevated temperature (39.1°C) and slight milk yield drop detected.'),
            (-1, 39.7, 'reduced', 'reduced', 9.5, ['fever', 'swollen_udder', 'milk_drop'], 'High', 0.88, 'RULE TRIGGERED: Udder inflammation + acute 32% milk drop + high fever (39.7°C). High risk for Mastitis.')
        ]
        for days_ago, temp, feed, water, milk, syms, risk, score, expl in vitals_history:
            log_dt = today + timedelta(days=days_ago)
            vlog = VitalsLog(
                cow_id=gauri.id,
                farmer_id=farmer_user.id,
                log_date=log_dt,
                temperature=temp,
                feed_intake=feed,
                water_intake=water,
                milk_yield=milk,
                symptoms_json=json.dumps(syms),
                calculated_risk=risk,
                risk_score=score,
                explanation=expl
            )
            db.add(vlog)
        db.commit()

        # Create a flagged case in Vet queue for Gauri
        latest_log = db.query(VitalsLog).filter_by(cow_id=gauri.id).order_by(VitalsLog.id.desc()).first()
        demo_case = Case(
            case_number='CASE-2026-0001',
            cow_id=gauri.id,
            farmer_id=farmer_user.id,
            source='vitals',
            vitals_log_id=latest_log.id,
            suspected_disease='Mastitis',
            urgency='High',
            status='pending',
            rule_explanation='Explicit Rule Matched: Acute udder inflammation (hot/hard/swollen) paired with >30% milk decline and high fever (>39.5°C).',
            ml_prediction_summary='Tabular Model: Mastitis Probability 89.4%, Urgency: High. Trend Features: -32.1% milk drop over 3 days, +1.2°C temperature drift.'
        )
        db.add(demo_case)
        db.commit()

    # Seed logs for Lakshmi (Healthy)
    lakshmi = created_cows['IN-GJ-002']
    if not db.query(VitalsLog).filter_by(cow_id=lakshmi.id).first():
        for i in range(6, -1, -1):
            log_dt = today - timedelta(days=i)
            vlog = VitalsLog(
                cow_id=lakshmi.id,
                farmer_id=farmer_user.id,
                log_date=log_dt,
                temperature=38.4 + (i % 3) * 0.1,
                feed_intake='normal',
                water_intake='normal',
                milk_yield=16.0 - (i % 2) * 0.4,
                symptoms_json=json.dumps([]),
                calculated_risk='Low',
                risk_score=0.04,
                explanation='Optimal health parameters.'
            )
            db.add(vlog)
        db.commit()

    print("[GoShala Seed] Completed successfully.")

if __name__ == '__main__':
    run_seed()
