import os
from pathlib import Path

from dotenv import load_dotenv

_backend_dir = Path(__file__).resolve().parent
_repo_root = _backend_dir.parent

# Load repo-root .env first (e.g. DB_PORT=3307), then backend/.env overrides.
load_dotenv(_repo_root / ".env")
load_dotenv(_backend_dir / ".env", override=True)

class Config:
    """Configuration settings for Flask app"""
    
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'overtake')
    DB_PORT = os.getenv('DB_PORT', 3306)
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    JSON_SORT_KEYS = False
