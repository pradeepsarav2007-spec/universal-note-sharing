#!/usr/bin/env python3
"""
Universal Notes Sharing Platform - Database Initializer
Creates database schema and populates with initial academic departments,
demo users, and rich sample educational notes.
"""

import sys
from config import Config
from models import db
from app import app
from seed_data import seed_database

def init_all():
    print("==================================================")
    print(" Universal Notes Sharing Platform: DB Initializer")
    print("==================================================")
    
    # Ensure directories
    Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    (Config.BASE_DIR / 'instance').mkdir(parents=True, exist_ok=True)
    
    print(f"[*] Target Database: {Config.SQLALCHEMY_DATABASE_URI}")
    print(f"[*] Upload Directory: {Config.UPLOAD_FOLDER}")
    
    seed_database()
    
    print("==================================================")
    print(" [OK] Database initialization complete!")
    print(" Default Accounts:")
    print("   - Administrator: admin@universalnotes.com / Admin@123")
    print("   - Student Demo:  sarah.mitchell@campus.edu / User@123")
    print("==================================================")

if __name__ == '__main__':
    init_all()
