#!/usr/bin/env python3
"""
JWT Authentication Testing Script for Merculy API
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_jwt_authentication():
    """Test the JWT authentication flow"""
    print("🧪 Testing JWT Authentication Flow")
    print("=" * 60)
    
    # Test user credentials
    test_user = {
        "email": "test@merculy.com",
        "password": "testpass123",
        "name": "Test User"
    }
    
    # 1. Test Registration
    print("\n1️⃣ Testing Registration...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            token = data.get('token')
            print(f"   ✅ Registration successful!")
            print(f"   Token received: {token[:50]}..." if token else "   ❌ No token received")
            return token
        elif response.status_code == 409:
            print(f"   ℹ️ User already exists, trying login...")
        else:
            print(f"   ❌ Registration failed: {response.json()}")
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
    
    # 2. Test Login
    print("\n2️⃣ Testing Login...")
    try:
        login_data = {"email": test_user["email"], "password": test_user["password"]}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"   ✅ Login successful!")
            print(f"   Token received: {token[:50]}..." if token else "   ❌ No token received")
            return token
        else:
            print(f"   ❌ Login failed: {response.json()}")
            return None
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return None

def test_protected_routes(token):
    """Test protected routes with JWT token"""
    print("\n3️⃣ Testing Protected Routes...")
    
    if not token:
        print("   ❌ No token available for testing")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test /api/auth/me
    print("\n   📋 Testing /api/auth/me...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"      Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"      ✅ User info retrieved: {data['user']['email']}")
        else:
            print(f"      ❌ Failed: {response.json()}")
    except Exception as e:
        print(f"      ❌ Error: {e}")
    
    # Test /api/topics
    print("\n   📰 Testing /api/topics...")
    try:
        response = requests.get(f"{BASE_URL}/api/topics")
        print(f"      Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"      ✅ Topics retrieved: {len(data.get('topics', []))} topics")
        else:
            print(f"      ❌ Failed: {response.json()}")
    except Exception as e:
        print(f"      ❌ Error: {e}")
    
    # Test /api/news/tecnologia
    print("\n   📡 Testing /api/news/tecnologia...")
    try:
        response = requests.get(f"{BASE_URL}/api/news/tecnologia?limit=5", headers=headers)
        print(f"      Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"      ✅ News retrieved: {data.get('count', 0)} articles")
        else:
            print(f"      ❌ Failed: {response.json()}")
    except Exception as e:
        print(f"      ❌ Error: {e}")

def test_without_token():
    """Test protected routes without token"""
    print("\n4️⃣ Testing Routes Without Token (Should Fail)...")
    
    # Test /api/auth/me without token
    print("\n   🚫 Testing /api/auth/me without token...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me")
        print(f"      Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"      ✅ Correctly rejected: {response.json().get('error', 'No error message')}")
        else:
            print(f"      ❌ Should have been rejected: {response.json()}")
    except Exception as e:
        print(f"      ❌ Error: {e}")
    
    # Test /api/news/tecnologia without token
    print("\n   🚫 Testing /api/news/tecnologia without token...")
    try:
        response = requests.get(f"{BASE_URL}/api/news/tecnologia")
        print(f"      Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"      ✅ Correctly rejected: {response.json().get('error', 'No error message')}")
        else:
            print(f"      ❌ Should have been rejected: {response.json()}")
    except Exception as e:
        print(f"      ❌ Error: {e}")

def test_debug_endpoints():
    """Test debug endpoints"""
    print("\n5️⃣ Testing Debug Endpoints...")
    
    # Test debug/jwt-info
    print("\n   🔍 Testing /debug/jwt-info...")
    try:
        response = requests.get(f"{BASE_URL}/debug/jwt-info")
        print(f"      Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"      ✅ Debug info retrieved")
            print(f"         JWT Secret Configured: {data.get('environment', {}).get('jwt_secret_configured')}")
            print(f"         JWT Expires In: {data.get('environment', {}).get('jwt_expires_in')}")
        else:
            print(f"      ❌ Failed: {response.json()}")
    except Exception as e:
        print(f"      ❌ Error: {e}")

if __name__ == "__main__":
    print("🔑 Merculy JWT Authentication Test Suite")
    print("Make sure your Flask app is running on http://localhost:5000")
    print()
    
    # Get token from login
    token = test_jwt_authentication()
    
    # Test protected routes
    test_protected_routes(token)
    
    # Test unauthorized access
    test_without_token()
    
    # Test debug endpoints
    test_debug_endpoints()
    
    print("\n" + "=" * 60)
    print("🎉 JWT Authentication Tests Complete!")
    print()
    print("📋 Expected Behavior:")
    print("   ✅ Login/Register should return JWT tokens")
    print("   ✅ Protected routes should work with valid tokens")
    print("   ✅ Protected routes should reject requests without tokens")
    print("   ✅ Debug endpoints should show JWT configuration")
    print()
    print("🚀 If all tests pass, your JWT authentication is working!")
    print("   Deploy to Azure and test with Authorization: Bearer <token> headers")
