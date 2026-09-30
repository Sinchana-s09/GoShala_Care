import os
import glob
import json
import joblib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.preprocessing import StandardScaler

from backend.config import Config
from backend.ml_pipeline.data_cleaner import DataCleaner

IMAGE_CLASSES = ['healthy', 'lumpy_skin', 'mastitis', 'foot_lesion']

def extract_image_features(image_path: str) -> np.ndarray:
    """
    Extracts high-dimensional visual feature vectors:
    - 3-channel color histograms (RGB & HSV)
    - Spatial grid color moments (mean & std across quadrants)
    - Texture/edge gradient energy
    """
    with Image.open(image_path) as img:
        img_rgb = img.convert('RGB').resize((128, 128))
        img_hsv = img_rgb.convert('HSV')
        
        arr_rgb = np.array(img_rgb, dtype=np.float32) / 255.0
        arr_hsv = np.array(img_hsv, dtype=np.float32) / 255.0

        features = []

        # 1. Global Color Histograms (16 bins per channel)
        for c in range(3):
            hist, _ = np.histogram(arr_rgb[:, :, c], bins=16, range=(0, 1))
            features.extend(hist / hist.sum())

        for c in range(3):
            hist, _ = np.histogram(arr_hsv[:, :, c], bins=16, range=(0, 1))
            features.extend(hist / hist.sum())

        # 2. Quadrant Spatial Color Moments (4 quadrants x 3 channels: mean, std)
        h, w, _ = arr_rgb.shape
        quads = [
            arr_rgb[:h//2, :w//2], arr_rgb[:h//2, w//2:],
            arr_rgb[h//2:, :w//2], arr_rgb[h//2:, w//2:]
        ]
        for q in quads:
            for c in range(3):
                features.append(float(np.mean(q[:, :, c])))
                features.append(float(np.std(q[:, :, c])))

        # 3. Texture Edge Gradient using simple Sobel filter
        gray = img_rgb.convert('L')
        edge_img = gray.filter(ImageFilter.FIND_EDGES)
        edge_arr = np.array(edge_img, dtype=np.float32) / 255.0
        features.append(float(np.mean(edge_arr)))
        features.append(float(np.std(edge_arr)))
        features.append(float(np.percentile(edge_arr, 90)))

        return np.array(features, dtype=np.float32)

def generate_sample_disease_images(base_dir: str, samples_per_class: int = 15):
    """
    Creates realistic synthetic sample images for training when no external images are present.
    """
    os.makedirs(base_dir, exist_ok=True)
    np.random.seed(42)

    for cls in IMAGE_CLASSES:
        cls_dir = os.path.join(base_dir, cls)
        os.makedirs(cls_dir, exist_ok=True)
        
        for i in range(1, samples_per_class + 1):
            img_file = os.path.join(cls_dir, f"{cls}_{i:03d}.jpg")
            if os.path.exists(img_file):
                continue
                
            img = Image.new('RGB', (256, 256), color=(220, 200, 180)) # Cattle skin base tone
            draw = ImageDraw.Draw(img)

            if cls == 'healthy':
                # Smooth coat, natural shading
                for _ in range(8):
                    x1 = np.random.randint(0, 250)
                    y1 = np.random.randint(0, 250)
                    draw.ellipse([x1, y1, x1 + 40, y1 + 40], fill=(210 + np.random.randint(-15, 15), 180, 150))
            elif cls == 'lumpy_skin':
                # Round raised nodular lesions
                for _ in range(12):
                    rx = np.random.randint(30, 220)
                    ry = np.random.randint(30, 220)
                    r = np.random.randint(15, 30)
                    draw.ellipse([rx - r, ry - r, rx + r, ry + r], fill=(139, 69, 19), outline=(90, 40, 10), width=3)
                    draw.ellipse([rx - r//2, ry - r//2, rx + r//2, ry + r//2], fill=(180, 100, 50))
            elif cls == 'mastitis':
                # Erythematous, inflamed hot pink/red swollen teat patches
                draw.rectangle([60, 60, 200, 200], fill=(215, 75, 75))
                for _ in range(10):
                    rx = np.random.randint(70, 190)
                    ry = np.random.randint(70, 190)
                    draw.ellipse([rx, ry, rx + 25, ry + 25], fill=(240, 110, 110))
            elif cls == 'foot_lesion':
                # Dark hoof necrosis, fissure, ulcer
                draw.rectangle([40, 120, 216, 240], fill=(60, 50, 45))
                draw.line([70, 140, 180, 200], fill=(180, 40, 30), width=8) # Fissure
                draw.line([90, 180, 160, 220], fill=(220, 60, 40), width=6)

            img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
            img.save(img_file, "JPEG")

    print(f"Generated {samples_per_class} sample images per class in {base_dir}")

def train_image_pipeline():
    print("=" * 60)
    print("[Image Pipeline Step 1] Ingesting Image Datasets...")
    print("=" * 60)
    
    train_dir = os.path.join(Config.DATA_DIR, 'train')
    
    # Check if images exist; if not, generate sample dataset
    total_existing = sum(len(glob.glob(os.path.join(train_dir, cls, "*.*"))) for cls in IMAGE_CLASSES)
    if total_existing < 12:
        generate_sample_disease_images(train_dir, samples_per_class=18)

    print("=" * 60)
    print("[Image Pipeline Step 2] Auditing & Validating Images...")
    print("=" * 60)
    audit_report = DataCleaner.audit_and_clean_images(train_dir)

    print("=" * 60)
    print("[Image Pipeline Step 3] Extracting Deep Visual Features...")
    print("=" * 60)
    
    X_list = []
    y_list = []

    for cls_name in IMAGE_CLASSES:
        cls_folder = os.path.join(train_dir, cls_name)
        files = glob.glob(os.path.join(cls_folder, "*.*"))
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                try:
                    feat = extract_image_features(f)
                    X_list.append(feat)
                    y_list.append(cls_name)
                except Exception as e:
                    print(f"Error reading {f}: {e}")

    if len(X_list) < 8:
        print("Not enough images to train. Please add images to data/train/<class>/.")
        return None

    X = np.array(X_list)
    y = np.array(y_list)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    print("=" * 60)
    print("[Image Pipeline Step 4] Training Visual Disease Classifier...")
    print("=" * 60)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf.fit(X_train_scaled, y_train)

    print("=" * 60)
    print("[Image Pipeline Step 5] Evaluating Visual Model...")
    print("=" * 60)
    y_pred = clf.predict(X_test_scaled)
    acc = float(accuracy_score(y_test, y_pred))

    classes = sorted(list(clf.classes_))
    p, r, f1, support = precision_recall_fscore_support(y_test, y_pred, labels=classes, zero_division=0)
    
    per_class_metrics = {}
    for idx, c in enumerate(classes):
        per_class_metrics[c] = {
            "precision": round(float(p[idx]), 3),
            "recall": round(float(r[idx]), 3),
            "f1_score": round(float(f1[idx]), 3),
            "support": int(support[idx])
        }

    conf_mat = confusion_matrix(y_test, y_pred, labels=classes).tolist()
    print(f"Visual Model Accuracy: {acc * 100:.2f}%")

    # Save model artifacts
    os.makedirs(Config.MODELS_DIR, exist_ok=True)
    model_bundle = {
        'model': clf,
        'scaler': scaler,
        'classes': classes
    }
    img_model_path = os.path.join(Config.MODELS_DIR, 'image_classifier.joblib')
    joblib.dump(model_bundle, img_model_path)

    # Update metrics.json
    metrics_file = os.path.join(Config.MODELS_DIR, 'metrics.json')
    current_metrics = {}
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, 'r') as f:
                current_metrics = json.load(f)
        except Exception:
            current_metrics = {}

    current_metrics["image_model"] = {
        "status": "trained",
        "last_trained": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "accuracy": round(acc, 4),
        "classes": classes,
        "per_class": per_class_metrics,
        "confusion_matrix": conf_mat,
        "audit_report": audit_report
    }

    with open(metrics_file, 'w') as f:
        json.dump(current_metrics, f, indent=2)

    print(f"Saved visual model to {img_model_path}")
    return current_metrics["image_model"]

if __name__ == '__main__':
    train_image_pipeline()
