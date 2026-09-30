import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple

ALL_SYMPTOMS = [
    'fever', 'milk_drop', 'mouth_blisters', 'skin_lumps', 'limping',
    'not_eating', 'swollen_udder', 'bloat', 'downer_cow', 'abortion',
    'leg_swelling', 'breathing_difficulty', 'sweet_breath', 'tremor_cold_ears'
]

class FeatureEngine:
    """
    Feature engineering for cow disease classification.
    Calculates rolling trends (last 3-7 days) such as milk yield % change,
    temperature drift, intake deficit history, and encoded symptom signals.
    """

    @staticmethod
    def engineer_tabular_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Takes raw/cleaned dataframe with cow_id, date, vitals and generates
        clinical trend features.
        """
        df = df.copy()
        
        # Sort by cow_id and date if present
        sort_cols = [c for c in ['cow_id', 'log_date'] if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols)

        # 1. Encode Categorical Feed & Water
        intake_map = {'normal': 0, 'reduced': 1, 'none': 2}
        df['feed_code'] = df['feed_intake'].map(lambda x: intake_map.get(str(x).lower(), 0))
        df['water_code'] = df['water_intake'].map(lambda x: intake_map.get(str(x).lower(), 0))
        df['intake_deficit_score'] = df['feed_code'] * 1.5 + df['water_code'] * 1.2

        # 2. Rolling History Features per cow
        if 'cow_id' in df.columns:
            # Grouped rolling features
            df['temp_rolling_3d'] = df.groupby('cow_id')['temperature'].transform(
                lambda s: s.shift(1).rolling(3, min_periods=1).mean()
            ).fillna(df['temperature'])
            
            df['temp_drift'] = df['temperature'] - df['temp_rolling_3d']

            df['milk_rolling_3d'] = df.groupby('cow_id')['milk_yield'].transform(
                lambda s: s.shift(1).rolling(3, min_periods=1).mean()
            ).fillna(df['milk_yield'])
            
            # % drop in milk relative to baseline
            baseline_safe = df['milk_rolling_3d'].replace(0, 0.1)
            df['milk_pct_change'] = ((df['milk_yield'] - df['milk_rolling_3d']) / baseline_safe) * 100.0

            # Consecutive reduced/none feed days
            df['feed_issue'] = (df['feed_code'] > 0).astype(int)
            df['feed_issue_rolling_3d'] = df.groupby('cow_id')['feed_issue'].transform(
                lambda s: s.rolling(3, min_periods=1).sum()
            )
        else:
            # Default drift if no historical group
            df['temp_drift'] = df['temperature'] - 38.6
            df['milk_pct_change'] = 0.0
            df['feed_issue_rolling_3d'] = df['feed_code']

        # 3. Symptom Checklist Binary Flags
        for sym in ALL_SYMPTOMS:
            if sym in df.columns:
                df[sym] = df[sym].fillna(0).astype(int)
            elif 'symptoms' in df.columns:
                df[sym] = df['symptoms'].apply(
                    lambda s: 1 if sym in str(s).lower() else 0
                )
            else:
                df[sym] = 0

        # Total active symptoms
        df['symptom_count'] = df[ALL_SYMPTOMS].sum(axis=1)

        # 4. Critical Clinical Indicators
        df['is_high_fever'] = (df['temperature'] > 39.5).astype(int)
        df['is_hypothermic'] = (df['temperature'] < 38.0).astype(int)
        df['is_acute_milk_drop'] = (df['milk_pct_change'] < -25.0).astype(int)

        return df

    @staticmethod
    def get_feature_column_names() -> List[str]:
        """Returns the standard feature columns used by the ML model."""
        return [
            'temperature', 'milk_yield', 'feed_code', 'water_code',
            'intake_deficit_score', 'temp_drift', 'milk_pct_change',
            'feed_issue_rolling_3d', 'symptom_count',
            'is_high_fever', 'is_hypothermic', 'is_acute_milk_drop'
        ] + ALL_SYMPTOMS
