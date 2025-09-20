"""
Unified comment fetcher service
Orchestrates YouTube and Reddit comment fetching with AI-powered query generation
Optimized for parallel processing to achieve sub-minute latency
"""
import time
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import Config
from services.ai_service import ai_service
from services.youtube_service import youtube_service
from services.reddit_service import reddit_service
from services.database import db_service
from utils.file_utils import save_to_json_file, sanitize_filename


class UnifiedCommentFetcher:
    """Service that orchestrates comment fetching from multiple sources"""
    
    def __init__(self):
        self.config = Config()
        self.ai_service = ai_service
        self.youtube_service = youtube_service
        self.reddit_service = reddit_service
        self.db_service = db_service
    
    def fetch_all_comments_parallel(self, query, min_total_comments=None, max_retries=None):
        """Fetch comments from both YouTube and Reddit in parallel with retry logic"""
        if min_total_comments is None:
            min_total_comments = self.config.TARGET_TOTAL_COMMENTS
        if max_retries is None:
            max_retries = self.config.MAX_RETRY_ATTEMPTS
        
        print(f"=== FETCHING COMMENTS FOR: '{query}' ===")
        print(f"Target: Minimum {min_total_comments} total comments (comments + replies)")

        all_videos = []
        total_comments = 0
        total_replies = 0
        attempt = 1
        sources_used = []

        while total_comments + total_replies < min_total_comments and attempt <= max_retries:
            print(f"\n--- ATTEMPT {attempt}/{max_retries} ---")

            results = {}
            errors = {}

            def fetch_youtube(max_videos=15, comments_per_video=100):  # Reduced for faster processing
                try:
                    print(f"🔍 Starting YouTube search for: '{query}'")
                    # Reduce video count and comments for faster processing
                    video_count = max_videos + (attempt - 1) * 5  # Smaller increments
                    comments_per_video = comments_per_video + (attempt - 1) * 20

                    videos_with_comments = self.youtube_service.search_and_get_comments(
                        query, 
                        max_videos=video_count, 
                        max_comments_per_video=comments_per_video
                    )

                    if not videos_with_comments:
                        return {'error': 'No YouTube videos found'}

                    total_yt_comments = sum(len(v['comments']) for v in videos_with_comments)
                    print(f"📺 YouTube result: {len(videos_with_comments)} videos, {total_yt_comments} comments")

                    return {
                        'source': 'youtube',
                        'videos': videos_with_comments,
                        'total_comments': total_yt_comments
                    }

                except Exception as e:
                    error_msg = str(e)
                    # Log the specific error but still count partial success
                    if "SSL" in error_msg or "ssl" in error_msg.lower():
                        print(f"⚠️ YouTube SSL error (partial data may still be collected): {e}")
                    else:
                        print(f"❌ YouTube fetch error: {e}")
                    return {'error': error_msg}

            def fetch_reddit(comments_limit=2000):  # Reduced for faster processing
                try:
                    print(f"🔍 Starting Reddit search for: '{query}'")
                    # Reduce comment limit for faster processing
                    reddit_limit = comments_limit + (attempt - 1) * 500

                    reddit_comments = self.reddit_service.get_comments_parallel(query, reddit_limit)

                    # Convert Reddit comments to unified format
                    reddit_posts = []
                    for comment in reddit_comments:
                        reddit_posts.append({
                            'post_info': {
                                'title': comment['post_title'],
                                'subreddit': comment['subreddit'],
                                'source': 'reddit'
                            },
                            'comments': [comment],
                            'comment_count': 1,
                            'source': 'reddit'
                        })

                    print(f"🟠 Reddit result: {len(reddit_comments)} comments")

                    return {
                        'source': 'reddit',
                        'videos': reddit_posts,
                        'total_comments': len(reddit_comments)
                    }

                except Exception as e:
                    print(f"❌ Reddit fetch error: {e}")
                    return {'error': str(e)}

            # Run both fetches in parallel with reduced timeout for speed
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_yt = executor.submit(fetch_youtube)
                future_reddit = executor.submit(fetch_reddit)

                # Get results with shorter timeout for faster processing
                try:
                    yt_result = future_yt.result(timeout=120)  # Reduced timeout for speed
                    if 'error' not in yt_result:
                        results['youtube'] = yt_result
                        if 'youtube' not in sources_used:
                            sources_used.append('youtube')
                        print(f"✅ YouTube successful: {yt_result['total_comments']} comments from {len(yt_result['videos'])} videos")
                    else:
                        errors['youtube'] = yt_result['error']
                        print(f"❌ YouTube failed: {yt_result['error']}")
                except Exception as e:
                    errors['youtube'] = str(e)
                    print(f"❌ YouTube exception: {str(e)}")

                try:
                    reddit_result = future_reddit.result(timeout=120)  # Reduced timeout for speed
                    if 'error' not in reddit_result:
                        results['reddit'] = reddit_result
                        if 'reddit' not in sources_used:
                            sources_used.append('reddit')
                        print(f"✅ Reddit successful: {reddit_result['total_comments']} comments")
                    else:
                        errors['reddit'] = reddit_result['error']
                        print(f"❌ Reddit failed: {reddit_result['error']}")
                except Exception as e:
                    errors['reddit'] = str(e)
                    print(f"❌ Reddit exception: {str(e)}")

            # Add new results to accumulated data
            attempt_videos = []
            attempt_comments = 0
            attempt_replies = 0

            if 'youtube' in results:
                attempt_videos.extend(results['youtube']['videos'])
                attempt_comments += results['youtube']['total_comments']
                print(f"✅ YouTube added: {len(results['youtube']['videos'])} videos, {results['youtube']['total_comments']} comments")

            if 'reddit' in results:
                attempt_videos.extend(results['reddit']['videos'])
                attempt_comments += results['reddit']['total_comments']
                print(f"✅ Reddit added: {len(results['reddit']['videos'])} posts, {results['reddit']['total_comments']} comments")

            # Calculate replies in this attempt
            for video in attempt_videos:
                for comment in video['comments']:
                    attempt_replies += len(comment.get('replies', []))

            # Add to totals
            all_videos.extend(attempt_videos)
            total_comments += attempt_comments
            total_replies += attempt_replies

            current_total = total_comments + total_replies
            print(f"📊 Attempt {attempt} results:")
            print(f"   Comments collected: {attempt_comments}")
            print(f"   Replies collected: {attempt_replies}")
            print(f"   Total so far: {current_total}")
            print(f"   Target: {min_total_comments}")
            print(f"   Videos in this attempt: {len(attempt_videos)}")
            print(f"   Total videos so far: {len(all_videos)}")

            # Check if we've reached the target OR if we have some data and no more sources to try
            if current_total >= min_total_comments:
                print(f"✅ Target reached! Total: {current_total}")
                break
            elif len(attempt_videos) == 0 and attempt < max_retries:
                print(f"⚠️  No data collected in this attempt. Starting attempt {attempt + 1}...")
                time.sleep(self.config.PAUSE_BETWEEN_ATTEMPTS)
            elif attempt < max_retries:
                print(f"⚠️  Target not reached but got some data. Starting attempt {attempt + 1}...")
                time.sleep(self.config.PAUSE_BETWEEN_ATTEMPTS)
            else:
                print(f"❌ Maximum retries reached. Final total: {current_total}")

            attempt += 1

        print(f"\n🎯 FINAL RESULTS:")
        print(f"   Total comments: {total_comments}")
        print(f"   Total replies: {total_replies}")
        print(f"   Grand total: {total_comments + total_replies}")
        print(f"   Total videos: {len(all_videos)}")
        print(f"   Sources used: {sources_used}")
        print(f"   Attempts made: {attempt - 1}")

        return {
            'videos': all_videos,
            'total_comments': total_comments,
            'total_replies': total_replies,
            'grand_total': total_comments + total_replies,
            'sources': sources_used,
            'errors': errors,
            'target_achieved': (total_comments + total_replies) >= min_total_comments,
            'attempts_made': attempt - 1
        }
    
    def fetch_multiple_queries_aggregated(self, queries, target_total_comments=None):
        """Fetch comments for multiple queries in parallel and aggregate unique results"""
        if target_total_comments is None:
            target_total_comments = self.config.TARGET_TOTAL_COMMENTS
        
        print(f"🚀 STARTING PARALLEL MULTI-QUERY AGGREGATION")
        print(f"📋 Total queries to process: {len(queries)}")
        print(f"🎯 Target unique comments: {target_total_comments}")
        print(f"⚡ Processing queries in parallel for maximum speed!")

        all_unique_comments = {}
        all_videos_data = []
        total_processed_comments = 0
        total_processed_replies = 0
        successful_queries = 0
        failed_queries = 0
        query_results = []
        
        start_time = time.time()

        def process_single_query(query_info):
            """Process a single query - designed for parallel execution"""
            i, query = query_info
            print(f"� Starting parallel processing for Query {i}/{len(queries)}: '{query}'")
            
            try:
                # Fetch comments for this specific query
                query_result = self.fetch_all_comments_parallel(
                    query=query,
                    min_total_comments=max(1000, target_total_comments // len(queries)),  # Further reduced for faster completion
                    max_retries=1  # Reduced retries for speed
                )

                # Consider query successful if we got ANY data (videos or comments)
                if query_result['videos'] and len(query_result['videos']) > 0:
                    # Extract unique comments from this query
                    query_unique, query_unique_count, query_replies = self.get_unique_comments_unified(query_result['videos'])

                    print(f"✅ Query {i} completed: {len(query_result['videos'])} videos, {query_result['total_comments']} comments, {query_unique_count} unique")
                    
                    return {
                        'success': True,
                        'query': query,
                        'query_unique': query_unique,
                        'query_unique_count': query_unique_count,
                        'query_replies': query_replies,
                        'videos': query_result['videos'],
                        'total_comments': query_result['total_comments'],
                        'total_replies': query_result['total_replies'],
                        'sources': query_result['sources'],
                        'attempts': query_result['attempts_made']
                    }
                else:
                    print(f"❌ Query {i} failed - no videos collected (comments: {query_result.get('total_comments', 0)})")
                    return {
                        'success': False,
                        'query': query,
                        'error': f'No videos collected (got {query_result.get("total_comments", 0)} comments)'
                    }

            except Exception as e:
                print(f"❌ Query {i} crashed: {e}")
                return {
                    'success': False,
                    'query': query,
                    'error': str(e)
                }

        # Process all queries in parallel using ThreadPoolExecutor
        print(f"🏃‍♂️ Launching {len(queries)} parallel query processors...")
        
        with ThreadPoolExecutor(max_workers=min(8, len(queries))) as executor:  # Limit to 8 concurrent threads
            # Submit all queries for parallel processing
            future_to_query = {
                executor.submit(process_single_query, (i+1, query)): (i+1, query) 
                for i, query in enumerate(queries)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_query):
                query_info = future_to_query[future]
                try:
                    result = future.result()
                    
                    if result['success']:
                        # Add to global unique comments (avoiding duplicates)
                        new_unique_count = 0
                        for comment in result['query_unique']:
                            comment_text = comment['text'].strip()
                            if comment_text not in all_unique_comments:
                                all_unique_comments[comment_text] = comment
                                new_unique_count += 1

                        # Add video data
                        all_videos_data.extend(result['videos'])

                        # Update totals
                        total_processed_comments += result['total_comments']
                        total_processed_replies += result['total_replies']

                        query_results.append({
                            'query': result['query'],
                            'status': 'success',
                            'total_comments': result['total_comments'],
                            'total_replies': result['total_replies'],
                            'unique_comments': result['query_unique_count'],
                            'new_unique_comments': new_unique_count,
                            'sources': result['sources'],
                            'attempts': result['attempts']
                        })

                        successful_queries += 1
                        current_unique_total = len(all_unique_comments)

                        print(f"✅ Processed query: {result['query'][:50]}...")
                        print(f"   📊 Comments: {result['total_comments']}, Replies: {result['total_replies']}")
                        print(f"   🆕 New unique added: {new_unique_count}")
                        print(f"   📈 Global unique total: {current_unique_total}")

                        # Check if we've reached the target
                        if current_unique_total >= target_total_comments:
                            print(f"🎉 TARGET REACHED! {current_unique_total} unique comments collected")
                            # Note: We don't break here because parallel processing is already running
                    else:
                        failed_queries += 1
                        query_results.append({
                            'query': result['query'],
                            'status': 'failed',
                            'error': result['error']
                        })
                        
                except Exception as e:
                    print(f"❌ Error processing result for query {query_info[1]}: {e}")
                    failed_queries += 1

        # Calculate timing
        end_time = time.time()
        processing_time = end_time - start_time

        # Final results
        final_unique_comments = list(all_unique_comments.values())
        final_unique_count = len(final_unique_comments)

        print(f"\n{'='*60}")
        print(f"🎯 MULTI-QUERY AGGREGATION COMPLETE")
        print(f"{'='*60}")
        print(f"📊 Summary:")
        print(f"   🔢 Total queries processed: {len(queries)}")
        print(f"   ✅ Successful queries: {successful_queries}")
        print(f"   ❌ Failed queries: {failed_queries}")
        print(f"   💬 Total comments processed: {total_processed_comments}")
        print(f"   🔄 Total replies processed: {total_processed_replies}")
        print(f"   🎯 Final unique comments: {final_unique_count}")
        print(f"   ⏱️  Total processing time: {processing_time:.2f} seconds ({processing_time/60:.1f} minutes)")
        print(f"   � Average time per query: {processing_time/len(queries):.2f} seconds (parallel processing)")
        print(f"   �📈 Target achieved: {'✅ YES' if final_unique_count >= target_total_comments else '❌ NO'}")

        return {
            'videos': all_videos_data,
            'unique_comments': final_unique_comments,
            'unique_count': final_unique_count,
            'total_processed_comments': total_processed_comments,
            'total_processed_replies': total_processed_replies,
            'grand_total': total_processed_comments + total_processed_replies,
            'successful_queries': successful_queries,
            'failed_queries': failed_queries,
            'query_results': query_results,
            'target_achieved': final_unique_count >= target_total_comments,
            'original_queries': queries,
            'processing_time_seconds': processing_time,
            'parallel_processing': True
        }
    
    def get_unique_comments_unified(self, videos_data):
        """Extract unique comments from both YouTube and Reddit data"""
        unique_comments = {}
        total_comments = 0
        total_replies = 0

        for video in videos_data:
            source = video.get('source', 'unknown')

            for comment in video['comments']:
                comment_text = comment['text'].strip()

                # Skip empty comments
                if not comment_text or len(comment_text) < 3:
                    continue

                if comment_text not in unique_comments:
                    unique_comments[comment_text] = {
                        'author': comment['author'],
                        'text': comment_text,
                        'likes': comment.get('likes', 0),
                        'published_at': comment['published_at'],
                        'author_profile': comment.get('author_profile', ''),
                        'source': source,
                        'video_title': video.get('video_info', {}).get('title', video.get('post_info', {}).get('title', 'Unknown')),
                        'subreddit': video.get('post_info', {}).get('subreddit', ''),
                        'replies': []
                    }
                    total_comments += 1

                # Add replies
                existing_replies = [r['text'] for r in unique_comments[comment_text]['replies']]
                for reply in comment.get('replies', []):
                    reply_text = reply['text'].strip()
                    if reply_text and reply_text not in existing_replies and len(reply_text) > 3:
                        unique_comments[comment_text]['replies'].append({
                            'author': reply['author'],
                            'text': reply_text,
                            'likes': reply.get('likes', 0),
                            'published_at': reply['published_at'],
                            'author_profile': reply.get('author_profile', ''),
                            'source': source
                        })
                        total_replies += 1

        return list(unique_comments.values()), total_comments, total_replies
    
    def save_unified_data(self, query, videos_data, unique_comments, unique_count, total_replies, total_comments, sources):
        """Save unified data from both YouTube and Reddit"""
        try:
            batch_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            sanitized_query = sanitize_filename(query)

            print(f"💾 Saving unified data...")
            print(f"   Query: '{query}'")
            print(f"   Batch ID: {batch_id}")
            print(f"   Timestamp: {timestamp}")

            # Separate YouTube and Reddit data
            youtube_videos = [v for v in videos_data if v.get('source') == 'youtube']
            reddit_posts = [v for v in videos_data if v.get('source') == 'reddit']

            combined_data = {
                'batch_id': batch_id,
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'sources': sources,
                'total_youtube_videos': len(youtube_videos),
                'total_reddit_posts': len(reddit_posts),
                'total_comments': total_comments,
                'total_replies': total_replies,
                'grand_total': total_comments + total_replies,
                'unique_comments': unique_count,
                'youtube_data': youtube_videos,
                'reddit_data': reddit_posts,
                'unique_comments_data': unique_comments,
                'processing_info': {
                    'processed_at': datetime.now().isoformat(),
                    'duplicates_removed': total_comments - unique_count,
                    'youtube_comments': sum(len(v['comments']) for v in youtube_videos),
                    'reddit_comments': sum(len(v['comments']) for v in reddit_posts),
                    'comments_per_source_avg': {
                        'youtube': sum(len(v['comments']) for v in youtube_videos) / len(youtube_videos) if youtube_videos else 0,
                        'reddit': sum(len(v['comments']) for v in reddit_posts) / len(reddit_posts) if reddit_posts else 0
                    }
                }
            }

            # Save to MongoDB
            mongo_result = self.db_service.save_search_result(combined_data)
            
            # Save to JSON files as backup
            videos_filename = save_to_json_file(
                data={
                    'batch_id': batch_id,
                    'query': query,
                    'timestamp': datetime.now().isoformat(),
                    'youtube_data': youtube_videos,
                    'reddit_data': reddit_posts
                },
                directory=self.config.DATA_DIRECTORY,
                filename_prefix=f"{sanitized_query}_videos_{timestamp}_{batch_id}"
            )

            history_filename = save_to_json_file(
                data={
                    'batch_id': batch_id,
                    'query': query,
                    'timestamp': datetime.now().isoformat(),
                    'total_unique_comments': unique_count,
                    'unique_comments': unique_comments
                },
                directory=self.config.HISTORY_DIRECTORY,
                filename_prefix=f"unique_comments_{sanitized_query}_{timestamp}_{batch_id}"
            )

            print(f"✅ Data saved successfully:")
            print(f"   MongoDB: {'✅' if mongo_result else '❌'}")
            print(f"   Videos file: {videos_filename}")
            print(f"   History file: {history_filename}")

            return f"mongodb:{mongo_result}" if mongo_result else "files_only", combined_data

        except Exception as e:
            print(f"❌ Error saving unified data: {e}")
            import traceback
            traceback.print_exc()
            return None, None


# Global unified comment fetcher instance
comment_fetcher = UnifiedCommentFetcher()