#!/usr/bin/env python
"""
Test script to verify Cosmos DB integration for topics and channels
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.cosmos_service import cosmos_service
from src.services.news_service import news_service

def test_cosmos_topics():
    """Test fetching topics from Cosmos DB"""
    print("Testing Cosmos DB topics integration...")
    
    if not cosmos_service.is_available():
        print("❌ Cosmos DB is not available - check your configuration")
        return False
    
    try:
        topics = cosmos_service.get_available_topics()
        print(f"✅ Successfully fetched {len(topics)} topics from Cosmos DB")
        
        if topics:
            print("📋 Available topics:")
            for topic in topics[:5]:  # Show first 5 topics
                print(f"  - {topic.get('id')}: {topic.get('name')} (Active: {topic.get('isActive')})")
                
            if len(topics) > 5:
                print(f"  ... and {len(topics) - 5} more")
        else:
            print("⚠️  No topics found in Cosmos DB")
            
        return True
        
    except Exception as e:
        print(f"❌ Error fetching topics: {e}")
        return False

def test_cosmos_channels():
    """Test fetching channels from Cosmos DB"""
    print("\nTesting Cosmos DB channels integration...")
    
    if not cosmos_service.is_available():
        print("❌ Cosmos DB is not available - check your configuration")
        return False
    
    try:
        channels = cosmos_service.get_available_channels()
        print(f"✅ Successfully fetched {len(channels)} channels from Cosmos DB")
        
        if channels:
            print("📺 Available channels:")
            for channel in channels[:5]:  # Show first 5 channels
                print(f"  - {channel.get('name')} ({channel.get('domain')}) - {channel.get('category')}")
                
            if len(channels) > 5:
                print(f"  ... and {len(channels) - 5} more")
        else:
            print("⚠️  No channels found in Cosmos DB")
            
        return True
        
    except Exception as e:
        print(f"❌ Error fetching channels: {e}")
        return False

def test_news_service_integration():
    """Test news service integration with Cosmos DB"""
    print("\nTesting news service integration...")
    
    try:
        # Test getting sources through news service
        sources = news_service.get_available_sources()
        print(f"✅ Successfully fetched {len(sources)} sources through news service")
        
        if sources:
            print("🗞️  Available sources:")
            for source in sources[:5]:
                print(f"  - {source.get('name')} ({source.get('domain')})")
                
            if len(sources) > 5:
                print(f"  ... and {len(sources) - 5} more")
        
        # Test getting domains
        domains = news_service.get_brazilian_sources_domains()
        print(f"✅ Successfully fetched {len(domains)} domains for news API")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in news service integration: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Merculy Cosmos DB Integration\n")
    print("=" * 50)
    
    # Run tests
    topics_ok = test_cosmos_topics()
    channels_ok = test_cosmos_channels()
    news_service_ok = test_news_service_integration()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"  Topics from Cosmos DB: {'✅ PASS' if topics_ok else '❌ FAIL'}")
    print(f"  Channels from Cosmos DB: {'✅ PASS' if channels_ok else '❌ FAIL'}")
    print(f"  News Service Integration: {'✅ PASS' if news_service_ok else '❌ FAIL'}")
    
    if all([topics_ok, channels_ok, news_service_ok]):
        print("\n🎉 All tests passed! Cosmos DB integration is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check your Cosmos DB configuration and data.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
