import math
from typing import Dict, Any, List, Optional

# Standard veterinary baseline requirements for healthy adult dairy/indigenous cattle
REQUIRED_DAILY_BENCHMARKS = {
    'temperature': {
        'name': 'Body Temperature',
        'unit': '°C',
        'min_normal': 38.2,
        'max_normal': 39.3,
        'optimal': 38.5,
        'critical_low': 37.5,
        'critical_high': 40.2,
        'category': 'Vitals',
        'description': 'Core bovine body temperature. Normal is 38.5°C.'
    },
    'feed_quantity_kg': {
        'name': 'Feed Intake (Dry Matter & Green)',
        'unit': 'kg/day',
        'min_normal': 12.0,
        'max_normal': 22.0,
        'optimal': 16.5,
        'critical_low': 6.0,
        'critical_high': 30.0,
        'category': 'Nutrition',
        'description': 'Daily feed consumption required for rumen microflora maintenance and body weight.'
    },
    'water_intake_litres': {
        'name': 'Water Intake',
        'unit': 'L/day',
        'min_normal': 45.0,
        'max_normal': 75.0,
        'optimal': 60.0,
        'critical_low': 25.0,
        'critical_high': 100.0,
        'category': 'Hydration',
        'description': 'Crucial for milk synthesis, temperature regulation, and ruminal fermentation.'
    },
    'walking_distance_km': {
        'name': 'Physical Activity (Walking / Steps)',
        'unit': 'km/day',
        'min_normal': 3.0,
        'max_normal': 6.5,
        'optimal': 4.5,
        'critical_low': 1.2,
        'critical_high': 10.0,
        'category': 'Activity',
        'description': 'Daily mobility and paddock exercise. Marked reduction indicates lameness, foot rot, or lethargy.'
    },
    'rumination_time_hrs': {
        'name': 'Rumination Time (Cud Chewing)',
        'unit': 'hrs/day',
        'min_normal': 6.5,
        'max_normal': 9.5,
        'optimal': 8.0,
        'critical_low': 3.5,
        'critical_high': 12.0,
        'category': 'Digestive',
        'description': 'Time spent regurgitating and re-chewing cud. Sensitive early indicator of digestive disorders.'
    },
    'resting_hours': {
        'name': 'Resting & Lying Duration',
        'unit': 'hrs/day',
        'min_normal': 8.5,
        'max_normal': 12.5,
        'optimal': 10.5,
        'critical_low': 5.0,
        'critical_high': 16.0,
        'category': 'Welfare',
        'description': 'Resting time facilitates blood circulation to the mammary gland for milk production.'
    },
    'heart_rate_bpm': {
        'name': 'Heart Rate',
        'unit': 'bpm',
        'min_normal': 50.0,
        'max_normal': 78.0,
        'optimal': 64.0,
        'critical_low': 40.0,
        'critical_high': 95.0,
        'category': 'Vitals',
        'description': 'Circulatory rate. High rate indicates fever, septicemia, or acute pain.'
    },
    'respiratory_rate': {
        'name': 'Respiratory Rate',
        'unit': 'breaths/min',
        'min_normal': 20.0,
        'max_normal': 32.0,
        'optimal': 25.0,
        'critical_low': 14.0,
        'critical_high': 45.0,
        'category': 'Vitals',
        'description': 'Breaths per minute. Rapid breathing signals bovine respiratory disease, pneumonia, or heat stress.'
    },
    'milk_yield': {
        'name': 'Milk Yield',
        'unit': 'L/day',
        'min_normal': 8.0,
        'max_normal': 20.0,
        'optimal': 12.0,
        'critical_low': 2.0,
        'critical_high': 35.0,
        'category': 'Production',
        'description': 'Daily milk harvest. Sudden drop (> 25%) is often the earliest signal of subclinical or clinical mastitis.'
    }
}

