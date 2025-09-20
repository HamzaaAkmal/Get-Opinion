"""
Configuration management for YouTube Scrapping Application
Contains all environment variables, API keys, and application settings
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'youtube_scraper')
    MONGODB_TIMEOUT = int(os.getenv('MONGODB_TIMEOUT', '5000'))
    
    # API Keys Configuration
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDbWs2fojEoXcvehGd-OddoLfCPlUVYTmM')
    
    # Reddit API Configuration
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')
    
    # Application Settings
    MAX_COMMENTS_PER_VIDEO = int(os.getenv('MAX_COMMENTS_PER_VIDEO', '150'))
    MAX_VIDEOS_PER_QUERY = int(os.getenv('MAX_VIDEOS_PER_QUERY', '20'))
    MAX_REDDIT_COMMENTS = int(os.getenv('MAX_REDDIT_COMMENTS', '3000'))
    TARGET_TOTAL_COMMENTS = int(os.getenv('TARGET_TOTAL_COMMENTS', '50000'))
    
    # Query Generation Settings
    NUM_QUERY_VARIATIONS = int(os.getenv('NUM_QUERY_VARIATIONS', '20'))
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    
    # File Storage Settings
    DATA_DIRECTORY = os.getenv('DATA_DIRECTORY', 'data')
    HISTORY_DIRECTORY = os.getenv('HISTORY_DIRECTORY', 'history')
    MAX_FILENAME_LENGTH = int(os.getenv('MAX_FILENAME_LENGTH', '50'))
    
    # Threading Configuration
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))
    FETCH_TIMEOUT = int(os.getenv('FETCH_TIMEOUT', '180'))
    
    # Rate Limiting - Optimized for parallel processing
    PAUSE_BETWEEN_QUERIES = int(os.getenv('PAUSE_BETWEEN_QUERIES', '1'))  # Reduced for faster processing
    PAUSE_BETWEEN_ATTEMPTS = int(os.getenv('PAUSE_BETWEEN_ATTEMPTS', '2'))  # Reduced for faster processing
    
    @classmethod
    def validate_required_env_vars(cls):
        """Validate that all required environment variables are set"""
        required_vars = []
        warnings = []
        
        # Check critical variables
        if not cls.YOUTUBE_API_KEY:
            required_vars.append('YOUTUBE_API_KEY')
        
        if not cls.MONGODB_URI:
            warnings.append('MONGODB_URI - MongoDB features will be disabled')
        
        if not all([cls.REDDIT_CLIENT_ID, cls.REDDIT_CLIENT_SECRET, cls.REDDIT_USER_AGENT]):
            warnings.append('Reddit API credentials - Reddit features will be disabled')
        
        if required_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(required_vars)}")
        
        if warnings:
            print("⚠️  Missing optional environment variables:")
            for warning in warnings:
                print(f"   - {warning}")
        
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    MONGODB_DATABASE = 'youtube_scraper_dev'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    MONGODB_DATABASE = 'youtube_scraper_prod'

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    MONGODB_DATABASE = 'youtube_scraper_test'

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(environment='default'):
    """Get configuration class based on environment"""
    return config_map.get(environment, DevelopmentConfig)