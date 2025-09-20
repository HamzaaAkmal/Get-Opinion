#!/usr/bin/env python3
"""
YouTube Scrapping Application - Main Entry Point

A professional, modular Flask application for scraping and analyzing
YouTube and Reddit comments with AI-powered query generation.

Author: Refactored with modern architecture
Version: 2.1 - Modern Modular Architecture
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flask import Flask
from config import get_config
from application import create_app


def setup_directories():
    """Create necessary directories for the application"""
    directories = ['data', 'history', 'logs']
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        print(f"📁 Directory ensured: {dir_path}")


def setup_logging(app: Flask) -> None:
    """Configure application logging"""
    log_level = logging.DEBUG if app.config.get('DEBUG', False) else logging.INFO
    
    # Create logs directory
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(logs_dir / 'youtube_scraper.log')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configure app logger
    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # Configure werkzeug logger (Flask's internal logger)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.addHandler(file_handler)


def validate_environment():
    """Validate critical environment variables and dependencies"""
    print("🔍 Validating environment...")
    
    try:
        # Test configuration loading
        config = get_config()
        config.validate_required_env_vars()
        print("✅ Environment validation completed")
        return True
        
    except ValueError as e:
        print(f"❌ Environment validation failed: {e}")
        print("\n💡 Please ensure the following:")
        print("   1. Create a .env file in the project root")
        print("   2. Add your YouTube API key: YOUTUBE_API_KEY=your_key_here")
        print("   3. Optionally add MongoDB URI for database features")
        print("   4. Optionally add Reddit API credentials for Reddit integration")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error during validation: {e}")
        return False


def display_startup_info(app: Flask):
    """Display application startup information"""
    config_name = os.getenv('FLASK_ENV', 'development')
    
    print("\n" + "="*60)
    print("🚀 YouTube Scrapping Application v2.1")
    print("="*60)
    print(f"📊 Environment: {config_name}")
    print(f"🐛 Debug Mode: {app.config.get('DEBUG', False)}")
    print(f"🗄️  Database: {app.config.get('MONGODB_DATABASE', 'Not configured')}")
    print(f"📁 Data Directory: {project_root / 'data'}")
    print(f"📜 History Directory: {project_root / 'history'}")
    print(f"📋 Logs Directory: {project_root / 'logs'}")
    print("="*60)
    
    # Display available routes
    print("\n🌐 Available Endpoints:")
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
            'path': str(rule.rule)
        })
    
    # Group routes by blueprint
    route_groups = {}
    for route in routes:
        blueprint = route['endpoint'].split('.')[0] if '.' in route['endpoint'] else 'main'
        if blueprint not in route_groups:
            route_groups[blueprint] = []
        route_groups[blueprint].append(route)
    
    for blueprint, blueprint_routes in route_groups.items():
        print(f"\n📋 {blueprint.upper()} Routes:")
        for route in blueprint_routes:
            methods_str = ', '.join(route['methods'])
            print(f"   {route['path']} [{methods_str}]")
    
    print("\n" + "="*60)


def main():
    """Main application entry point"""
    print("🚀 Starting YouTube Scrapping Application...")
    
    try:
        # Setup project directories
        setup_directories()
        
        # Validate environment
        if not validate_environment():
            print("\n❌ Application startup failed due to environment issues")
            sys.exit(1)
        
        # Get environment configuration
        environment = os.getenv('FLASK_ENV', 'development')
        print(f"🔧 Loading {environment} configuration...")
        
        # Create Flask application using factory pattern
        app = create_app(environment)
        
        # Setup logging
        setup_logging(app)
        
        # Display startup information
        display_startup_info(app)
        
        # Get runtime configuration
        host = os.getenv('FLASK_HOST', '127.0.0.1')
        port = int(os.getenv('FLASK_PORT', '5000'))
        debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        
        print(f"\n🌍 Server starting on http://{host}:{port}")
        print("📝 Access the web interface to start scraping!")
        
        if debug:
            print("⚠️  Debug mode is enabled - do not use in production!")
        
        print("\n💡 Press Ctrl+C to stop the server")
        print("="*60 + "\n")
        
        # Start the Flask development server
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.exception("Fatal error during application startup")
        sys.exit(1)


if __name__ == '__main__':
    main()