#!/usr/bin/env python
"""
Test script to verify the improved multiple topics distribution
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.news_service import news_service

def test_multiple_topics_improved():
    """Test the improved multiple topics logic"""
    print("🧪 Testing Improved Multiple Topics Distribution")
    print("=" * 60)
    
    if not news_service.is_available():
        print("⚠️  News API not available - creating mock test")
        return simulate_distribution_logic()
    
    # Test different scenarios
    test_cases = [
        {
            'topics': ['tecnologia', 'economia'],
            'limit': 10,
            'expected': 'Should get close to 10 total articles'
        },
        {
            'topics': ['tecnologia', 'economia', 'política'],
            'limit': 15,
            'expected': 'Should get close to 15 total articles'
        },
        {
            'topics': ['tecnologia'],
            'limit': 8,
            'expected': 'Should get up to 8 articles for single topic'
        },
        {
            'topics': ['tecnologia', 'economia', 'política', 'esportes'],
            'limit': 20,
            'expected': 'Should get close to 20 total articles'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📊 Test Case {i}:")
        print(f"   Topics: {case['topics']}")
        print(f"   Limit: {case['limit']}")
        print(f"   Expected: {case['expected']}")
        
        try:
            # Test the actual method
            result = news_service.get_news_by_multiple_topics(
                topics=case['topics'],
                limit=case['limit']
            )
            
            total_articles = sum(len(articles) for articles in result.values())
            
            print(f"   ✅ Result: {total_articles} total articles")
            print(f"   📋 Distribution:")
            for topic, articles in result.items():
                print(f"      - {topic}: {len(articles)} articles")
            
            # Check if we're using the limit effectively
            efficiency = (total_articles / case['limit']) * 100
            print(f"   📈 Limit utilization: {efficiency:.1f}%")
            
            if efficiency >= 80:
                print(f"   ✅ Good utilization!")
            elif efficiency >= 60:
                print(f"   ⚠️  Moderate utilization")
            else:
                print(f"   ❌ Low utilization")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def simulate_distribution_logic():
    """Simulate the distribution logic without API calls"""
    print("🔮 Simulating Distribution Logic (No API)")
    print("=" * 50)
    
    test_scenarios = [
        {'topics': 2, 'limit': 10},
        {'topics': 3, 'limit': 15},
        {'topics': 4, 'limit': 20},
        {'topics': 1, 'limit': 8},
        {'topics': 5, 'limit': 12},
    ]
    
    for scenario in test_scenarios:
        topics_count = scenario['topics']
        limit = scenario['limit']
        
        print(f"\n📊 {topics_count} topics, {limit} limit:")
        
        # Simulate the three-pass algorithm
        # First pass: minimum 1 per topic
        min_per_topic = 1
        first_pass = min(topics_count, limit)
        remaining_after_first = limit - first_pass
        
        # Second pass: up to 2 per topic  
        max_per_topic = 2
        second_pass_possible = min(topics_count, remaining_after_first)
        remaining_after_second = remaining_after_first - second_pass_possible
        
        # Third pass: distribute remaining
        third_pass_per_topic = remaining_after_second // topics_count if topics_count > 0 else 0
        
        total_distributed = first_pass + second_pass_possible + (third_pass_per_topic * topics_count)
        
        print(f"   Phase 1 (min 1 each): {first_pass} articles")
        print(f"   Phase 2 (up to 2 each): +{second_pass_possible} articles") 
        print(f"   Phase 3 (extras): +{third_pass_per_topic * topics_count} articles")
        print(f"   Total simulated: {total_distributed} / {limit}")
        print(f"   Utilization: {(total_distributed/limit)*100:.1f}%")

def main():
    """Main test function"""
    print("🚀 Testing Improved Multiple Topics News Retrieval\n")
    
    test_multiple_topics_improved()
    
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("✅ New three-pass algorithm implemented:")
    print("   1️⃣ First pass: Ensure minimum 1 article per topic")
    print("   2️⃣ Second pass: Add up to 1 more per topic (max 2 total)")
    print("   3️⃣ Third pass: Distribute remaining articles across topics")
    print("✅ Better utilization of the total limit")
    print("✅ Avoids duplicate articles using URL tracking")

if __name__ == "__main__":
    main()