# Empirical disease profiles derived from the 250,000-record Global Cattle Dataset & Veterinary Literature
DATASET_DISEASE_PROFILES = {
    'Healthy': {
        'name': 'Normal Healthy Baseline',
        'description': 'Balanced vitals, optimal rumination, active grazing, consistent milk production.',
        'vitals': {
            'temperature': 38.5,
            'feed_quantity_kg': 16.0,
            'water_intake_litres': 65.0,
            'walking_distance_km': 4.5,
            'rumination_time_hrs': 8.0,
            'resting_hours': 10.0,
            'heart_rate_bpm': 64.0,
            'respiratory_rate': 25.0,
            'milk_yield': 12.0
        },
        'key_hallmarks': ['Normal body temperature', 'Consistent rumination > 7h', 'Good appetite and water intake']
    },
    'Mastitis_Clinical': {
        'name': 'Clinical Mastitis',
        'description': 'Acute or chronic mammary infection causing milk drop, udder swelling, and mild to moderate fever.',
        'vitals': {
            'temperature': 39.4,
            'feed_quantity_kg': 11.0,
            'water_intake_litres': 52.0,
            'walking_distance_km': 3.2,
            'rumination_time_hrs': 6.0,
            'resting_hours': 12.5,
            'heart_rate_bpm': 76.0,
            'respiratory_rate': 28.0,
            'milk_yield': 5.5
        },
        'key_hallmarks': ['Severe milk drop (> 40%)', 'Udder warmth or hardness', 'Reduced rumination']
    },
    'Foot_and_Mouth': {
        'name': 'Foot and Mouth Disease (FMD)',
        'description': 'Highly contagious viral disease characterized by vesicles on oral mucosa, tongue, and interdigital clefts.',
        'vitals': {
            'temperature': 40.2,
            'feed_quantity_kg': 6.5,
            'water_intake_litres': 38.0,
            'walking_distance_km': 1.2,
            'rumination_time_hrs': 3.5,
            'resting_hours': 14.0,
            'heart_rate_bpm': 86.0,
            'respiratory_rate': 36.0,
            'milk_yield': 3.0
        },
        'key_hallmarks': ['High fever (> 40°C)', 'Severe mobility drop (lameness)', 'Excessive salivation', 'Off feed']
    },
    'Lumpy_Skin_Disease': {
        'name': 'Lumpy Skin Disease (LSD)',
        'description': 'Capripoxvirus infection causing firm circumscribed nodules on skin, fever, and enlarged superficial lymph nodes.',
        'vitals': {
            'temperature': 39.9,
            'feed_quantity_kg': 9.0,
            'water_intake_litres': 45.0,
            'walking_distance_km': 2.5,
            'rumination_time_hrs': 5.0,
            'resting_hours': 12.0,
            'heart_rate_bpm': 78.0,
            'respiratory_rate': 30.0,
            'milk_yield': 4.8
        },
        'key_hallmarks': ['High persistent fever', 'Cutaneous nodules', 'Nasal discharge', 'Reduced yield']
    },
    'Bovine_Respiratory_Disease': {
        'name': 'Bovine Respiratory Disease / Pneumonia',
        'description': 'Infectious bronchopneumonia presenting with dyspnea, tachypnea, fever, coughing, and bilateral nasal discharge.',
        'vitals': {
            'temperature': 40.0,
            'feed_quantity_kg': 8.5,
            'water_intake_litres': 48.0,
            'walking_distance_km': 2.0,
            'rumination_time_hrs': 4.2,
            'resting_hours': 13.0,
            'heart_rate_bpm': 88.0,
            'respiratory_rate': 42.0,
            'milk_yield': 5.0
        },
        'key_hallmarks': ['High respiratory rate (> 38 bpm)', 'Coughing / nasal discharge', 'High fever']
    },
    'Ketosis_Acidosis': {
        'name': 'Ketosis / Rumen Acidosis',
        'description': 'Metabolic disorder caused by negative energy balance or carbohydrate overload, depressing rumination and milk.',
        'vitals': {
            'temperature': 38.3,
            'feed_quantity_kg': 7.0,
            'water_intake_litres': 40.0,
            'walking_distance_km': 2.8,
            'rumination_time_hrs': 3.8,
            'resting_hours': 12.0,
            'heart_rate_bpm': 68.0,
            'respiratory_rate': 24.0,
            'milk_yield': 6.0
        },
        'key_hallmarks': ['Sharply reduced rumination (< 4.5h)', 'Sweet ketone breath or diarrhea', 'Selective inappetence']
    },
    'Heat_Stress': {
        'name': 'Heat Stress & Hyperthermia',
        'description': 'Environmental heat load exceeding cooling capacity; marked by panting, elevated water demand, and drop in production.',
        'vitals': {
            'temperature': 39.6,
            'feed_quantity_kg': 10.5,
            'water_intake_litres': 92.0,
            'walking_distance_km': 2.4,
            'rumination_time_hrs': 5.2,
            'resting_hours': 8.0,
            'heart_rate_bpm': 82.0,
            'respiratory_rate': 46.0,
            'milk_yield': 7.5
        },
        'key_hallmarks': ['Extreme water intake (> 80L)', 'Rapid shallow panting (> 40 bpm)', 'Elevated temperature']
    },
    'Milk_Fever': {
        'name': 'Milk Fever (Hypocalcemia / Downer Cow)',
        'description': 'Acute blood calcium deficiency around calving; results in flaccid paralysis, cold extremities, and subnormal temperature.',
        'vitals': {
            'temperature': 37.4,
            'feed_quantity_kg': 2.0,
            'water_intake_litres': 18.0,
            'walking_distance_km': 0.3,
            'rumination_time_hrs': 1.0,
            'resting_hours': 18.0,
            'heart_rate_bpm': 85.0,
            'respiratory_rate': 18.0,
            'milk_yield': 2.0
        },
        'key_hallmarks': ['Subnormal body temp (< 38.0°C)', 'Inability to stand (sternal recumbency)', 'Cold ears/extremities']
    }
}


