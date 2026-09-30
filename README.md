<div align="center">

# GoShala Care

### Early Detection & Management of Bovine Diseases

A full-stack web application for **cattle health monitoring**, **disease detection**, and **veterinary triage** built for smallholder farmers and traditional gaushalas.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Fallback-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## Overview

Most cattle health systems depend on expensive IoT sensor hardware that is financially out of reach for smallholder farmers. **GoShala Care** takes a different approach:

- Farmers log daily vitals and visible symptoms in under 60 seconds via a mobile-friendly interface
- A **Two-Layer Hybrid Engine** (Rule Engine + ML) analyzes entries and generates risk scores
- **Moderate/High risk** cases are automatically forwarded to the **Veterinary Review Queue**
- A **Photo Scan** module detects skin lesions (Lumpy Skin Disease, Mastitis, Foot Rot) from uploaded images
- A **Vet Contacts Directory** provides quick access to nearby veterinary clinics with emergency contacts

---

## Features

| Feature | Description |
|---|---|
| **Role-Based Auth** | Farmer self-registration, Vet login, Admin portal |
| **Herd Management** | Add/manage cows with full profile and history |
| **Daily Vitals Logging** | Temperature, milk yield, feed intake, symptoms |
| **AI Risk Assessment** | Two-layer hybrid: Rule Engine + Random Forest ML |
| **Photo Disease Scan** | Upload cattle images for CV-based lesion classification |
| **Vitals Comparison** | Historical trend charts per cow |
| **Vet Triage Queue** | Vets receive auto-generated cases with AI explanations |
| **Vet Contacts** | Searchable directory of clinics and emergency contacts |
| **Disease Library** | Public reference for common bovine diseases |
| **Admin Dashboard** | User management, disease KB, ML pipeline status |

---

## Tech Stack

```
Backend   -> Python 3.10+ / Flask (Blueprints) / SQLAlchemy ORM
Database  -> MySQL 8.0+ (primary) / SQLite (auto-fallback for dev)
Frontend  -> Jinja2 templates / Vanilla CSS3 / JavaScript
ML        -> scikit-learn / pandas / numpy / Pillow
Auth      -> Flask-Login / Werkzeug password hashing
```

---

## Project Structure

```
GoShala_Care/
├── backend/
│   ├── app.py                   # Flask app factory & blueprint registration
│   ├── config.py                # Environment config reader
│   ├── database.py              # SQLAlchemy engine & session (MySQL + SQLite fallback)
│   ├── db_models.py             # ORM models: User, Cow, VitalsLog, Case, Disease
│   ├── schema.sql               # Full MySQL DDL schema + seed data
│   ├── seed.py                  # Database seeder
│   ├── rule_engine.py           # Explainable clinical threshold rule engine
│   ├── ml_service.py            # Runtime ML inference service
│   ├── vitals_comparator.py     # Historical vitals comparison logic
│   ├── models/
│   │   └── metrics.json         # Saved model evaluation metrics
│   ├── ml_pipeline/
│   │   ├── data_cleaner.py      # Data validation & missing value handling
│   │   ├── feature_engine.py    # 3-7 day rolling trend feature engineering
│   │   ├── train_tabular.py     # Tabular vitals ML training
│   │   └── train_image.py       # Image classification training
│   └── routes/
│       ├── auth.py              # Login, register, logout
│       ├── farmer.py            # Herd, vitals, photo scan, vet contacts
│       ├── vet.py               # Case triage & prescription
│       ├── admin.py             # Admin management & ML pipeline
│       ├── library.py           # Disease reference library
│       └── api.py               # Chart.js JSON API endpoints
├── frontend/
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── templates/
│       ├── base.html
│       ├── auth/
│       ├── farmer/
│       ├── vet/
│       ├── admin/
│       └── library/
├── data/
│   ├── vitals/                  # Place CSV vitals datasets here
│   ├── train/                   # Training images
│   └── val/                     # Validation images
├── uploads/                     # User-uploaded cattle photos
├── run.py
├── train_model.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Sinchana-s09/GoShala_Care.git
cd GoShala_Care
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```ini
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=goshala_db
```

> **Note:** If MySQL credentials are not set or connection fails, the app **automatically falls back to SQLite** (`goshala.db`) with no extra setup needed.

### 5. (Optional) Set Up MySQL

```bash
mysql -u root -p < backend/schema.sql
```

### 6. Seed the Database

```bash
python -m backend.seed
```

#### Default Login Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@123` |
| Veterinarian | `dr_ramesh` | `Vet@123` |
| Farmer | `ramesh_farmer` | `Farmer@123` |

> Farmers can also **self-register** at `/register`.

### 7. (Optional) Train ML Models

Place datasets in `data/vitals/` and `data/train/<class>/`, then:

```bash
python train_model.py
```

### 8. Run the App

```bash
python run.py
```

Open your browser at: **http://127.0.0.1:5000**

---

## Application Routes

| Route | Role | Description |
|---|---|---|
| `/` | All | Redirects to role dashboard or login |
| `/login` | All | Login page |
| `/register` | Guest | Farmer self-registration |
| `/farmer/dashboard` | Farmer | Overview & milk trend chart |
| `/farmer/cows` | Farmer | Herd list & add cow |
| `/farmer/log_vitals` | Farmer | Log daily vitals & symptoms |
| `/farmer/photo_scan` | Farmer | Upload photo for disease detection |
| `/farmer/vets_map` | Farmer | Veterinary contacts directory |
| `/diseases` | All | Public disease reference library |
| `/vet/dashboard` | Vet | Triage queue with AI case summaries |
| `/admin/dashboard` | Admin | User & system management |
| `/admin/pipeline_status` | Admin | ML pipeline health & retraining |

---

## Disease Detection Logic

### Layer 1 - Rule Engine (Explainable)

| Condition | Possible Disease |
|---|---|
| Temperature > 40.2C | Sepsis / Toxemia |
| Temperature < 37.5C | Milk Fever |
| Feed = none for 2+ days | Multiple |
| Milk drop > 35% | Mastitis / Ketosis |
| Hot/swollen udder + milk drop | Mastitis |
| Mouth blisters + limping | FMD |
| Cutaneous nodules + fever | Lumpy Skin Disease |
| Downer + cold ears | Milk Fever |
| Distended flank + grunting | Bloat |
| Acetone breath + milk drop | Ketosis |

### Layer 2 - Machine Learning (Predictive)

Uses rolling 3-7 day trend features (temperature drift, % milk change, feed deficit count) to compute risk probabilities using a `RandomForestClassifier`.

### Combined Decision

| Result | Trigger |
|---|---|
| **High Risk** (auto vet case) | Rule: High OR ML P(High) >= 0.55 |
| **Moderate Risk** (auto vet case) | Rule: Moderate OR ML P(Moderate) >= 0.45 |
| **Low Risk** | Otherwise |

---

## Photo Disease Scan

Upload a photo of cattle skin, udder, or hooves at `/farmer/photo_scan`:

- Supports JPG, PNG, WebP, BMP
- Drag-and-drop or click-to-upload
- Instant confidence rating with disease classification
- Results logged to database for veterinary review

---

## Future Extensions

- **IoT Integration**: REST endpoint ready for ear-tag sensors & milk meters
- **Mobile App**: PWA-ready frontend for offline vitals entry
- **Cloud Deployment**: Docker + Gunicorn + Nginx support
- **Analytics**: Herd-level health trend dashboards

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

This project is licensed under the **MIT License**.

---

<div align="center">

Built with love for farmers, gaushalas, and bovine practitioners committed to ethical livestock welfare.

**Star this repo if you find it useful!**

</div>
