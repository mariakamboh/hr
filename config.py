"""
Configuration file for Flask application
"""
import os

class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Agent paths (relative to app root)
    HIRING_AGENT_PATH = 'hiring-agent'
    RAG_DB_PATH = 'cv_db'  # Shared database path
    
    # API Keys
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY') or 'AIzaSyDzSW4KWALJ4ckBBZax-ZBcALZa4cv8A0A'

