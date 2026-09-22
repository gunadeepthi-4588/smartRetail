import os
from dotenv import load_dotenv

# Load variables from .env file if present
load_dotenv()

class Config:
    """Base configuration loaded from environment variables."""
    SECRET_KEY = os.getenv("SECRET_KEY", "smartretail-default-dev-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
    PORT = int(os.getenv("PORT", 5000))
    
    # Database Settings
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "smart_retail_db")

    # Security & CORS Settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Business Logic Defaults
    DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "INR")
    DEFAULT_CURRENCY_SYMBOL = os.getenv("DEFAULT_CURRENCY_SYMBOL", "₹")
    DEFAULT_SAFETY_STOCK_DAYS = int(os.getenv("DEFAULT_SAFETY_STOCK_DAYS", 7))
    DEFAULT_LEAD_TIME_DAYS = int(os.getenv("DEFAULT_LEAD_TIME_DAYS", 3))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    DB_NAME = os.getenv("TEST_DB_NAME", "smart_retail_test_db")

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}
