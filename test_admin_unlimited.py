#!/usr/bin/env python
"""
Test script to verify admin users have unlimited calculations
Run this to test if admin users can make unlimited calculations
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roi_calculator.settings')
django.setup()

from django.contrib.auth.models import User
from calculator.models import UserCalculationLimit, ROIResult
from calculator.views import get_or_create_user_limit

def test_admin_unlimited():
    """Test if admin users have unlimited calculations"""
    
    print("🧪 Testing Admin Unlimited Calculations...")
    print("=" * 50)
    
    # Get or create an admin test user
    admin_user, created = User.objects.get_or_create(
        username='admin_test_user',
        defaults={
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        print(f"✅ Created admin test user: {admin_user.username}")
    else:
        # Ensure user is admin
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        print(f"✅ Using existing admin test user: {admin_user.username}")
    
    # Get user limit
    user_limit = get_or_create_user_limit(admin_user)
    print(f"📊 Admin calculations used: {user_limit.full_calculations_used}")
    print(f"📊 Admin remaining calculations: {user_limit.get_remaining_free_calculations()}")
    print(f"🔍 Admin can make calculation: {user_limit.can_make_calculation()}")
    
    # Test that admin has unlimited calculations
    if user_limit.get_remaining_free_calculations() == float('inf'):
        print("✅ Admin has unlimited calculations (infinity)")
    else:
        print("❌ Admin should have unlimited calculations")
        return False
    
    if user_limit.can_make_calculation():
        print("✅ Admin can make calculations")
    else:
        print("❌ Admin should be able to make calculations")
        return False
    
    # Test incrementing calculation count for admin (should not increment)
    print("\n🔄 Testing calculation count increment for admin...")
    
    initial_used = user_limit.full_calculations_used
    print(f"Before increment: Used={initial_used}")
    
    # Increment count (should not change for admin)
    user_limit.increment_calculation_count()
    user_limit.refresh_from_db()
    
    final_used = user_limit.full_calculations_used
    print(f"After increment: Used={final_used}")
    
    if final_used == initial_used:
        print("✅ Admin calculation count did not increment (correct behavior)")
    else:
        print("❌ Admin calculation count should not increment")
        return False
    
    # Test multiple increments
    print("\n🔄 Testing multiple increments for admin...")
    
    for i in range(5):
        user_limit.increment_calculation_count()
        user_limit.refresh_from_db()
        print(f"Increment {i+1}: Used={user_limit.full_calculations_used}")
    
    if user_limit.full_calculations_used == initial_used:
        print("✅ Admin calculation count remained unchanged after multiple increments")
    else:
        print("❌ Admin calculation count should remain unchanged")
        return False
    
    # Test that admin can still make calculations
    if user_limit.can_make_calculation():
        print("✅ Admin can still make calculations after increments")
    else:
        print("❌ Admin should still be able to make calculations")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 SUCCESS: Admin unlimited calculations are working correctly!")
    print("   Admin users have unlimited calculations and count doesn't increment.")
    
    return True

def test_regular_user_limits():
    """Test that regular users still have limits"""
    
    print("\n🧪 Testing Regular User Limits...")
    print("=" * 50)
    
    # Get or create a regular test user
    regular_user, created = User.objects.get_or_create(
        username='regular_test_user',
        defaults={
            'email': 'regular@example.com',
            'is_staff': False,
            'is_superuser': False
        }
    )
    
    if created:
        print(f"✅ Created regular test user: {regular_user.username}")
    else:
        # Ensure user is not admin
        regular_user.is_staff = False
        regular_user.is_superuser = False
        regular_user.save()
        print(f"✅ Using existing regular test user: {regular_user.username}")
    
    # Get user limit
    user_limit = get_or_create_user_limit(regular_user)
    print(f"📊 Regular user calculations used: {user_limit.full_calculations_used}")
    print(f"📊 Regular user remaining calculations: {user_limit.get_remaining_free_calculations()}")
    print(f"🔍 Regular user can make calculation: {user_limit.can_make_calculation()}")
    
    # Test that regular user has limited calculations
    if user_limit.get_remaining_free_calculations() == 5:
        print("✅ Regular user has 5 free calculations")
    else:
        print("❌ Regular user should have 5 free calculations")
        return False
    
    if user_limit.can_make_calculation():
        print("✅ Regular user can make calculations")
    else:
        print("❌ Regular user should be able to make calculations")
        return False
    
    # Test incrementing calculation count for regular user (should increment)
    print("\n🔄 Testing calculation count increment for regular user...")
    
    initial_used = user_limit.full_calculations_used
    print(f"Before increment: Used={initial_used}")
    
    # Increment count (should change for regular user)
    user_limit.increment_calculation_count()
    user_limit.refresh_from_db()
    
    final_used = user_limit.full_calculations_used
    print(f"After increment: Used={final_used}")
    
    if final_used == initial_used + 1:
        print("✅ Regular user calculation count incremented correctly")
    else:
        print("❌ Regular user calculation count should increment")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 SUCCESS: Regular user limits are working correctly!")
    print("   Regular users have 5 free calculations and count increments properly.")
    
    return True

if __name__ == "__main__":
    admin_success = test_admin_unlimited()
    regular_success = test_regular_user_limits()
    
    print("\n" + "=" * 60)
    if admin_success and regular_success:
        print("🎉 ALL TESTS PASSED!")
        print("   ✅ Admin users have unlimited calculations")
        print("   ✅ Regular users have 5 free calculations")
        print("   ✅ Calculation counts work correctly for both user types")
    else:
        print("❌ SOME TESTS FAILED!")
        if not admin_success:
            print("   ❌ Admin unlimited calculations test failed")
        if not regular_success:
            print("   ❌ Regular user limits test failed")
        sys.exit(1)
    
    sys.exit(0)
