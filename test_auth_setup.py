#!/usr/bin/env python3
"""
Quick test script to verify Supabase authentication setup.
Run this to check if your Supabase configuration is correct.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "omium-platform" / "api-gateway" / "auth-service"))

def test_supabase_config():
    """Test Supabase configuration."""
    print("🔍 Testing Supabase Configuration...\n")
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    print("📋 Environment Variables:")
    print(f"  SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    print(f"  SUPABASE_ANON_KEY: {'✅ Set' if supabase_anon_key else '❌ Missing'}")
    print(f"  SUPABASE_SERVICE_ROLE_KEY: {'✅ Set' if supabase_service_key else '❌ Missing'}")
    print()
    
    if not supabase_url or not supabase_anon_key:
        print("❌ Missing required Supabase environment variables!")
        print("   Please check your .env file in omium-platform/")
        return False
    
    # Try to import and initialize Supabase
    try:
        from supabase import create_client
        print("📦 Testing Supabase SDK Import...")
        client = create_client(supabase_url, supabase_anon_key)
        print("  ✅ Supabase client created successfully")
        print()
        
        # Test service initialization
        print("🔧 Testing Service Initialization...")
        from app.services.supabase_service import SupabaseService
        service = SupabaseService()
        
        if service.is_enabled():
            print("  ✅ Supabase service enabled")
        else:
            print("  ❌ Supabase service not enabled")
            return False
        
        print()
        print("✅ All Supabase configuration checks passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Supabase SDK: {e}")
        print("   Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Error testing Supabase: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints are accessible."""
    print("\n🌐 Testing API Endpoints...\n")
    
    import httpx
    
    api_base = os.getenv("VITE_API_BASE_URL", "https://omium.ai/api/v1")
    
    try:
        # Test config endpoint
        print(f"Testing: GET {api_base}/auth/supabase/config")
        response = httpx.get(f"{api_base}/auth/supabase/config", timeout=5.0)
        
        if response.status_code == 200:
            config = response.json()
            print(f"  ✅ Config endpoint working")
            print(f"     Supabase URL: {config.get('supabase_url', 'N/A')[:50]}...")
            print(f"     Has anon key: {'✅' if config.get('supabase_anon_key') else '❌'}")
        elif response.status_code == 503:
            print(f"  ⚠️  Config endpoint returned 503 (service not configured)")
            print(f"     This is OK if Supabase is not set up yet")
        else:
            print(f"  ❌ Config endpoint returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ⚠️  Could not test API endpoint: {e}")
        print(f"     This is OK if the service is not running")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Supabase Authentication Setup Test")
    print("=" * 60)
    print()
    
    # Load environment variables from .env file
    env_file = Path(__file__).parent / "omium-platform" / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"📄 Loaded environment from: {env_file}")
        print()
    
    # Run tests
    config_ok = test_supabase_config()
    api_ok = test_api_endpoints()
    
    print()
    print("=" * 60)
    if config_ok:
        print("✅ Configuration looks good!")
        print("   You can now test the authentication system.")
    else:
        print("❌ Configuration issues found.")
        print("   Please fix the issues above before testing.")
    print("=" * 60)

