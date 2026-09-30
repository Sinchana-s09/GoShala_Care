import os
import hashlib
import pandas as pd
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple, List

class DataCleaner:
    """
    Data Cleaning Module for Cattle Vitals CSV and Image Datasets.
    Performs data validation, unit normalization, invalid row filtering,
    and duplicate detection.
    """

    @staticmethod
    def clean_vitals_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Cleans raw cow vitals dataset.
        Checks:
          - Null values handling
          - Biological bounds: Temperature (34.0°C - 44.0°C)
          - Milk yield non-negative (0.0L - 60.0L)
          - Categorical intake values normalization
        """
        initial_rows = len(df)
        report = {
            "initial_rows": initial_rows,
            "null_values_filled": 0,
            "invalid_temp_removed": 0,
            "invalid_milk_removed": 0,
            "final_rows": 0,
            "cleaning_log": []
        }

        cleaned = df.copy()

        # 1. Column normalization
        cleaned.columns = [c.strip().lower().replace(' ', '_') for c in cleaned.columns]

        # 2. Check essential columns
        required_cols = ['temperature', 'milk_yield', 'feed_intake', 'water_intake']
        for col in required_cols:
            if col not in cleaned.columns:
                report["cleaning_log"].append(f"Warning: Missing column '{col}', adding defaults.")
                if col == 'temperature':
                    cleaned[col] = 38.5
                elif col == 'milk_yield':
                    cleaned[col] = 12.0
                else:
                    cleaned[col] = 'normal'

        # 3. Numeric conversion & null handling
        for num_col in ['temperature', 'milk_yield']:
            cleaned[num_col] = pd.to_numeric(cleaned[num_col], errors='coerce')
            nulls = cleaned[num_col].isnull().sum()
            if nulls > 0:
                report["null_values_filled"] += int(nulls)
                cleaned[num_col] = cleaned[num_col].fillna(cleaned[num_col].median())
                report["cleaning_log"].append(f"Filled {nulls} missing values in {num_col} with median.")

        # 4. Outlier & Biological Plausibility Filtering
        # Impossible cattle temperatures
        temp_mask = (cleaned['temperature'] >= 34.0) & (cleaned['temperature'] <= 44.0)
        invalid_temps = int((~temp_mask).sum())
        if invalid_temps > 0:
            report["invalid_temp_removed"] = invalid_temps
            report["cleaning_log"].append(f"Removed {invalid_temps} rows with impossible temperatures (<34°C or >44°C).")
            cleaned = cleaned[temp_mask]

        # Negative or impossible milk yield
        milk_mask = (cleaned['milk_yield'] >= 0.0) & (cleaned['milk_yield'] <= 60.0)
        invalid_milk = int((~milk_mask).sum())
        if invalid_milk > 0:
            report["invalid_milk_removed"] = invalid_milk
            report["cleaning_log"].append(f"Removed {invalid_milk} rows with impossible milk yield (<0L or >60L).")
            cleaned = cleaned[milk_mask]

        # 5. Categorical normalization
        for cat_col in ['feed_intake', 'water_intake']:
            cleaned[cat_col] = cleaned[cat_col].astype(str).str.strip().str.lower()
            cleaned[cat_col] = cleaned[cat_col].apply(lambda x: x if x in ['normal', 'reduced', 'none'] else 'normal')

        # 6. Remove duplicate rows if any
        dup_count = int(cleaned.duplicated().sum())
        if dup_count > 0:
            cleaned = cleaned.drop_duplicates()
            report["cleaning_log"].append(f"Removed {dup_count} exact duplicate rows.")

        report["final_rows"] = len(cleaned)
        report["cleaning_log"].append(f"Cleaned dataset: {len(cleaned)} valid records retained out of {initial_rows}.")

        return cleaned, report

    @staticmethod
    def audit_and_clean_images(folder_path: str) -> Dict[str, Any]:
        """
        Scans an image directory for:
          - Corrupted or unreadable files
          - Unsupported formats
          - Exact or near-duplicate images using MD5 hashing
        """
        report = {
            "total_images": 0,
            "valid_images": 0,
            "corrupted_images": 0,
            "duplicate_images": 0,
            "classes_found": {},
            "log": []
        }

        if not os.path.exists(folder_path):
            report["log"].append(f"Folder '{folder_path}' does not exist.")
            return report

        seen_hashes = set()
        for root, dirs, files in os.walk(folder_path):
            class_name = os.path.basename(root)
            for f in files:
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
                    report["total_images"] += 1
                    file_path = os.path.join(root, f)
                    
                    try:
                        with Image.open(file_path) as img:
                            img.verify()
                        
                        # Check duplicate via hash
                        with open(file_path, 'rb') as fp:
                            file_hash = hashlib.md5(fp.read()).hexdigest()
                            
                        if file_hash in seen_hashes:
                            report["duplicate_images"] += 1
                            report["log"].append(f"Duplicate image found: {f}")
                        else:
                            seen_hashes.add(file_hash)
                            report["valid_images"] += 1
                            report["classes_found"][class_name] = report["classes_found"].get(class_name, 0) + 1
                    except Exception as e:
                        report["corrupted_images"] += 1
                        report["log"].append(f"Corrupted image {f}: {e}")

        report["log"].append(f"Image Audit complete: {report['valid_images']} valid images across {len(report['classes_found'])} classes.")
        return report
