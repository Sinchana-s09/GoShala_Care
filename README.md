# GoShala Care — Early Detection & Management of Bovine Diseases

A production-quality web application built with **Python (Flask)**, **MySQL**, and **Machine Learning** for early cattle disease detection, longitudinal herd telemetry, and veterinary triage.

---

## 🌟 Philosophy & Core Idea

Most academic and industrial cattle health systems depend on expensive IoT sensor collars, rumination boluses, and automated milking gates that are financially out of reach for smallholder farmers and traditional gaushalas. 

**GoShala Care** flips this paradigm:
1. Farmers manually log **daily vitals and visible symptoms** in under 60 seconds through a mobile-friendly web interface.
2. A **Two-Layer Hybrid Engine** evaluates the entry:
   - **Layer 1 (Explainable Rule Engine)**: Evaluates strict biological thresholds (rectal temperature outside 38.0–39.3°C, feed cessation for 2+ days, acute milk drops, and specific symptom combinations) directly backed by the database's disease knowledge base.
   - **Layer 2 (Machine Learning Engine)**: Analyzes rolling 3–7 day longitudinal trends (temperature drift, % milk yield drop, consecutive feed deficit counts) using Random Forest / Gradient Boosting tabular models.
3. If risk is **Moderate** or **High**, the system automatically generates an active case in the **Veterinary Review Queue**.
4. A dedicated **Computer Vision Photo Scan** module allows farmers to upload photos of cattle skin, udders, or hooves to detect lesions (Lumpy Skin Disease, Mastitis, Foot Rot) with instant confidence ratings.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+ with **Flask** (Modular Blueprints architecture: Auth, Farmer, Vet, Admin, Library, API).
- **Database**: **MySQL 8.0+** using `PyMySQL` and `mysql-connector-python` with **SQLAlchemy ORM**. Full schema provided in `backend/schema.sql` (InnoDB, foreign keys, constraints, and seed data). Automatic SQLite fallback enables immediate out-of-the-box evaluation if MySQL credentials are not yet configured.
- **Frontend**: Server-rendered **Jinja2 templates** with vanilla modern CSS3 and responsive JavaScript. All frontend assets are strictly contained within `frontend/templates/` and `frontend/static/`.
- **Machine Learning**: Standalone pipelines in `backend/ml_pipeline/` leveraging `scikit-learn`, `Pillow`, `pandas`, and `numpy`. Trains tabular models on longitudinal vitals CSVs and visual classifiers on lesion image folders, saving weights in `backend/models/`.

---

## 📁 Project Structure

```
d:/goshala/
├── backend/
│   ├── app.py                   # Flask Application Factory & routing
│   ├── config.py                # Environment configuration reader
│   ├── database.py              # SQLAlchemy engine & session factory
│   ├── db_models.py             # ORM models (User, Cow, Vitals, Case, Disease, etc.)
│   ├── schema.sql               # Full MySQL DDL schema + initial seed data
│   ├── seed.py                  # Database seeder (users, diseases, demo cows)
│   ├── rule_engine.py           # Two-layer explainable clinical threshold engine
│   ├── ml_service.py            # Live runtime inference service for Flask
│   ├── models/                  # Saved ML models and evaluation metrics
│   │   ├── vitals_classifier.joblib
│   │   ├── vitals_scaler.joblib
│   │   ├── image_classifier.joblib
│   │   └── metrics.json
│   ├── ml_pipeline/             # Visible 7-stage Data Science Pipeline
│   │   ├── data_cleaner.py      # Missing value, bounds & duplicate filtering
│   │   ├── feature_engine.py    # Rolling 3-7d trend & symptom engineering
│   │   ├── train_tabular.py     # Tabular ML training & evaluation
│   │   └── train_image.py       # Visual image scan training & evaluation
│   └── routes/                  # Modular route blueprints
│       ├── auth.py              # Login, Farmer self-registration, RBAC
│       ├── farmer.py            # Herd management, vitals, photo scan, map
│       ├── vet.py               # Triage queue, case review & prescriptions
│       ├── admin.py             # User admin, vet directory, KB, ML telemetry
│       ├── library.py           # Searchable public disease reference
│       └── api.py               # Chart.js time-series endpoints
├── frontend/
│   ├── static/
│   │   ├── css/style.css        # Warm agrarian design system & typography
│   │   └── js/main.js           # Live client validations & UI interactions
│   └── templates/               # Server-rendered Jinja2 templates
│       ├── base.html            # Persistent sidebar & topbar layout
│       ├── auth/                # Login and Farmer registration
│       ├── farmer/              # Farmer dashboard, cows, vitals log, map
│       ├── vet/                 # Triage queue and case detail review
│       ├── admin/               # User, vet, disease and ML pipeline status
│       └── library/             # Disease reference library
├── data/
│   ├── vitals/                  # Place cow vitals CSV files here
│   ├── train/                   # Training images (healthy, lumpy_skin, etc.)
│   └── val/                     # Validation images
├── uploads/                     # Uploaded cattle photos and lesion scans
├── train_model.py               # Master ML pipeline orchestrator
├── run.py                       # Application server entrypoint
├── requirements.txt             # Python package dependencies
├── .env.example                 # Environment configuration template
├── .env                         # Active configuration
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Virtual Environment
Ensure Python 3.10+ is installed on your system.

```bash
# Clone or navigate to the repository
cd d:/goshala

