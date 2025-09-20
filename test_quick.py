import requests
import json
import time

def test_improved_scraper():
    """Test the improved YouTube scraper with a simple query"""
    print("🧪 Testing improved YouTube scraper...")
    
    # Test payload with small numbers for quick testing
    test_payload = {
        "query": "Tesla 2025",
        "num_variations": 3,  # Small number for testing
        "target_comments": 5000  # Smaller target for testing
    }
    
    print(f"📋 Test configuration:")
    print(f"   Query: {test_payload['query']}")
    print(f"   Variations: {test_payload['num_variations']}")
    print(f"   Target: {test_payload['target_comments']}")
    
    try:
        print("\n🚀 Sending request to /api/search...")
        start_time = time.time()
        
        response = requests.post(
            'http://localhost:5000/api/search',
            json=test_payload,
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        
        print(f"📡 Response received in {end_time - start_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ SUCCESS! Results:")
            print(f"   🔢 Query variations generated: {data.get('query_variations_generated', 0)}")
            print(f"   📺 YouTube videos: {data.get('total_youtube_videos', 0)}")
            print(f"   🟠 Reddit posts: {data.get('total_reddit_posts', 0)}")
            print(f"   💬 Total comments: {data.get('total_comments', 0)}")
            print(f"   🔄 Total replies: {data.get('total_replies', 0)}")
            print(f"   📈 Unique comments: {data.get('unique_comments', 0)}")
            print(f"   ✅ Successful queries: {data.get('successful_queries', 0)}")
            print(f"   ❌ Failed queries: {data.get('failed_queries', 0)}")
            print(f"   ⏱️ Latency: {data.get('latency_seconds', 0)}s")
            print(f"   🎯 Target achieved: {data.get('target_achieved', False)}")
            
            # Test if we got YouTube videos
            if data.get('total_youtube_videos', 0) > 0:
                print(f"\n🎉 YouTube videos successfully retrieved!")
            else:
                print(f"\n⚠️ No YouTube videos in results")
                
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 YouTube Scraper Improvement Test")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    success = test_improved_scraper()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
    else:
        print(f"\n❌ Test failed. Please check the server logs.")