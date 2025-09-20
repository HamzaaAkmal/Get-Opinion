"""
Main search routes for the YouTube Scrapping API
Handles search requests and AI-powered query generation
"""
import time
from flask import Blueprint, request, jsonify
from services.ai_service import ai_service
from services.comment_fetcher import comment_fetcher
from utils.helpers import validate_query, format_duration, get_current_timestamp

search_bp = Blueprint('search', __name__)


@search_bp.route('/search', methods=['POST'])
def search():
    """Main AI-powered multi-query search endpoint"""
    print("=== AI-POWERED MULTI-QUERY SEARCH ENDPOINT CALLED ===")
    
    try:
        data = request.get_json()
        print(f"Received data: {data}")
        
        original_query = data.get('query', '').strip()
        print(f"Original Query: '{original_query}'")

        # Validate query
        is_valid, validation_message = validate_query(original_query)
        if not is_valid:
            print(f"ERROR: Invalid query - {validation_message}")
            return jsonify({'error': validation_message}), 400

        print("🤖 Generating query variations with Gemini AI...")
        start_time = time.time()

        # Generate query variations using AI
        num_variations = data.get('num_variations', 20)
        target_comments = data.get('target_comments', 50000)
        
        print(f"🎯 Configuration: {num_variations} query variations, target: {target_comments:,} comments")
        
        query_variations = ai_service.generate_query_variations(
            original_query, 
            num_variations=num_variations
        )

        if not query_variations:
            return jsonify({'error': 'Failed to generate query variations!'}), 500

        print(f"✅ Generated {len(query_variations)} query variations")

        print("🚀 Starting multi-query aggregation...")

        # Process all query variations and aggregate results
        aggregation_result = comment_fetcher.fetch_multiple_queries_aggregated(
            queries=query_variations,
            target_total_comments=target_comments
        )

        # End timing
        end_time = time.time()
        latency_seconds = end_time - start_time

        if not aggregation_result['videos']:
            return jsonify({'error': 'No content found from any query variation!'}), 404

        # Extract final results
        total_comments = aggregation_result['total_processed_comments']
        total_replies = aggregation_result['total_processed_replies']
        grand_total = aggregation_result['grand_total']
        unique_count = aggregation_result['unique_count']
        unique_comments = aggregation_result['unique_comments']

        print(f"🎯 Final Results:")
        print(f"   Total comments processed: {total_comments}")
        print(f"   Total replies processed: {total_replies}")
        print(f"   Grand total processed: {grand_total}")
        print(f"   Unique comments: {unique_count}")
        print(f"   Target achieved: {aggregation_result['target_achieved']}")
        print(f"   Successful queries: {aggregation_result['successful_queries']}")
        print(f"   Failed queries: {aggregation_result['failed_queries']}")
        print(f"   Total latency: {format_duration(latency_seconds)}")

        # Save unified data
        print("💾 Saving unified data...")
        save_result, combined_data = comment_fetcher.save_unified_data(
            original_query,
            aggregation_result['videos'],
            unique_comments,
            unique_count,
            total_replies,
            grand_total,
            ['youtube', 'reddit']
        )

        print(f"✅ Data saved with result: {save_result}")

        # Calculate additional stats with debug info
        youtube_videos = [v for v in aggregation_result['videos'] if v.get('source') == 'youtube']
        reddit_posts = [v for v in aggregation_result['videos'] if v.get('source') == 'reddit']
        
        print(f"📊 Final video breakdown:")
        print(f"   Total videos in aggregation result: {len(aggregation_result['videos'])}")
        print(f"   YouTube videos found: {len(youtube_videos)}")
        print(f"   Reddit posts found: {len(reddit_posts)}")
        
        # Debug: Show sources of all videos
        sources_debug = {}
        for video in aggregation_result['videos']:
            source = video.get('source', 'unknown')
            sources_debug[source] = sources_debug.get(source, 0) + 1
        print(f"   Sources breakdown: {sources_debug}")

        result = {
            'search_query': original_query,
            'query_variations_generated': len(query_variations),
            'batch_id': combined_data['batch_id'] if combined_data else None,
            'sources': ['youtube', 'reddit'],
            'total_youtube_videos': len(youtube_videos),
            'total_reddit_posts': len(reddit_posts),
            'total_comments': total_comments,
            'total_replies': total_replies,
            'grand_total': grand_total,
            'unique_comments': unique_count,
            'videos': aggregation_result['videos'],
            'saved_to': save_result,
            'storage_type': 'mongodb',
            'target_achieved': aggregation_result['target_achieved'],
            'successful_queries': aggregation_result['successful_queries'],
            'failed_queries': aggregation_result['failed_queries'],
            'latency_seconds': round(latency_seconds, 2),
            'query_results': aggregation_result['query_results'],
            'processing_complete': True,
            'ai_powered': True,
            'timestamp': get_current_timestamp()
        }

        print("🎉 AI-powered multi-query search completed successfully!")
        return jsonify(result)

    except Exception as e:
        print(f"ERROR in AI search endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'AI-powered search failed: {str(e)}'}), 500


@search_bp.route('/search/simple', methods=['POST'])
def simple_search():
    """Simple search endpoint for single query without AI variations"""
    print("=== SIMPLE SEARCH ENDPOINT CALLED ===")
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()

        # Validate query
        is_valid, validation_message = validate_query(query)
        if not is_valid:
            return jsonify({'error': validation_message}), 400

        print(f"🔍 Starting simple search for: '{query}'")
        start_time = time.time()

        # Fetch comments using single query
        result = comment_fetcher.fetch_all_comments_parallel(
            query=query,
            min_total_comments=data.get('target_comments', 10000),
            max_retries=data.get('max_retries', 2)
        )

        end_time = time.time()
        latency_seconds = end_time - start_time

        if not result['videos']:
            return jsonify({'error': 'No content found!'}), 404

        # Get unique comments
        unique_comments, unique_count, total_replies = comment_fetcher.get_unique_comments_unified(result['videos'])

        # Save data
        save_result, combined_data = comment_fetcher.save_unified_data(
            query,
            result['videos'],
            unique_comments,
            unique_count,
            total_replies,
            result['total_comments'],
            result['sources']
        )

        response = {
            'search_query': query,
            'batch_id': combined_data['batch_id'] if combined_data else None,
            'sources': result['sources'],
            'total_comments': result['total_comments'],
            'total_replies': result['total_replies'],
            'grand_total': result['grand_total'],
            'unique_comments': unique_count,
            'videos': result['videos'],
            'saved_to': save_result,
            'target_achieved': result['target_achieved'],
            'attempts_made': result['attempts_made'],
            'latency_seconds': round(latency_seconds, 2),
            'processing_complete': True,
            'ai_powered': False,
            'timestamp': get_current_timestamp()
        }

        print("✅ Simple search completed successfully!")
        return jsonify(response)

    except Exception as e:
        print(f"ERROR in simple search endpoint: {str(e)}")
        return jsonify({'error': f'Simple search failed: {str(e)}'}), 500


@search_bp.route('/search/status/<batch_id>', methods=['GET'])
def get_search_status(batch_id):
    """Get status of a search operation by batch ID"""
    try:
        from services.database import db_service
        
        result = db_service.get_search_result(batch_id)
        
        if not result:
            return jsonify({'error': 'Search result not found'}), 404
        
        return jsonify({
            'batch_id': batch_id,
            'status': 'completed',
            'result': result
        })
        
    except Exception as e:
        print(f"Error getting search status for {batch_id}: {e}")
        return jsonify({'error': str(e)}), 500


@search_bp.route('/search/suggestions', methods=['POST'])
def get_search_suggestions():
    """Get AI-generated search suggestions based on a query"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Validate query
        is_valid, validation_message = validate_query(query)
        if not is_valid:
            return jsonify({'error': validation_message}), 400
        
        # Generate suggestions using AI
        suggestions = ai_service.suggest_related_queries(
            query, 
            num_suggestions=data.get('num_suggestions', 5)
        )
        
        return jsonify({
            'original_query': query,
            'suggestions': suggestions,
            'count': len(suggestions)
        })
        
    except Exception as e:
        print(f"Error generating search suggestions: {e}")
        return jsonify({'error': str(e)}), 500