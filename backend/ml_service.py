import os
import json
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import date

from backend.config import Config
from backend.rule_engine import RuleEngine
from backend.ml_pipeline.feature_engine import FeatureEngine, ALL_SYMPTOMS
from backend.ml_pipeline.train_image import extract_image_features
from backend.vitals_comparator import VitalsComparator

class MLService:
    """
    Live runtime inference engine combining Rule-Based Clinical Logic,
    Machine Learning Models, and Dataset Benchmark Comparisons for Cow Disease Detection.
    """
    _tabular_model = None
    _tabular_scaler = None
    _image_model_bundle = None

    @classmethod
    def load_models(cls):
        """Loads models lazily or on startup."""
        tabular_path = os.path.join(Config.MODELS_DIR, 'vitals_classifier.joblib')
        scaler_path = os.path.join(Config.MODELS_DIR, 'vitals_scaler.joblib')
        image_path = os.path.join(Config.MODELS_DIR, 'image_classifier.joblib')

        if os.path.exists(tabular_path) and os.path.exists(scaler_path):
            try:
                cls._tabular_model = joblib.load(tabular_path)
                cls._tabular_scaler = joblib.load(scaler_path)
            except Exception as e:
                print(f"[MLService] Error loading tabular model: {e}")

        if os.path.exists(image_path):
            try:
                cls._image_model_bundle = joblib.load(image_path)
            except Exception as e:
                print(f"[MLService] Error loading image model: {e}")

    @classmethod
    def classify_vitals(
        cls,
        cow_id: int,
        temperature: float,
        feed_intake: str,
        water_intake: str,
        milk_yield: float,
        symptoms: List[str],
        other_symptoms: Optional[str] = None,
        recent_history: Optional[List[Any]] = None,
        walking_distance_km: float = 4.0,
        rumination_time_hrs: float = 7.5,
        resting_hours: float = 10.0,
        heart_rate_bpm: float = 65.0,
        respiratory_rate: float = 25.0,
        feed_quantity_kg: Optional[float] = None,
        water_intake_litres: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive Multi-Layer Classification & Everyday Requirements Comparison:
          Layer 1: Clinical Rule Engine (immediate acute alarms)
          Layer 2: Everyday Requirements vs Dataset Disease Benchmarks (statistical similarity)
          Layer 3: Supervised ML Model (rolling feature vectors & probabilities)
        Returns:
          final_risk, blended_score, predicted_disease, comparison_report, and explanation.
        """
        if cls._tabular_model is None or cls._tabular_scaler is None:
            cls.load_models()

        current_vitals = {
            'temperature': temperature,
            'feed_intake': feed_intake,
            'water_intake': water_intake,
            'milk_yield': milk_yield,
            'symptoms': symptoms,
            'other_symptoms': other_symptoms
        }

        # 1. Rule Layer Evaluation
        rule_result = RuleEngine.evaluate(current_vitals, recent_history)
        rule_risk = rule_result['risk_level']
        rule_score = rule_result['risk_score']
        matched_rules = rule_result['matched_rules']
        suspected_diseases = rule_result['suspected_diseases']

        # 2. ML Feature Engineering & Inference
        ml_probs = {'Low': 0.85, 'Moderate': 0.10, 'High': 0.05}
        ml_risk = 'Low'
        ml_explanation = "ML baseline prediction."

        # Compute rolling features from history
        temp_drift = 0.0
        milk_pct_change = 0.0
        feed_issue_rolling = 1 if feed_intake in ['reduced', 'none'] else 0

        if recent_history and len(recent_history) > 0:
            past_temps = [h.temperature for h in recent_history[:3]]
            if past_temps:
                temp_drift = temperature - (sum(past_temps) / len(past_temps))

            past_milks = [h.milk_yield for h in recent_history[:3] if h.milk_yield > 0]
            if past_milks:
                avg_milk = sum(past_milks) / len(past_milks)
                milk_pct_change = ((milk_yield - avg_milk) / max(0.1, avg_milk)) * 100.0

            feed_issue_rolling += sum(1 for h in recent_history[:2] if h.feed_intake in ['reduced', 'none'])

        intake_map = {'normal': 0, 'reduced': 1, 'none': 2}
        feed_code = intake_map.get(feed_intake, 0)
        water_code = intake_map.get(water_intake, 0)
        intake_deficit = feed_code * 1.5 + water_code * 1.2
        symptom_set = set(symptoms)

        row_dict = {
            'temperature': temperature,
            'milk_yield': milk_yield,
            'feed_code': feed_code,
            'water_code': water_code,
            'intake_deficit_score': intake_deficit,
            'temp_drift': temp_drift,
            'milk_pct_change': milk_pct_change,
            'feed_issue_rolling_3d': feed_issue_rolling,
            'symptom_count': len(symptoms),
            'is_high_fever': 1 if temperature > 39.5 else 0,
            'is_hypothermic': 1 if temperature < 38.0 else 0,
            'is_acute_milk_drop': 1 if milk_pct_change < -25.0 else 0
        }
        for s in ALL_SYMPTOMS:
            row_dict[s] = 1 if s in symptom_set else 0

        feature_cols = FeatureEngine.get_feature_column_names()
        X_vec = pd.DataFrame([row_dict])[feature_cols]

        if cls._tabular_model is not None and cls._tabular_scaler is not None:
            try:
                X_scaled = cls._tabular_scaler.transform(X_vec)
                probs = cls._tabular_model.predict_proba(X_scaled)[0]
                classes = cls._tabular_model.classes_
                ml_probs = {c: round(float(p), 3) for c, p in zip(classes, probs)}
                ml_risk = cls._tabular_model.predict(X_scaled)[0]
                ml_explanation = f"ML Tabular Model: High Risk Prob: {ml_probs.get('High', 0)*100:.1f}%, Moderate: {ml_probs.get('Moderate', 0)*100:.1f}%, Low: {ml_probs.get('Low', 0)*100:.1f}%."
            except Exception as e:
                print(f"[MLService] Tabular prediction fallback: {e}")

        # 3. Everyday Requirements vs Normal Benchmarks & Disease Datasets Comparison
        comp_input = {
            'temperature': temperature,
            'feed_intake': feed_intake,
            'feed_quantity_kg': feed_quantity_kg,
            'water_intake': water_intake,
            'water_intake_litres': water_intake_litres,
            'milk_yield': milk_yield,
            'walking_distance_km': walking_distance_km,
            'rumination_time_hrs': rumination_time_hrs,
            'resting_hours': resting_hours,
            'heart_rate_bpm': heart_rate_bpm,
            'respiratory_rate': respiratory_rate,
            'symptoms': symptoms,
            'other_symptoms': other_symptoms
        }
        comparison_report = VitalsComparator.compare_everyday_vitals(comp_input, recent_history)
        top_match = comparison_report.get('top_match')
        dataset_predicted_disease = top_match['name'] if top_match else 'Healthy'
        dataset_similarity = top_match['similarity_score'] if top_match else 90.0

        # 4. Multi-Layer Decision Gate (Rules + ML + Dataset Benchmarks)
        final_risk = 'Low'
        if (rule_risk == 'High' or 
            ml_probs.get('High', 0.0) >= 0.55 or 
            comparison_report.get('critical_count', 0) > 0 or 
            (dataset_predicted_disease != 'Normal Healthy Baseline' and dataset_similarity >= 75.0)):
            final_risk = 'High'
        elif (rule_risk == 'Moderate' or 
              ml_probs.get('Moderate', 0.0) >= 0.45 or 
              ml_probs.get('High', 0.0) >= 0.35 or 
              comparison_report.get('warning_count', 0) >= 2 or 
              (dataset_predicted_disease != 'Normal Healthy Baseline' and dataset_similarity >= 50.0)):
            final_risk = 'Moderate'
        else:
            final_risk = 'Low'

        # Determine predicted disease label
        primary_disease = rule_result.get('primary_disease')
        if not primary_disease or primary_disease == 'Unknown':
            if dataset_predicted_disease != 'Normal Healthy Baseline' and dataset_similarity >= 45.0:
                primary_disease = dataset_predicted_disease
            elif final_risk == 'Low':
                primary_disease = 'Healthy (Within Standard Parameters)'
            else:
                primary_disease = 'Undetermined Bovine Disturbance'

        # Calculate blended numeric score
        base_ml_score = ml_probs.get('High', 0.0) * 1.0 + ml_probs.get('Moderate', 0.0) * 0.5
        dataset_risk_factor = (100.0 - comparison_report['health_index']) / 100.0
        blended_score = round(0.40 * rule_score + 0.35 * base_ml_score + 0.25 * dataset_risk_factor, 3)

        # Synthesize plain-language explanation
        explanation_lines = []
        if matched_rules:
            explanation_lines.append("Clinical Rules Triggered:\n• " + "\n• ".join(matched_rules))
        else:
            explanation_lines.append("No acute clinical threshold violations detected.")

        explanation_lines.append(f"\nEveryday Requirements Analysis (Health Index: {comparison_report['health_index']}/100):\n"
                                 f"• Top Dataset Condition Match: {dataset_predicted_disease} ({dataset_similarity}% similarity)\n"
                                 f"• Abnormal Deficits Flagged: {comparison_report['critical_count']} critical, {comparison_report['warning_count']} warnings")

        explanation_lines.append(f"\nTrend Analysis (3-7 Days):\n• Temperature Drift: {temp_drift:+.2f}°C\n• Milk Yield Change: {milk_pct_change:+.1f}%\n• Feed Disturbance Index: {feed_issue_rolling}/3 days")
        explanation_lines.append(f"\n{ml_explanation}")

        full_explanation = "\n".join(explanation_lines)

        return {
            'final_risk': final_risk,
            'blended_score': blended_score,
            'rule_risk': rule_risk,
            'ml_risk': ml_risk,
            'ml_probabilities': ml_probs,
            'matched_rules': matched_rules,
            'suspected_diseases': suspected_diseases,
            'primary_disease': primary_disease,
            'predicted_disease': primary_disease,
            'explanation': full_explanation,
            'comparison_report': comparison_report,
            'health_index': comparison_report['health_index']
        }

    @classmethod
    def classify_image(cls, image_path: str) -> Dict[str, Any]:
        """
        Classifies an uploaded cattle image (skin, udder, hoof).
        Returns predicted label, confidence, and mapped risk.
        """
        if cls._image_model_bundle is None:
            cls.load_models()

        if cls._image_model_bundle is None:
            return {
                'label': 'healthy',
                'display_label': 'Healthy',
                'confidence': 0.90,
                'detected_risk': 'Low',
                'notes': 'Image classifier not yet loaded; default healthy baseline.'
            }

        try:
            model = cls._image_model_bundle['model']
            scaler = cls._image_model_bundle['scaler']
            classes = cls._image_model_bundle['classes']

            feat = extract_image_features(image_path)
            feat_scaled = scaler.transform([feat])
            probs = model.predict_proba(feat_scaled)[0]
            pred_idx = int(np.argmax(probs))
            pred_label = classes[pred_idx]
            confidence = round(float(probs[pred_idx]), 3)

            # Map class to risk and readable label
            label_map = {
                'healthy': ('Healthy (No Abnormal Lesions)', 'Low'),
                'lumpy_skin': ('Lumpy Skin Disease (Cutaneous Nodules)', 'High'),
                'mastitis': ('Mastitis (Udder Inflammation & Erythema)', 'High'),
                'foot_lesion': ('Foot Rot / Interdigital Lesion', 'Moderate')
            }
            display_label, detected_risk = label_map.get(pred_label, (pred_label.replace('_', ' ').title(), 'Moderate'))

            return {
                'label': pred_label,
                'display_label': display_label,
                'confidence': confidence,
                'detected_risk': detected_risk,
                'class_probabilities': {c: round(float(p), 3) for c, p in zip(classes, probs)},
                'notes': f"Visual scan classified as {display_label} with {confidence*100:.1f}% confidence."
            }
        except Exception as e:
            print(f"[MLService] Error during image classification: {e}")
            return {
                'label': 'unknown',
                'display_label': 'Analysis Inconclusive',
                'confidence': 0.50,
                'detected_risk': 'Moderate',
                'notes': f"Error evaluating image: {e}"
            }

    @classmethod
    def get_pipeline_metrics(cls) -> Dict[str, Any]:
        """Reads latest metrics and audit reports for the Admin dashboard."""
        metrics_file = os.path.join(Config.MODELS_DIR, 'metrics.json')
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading metrics: {e}")
        return {}
