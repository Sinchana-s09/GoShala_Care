import os
import glob
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.preprocessing import StandardScaler

from backend.config import Config
from backend.ml_pipeline.data_cleaner import DataCleaner
from backend.ml_pipeline.feature_engine import FeatureEngine, ALL_SYMPTOMS

def generate_synthetic_dataset(output_path: str, n_cows: int = 40, days: int = 30) -> pd.DataFrame:
    """
    Generates a realistic cattle vitals dataset when no external CSV is present.
    Includes healthy trends, mastitis drops, LSD fever+lumps, bloat, milk fever, etc.
    """
    np.random.seed(42)
    records = []
    start_date = date.today() - timedelta(days=days)

    for cow_idx in range(1, n_cows + 1):
        cow_id = f"COW-{cow_idx:03d}"
        baseline_temp = np.random.normal(38.5, 0.2)
        baseline_milk = np.random.uniform(10.0, 24.0)
        
        # Decide if this cow experiences an episode during the period
        has_episode = np.random.rand() < 0.4
        episode_start = np.random.randint(10, days - 5) if has_episode else -1
        episode_type = np.random.choice([
            'mastitis', 'fmd', 'lsd', 'milk_fever', 'bloat', 'ketosis'
        ]) if has_episode else 'none'

        for day in range(days):
            current_date = start_date + timedelta(days=day)
            is_sick = has_episode and (episode_start <= day <= episode_start + 6)
            
            temp = baseline_temp + np.random.normal(0, 0.15)
            milk = baseline_milk + np.random.normal(0, 0.4)
            feed = 'normal'
            water = 'normal'
            symptoms = []
            risk = 'Low'

            if is_sick:
                if episode_type == 'mastitis':
                    temp += np.random.uniform(0.8, 1.6)
                    milk *= np.random.uniform(0.5, 0.7) # 30-50% drop
                    feed = np.random.choice(['reduced', 'none'])
                    symptoms = ['swollen_udder', 'milk_drop', 'fever']
                    risk = 'High'
                elif episode_type == 'lsd':
                    temp += np.random.uniform(1.0, 2.0)
                    milk *= np.random.uniform(0.65, 0.8)
                    feed = 'reduced'
                    symptoms = ['skin_lumps', 'fever']
                    risk = 'High'
                elif episode_type == 'bloat':
                    temp += np.random.uniform(0.2, 0.6)
                    milk *= 0.7
                    feed = 'none'
                    water = 'none'
                    symptoms = ['bloat', 'breathing_difficulty', 'not_eating']
                    risk = 'High'
                elif episode_type == 'milk_fever':
                    temp -= np.random.uniform(0.8, 1.5) # Subnormal temp
                    milk *= 0.5
                    feed = 'none'
                    symptoms = ['downer_cow', 'tremor_cold_ears', 'not_eating']
                    risk = 'High'
                elif episode_type == 'fmd':
                    temp += np.random.uniform(1.2, 2.2)
                    milk *= 0.55
                    feed = 'none'
                    water = 'reduced'
                    symptoms = ['mouth_blisters', 'limping', 'fever']
                    risk = 'High'
                elif episode_type == 'ketosis':
                    temp += np.random.uniform(0.1, 0.3)
                    milk *= 0.75
                    feed = 'reduced'
                    symptoms = ['sweet_breath', 'milk_drop', 'not_eating']
                    risk = 'Moderate'
            else:
                # Random mild anomaly
                if np.random.rand() < 0.05:
                    feed = 'reduced'
                    risk = 'Moderate'

            records.append({
                'cow_id': cow_id,
                'log_date': current_date.strftime('%Y-%m-%d'),
                'temperature': round(float(temp), 2),
                'feed_intake': feed,
                'water_intake': water,
                'milk_yield': round(max(0.0, float(milk)), 2),
                'symptoms': ";".join(symptoms),
                'risk_label': risk
            })

    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated synthetic training dataset with {len(df)} rows at {output_path}")
    return df

