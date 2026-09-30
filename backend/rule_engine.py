from typing import List, Dict, Any, Tuple
from datetime import timedelta
from backend.database import get_db
from backend.db_models import Disease, DiseaseSymptom, VitalsLog

class RuleEngine:
    """
    Explainable, threshold-based Cattle Disease Rule Engine.
    Directly backed by the database's Disease and DiseaseSymptom tables.
    """

    @staticmethod
    def evaluate(
        current_vitals: Dict[str, Any],
        recent_history: List[VitalsLog] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a daily vitals log against clinical rules and thresholds.
        
        current_vitals: dict containing:
          - temperature (float)
          - feed_intake ('normal', 'reduced', 'none')
          - water_intake ('normal', 'reduced', 'none')
          - milk_yield (float)
          - symptoms (list of symptom codes)
          - other_symptoms (str)
        """
        temp = float(current_vitals.get('temperature', 38.5))
        feed = current_vitals.get('feed_intake', 'normal')
        water = current_vitals.get('water_intake', 'normal')
        milk = float(current_vitals.get('milk_yield', 0.0))
        symptoms = set(current_vitals.get('symptoms', []))
        
        matched_rules = []
        rule_risk = 'Low'
        base_score = 0.05
        suspected_diseases = []

        # 1. Temperature Threshold Checks (Bovine Normal: 38.0°C - 39.3°C)
        if temp > 40.2:
            matched_rules.append(
                f"Critical Hyperthermia: Temperature is {temp:.1f}°C (>40.2°C indicates severe acute infection or toxemia)."
            )
            rule_risk = 'High'
            base_score = max(base_score, 0.85)
        elif temp > 39.3:
            matched_rules.append(
                f"Elevated Fever: Temperature is {temp:.1f}°C (Normal bovine range: 38.0°C - 39.3°C)."
            )
            if rule_risk != 'High':
                rule_risk = 'Moderate'
            base_score = max(base_score, 0.50)
        elif temp < 37.5:
            matched_rules.append(
                f"Severe Hypothermia: Temperature is {temp:.1f}°C (<37.5°C indicates circulatory collapse, shock, or advanced milk fever)."
            )
            rule_risk = 'High'
            base_score = max(base_score, 0.85)
        elif temp < 38.0:
            matched_rules.append(
                f"Subnormal Temperature: Temperature is {temp:.1f}°C (Below normal 38.0°C)."
            )
            if rule_risk != 'High':
                rule_risk = 'Moderate'
            base_score = max(base_score, 0.45)

        # 2. Feed & Water Intake Checks
        if feed == 'none' and water == 'none':
            matched_rules.append("Critical Inappetence: Complete cessation of both feed and water intake (aphagia/anorexia).")
            rule_risk = 'High'
            base_score = max(base_score, 0.80)
        elif feed == 'none':
            matched_rules.append("Severe Inappetence: Cow has completely stopped eating (no cudding/anorexia).")
            if rule_risk != 'High':
                rule_risk = 'Moderate'
            base_score = max(base_score, 0.60)
        elif feed == 'reduced' and water == 'reduced':
            matched_rules.append("Decreased Feed & Water Intake: Simultaneous drop in feed and hydration.")
            if rule_risk == 'Low':
                rule_risk = 'Moderate'
            base_score = max(base_score, 0.40)

        # 3. Rolling History Trend Checks (Last 3-7 Days)
        if recent_history and len(recent_history) > 0:
            # Check consecutive days of none/reduced feed
            prev_none_count = sum(1 for log in recent_history[:2] if log.feed_intake == 'none')
            if feed == 'none' and prev_none_count >= 1:
                matched_rules.append("Persistent Anorexia: Cow has refused feed for 2 or more consecutive days.")
                rule_risk = 'High'
                base_score = max(base_score, 0.85)

            # Rolling milk yield drop comparison
            past_milk_values = [log.milk_yield for log in recent_history if log.milk_yield > 0]
            if past_milk_values:
                baseline_milk = sum(past_milk_values) / len(past_milk_values)
                if baseline_milk > 2.0:
                    pct_drop = ((baseline_milk - milk) / baseline_milk) * 100.0
                    if pct_drop >= 35.0:
                        matched_rules.append(
                            f"Acute Milk Yield Drop: Today's milk ({milk:.1f}L) dropped by {pct_drop:.1f}% compared to recent baseline ({baseline_milk:.1f}L)."
                        )
                        rule_risk = 'High'
                        base_score = max(base_score, 0.75)
                    elif pct_drop >= 20.0:
                        matched_rules.append(
                            f"Moderate Milk Yield Drop: Today's milk ({milk:.1f}L) dropped by {pct_drop:.1f}% vs baseline ({baseline_milk:.1f}L)."
                        )
                        if rule_risk == 'Low':
                            rule_risk = 'Moderate'
                        base_score = max(base_score, 0.45)

            # Temperature drift trend
            prev_temps = [log.temperature for log in recent_history[:3]]
            if prev_temps:
                avg_prev_temp = sum(prev_temps) / len(prev_temps)
                temp_drift = temp - avg_prev_temp
                if temp_drift >= 1.2:
                    matched_rules.append(
                        f"Rapid Temperature Surge: Current temperature spiked by +{temp_drift:.1f}°C over the 3-day baseline."
                    )
                    if rule_risk != 'High':
                        rule_risk = 'Moderate'
                    base_score = max(base_score, 0.55)

        # 4. Disease Symptom Matching from Database Library
        db = get_db()
        try:
            diseases = db.query(Disease).all()
            for d in diseases:
                d_symptoms = db.query(DiseaseSymptom).filter_by(disease_id=d.id).all()
                if not d_symptoms:
                    continue
                
                matched_disease_syms = []
                primary_matched = 0
                total_weight = 0.0
                max_weight = sum(ds.weight for ds in d_symptoms) or 1.0

                for ds in d_symptoms:
                    if ds.symptom_code in symptoms:
                        matched_disease_syms.append(ds.symptom_code)
                        total_weight += ds.weight
                        if ds.is_primary:
                            primary_matched += 1

                # If primary symptoms or significant symptoms matched
                if primary_matched > 0:
                    match_percentage = min(100.0, (total_weight / max_weight) * 100.0)
                    suspected_diseases.append({
                        'disease_name': d.name,
                        'urgency': d.urgency_level,
                        'match_score': round(total_weight, 2),
                        'confidence': round(match_percentage, 1),
                        'matched_symptoms': matched_disease_syms,
                        'prevention': d.prevention_guidance,
                        'first_aid': d.first_aid
                    })

                    # Disease specific alert messages
                    sym_display = ", ".join(matched_disease_syms).replace('_', ' ')
                    matched_rules.append(
                        f"Clinical Symptom Match: Symptoms [{sym_display}] match key markers for {d.name} ({d.urgency_level} urgency)."
                    )

                    if d.urgency_level == 'High':
                        rule_risk = 'High'
                        base_score = max(base_score, 0.80)
                    elif d.urgency_level == 'Moderate' and rule_risk == 'Low':
                        rule_risk = 'Moderate'
                        base_score = max(base_score, 0.50)

        except Exception as e:
            # Safe fallback if db query fails
            print(f"[RuleEngine Error] {e}")

        # Sort suspected diseases by match score descending
        suspected_diseases.sort(key=lambda x: x['match_score'], reverse=True)

        return {
            'risk_level': rule_risk,
            'risk_score': round(base_score, 3),
            'matched_rules': matched_rules,
            'suspected_diseases': suspected_diseases,
            'primary_disease': suspected_diseases[0]['disease_name'] if suspected_diseases else None
        }
