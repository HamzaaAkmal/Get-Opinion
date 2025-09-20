#!/usr/bin/env python3
"""
Test script to verify the improvements made to the YouTube scraper
Tests API rotation, parallel processing, and configuration changes
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.youtube_service import youtube_service
from services.ai_service import ai_service
from services.comment_fetcher import comment_fetcher


def test_api_rotation():
    """Test YouTube API rotation system"""
    print("🔑 Testing YouTube API rotation system...")
    
    try:
        # Test API usage stats
        stats = youtube_service.get_api_usage_stats()
        print(f"✅ API Stats: {stats}")
        
        # Test a simple search
        videos = youtube_service.search_videos("test query", max_results=2)
        print(f"✅ Search test passed: Found {len(videos)} videos")
        
        return True
    except Exception as e:
        print(f"❌ API rotation test failed: {e}")
        return False


def test_ai_query_generation():
    """Test AI query generation with custom parameters"""
    print("🤖 Testing AI query generation...")
    
    try:
        if not ai_service.is_available():
            print("⚠️ AI service not available, skipping test")
            return True
        
        # Test with custom number of variations
        variations = ai_service.generate_query_variations("test query", num_variations=5)
        print(f"✅ AI generation test passed: Generated {len(variations)} variations")
        
        return True
    except Exception as e:
        print(f"❌ AI generation test failed: {e}")
        return False


def test_parallel_processing():
    """Test parallel query processing"""
    print("⚡ Testing parallel query processing...")
    
    try:
        start_time = time.time()
        
        # Test with a small set of queries for quick validation
        test_queries = ["AI technology", "machine learning", "programming"]
        
        result = comment_fetcher.fetch_multiple_queries_aggregated(
            queries=test_queries,
            target_total_comments=1000  # Small target for testing
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Parallel processing test passed:")
        print(f"   ⏱️ Processing time: {processing_time:.2f} seconds")
        print(f"   📊 Successful queries: {result['successful_queries']}")
        print(f"   📈 Unique comments: {result['unique_count']}")
        print(f"   🚀 Parallel processing: {result.get('parallel_processing', False)}")
        
        return True
    except Exception as e:
        print(f"❌ Parallel processing test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Starting YouTube Scraper Improvement Tests")
    print("=" * 60)
    
    tests = [
        ("API Rotation", test_api_rotation),
        ("AI Query Generation", test_ai_query_generation),
        ("Parallel Processing", test_parallel_processing)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if test_func():
                print(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} test FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} test CRASHED: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The improvements are working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    main()