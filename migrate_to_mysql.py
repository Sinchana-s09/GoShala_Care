"""
GoShala Care - SQLite to MySQL Migration and Schema Sync Utility
Safely syncs database schema and copies all existing data from goshala.db (SQLite)
to the target MySQL database (goshala_db).
"""
import sys
import os
import sqlite3
import pymysql
from urllib.parse import quote_plus

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.config import Config

def get_mysql_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4',
        autocommit=True
    )

def ensure_columns():
    """Ensure all required columns exist in MySQL tables, especially vitals_logs."""
    conn = get_mysql_connection()
    cur = conn.cursor()
    
    # Columns expected in vitals_logs
    expected_vitals_columns = [
        ("feed_quantity_kg", "FLOAT DEFAULT 15.0"),
        ("water_intake_litres", "FLOAT DEFAULT 50.0"),
        ("walking_distance_km", "FLOAT DEFAULT 4.0"),
        ("rumination_time_hrs", "FLOAT DEFAULT 7.5"),
        ("resting_hours", "FLOAT DEFAULT 10.0"),
        ("heart_rate_bpm", "FLOAT DEFAULT 65.0"),
        ("respiratory_rate", "FLOAT DEFAULT 26.0"),
        ("predicted_disease", "VARCHAR(100) DEFAULT NULL"),
        ("comparison_data_json", "TEXT DEFAULT NULL")
    ]
    
    cur.execute("DESCRIBE vitals_logs")
    existing_cols = {row[0].lower() for row in cur.fetchall()}
    
    for col_name, col_def in expected_vitals_columns:
        if col_name.lower() not in existing_cols:
            print(f"[+] Adding missing column {col_name} to vitals_logs table in MySQL...")
            cur.execute(f"ALTER TABLE vitals_logs ADD COLUMN `{col_name}` {col_def}")
            
    conn.close()
    print("[+] Schema columns verified in MySQL.")

def migrate_data():
    sqlite_path = os.path.join(Config.BASE_DIR, 'goshala.db')
    if not os.path.exists(sqlite_path):
        print(f"[-] SQLite database not found at {sqlite_path}. Skipping data transfer.")
        return

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    mysql_conn = get_mysql_connection()
    mysql_cur = mysql_conn.cursor()

    # Tables in dependency order
    tables = [
        'users',
        'diseases',
        'symptoms',
        'cows',
        'disease_symptoms',
        'vet_directory',
        'vitals_logs',
        'photo_scans',
        'cases'
    ]

    print("[+] Beginning migration from SQLite to MySQL...")
    mysql_cur.execute("SET FOREIGN_KEY_CHECKS = 0;")

    for table in tables:
        try:
            sqlite_cur.execute(f"SELECT * FROM {table}")
            rows = sqlite_cur.fetchall()
            if not rows:
                print(f"  * Table '{table}': 0 rows in SQLite.")
                continue

            # Get column names
            columns = rows[0].keys()
            col_list = ", ".join([f"`{c}`" for c in columns])
            placeholders = ", ".join(["%s"] * len(columns))

            # Upsert using REPLACE INTO
            sql = f"REPLACE INTO `{table}` ({col_list}) VALUES ({placeholders})"
            
            records = []
            for r in rows:
                # Convert row values
                val_list = []
                for val in tuple(r):
                    val_list.append(val)
                records.append(val_list)

            mysql_cur.executemany(sql, records)
            print(f"  * Table '{table}': successfully migrated {len(records)} records.")
        except Exception as e:
            print(f"  [!] Error migrating table '{table}': {e}")

    mysql_cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    print("[+] SQLite data migration to MySQL completed successfully!")

    mysql_conn.close()
    sqlite_conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print(" GOSHALA CARE - MYSQL SETUP & MIGRATION ")
    print("=" * 60)
    print(f"Target MySQL Host: {Config.DB_HOST}:{Config.DB_PORT}")
    print(f"Target Database:   {Config.DB_NAME}")
    print(f"Target User:       {Config.DB_USER}")
    
    # 1. First ensure all tables exist in MySQL via SQLAlchemy
    from backend.database import create_all_tables
    create_all_tables()
    
    # 2. Ensure all columns match latest schema
    ensure_columns()
    
    # 3. Migrate records from SQLite into MySQL
    migrate_data()
    
    print("=" * 60)
    print(" DATABASE IS FULLY CONFIGURED & READY FOR MYSQL ")
    print("=" * 60)
