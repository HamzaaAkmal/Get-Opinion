"""
Database service for MongoDB operations
Handles connection management and database operations
"""
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import Config


class DatabaseService:
    """MongoDB database service for managing connections and operations"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.config = Config()
        
    def connect(self):
        """Establish MongoDB connection"""
        if self.client is None:
            try:
                print("🔌 Connecting to MongoDB...")
                print(f"📍 URI: {self.config.MONGODB_URI[:30]}..." if self.config.MONGODB_URI else "No URI configured")
                print(f"📊 Database: {self.config.MONGODB_DATABASE}")

                if not self.config.MONGODB_URI:
                    print("❌ MongoDB URI not configured in environment variables")
                    return False

                self.client = MongoClient(
                    self.config.MONGODB_URI, 
                    serverSelectionTimeoutMS=self.config.MONGODB_TIMEOUT
                )
                
                # Test the connection
                self.client.admin.command('ping')
                self.db = self.client[self.config.MONGODB_DATABASE]
                print(f"✅ Connected to MongoDB database: {self.config.MONGODB_DATABASE}")
                return True
                
            except ConnectionFailure as e:
                print(f"❌ MongoDB connection failed: {e}")
                print("💡 This might be due to network issues or incorrect credentials")
                return False
                
            except ServerSelectionTimeoutError as e:
                print(f"❌ MongoDB server timeout: {e}")
                print("💡 Check your internet connection and MongoDB Atlas IP whitelist")
                return False
                
            except Exception as e:
                error_msg = str(e)
                if "authentication failed" in error_msg.lower():
                    print("❌ MongoDB authentication failed!")
                    print("💡 Please check:")
                    print("   1. Username and password in MONGODB_URI")
                    print("   2. User exists in MongoDB Atlas")
                    print("   3. User has read/write permissions")
                    print("   4. IP address is whitelisted in MongoDB Atlas")
                else:
                    print(f"❌ Unexpected MongoDB error: {e}")
                return False
        
        return True
    
    def get_database(self):
        """Get database instance, connecting if necessary"""
        if not self.connect():
            return None
        return self.db
    
    def test_connection(self):
        """Test MongoDB connection and basic operations"""
        try:
            if not self.connect():
                return False, "Failed to connect to MongoDB. Check your connection string and Atlas settings."
            
            # Test database operations
            collections = self.db.list_collection_names()
            print(f"📊 Available collections: {collections}")

            # Test a simple operation
            test_doc = {"test": "connection", "timestamp": datetime.now().isoformat()}
            result = self.db.test_collection.insert_one(test_doc)
            print(f"✅ Test document inserted with ID: {result.inserted_id}")

            # Clean up test document
            self.db.test_collection.delete_one({"_id": result.inserted_id})
            print("🧹 Test document cleaned up")

            return True, f"Connected to {self.config.MONGODB_DATABASE}. Collections: {collections}"
            
        except Exception as e:
            error_details = str(e)
            if "authentication failed" in error_details:
                return False, ("Authentication failed. Please check:\n"
                              "1. Username/password in MONGODB_URI\n"
                              "2. User exists in MongoDB Atlas dashboard\n"
                              "3. User has database access permissions\n"
                              "4. Your IP is whitelisted in Network Access")
            elif "connection" in error_details.lower():
                return False, "Connection failed. Check your internet connection and MongoDB Atlas cluster status."
            else:
                return False, f"MongoDB test failed: {error_details}"
    
    def save_search_result(self, data):
        """Save search result to MongoDB"""
        try:
            if not self.connect():
                return None
            
            collection = self.db['search_results']
            result = collection.insert_one(data)
            print(f"✅ Search result saved to MongoDB with ID: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            if "DocumentTooLarge" in str(e):
                print(f"⚠️  MongoDB document too large, saving minimal metadata only...")
                # Save minimal metadata
                minimal_data = {
                    'batch_id': data.get('batch_id'),
                    'query': data.get('query'),
                    'timestamp': data.get('timestamp'),
                    'total_comments': data.get('total_comments'),
                    'unique_comments': data.get('unique_comments'),
                    'error': 'Data too large for MongoDB',
                    'data_storage': {
                        'full_data_saved_to_files': True,
                        'note': 'Full data available in JSON files due to size constraints'
                    }
                }
                try:
                    result = collection.insert_one(minimal_data)
                    print(f"✅ Minimal metadata saved to MongoDB with ID: {result.inserted_id}")
                    return result.inserted_id
                except Exception as e2:
                    print(f"❌ Failed to save even metadata to MongoDB: {e2}")
                    return None
            else:
                print(f"❌ MongoDB error: {e}")
                return None
    
    def get_search_result(self, batch_id):
        """Get search result by batch ID"""
        try:
            if not self.connect():
                return None
            
            collection = self.db['search_results']
            result = collection.find_one({'batch_id': batch_id})
            
            if result:
                # Convert ObjectId to string for JSON serialization
                result['_id'] = str(result['_id'])
            
            return result
            
        except Exception as e:
            print(f"❌ Error retrieving batch {batch_id}: {e}")
            return None
    
    def list_search_results(self):
        """List all search results"""
        try:
            if not self.connect():
                return []
            
            collection = self.db['search_results']
            
            # Get all results, sorted by timestamp (newest first)
            results_cursor = collection.find({}, {
                'batch_id': 1,
                'query': 1,
                'timestamp': 1,
                'total_youtube_videos': 1,
                'total_reddit_posts': 1,
                'grand_total': 1,
                'unique_comments': 1,
                'sources': 1
            }).sort('timestamp', -1)

            results = []
            for result in results_cursor:
                results.append({
                    'batch_id': result['batch_id'],
                    'query': result['query'],
                    'timestamp': result['timestamp'],
                    'total_youtube_videos': result.get('total_youtube_videos', 0),
                    'total_reddit_posts': result.get('total_reddit_posts', 0),
                    'grand_total': result.get('grand_total', 0),
                    'unique_comments': result.get('unique_comments', 0),
                    'sources': result.get('sources', []),
                    'storage': 'mongodb'
                })

            return results
            
        except Exception as e:
            print(f"❌ Error listing search results: {e}")
            return []
    
    def get_collection_stats(self):
        """Get database collection statistics"""
        try:
            if not self.connect():
                return None
            
            collections = self.db.list_collection_names()
            stats = {}

            for collection_name in collections:
                collection = self.db[collection_name]
                count = collection.count_documents({})
                stats[collection_name] = {
                    'document_count': count,
                    'collection_name': collection_name
                }

            return {
                'database': self.config.MONGODB_DATABASE,
                'collections': stats,
                'total_collections': len(collections)
            }
            
        except Exception as e:
            print(f"❌ Error getting collection stats: {e}")
            return None
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            print("🔌 MongoDB connection closed")


# Global database service instance
db_service = DatabaseService()