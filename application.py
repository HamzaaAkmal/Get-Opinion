"""
Application Factory for YouTube Scrapping Flask Application

This module implements the Flask application factory pattern for creating
and configuring the Flask application with all necessary components.

Author: Refactored with modern architecture
Version: 2.1
"""

import os
import logging
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

# Import configuration
from config import get_config

# Import service instances (these are singletons created in each service module)
from services.database import db_service
from services.ai_service import ai_service
from services.youtube_service import youtube_service
from services.reddit_service import reddit_service
from services.comment_fetcher import comment_fetcher

# Import route blueprints
from routes.database_routes import database_bp
from routes.search_routes import search_bp
from routes.testing_routes import testing_bp


def create_app(environment='development'):
    """
    Application factory pattern for creating Flask app instances
    
    Args:
        environment (str): Configuration environment ('development', 'production', 'testing')
        
    Returns:
        Flask: Configured Flask application instance
    """
    
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config(environment)
    app.config.from_object(config_class)
    
    # Store environment in app config for reference
    app.config['ENVIRONMENT'] = environment
    
    # Initialize services
    initialize_services(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Setup health check endpoint
    setup_health_check(app)
    
    # Log successful initialization
    app.logger.info(f"Flask application created successfully in {environment} mode")
    
    return app


def initialize_services(app: Flask):
    """Initialize all application services"""
    app.logger.info("Initializing application services...")
    
    try:
        # Attach existing service instances to the app
        app.db_service = db_service
        app.ai_service = ai_service
        app.youtube_service = youtube_service
        app.reddit_service = reddit_service
        app.comment_fetcher = comment_fetcher
        
        # Test service availability
        if app.ai_service.is_available():
            app.logger.info("AI service (Gemini) is available")
        else:
            app.logger.warning("AI service is not available - check GEMINI_API_KEY")
        
        if app.youtube_service:
            app.logger.info("YouTube service initialized successfully")
        else:
            app.logger.warning("YouTube service not available - check YOUTUBE_API_KEY")
        
        if app.reddit_service:
            app.logger.info("Reddit service initialized successfully")
        else:
            app.logger.warning("Reddit service not available - check Reddit credentials")
        
        # Test database connection
        try:
            success, message = app.db_service.test_connection()
            if success:
                app.logger.info(f"Database service: {message}")
            else:
                app.logger.warning(f"Database service: {message}")
        except Exception as e:
            app.logger.warning(f"Database connection test failed: {e}")
        
        app.logger.info("All services initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Error initializing services: {e}")
        raise


def register_blueprints(app: Flask):
    """Register all application blueprints"""
    app.logger.info("Registering application blueprints...")
    
    try:
        # Register database routes
        app.register_blueprint(database_bp, url_prefix='/api/database')
        
        # Register search routes  
        app.register_blueprint(search_bp, url_prefix='/api')
        
        # Register testing routes (includes main page)
        app.register_blueprint(testing_bp)
        
        app.logger.info("All blueprints registered successfully")
        
    except Exception as e:
        app.logger.error(f"Error registering blueprints: {e}")
        raise


def setup_error_handlers(app: Flask):
    """Setup global error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        return jsonify({
            'error': 'Resource not found',
            'message': 'The requested resource could not be found on this server.',
            'status_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.',
            'status_code': 500
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors"""
        return jsonify({
            'error': 'Bad request',
            'message': 'The request could not be understood by the server.',
            'status_code': 400
        }), 400
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle all other HTTP exceptions"""
        return jsonify({
            'error': error.name,
            'message': error.description,
            'status_code': error.code
        }), error.code
    
    app.logger.info("Error handlers configured successfully")


def setup_health_check(app: Flask):
    """Setup application health check endpoint"""
    
    @app.route('/health')
    def health_check():
        """Application health check endpoint"""
        try:
            # Basic service health checks
            services_status = {
                'database': 'unknown',
                'ai_service': 'available' if app.ai_service and app.ai_service.is_available() else 'unavailable',
                'youtube_service': 'available' if app.youtube_service else 'unavailable',
                'reddit_service': 'available' if app.reddit_service else 'unavailable'
            }
            
            # Check database connection if available
            if app.db_service:
                try:
                    success, _ = app.db_service.test_connection()
                    services_status['database'] = 'connected' if success else 'disconnected'
                except Exception:
                    services_status['database'] = 'error'
            
            # Determine overall health
            critical_services = ['ai_service', 'youtube_service']  # These are critical for basic functionality
            overall_health = 'healthy'
            
            for service in critical_services:
                if services_status.get(service) == 'unavailable':
                    overall_health = 'degraded'
                    break
            
            return jsonify({
                'status': overall_health,
                'environment': app.config.get('ENVIRONMENT', 'unknown'),
                'debug': app.config.get('DEBUG', False),
                'services': services_status,
                'version': '2.1'
            })
            
        except Exception as e:
            app.logger.error(f"Health check error: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500


# Service access functions for other modules to use
def get_db_service():
    """Get the database service instance"""
    return db_service


def get_ai_service():
    """Get the AI service instance"""
    return ai_service


def get_youtube_service():
    """Get the YouTube service instance"""
    return youtube_service


def get_reddit_service():
    """Get the Reddit service instance"""
    return reddit_service


def get_comment_fetcher():
    """Get the comment fetcher service instance"""
    return comment_fetcher