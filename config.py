import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Foursquare API Configuration
    FOURSQUARE_SERVICE_KEY = os.getenv("FOURSQUARE_SERVICE_KEY")
    FOURSQUARE_PLACES_API_VERSION = "2025-06-17"
    FOURSQUARE_USERS_API_VERSION = "2025-06-17"
    
    # API Base URLs (using new API endpoints)
    PLACES_API_BASE = "https://places-api.foursquare.com"
    USERS_API_BASE = "https://users-api.foursquare.com"
    
    # Mistral AI Configuration
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    
    # Database
    DATABASE_URL = "sqlite:///./business_matchmaking.db"
    
    # Application Settings
    APP_NAME = "Business Matchmaking Platform"
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
