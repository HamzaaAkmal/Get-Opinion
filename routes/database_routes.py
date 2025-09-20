"""
Database and batch management routes
Handles MongoDB operations, batch retrieval, and data management
"""
from flask import Blueprint, jsonify, request
from services.database import db_service
from utils.helpers import format_number

database_bp = Blueprint('database', __name__)


@database_bp.route('/test_mongodb', methods=['GET'])
def test_mongodb():
    """Test MongoDB connection manually"""
    try:
        success, message = db_service.test_connection()

        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'database': db_service.config.MONGODB_DATABASE,
                'connection_uri': db_service.config.MONGODB_URI[:50] + '...' if db_service.config.MONGODB_URI else 'Not configured'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message,
                'database': db_service.config.MONGODB_DATABASE,
                'connection_uri': db_service.config.MONGODB_URI[:50] + '...' if db_service.config.MONGODB_URI else 'Not configured'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Test failed: {str(e)}',
            'database': db_service.config.MONGODB_DATABASE
        }), 500


@database_bp.route('/mongodb_stats', methods=['GET'])
def mongodb_stats():
    """Get MongoDB collection statistics"""
    try:
        stats = db_service.get_collection_stats()
        
        if stats is None:
            return jsonify({'error': 'MongoDB connection failed'}), 500

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@database_bp.route('/batch/<batch_id>')
def get_batch(batch_id):
    """Get batch data by ID from MongoDB"""
    try:
        batch_data = db_service.get_search_result(batch_id)

        if not batch_data:
            return jsonify({'error': 'Batch not found in MongoDB!'}), 404

        return jsonify(batch_data)

    except Exception as e:
        print(f"Error retrieving batch {batch_id}: {e}")
        return jsonify({'error': str(e)}), 500


@database_bp.route('/batches')
def list_batches():
    """List all saved batches from MongoDB"""
    try:
        batches = db_service.list_search_results()
        
        if not batches:
            return jsonify({
                'batches': [], 
                'total': 0,
                'message': 'No batches found or MongoDB connection failed'
            })

        # Add formatted numbers for display
        for batch in batches:
            batch['formatted_total'] = format_number(batch.get('grand_total', 0))
            batch['formatted_unique'] = format_number(batch.get('unique_comments', 0))

        return jsonify({
            'batches': batches, 
            'total': len(batches),
            'status': 'success'
        })

    except Exception as e:
        print(f"Error listing batches: {e}")
        return jsonify({'error': str(e)}), 500


@database_bp.route('/batch/<batch_id>/summary')
def get_batch_summary(batch_id):
    """Get a summary of batch data without full content"""
    try:
        batch_data = db_service.get_search_result(batch_id)

        if not batch_data:
            return jsonify({'error': 'Batch not found!'}), 404

        # Extract summary information
        summary = {
            'batch_id': batch_data.get('batch_id'),
            'query': batch_data.get('query'),
            'timestamp': batch_data.get('timestamp'),
            'sources': batch_data.get('sources', []),
            'total_youtube_videos': batch_data.get('total_youtube_videos', 0),
            'total_reddit_posts': batch_data.get('total_reddit_posts', 0),
            'total_comments': batch_data.get('total_comments', 0),
            'total_replies': batch_data.get('total_replies', 0),
            'grand_total': batch_data.get('grand_total', 0),
            'unique_comments': batch_data.get('unique_comments', 0),
            'processing_info': batch_data.get('processing_info', {}),
            'data_available': True
        }

        return jsonify(summary)

    except Exception as e:
        print(f"Error retrieving batch summary {batch_id}: {e}")
        return jsonify({'error': str(e)}), 500


@database_bp.route('/batch/<batch_id>/delete', methods=['DELETE'])
def delete_batch(batch_id):
    """Delete a batch from MongoDB"""
    try:
        # Get database connection
        db = db_service.get_database()
        if db is None:
            return jsonify({'error': 'MongoDB connection failed'}), 500

        collection = db['search_results']
        result = collection.delete_one({'batch_id': batch_id})

        if result.deleted_count == 0:
            return jsonify({'error': 'Batch not found or already deleted'}), 404

        return jsonify({
            'message': f'Batch {batch_id} deleted successfully',
            'deleted_count': result.deleted_count
        })

    except Exception as e:
        print(f"Error deleting batch {batch_id}: {e}")
        return jsonify({'error': str(e)}), 500


@database_bp.route('/batches/search', methods=['POST'])
def search_batches():
    """Search batches by query text"""
    try:
        data = request.get_json()
        search_term = data.get('search', '').strip().lower()
        
        if not search_term:
            return jsonify({'error': 'Search term is required'}), 400

        batches = db_service.list_search_results()
        
        if not batches:
            return jsonify({'batches': [], 'total': 0})

        # Filter batches by search term
        filtered_batches = []
        for batch in batches:
            query = batch.get('query', '').lower()
            if search_term in query:
                batch['formatted_total'] = format_number(batch.get('grand_total', 0))
                batch['formatted_unique'] = format_number(batch.get('unique_comments', 0))
                filtered_batches.append(batch)

        return jsonify({
            'batches': filtered_batches,
            'total': len(filtered_batches),
            'search_term': search_term
        })

    except Exception as e:
        print(f"Error searching batches: {e}")
        return jsonify({'error': str(e)}), 500


@database_bp.route('/database/cleanup', methods=['POST'])
def cleanup_database():
    """Clean up old database records"""
    try:
        data = request.get_json()
        keep_latest = data.get('keep_latest', 100)  # Keep latest 100 records by default
        
        # Get database connection
        db = db_service.get_database()
        if db is None:
            return jsonify({'error': 'MongoDB connection failed'}), 500

        collection = db['search_results']
        
        # Get all records sorted by timestamp (oldest first)
        all_records = list(collection.find({}).sort('timestamp', 1))
        total_records = len(all_records)
        
        if total_records <= keep_latest:
            return jsonify({
                'message': f'No cleanup needed. Total records: {total_records}, keeping latest: {keep_latest}',
                'deleted_count': 0
            })
        
        # Delete oldest records
        records_to_delete = all_records[:-keep_latest]
        batch_ids_to_delete = [record['batch_id'] for record in records_to_delete]
        
        result = collection.delete_many({'batch_id': {'$in': batch_ids_to_delete}})
        
        return jsonify({
            'message': f'Cleanup completed. Deleted {result.deleted_count} old records.',
            'deleted_count': result.deleted_count,
            'remaining_records': total_records - result.deleted_count
        })

    except Exception as e:
        print(f"Error during database cleanup: {e}")
        return jsonify({'error': str(e)}), 500