import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Query
from flask import abort
from backend.config import Config
from backend.db_models import Base

# Ensure standard SQLAlchemy Query has first_or_404 support across the entire app
def _first_or_404(self, description=None):
    rv = self.first()
    if rv is None:
        abort(404, description=description)
    return rv

Query.first_or_404 = _first_or_404

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GoShalaDB")

engine = None
db_session = None

def init_engine():
    global engine, db_session
    mysql_uri = Config.get_database_uri()
    
    # Try connecting to MySQL first
    try:
        test_engine = create_engine(
            mysql_uri,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        with test_engine.connect() as conn:
            pass
        logger.info(f"Successfully connected to MySQL database: {Config.DB_NAME} at {Config.DB_HOST}")
        engine = test_engine
    except Exception as e:
        logger.warning(f"Could not connect to MySQL ({e}).")
        if Config.USE_SQLITE_FALLBACK:
            sqlite_path = os.path.join(Config.BASE_DIR, 'goshala.db')
            logger.info(f"Falling back to local SQLite database: {sqlite_path}")
            engine = create_engine(
                f"sqlite:///{sqlite_path}",
                connect_args={"check_same_thread": False}
            )
        else:
            raise e

    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db_session = scoped_session(session_factory)
    return engine, db_session

def get_db():
    global db_session
    if db_session is None:
        init_engine()
    return db_session

def create_all_tables():
    global engine
    if engine is None:
        init_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("All database tables verified/created successfully.")

def check_db_health():
    global engine
    if engine is None:
        init_engine()
    dialect = engine.dialect.name
    return {
        'status': 'healthy',
        'engine': 'MySQL' if dialect == 'mysql' else f"SQLite ({dialect})"
    }