# Create and activate a virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

### 2. Configure Database Connection

Create or edit your `.env` file in the project root:

```ini
# Flask Security
SECRET_KEY=goshala-care-production-secret-key-928471
FLASK_ENV=development

# MySQL Database Settings
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=goshala_db

# Fallback to local SQLite if MySQL credentials are empty during development
USE_SQLITE_FALLBACK=true
```

#### Setting up MySQL:
1. Log into your MySQL console:
   ```bash
   mysql -u root -p
   ```
2. Execute the provided `backend/schema.sql`:
   ```sql
   source d:/goshala/backend/schema.sql;
   ```
   *(Or run: `mysql -u root -p < backend/schema.sql`)*

---

### 3. Seed Database with Default Users & Knowledge Base

Run the automated seeder script to populate default user roles, clinical diseases, symptoms, sample clinics, and demo cows:

```bash
python -m backend.seed
```

#### Default Credentials:
| Role | Username | Email | Password | Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin@goshala.org` | `Admin@123` | User admin, vet directory, disease library, ML pipeline |
| **Veterinarian** | `dr_ramesh` | `dr.ramesh@kamdhenuvet.in` | `Vet@123` | Case triage queue, diagnosis & prescription response |
| **Farmer** | `ramesh_farmer` | `farmer.ramesh@gmail.com` | `Farmer@123` | Herd management, vitals logging, photo scan, map |

*(Farmers can also freely register new accounts from the `/register` page).*

---

### 4. Train the ML Models

Train both the **Tabular Vitals Model** and the **Computer Vision Lesion Model** using the master orchestrator:

```bash
python train_model.py
```

- **Dropping External Datasets**:
  - Place your tabular CSVs into `data/vitals/`.
  - Place your lesion photos into subfolders under `data/train/<class>/` (e.g. `healthy`, `mastitis`, `lumpy_skin`, `foot_lesion`).
  - Run `python train_model.py` to ingest, clean, extract features, and retrain both models. Model weights and per-class metrics will be saved into `backend/models/`.

---

### 5. Launch the Web Application

Start the Flask development server:

```bash
python run.py
```

Open your browser at:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔬 Classification & Triage Logic

### Layer 1: Explainable Rule & Threshold Layer
Normal bovine rectal temperature is **38.0°C to 39.3°C**. The rule engine flags immediate physiological alerts:
- **Temperature > 40.2°C**: Critical Hyperthermia (acute sepsis / toxemia).
- **Temperature < 37.5°C**: Severe Hypothermia (circulatory collapse / advanced milk fever).
- **Feed/Water Cessation**: `none` for 2+ consecutive days.
- **Acute Milk Drop**: Yield drop $>35\%$ compared to the cow's recent rolling baseline.
- **Symptom Combinations**:
  - `hot/swollen udder` + `acute milk drop` $\rightarrow$ **Mastitis**
  - `mouth blisters / drooling` + `limping / hoof sores` $\rightarrow$ **Foot-and-Mouth Disease (FMD)**
  - `round cutaneous nodules` + `fever` $\rightarrow$ **Lumpy Skin Disease (LSD)**
  - `unable to stand (downer)` + `cold ears / muscle tremors` $\rightarrow$ **Milk Fever (Hypocalcemia)**
  - `distended left flank (bloat)` + `labored grunting` $\rightarrow$ **Acute Bloat**
  - `sweet acetone odor in breath/milk` + `milk drop` $\rightarrow$ **Ketosis**

*Every rule triggered generates a transparent, plain-English explanation displayed directly to the farmer and veterinarian.*

### Layer 2: Machine Learning Layer
- Computes trend features: `temperature_drift` ($T_{\text{today}} - \overline{T}_{3\text{d}}$), `milk_pct_change` ($\frac{M_{\text{today}} - \overline{M}_{3\text{d}}}{\overline{M}_{3\text{d}}}$), and cumulative feed disturbance counts.
- Evaluates feature vector via a trained `RandomForestClassifier` with balanced class weights.
- Generates probability distribution: $P(\text{Low}), P(\text{Moderate}), P(\text{High})$.

### Combined Risk Decision:
- If Rule Layer detects a High emergency or ML $P(\text{High}) \ge 0.55 \rightarrow$ **High Risk**.
- If Rule Layer detects Moderate or ML $P(\text{Moderate}) \ge 0.45 \rightarrow$ **Moderate Risk**.
- Otherwise $\rightarrow$ **Low Risk**.
- **Moderate** or **High** risk logs automatically spawn a triage case in the veterinarian queue.

---

## 📊 Admin ML Pipeline Status Dashboard

Accessible to Administrators at `/admin/pipeline_status`, this dashboard renders all 7 steps of the data science workflow:
1. **Ingestion**: Tracks all ingested CSV files and image folders.
2. **Cleaning & Validation**: Displays duplicate image hashes filtered, invalid temperatures ($<34^\circ\text{C}$ or $>44^\circ\text{C}$) scrubbed, and missing values imputed.
3. **EDA Summary**: Class distributions, mean temperatures, and symptom frequencies.
4. **Feature Engineering**: Feature importance rankings for rolling 3–7 day trend signals.
5. **Model Training**: Architecture details for Random Forest and visual classifiers.
6. **Evaluation**: Per-class Precision, Recall, and F1-Scores for Low, Moderate, and High classes.
7. **Retraining**: One-click retraining button that executes the pipeline and hot-reloads model weights into the active Flask server.

---

## 🗺️ Interactive Vet Directory & First-Aid Reference

Accessible at `/farmer/vets_map`:
- Uses **Leaflet.js** and OpenStreetMap to display geocoded veterinary clinics with 24/7 emergency dispatch tags and direct phone dial buttons.
- Features a clinical accordion providing step-by-step first-aid protocols:
  - **Bloat**: Sternal elevation, wooden mouth bit to stimulate belching, vegetable oil administration, emergency trocarization guidance.
  - **Downer Cow**: Sternal chest resting position with straw bales, avoiding oral drenching to prevent aspiration pneumonia, extremity warming.
  - **FMD Blister Hygiene**: 1% Potassium Permanganate antiseptic mouth wash, zinc oxide hoof barrier.
  - **Heat Stress**: Cold water neck/spine evaporation, shade relocation.

---

## 🔮 Future Extension to IoT Sensors

While GoShala Care is designed specifically to avoid mandatory hardware investments, the platform's backend is modularly structured to easily ingest automated sensor feeds in the future:
1. **Ear Tag Temperature Sensors**: Can push hourly temperature readings to a REST endpoint (`POST /api/vitals/stream`) using MQTT or HTTP.
2. **Automated Milk Meters**: Smart milking machines can publish daily per-cow yield data directly to the `vitals_logs` table.
3. **Pedometer Activity Collars**: Can log step counts to compute rumination and estrus deficit scores alongside the existing feed intake parameters.

---

## 📜 License & Acknowledgments

Built for farmers, gaushalas, and bovine practitioners committed to ethical livestock welfare and data-driven agricultural science.