class VitalsComparator:
    """
    Compares everyday cow vitals and physical activity logs against:
    1. Normal Required Scientific Benchmarks
    2. Empirical Disease Profiles from the Global Cattle Dataset
    """

    @classmethod
    def compare_everyday_vitals(
        cls,
        logged_vitals: Dict[str, Any],
        historical_logs: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Takes raw daily vitals input (dict) and generates a detailed comparison report
        showing status, percentage deviation, and diagnostic recommendations.
        """
        comparisons = []
        abnormal_count = 0
        warning_count = 0
        critical_count = 0

        # Normalization of fields
        temp = float(logged_vitals.get('temperature') or 38.5)
        feed_kg = float(logged_vitals.get('feed_quantity_kg') or (16.0 if logged_vitals.get('feed_intake') == 'normal' else (8.0 if logged_vitals.get('feed_intake') == 'reduced' else 2.0)))
        water_l = float(logged_vitals.get('water_intake_litres') or (60.0 if logged_vitals.get('water_intake') == 'normal' else (35.0 if logged_vitals.get('water_intake') == 'reduced' else 15.0)))
        walking_km = float(logged_vitals.get('walking_distance_km') or 4.0)
        rumination_hrs = float(logged_vitals.get('rumination_time_hrs') or 7.5)
        resting_hrs = float(logged_vitals.get('resting_hours') or 10.0)
        heart_bpm = float(logged_vitals.get('heart_rate_bpm') or 65.0)
        resp_rate = float(logged_vitals.get('respiratory_rate') or 25.0)
        milk_l = float(logged_vitals.get('milk_yield') or 0.0)

        current_values = {
            'temperature': temp,
            'feed_quantity_kg': feed_kg,
            'water_intake_litres': water_l,
            'walking_distance_km': walking_km,
            'rumination_time_hrs': rumination_hrs,
            'resting_hours': resting_hrs,
            'heart_rate_bpm': heart_bpm,
            'respiratory_rate': resp_rate,
            'milk_yield': milk_l
        }

        for key, bench in REQUIRED_DAILY_BENCHMARKS.items():
            val = current_values.get(key, bench['optimal'])
            min_n = bench['min_normal']
            max_n = bench['max_normal']
            opt = bench['optimal']
            crit_low = bench['critical_low']
            crit_high = bench['critical_high']

            # Calculate % deviation from optimal standard
            pct_deviation = round(((val - opt) / opt) * 100.0, 1)

            # Determine clinical status
            if val < crit_low:
                status = 'Critically Low'
                badge_class = 'danger'
                critical_count += 1
                tip = f"Dangerous deficit. Immediate veterinary intervention recommended for severe {bench['name'].lower()} collapse."
            elif val > crit_high:
                status = 'Critically High'
                badge_class = 'danger'
                critical_count += 1
                tip = f"Dangerously elevated. Extreme risk threshold exceeded for {bench['name'].lower()}."
            elif val < min_n:
                status = 'Below Normal'
                badge_class = 'warning'
                warning_count += 1
                tip = f"Below optimal bovine baseline ({min_n} - {max_n} {bench['unit']}). Monitor closely for progression."
            elif val > max_n:
                status = 'Above Normal'
                badge_class = 'warning'
                warning_count += 1
                tip = f"Elevated above standard range ({min_n} - {max_n} {bench['unit']}). Assess for underlying fever or stress."
            else:
                status = 'Optimal'
                badge_class = 'success'
                tip = f"Within standard required healthy range ({min_n} - {max_n} {bench['unit']})."

            comparisons.append({
                'key': key,
                'name': bench['name'],
                'category': bench['category'],
                'current_value': val,
                'unit': bench['unit'],
                'required_min': min_n,
                'required_max': max_n,
                'optimal': opt,
                'pct_deviation': pct_deviation,
                'status': status,
                'badge_class': badge_class,
                'clinical_tip': tip
            })

        # Calculate Overall Health Index (0 - 100)
        penalty = (critical_count * 25.0) + (warning_count * 10.0)
        health_index = max(10, min(100, round(100.0 - penalty)))

        # Disease Dataset Pattern Matching
        dataset_matches = cls._match_disease_profiles(current_values, logged_vitals.get('symptoms', []))

        return {
            'health_index': health_index,
            'summary_status': 'Optimal' if critical_count == 0 and warning_count <= 1 else ('Warning' if critical_count == 0 else 'Critical Alert'),
            'critical_count': critical_count,
            'warning_count': warning_count,
            'comparisons': comparisons,
            'current_values': current_values,
            'dataset_matches': dataset_matches,
            'top_match': dataset_matches[0] if dataset_matches else None
        }

    @classmethod
    def _match_disease_profiles(
        cls,
        current_vitals: Dict[str, float],
        symptoms: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Calculates similarity scores (0-100%) against each condition profile in the dataset.
        Combines vital vector distance and symptom hallmark matching.
        """
        matches = []
        symptom_set = set(symptoms or [])

        # Weights for vitals distance
        v_weights = {
            'temperature': 3.5,
            'milk_yield': 2.5,
            'water_intake_litres': 2.0,
            'feed_quantity_kg': 2.0,
            'rumination_time_hrs': 2.5,
            'respiratory_rate': 2.0,
            'walking_distance_km': 1.5,
            'heart_rate_bpm': 1.5,
            'resting_hours': 1.0
        }

        for disease_key, profile in DATASET_DISEASE_PROFILES.items():
            dist_sq = 0.0
            total_weight = 0.0

            for v_key, weight in v_weights.items():
                cur = current_vitals.get(v_key, 0.0)
                target = profile['vitals'].get(v_key, 0.0)
                # Standardize scale difference
                denom = max(1.0, REQUIRED_DAILY_BENCHMARKS[v_key]['max_normal'] - REQUIRED_DAILY_BENCHMARKS[v_key]['min_normal'])
                norm_diff = (cur - target) / denom
                dist_sq += weight * (norm_diff ** 2)
                total_weight += weight

            # Exponential decay to similarity score between 0 and 100
            weighted_rmse = math.sqrt(dist_sq / total_weight)
            vital_similarity = math.exp(-0.85 * weighted_rmse) * 100.0

            # Symptom alignment bonus
            symptom_bonus = 0.0
            if disease_key == 'Mastitis_Clinical':
                if any(s in symptom_set for s in ['udder_swelling', 'udder_warmth', 'abnormal_milk', 'mastitis']):
                    symptom_bonus += 25.0
            elif disease_key == 'Foot_and_Mouth':
                if any(s in symptom_set for s in ['excessive_salivation', 'drooling', 'mouth_blisters', 'limping', 'lameness']):
                    symptom_bonus += 30.0
            elif disease_key == 'Lumpy_Skin_Disease':
                if any(s in symptom_set for s in ['skin_nodules', 'cutaneous_lumps', 'swollen_lymph']):
                    symptom_bonus += 30.0
            elif disease_key == 'Bovine_Respiratory_Disease':
                if any(s in symptom_set for s in ['nasal_discharge', 'coughing', 'rapid_breathing', 'dyspnea']):
                    symptom_bonus += 25.0
            elif disease_key == 'Ketosis_Acidosis':
                if any(s in symptom_set for s in ['sweet_breath', 'ketone_odor', 'diarrhea', 'off_feed']):
                    symptom_bonus += 20.0
            elif disease_key == 'Milk_Fever':
                if any(s in symptom_set for s in ['downer_cow', 'inability_to_stand', 'cold_ears', 'sternal_recumbency']):
                    symptom_bonus += 35.0

            # If healthy and symptoms present, penalize healthy match
            if disease_key == 'Healthy' and len(symptom_set) > 0:
                vital_similarity = max(5.0, vital_similarity - (len(symptom_set) * 15.0))

            final_score = min(99.0, max(1.0, vital_similarity + symptom_bonus))

            matches.append({
                'disease_key': disease_key,
                'name': profile['name'],
                'description': profile['description'],
                'similarity_score': round(final_score, 1),
                'key_hallmarks': profile['key_hallmarks'],
                'benchmark_vitals': profile['vitals']
            })

        # Sort descending by similarity score
        matches.sort(key=lambda m: m['similarity_score'], reverse=True)
        return matches
