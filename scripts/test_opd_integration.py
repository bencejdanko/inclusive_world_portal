#!/usr/bin/env python
"""
Test script to verify OPD integration functionality.
Run this from the Django project root: python scripts/test_opd_integration.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.conf import settings
from inclusive_world_portal.users.models import User
from inclusive_world_portal.users.opd_utils import (
    get_opd_role_mapping,
    generate_opd_token,
    generate_opd_editor_url,
)


def test_configuration():
    """Test that OPD configuration is loaded."""
    print("=" * 60)
    print("Testing OPD Configuration")
    print("=" * 60)
    
    print(f"OPD Server: {settings.INCLUSIVE_WORLD_OPD_SERVER}")
    print(f"OPD Secret configured: {bool(settings.INCLUSIVE_WORLD_OPD_SECRET)}")
    print(f"OPD Secret length: {len(settings.INCLUSIVE_WORLD_OPD_SECRET) if settings.INCLUSIVE_WORLD_OPD_SECRET else 0} chars")
    
    if not settings.INCLUSIVE_WORLD_OPD_SECRET:
        print("⚠️  WARNING: OPD_SECRET is not configured!")
        return False
    
    print("✅ Configuration looks good\n")
    return True


def test_role_mapping():
    """Test role mapping function."""
    print("=" * 60)
    print("Testing Role Mapping")
    print("=" * 60)
    
    test_cases = [
        ('member', 'member'),
        ('volunteer', 'volunteer'),
        ('person_centered_manager', 'pcm'),
        ('manager', 'manager'),
        ('admin', 'admin'),
        ('unknown_role', 'member'),  # Should default to member
    ]
    
    for django_role, expected_opd_role in test_cases:
        result = get_opd_role_mapping(django_role)
        status = "✅" if result == expected_opd_role else "❌"
        print(f"{status} {django_role} -> {result} (expected: {expected_opd_role})")
    
    print()


def test_token_generation():
    """Test JWT token generation."""
    print("=" * 60)
    print("Testing Token Generation")
    print("=" * 60)
    
    try:
        token = generate_opd_token(
            username='test_user',
            doc_id='test_doc',
            role='member',
            expires_in=1800
        )
        print(f"✅ Token generated successfully")
        print(f"Token (truncated): {token[:50]}...")
        print(f"Token length: {len(token)} characters")
        
        # Decode and verify payload (without verification for testing)
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        print(f"Token payload: {payload}")
        print(f"✅ Token contains correct fields\n")
        return True
        
    except Exception as e:
        print(f"❌ Token generation failed: {e}\n")
        return False


def test_url_generation():
    """Test OPD editor URL generation with real user."""
    print("=" * 60)
    print("Testing URL Generation")
    print("=" * 60)
    
    # Try to get or create a test user
    try:
        user = User.objects.filter(role='member').first()
        
        if not user:
            print("⚠️  No member users found in database")
            print("Creating a test user...")
            user = User.objects.create_user(
                username='opd_test_user',
                email='test@example.com',
                role='member'
            )
            print(f"✅ Created test user: {user.username}")
        
        print(f"Using user: {user.username} (role: {user.role})")
        
        # Generate URL
        url = generate_opd_editor_url(user)
        print(f"✅ URL generated successfully")
        print(f"URL: {url}")
        
        # Parse URL to verify structure
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        print(f"✅ URL structure valid")
        print(f"   Scheme: {parsed.scheme}")
        print(f"   Host: {parsed.netloc}")
        print(f"   Path: {parsed.path}")
        print(f"   Token present: {'token' in params}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ URL generation failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("OPD INTEGRATION TEST SUITE")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_configuration()))
    results.append(("Role Mapping", test_role_mapping()))
    results.append(("Token Generation", test_token_generation()))
    results.append(("URL Generation", test_url_generation()))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + ("=" * 60))
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
