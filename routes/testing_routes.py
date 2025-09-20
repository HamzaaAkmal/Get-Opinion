"""
Testing and utility routes
Provides endpoints for testing functionality and utilities
"""
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from utils.helpers import validate_query, generate_batch_id, get_current_timestamp
from utils.file_utils import sanitize_filename

testing_bp = Blueprint('testing', __name__)


@testing_bp.route('/')
def home():
    """Serve the main application page"""
    return render_template('index.html')


@testing_bp.route('/test_filename', methods=['POST'])
def test_filename():
    """Test endpoint to verify filename generation"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()

        if not query:
            return jsonify({'error': 'Please enter a query!'}), 400

        print(f"Testing filename generation for query: {query}")

        # Test the sanitization method
        sanitized = sanitize_filename(query)
        batch_id = generate_batch_id()
        timestamp = get_current_timestamp()
        filename = f"data/{sanitized}_unified_{timestamp}_{batch_id}.json"

        print(f"Generated filename: {filename}")

        return jsonify({
            'original_query': query,
            'sanitized_query': sanitized,
            'batch_id': batch_id,
            'timestamp': timestamp,
            'filename': filename,
            'validation': validate_query(query)
        })

    except Exception as e:
        print(f"Error in test_filename: {e}")
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/validate_query', methods=['POST'])
def validate_query_endpoint():
    """Validate a search query"""
    try:
        data = request.get_json()
        query = data.get('query', '')

        is_valid, message = validate_query(query)

        return jsonify({
            'query': query,
            'is_valid': is_valid,
            'message': message,
            'length': len(query.strip()) if query else 0
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        from services.database import db_service
        from services.ai_service import ai_service
        from config import Config
        
        config = Config()
        
        # Check various service statuses
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': {
                    'available': db_service.connect(),
                    'configured': bool(config.MONGODB_URI)
                },
                'ai_service': {
                    'available': ai_service.is_available(),
                    'configured': bool(config.GEMINI_API_KEY)
                },
                'youtube_api': {
                    'configured': bool(config.YOUTUBE_API_KEY)
                },
                'reddit_api': {
                    'configured': all([
                        config.REDDIT_CLIENT_ID,
                        config.REDDIT_CLIENT_SECRET,
                        config.REDDIT_USER_AGENT
                    ])
                }
            },
            'configuration': {
                'debug_mode': config.DEBUG,
                'target_comments': config.TARGET_TOTAL_COMMENTS,
                'max_videos_per_query': config.MAX_VIDEOS_PER_QUERY,
                'max_reddit_comments': config.MAX_REDDIT_COMMENTS
            }
        }
        
        # Determine overall health
        all_critical_services_ok = (
            health_status['services']['youtube_api']['configured'] and
            (health_status['services']['database']['available'] or True)  # DB is optional
        )
        
        if not all_critical_services_ok:
            health_status['status'] = 'degraded'
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@testing_bp.route('/config_check', methods=['GET'])
def config_check():
    """Check configuration status"""
    try:
        from config import Config
        
        config = Config()
        
        # Check which environment variables are set
        env_status = {
            'YOUTUBE_API_KEY': bool(config.YOUTUBE_API_KEY),
            'GEMINI_API_KEY': bool(config.GEMINI_API_KEY),
            'MONGODB_URI': bool(config.MONGODB_URI),
            'MONGODB_DATABASE': bool(config.MONGODB_DATABASE),
            'REDDIT_CLIENT_ID': bool(config.REDDIT_CLIENT_ID),
            'REDDIT_CLIENT_SECRET': bool(config.REDDIT_CLIENT_SECRET),
            'REDDIT_USER_AGENT': bool(config.REDDIT_USER_AGENT)
        }
        
        # Validate configuration
        try:
            config.validate_required_env_vars()
            validation_status = 'valid'
            validation_message = 'All required environment variables are set'
        except ValueError as e:
            validation_status = 'invalid'
            validation_message = str(e)
        
        return jsonify({
            'validation_status': validation_status,
            'validation_message': validation_message,
            'environment_variables': env_status,
            'configuration': {
                'debug': config.DEBUG,
                'database': config.MONGODB_DATABASE,
                'target_comments': config.TARGET_TOTAL_COMMENTS,
                'max_workers': config.MAX_WORKERS,
                'fetch_timeout': config.FETCH_TIMEOUT
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/generate_batch_id', methods=['GET'])
def generate_new_batch_id():
    """Generate a new batch ID for testing"""
    try:
        batch_id = generate_batch_id()
        timestamp = get_current_timestamp()
        
        return jsonify({
            'batch_id': batch_id,
            'timestamp': timestamp,
            'full_uuid': str(uuid.uuid4())
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/test_services', methods=['GET'])
def test_services():
    """Test all services individually"""
    try:
        from services.database import db_service
        from services.ai_service import ai_service
        from services.youtube_service import youtube_service
        from services.reddit_service import reddit_service
        
        test_results = {}
        
        # Test database service
        try:
            db_success, db_message = db_service.test_connection()
            test_results['database'] = {
                'status': 'success' if db_success else 'error',
                'message': db_message
            }
        except Exception as e:
            test_results['database'] = {
                'status': 'error',
                'message': str(e)
            }
        
        # Test AI service
        try:
            ai_available = ai_service.is_available()
            test_results['ai_service'] = {
                'status': 'success' if ai_available else 'error',
                'message': 'AI service available' if ai_available else 'AI service not configured'
            }
        except Exception as e:
            test_results['ai_service'] = {
                'status': 'error',
                'message': str(e)
            }
        
        # Test YouTube service
        try:
            # Just check if it initializes properly
            youtube_service.youtube  # This will throw if API key is invalid
            test_results['youtube_service'] = {
                'status': 'success',
                'message': 'YouTube service initialized successfully'
            }
        except Exception as e:
            test_results['youtube_service'] = {
                'status': 'error',
                'message': str(e)
            }
        
        # Test Reddit service
        try:
            # Just check if it initializes properly
            reddit_service.reddit  # This will throw if credentials are invalid
            test_results['reddit_service'] = {
                'status': 'success',
                'message': 'Reddit service initialized successfully'
            }
        except Exception as e:
            test_results['reddit_service'] = {
                'status': 'error',
                'message': str(e)
            }
        
        return jsonify({
            'test_results': test_results,
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'success' if all(
                result['status'] == 'success' 
                for result in test_results.values()
            ) else 'partial'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500