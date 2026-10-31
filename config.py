import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    BASE_DIR = BASE_DIR
    # Secret key for session management and CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY', 'universal-notes-secret-key-2026-secure-random')
    
    # SQLite Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f'sqlite:///{BASE_DIR / "instance" / "universal_notes.db"}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Uploads
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB maximum file upload size
    
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'pptx', 'ppt', 'txt'}
    
    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