def train_tabular_pipeline():
    print("=" * 60)
    print("[Pipeline Step 1] Ingesting Vitals Datasets...")
    print("=" * 60)
    
    vitals_dir = Config.VITALS_DATA_DIR
    csv_files = glob.glob(os.path.join(vitals_dir, "*.csv"))
    
    if not csv_files:
        sample_path = os.path.join(vitals_dir, "cow_vitals_training.csv")
        df_raw = generate_synthetic_dataset(sample_path)
    else:
        dfs = [pd.read_csv(f) for f in csv_files]
        df_raw = pd.concat(dfs, ignore_index=True)
        print(f"Loaded {len(df_raw)} records from {len(csv_files)} CSV files in {vitals_dir}.")

    print("=" * 60)
    print("[Pipeline Step 2] Cleaning & Validating Ingested Data...")
    print("=" * 60)
    cleaned_df, clean_report = DataCleaner.clean_vitals_dataframe(df_raw)

    print("=" * 60)
    print("[Pipeline Step 3] Feature Engineering (Rolling 3-7d Trends & Indicators)...")
    print("=" * 60)
    featured_df = FeatureEngine.engineer_tabular_features(cleaned_df)

    # Assign risk_label if not present
    if 'risk_label' not in featured_df.columns:
        def compute_target(row):
            if row['symptom_count'] >= 2 or row['is_high_fever'] or row['is_hypothermic'] or row['is_acute_milk_drop']:
                return 'High'
            elif row['symptom_count'] == 1 or row['feed_code'] >= 1:
                return 'Moderate'
            return 'Low'
        featured_df['risk_label'] = featured_df.apply(compute_target, axis=1)

    print("=" * 60)
    print("[Pipeline Step 4] EDA & Summary Statistics...")
    print("=" * 60)
    class_counts = featured_df['risk_label'].value_counts().to_dict()
    eda_stats = {
        "class_balance": class_counts,
        "total_samples": len(featured_df),
        "mean_temp": round(float(featured_df['temperature'].mean()), 2),
        "mean_milk": round(float(featured_df['milk_yield'].mean()), 2),
        "symptom_frequency": {sym: int(featured_df[sym].sum()) for sym in ALL_SYMPTOMS}
    }

    feature_cols = FeatureEngine.get_feature_column_names()
    X = featured_df[feature_cols].copy()
    y = featured_df['risk_label']

    # Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    print("=" * 60)
    print("[Pipeline Step 5] Training Tabular Classifier (Random Forest)...")
    print("=" * 60)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        class_weight='balanced',
        random_state=42
    )
    model.fit(X_train_scaled, y_train)

    print("=" * 60)
    print("[Pipeline Step 6] Evaluating Model Performance (Precision, Recall, F1)...")
    print("=" * 60)
    y_pred = model.predict(X_test_scaled)
    acc = float(accuracy_score(y_test, y_pred))
    
    unique_classes = sorted(list(model.classes_))
    p, r, f1, support = precision_recall_fscore_support(y_test, y_pred, labels=unique_classes, zero_division=0)
    
    per_class_metrics = {}
    for idx, cls_name in enumerate(unique_classes):
        per_class_metrics[cls_name] = {
            "precision": round(float(p[idx]), 3),
            "recall": round(float(r[idx]), 3),
            "f1_score": round(float(f1[idx]), 3),
            "support": int(support[idx])
        }

    conf_matrix = confusion_matrix(y_test, y_pred, labels=unique_classes).tolist()
    
    # Feature importances
    importances = dict(zip(feature_cols, [round(float(val), 4) for val in model.feature_importances_]))
    top_features = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True)[:8])

    print(f"Model Accuracy: {acc * 100:.2f}%")
    for cls_name, m in per_class_metrics.items():
        print(f"  Class [{cls_name}]: Precision={m['precision']}, Recall={m['recall']}, F1={m['f1_score']}")

    # Save artifacts
    os.makedirs(Config.MODELS_DIR, exist_ok=True)
    model_path = os.path.join(Config.MODELS_DIR, 'vitals_classifier.joblib')
    scaler_path = os.path.join(Config.MODELS_DIR, 'vitals_scaler.joblib')
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    # Save / Update metrics JSON
    metrics_file = os.path.join(Config.MODELS_DIR, 'metrics.json')
    current_metrics = {}
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, 'r') as f:
                current_metrics = json.load(f)
        except Exception:
            current_metrics = {}

    current_metrics["tabular_model"] = {
        "status": "trained",
        "last_trained": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "accuracy": round(acc, 4),
        "classes": unique_classes,
        "per_class": per_class_metrics,
        "confusion_matrix": conf_matrix,
        "top_features": top_features,
        "eda": eda_stats,
        "clean_report": clean_report
    }

    with open(metrics_file, 'w') as f:
        json.dump(current_metrics, f, indent=2)

    print(f"Saved tabular model to {model_path} and metrics to {metrics_file}")
    return current_metrics["tabular_model"]

if __name__ == '__main__':
    train_tabular_pipeline()
