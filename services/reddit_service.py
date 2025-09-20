"""
Reddit service for comment fetching and processing
Handles Reddit API integration and comment filtering
"""
import praw
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import Config


class RedditService:
    """Service for Reddit API operations and comment fetching"""
    
    def __init__(self):
        self.config = Config()
        self.client_id = self.config.REDDIT_CLIENT_ID
        self.client_secret = self.config.REDDIT_CLIENT_SECRET
        self.user_agent = self.config.REDDIT_USER_AGENT

        if not all([self.client_id, self.client_secret, self.user_agent]):
            raise ValueError("Please set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT in environment variables")

        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent
        )
    
    def search_subreddits(self, query, limit=10):
        """Search for relevant subreddits based on query"""
        try:
            # Common subreddits that might be relevant for various topics
            relevant_subreddits = [
                'all', 'AskReddit', 'todayilearned', 'news', 'worldnews',
                'technology', 'science', 'politics', 'gaming', 'movies',
                'music', 'books', 'sports', 'food', 'travel', 'history',
                'personalfinance', 'investing', 'explainlikeimfive', 'askscience'
            ]

            # Filter subreddits that might be relevant to the query
            query_lower = query.lower()
            filtered_subreddits = []

            # Add query-specific subreddits if they might exist
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 3:  # Only add meaningful words
                    relevant_subreddits.append(word)

            for subreddit_name in relevant_subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    # Check if subreddit exists and is accessible
                    subreddit.display_name
                    filtered_subreddits.append(subreddit_name)
                except:
                    continue

            # Limit and return
            result = filtered_subreddits[:limit]
            print(f"🔍 Selected subreddits for search: {result}")
            return result

        except Exception as e:
            print(f"❌ Error searching subreddits: {e}")
            return ['all', 'AskReddit']  # fallback
    
    def filter_comment_relevance(self, comment_text, query_terms):
        """Filter comments for relevance to query terms"""
        comment_lower = comment_text.lower()
        
        # Basic relevance check
        matching_terms = sum(1 for term in query_terms if term in comment_lower)
        
        # For single term queries, check for partial matches
        if len(query_terms) == 1 and len(list(query_terms)[0]) > 3:
            partial_term = list(query_terms)[0][:4]
            if partial_term in comment_lower:
                matching_terms += 0.5
        
        # For multi-term queries, require at least half the terms to match
        if len(query_terms) > 1:
            return matching_terms >= max(1, len(query_terms) // 2)
        else:
            return matching_terms > 0
    
    def get_comments_from_subreddit(self, subreddit_name, query, limit=None):
        """Fetch comments from a specific subreddit"""
        if limit is None:
            limit = self.config.MAX_REDDIT_COMMENTS // 8  # Distribute across subreddits
        
        try:
            print(f"🔍 Searching r/{subreddit_name} for: '{query}' (limit: {limit})")
            
            subreddit = self.reddit.subreddit(subreddit_name)
            comments_data = []

            # Search for posts related to the query
            search_results = subreddit.search(
                query, 
                limit=min(limit // 10, 50), 
                sort='relevance', 
                time_filter='all'
            )

            # Prepare query terms for relevance filtering
            query_terms = set(query.lower().split())
            if len(query_terms) == 1 and len(list(query_terms)[0]) > 3:
                # For single word queries, also check for partial matches
                query_terms.add(list(query_terms)[0][:4])  # First 4 characters

            total_comments_processed = 0
            relevant_comments_found = 0

            for post in search_results:
                try:
                    # Get comments from this post
                    post.comments.replace_more(limit=0)  # Remove "load more comments" objects

                    for comment in post.comments.list():
                        if len(comments_data) >= limit:
                            break

                        total_comments_processed += 1
                        
                        # Skip deleted/removed comments
                        if not hasattr(comment, 'body') or comment.body in ['[deleted]', '[removed]']:
                            continue
                        
                        # Filter for relevance
                        if not self.filter_comment_relevance(comment.body, query_terms):
                            continue

                        relevant_comments_found += 1

                        comment_data = {
                            'author': str(comment.author) if comment.author else 'Anonymous',
                            'text': comment.body,
                            'likes': comment.score,
                            'published_at': datetime.fromtimestamp(comment.created_utc).isoformat(),
                            'author_profile': '',
                            'post_title': post.title,
                            'subreddit': subreddit_name,
                            'replies': []
                        }

                        # Get replies and filter them for relevance too
                        if hasattr(comment, 'replies') and comment.replies:
                            for reply in comment.replies.list():
                                if len(comment_data['replies']) >= 5:  # Limit replies per comment
                                    break

                                if not hasattr(reply, 'body') or reply.body in ['[deleted]', '[removed]']:
                                    continue

                                if self.filter_comment_relevance(reply.body, query_terms):
                                    reply_data = {
                                        'author': str(reply.author) if reply.author else 'Anonymous',
                                        'text': reply.body,
                                        'likes': reply.score,
                                        'published_at': datetime.fromtimestamp(reply.created_utc).isoformat(),
                                        'author_profile': ''
                                    }
                                    comment_data['replies'].append(reply_data)

                        comments_data.append(comment_data)

                    if len(comments_data) >= limit:
                        break

                except Exception as e:
                    print(f"⚠️  Error processing post in r/{subreddit_name}: {e}")
                    continue

            print(f"✅ r/{subreddit_name}: Processed {total_comments_processed} comments, found {relevant_comments_found} relevant")
            return comments_data

        except Exception as e:
            print(f"❌ Error fetching comments from r/{subreddit_name}: {e}")
            return []
    
    def get_comments_parallel(self, query, total_limit=None):
        """Fetch comments from multiple subreddits in parallel"""
        if total_limit is None:
            total_limit = self.config.MAX_REDDIT_COMMENTS
        
        try:
            print(f"🚀 Starting parallel Reddit search for: '{query}' (target: {total_limit} comments)")
            
            subreddits = self.search_subreddits(query, limit=8)
            print(f"📋 Searching in subreddits: {subreddits}")

            all_comments = []
            comments_per_subreddit = max(100, total_limit // len(subreddits))

            def fetch_from_subreddit(subreddit_name):
                return self.get_comments_from_subreddit(subreddit_name, query, comments_per_subreddit)

            with ThreadPoolExecutor(max_workers=min(len(subreddits), self.config.MAX_WORKERS)) as executor:
                future_to_subreddit = {
                    executor.submit(fetch_from_subreddit, subreddit): subreddit
                    for subreddit in subreddits
                }

                for future in as_completed(future_to_subreddit):
                    subreddit = future_to_subreddit[future]
                    try:
                        comments = future.result()
                        all_comments.extend(comments)
                        print(f"✅ Got {len(comments)} comments from r/{subreddit}")
                    except Exception as e:
                        print(f"❌ Error fetching from r/{subreddit}: {e}")

            print(f"🎯 Reddit fetch complete: {len(all_comments)} total comments from {len(subreddits)} subreddits")
            return all_comments

        except Exception as e:
            print(f"❌ Error in parallel Reddit comment fetching: {e}")
            return []
    
    def get_hot_posts(self, subreddit_name, limit=25):
        """Get hot posts from a subreddit"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            hot_posts = []
            
            for post in subreddit.hot(limit=limit):
                post_data = {
                    'post_id': post.id,
                    'title': post.title,
                    'author': str(post.author) if post.author else 'Anonymous',
                    'score': post.score,
                    'url': post.url,
                    'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                    'num_comments': post.num_comments,
                    'subreddit': subreddit_name,
                    'text': post.selftext if hasattr(post, 'selftext') else ''
                }
                hot_posts.append(post_data)
            
            return hot_posts
            
        except Exception as e:
            print(f"❌ Error getting hot posts from r/{subreddit_name}: {e}")
            return []
    
    def get_trending_subreddits(self, limit=10):
        """Get trending subreddits"""
        try:
            # This is a simplified version - Reddit API doesn't directly provide trending subreddits
            # We return popular general subreddits instead
            popular_subreddits = [
                'all', 'AskReddit', 'todayilearned', 'news', 'worldnews',
                'technology', 'science', 'gaming', 'movies', 'music'
            ]
            
            trending_data = []
            for subreddit_name in popular_subreddits[:limit]:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    trending_data.append({
                        'name': subreddit_name,
                        'display_name': subreddit.display_name,
                        'subscribers': subreddit.subscribers if hasattr(subreddit, 'subscribers') else 0,
                        'description': subreddit.public_description if hasattr(subreddit, 'public_description') else ''
                    })
                except:
                    continue
            
            return trending_data
            
        except Exception as e:
            print(f"❌ Error getting trending subreddits: {e}")
            return []
    
    def search_posts_by_query(self, query, subreddit_names=None, limit=50):
        """Search for posts across multiple subreddits"""
        if subreddit_names is None:
            subreddit_names = self.search_subreddits(query, limit=5)
        
        all_posts = []
        
        for subreddit_name in subreddit_names:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                posts = subreddit.search(query, limit=limit//len(subreddit_names), sort='relevance')
                
                for post in posts:
                    post_data = {
                        'post_id': post.id,
                        'title': post.title,
                        'author': str(post.author) if post.author else 'Anonymous',
                        'score': post.score,
                        'url': post.url,
                        'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                        'num_comments': post.num_comments,
                        'subreddit': subreddit_name,
                        'text': post.selftext if hasattr(post, 'selftext') else ''
                    }
                    all_posts.append(post_data)
                    
            except Exception as e:
                print(f"❌ Error searching r/{subreddit_name}: {e}")
                continue
        
        return all_posts


# Global Reddit service instance
reddit_service = RedditService()