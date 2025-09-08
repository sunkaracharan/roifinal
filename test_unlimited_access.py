#!/usr/bin/env python
"""
Test script to verify unlimited access functionality
Run this to test if users get unlimited access after payment
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
from calculator.models import UserCalculationLimit, Payment
from calculator.views import get_or_create_user_limit
from django.utils import timezone

def test_unlimited_access():
    """Test unlimited access functionality"""
    
    print("🧪 Testing Unlimited Access Functionality...")
    print("=" * 60)
    
    # Create a fresh test user with unique username
    import uuid
    unique_username = f'unlimited_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'unlimited_{uuid.uuid4().hex[:8]}@example.com',
        first_name='Unlimited',
        last_name='Test'
    )
    
    print(f"✅ Created fresh test user: {test_user.username}")
    
    # Get user limit
    user_limit = get_or_create_user_limit(test_user)
    print(f"📊 Initial calculations used: {user_limit.full_calculations_used}")
    print(f"📊 Initial unlimited access: {user_limit.unlimited_access}")
    print(f"📊 Initial remaining calculations: {user_limit.get_remaining_free_calculations()}")
    print(f"🔍 Initial can make calculation: {user_limit.can_make_calculation()}")
    
    # Test that user starts with limited access
    if not user_limit.unlimited_access:
        print("✅ User starts with limited access (correct)")
    else:
        print("❌ User should start with limited access")
        return False
    
    if user_limit.get_remaining_free_calculations() == 5:
        print("✅ User starts with 5 free calculations")
    else:
        print("❌ User should start with 5 free calculations")
        return False
    
    # Simulate using up all free calculations
    print("\n🔄 Simulating usage of all free calculations...")
    for i in range(5):
        user_limit.increment_calculation_count()
        user_limit.refresh_from_db()
        print(f"Calculation {i+1}: Used={user_limit.full_calculations_used}, Remaining={user_limit.get_remaining_free_calculations()}")
    
    # Test that user can no longer make calculations
    if not user_limit.can_make_calculation():
        print("✅ User cannot make calculations after using all free ones")
    else:
        print("❌ User should not be able to make calculations")
        return False
    
    if user_limit.get_remaining_free_calculations() == 0:
        print("✅ User has 0 remaining calculations")
    else:
        print("❌ User should have 0 remaining calculations")
        return False
    
    # Simulate payment and grant unlimited access
    print("\n💳 Simulating payment and granting unlimited access...")
    
    # Create a payment record with unique ID
    import uuid
    unique_payment_id = f'test_payment_{uuid.uuid4().hex[:8]}'
    payment = Payment.objects.create(
        user=test_user,
        amount=1.00,
        currency='INR',
        payment_id=unique_payment_id,
        status='completed',
        razorpay_payment_id=f'test_razorpay_{uuid.uuid4().hex[:8]}',
        razorpay_signature=f'test_signature_{uuid.uuid4().hex[:8]}',
        paid_at=timezone.now()
    )
    print(f"✅ Created payment record: {payment.payment_id}")
    
    # Grant unlimited access
    user_limit.grant_unlimited_access()
    user_limit.refresh_from_db()
    
    print(f"📊 After payment - unlimited access: {user_limit.unlimited_access}")
    print(f"📊 After payment - purchased at: {user_limit.unlimited_access_purchased_at}")
    print(f"📊 After payment - remaining calculations: {user_limit.get_remaining_free_calculations()}")
    print(f"🔍 After payment - can make calculation: {user_limit.can_make_calculation()}")
    
    # Test that user now has unlimited access
    if user_limit.unlimited_access:
        print("✅ User now has unlimited access")
    else:
        print("❌ User should have unlimited access after payment")
        return False
    
    if user_limit.get_remaining_free_calculations() == float('inf'):
        print("✅ User has unlimited remaining calculations")
    else:
        print("❌ User should have unlimited remaining calculations")
        return False
    
    if user_limit.can_make_calculation():
        print("✅ User can now make unlimited calculations")
    else:
        print("❌ User should be able to make unlimited calculations")
        return False
    
    # Test that calculation count doesn't increment for unlimited access users
    print("\n🔄 Testing calculation count increment for unlimited access user...")
    
    initial_used = user_limit.full_calculations_used
    print(f"Before increment: Used={initial_used}")
    
    # Try to increment count (should not change for unlimited access users)
    user_limit.increment_calculation_count()
    user_limit.refresh_from_db()
    
    final_used = user_limit.full_calculations_used
    print(f"After increment: Used={final_used}")
    
    if final_used == initial_used:
        print("✅ Calculation count did not increment for unlimited access user (correct behavior)")
    else:
        print("❌ Calculation count should not increment for unlimited access users")
        return False
    
    # Test multiple increments
    print("\n🔄 Testing multiple increments for unlimited access user...")
    
    for i in range(5):
        user_limit.increment_calculation_count()
        user_limit.refresh_from_db()
        print(f"Increment {i+1}: Used={user_limit.full_calculations_used}")
    
    if user_limit.full_calculations_used == initial_used:
        print("✅ Calculation count remained unchanged after multiple increments")
    else:
        print("❌ Calculation count should remain unchanged")
        return False
    
    # Test that user can still make calculations
    if user_limit.can_make_calculation():
        print("✅ User can still make calculations after increments")
    else:
        print("❌ User should still be able to make calculations")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Unlimited access functionality is working correctly!")
    print("   ✅ Users start with 5 free calculations")
    print("   ✅ Users cannot make calculations after using all free ones")
    print("   ✅ Payment grants unlimited access")
    print("   ✅ Unlimited access users have infinite calculations")
    print("   ✅ Calculation count doesn't increment for unlimited access users")
    print("   ✅ Unlimited access users can always make calculations")
    
    return True

def test_admin_vs_unlimited_access():
    """Test that admin users and unlimited access users both have unlimited calculations"""
    
    print("\n🧪 Testing Admin vs Unlimited Access...")
    print("=" * 60)
    
    # Test admin user
    admin_user, created = User.objects.get_or_create(
        username='admin_unlimited_test',
        defaults={
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    admin_limit = get_or_create_user_limit(admin_user)
    print(f"📊 Admin - unlimited access: {admin_limit.unlimited_access}")
    print(f"📊 Admin - remaining calculations: {admin_limit.get_remaining_free_calculations()}")
    print(f"🔍 Admin - can make calculation: {admin_limit.can_make_calculation()}")
    
    # Test unlimited access user
    unlimited_user, created = User.objects.get_or_create(
        username='unlimited_access_test',
        defaults={
            'email': 'unlimited@example.com'
        }
    )
    
    unlimited_limit = get_or_create_user_limit(unlimited_user)
    unlimited_limit.grant_unlimited_access()
    
    print(f"📊 Unlimited Access User - unlimited access: {unlimited_limit.unlimited_access}")
    print(f"📊 Unlimited Access User - remaining calculations: {unlimited_limit.get_remaining_free_calculations()}")
    print(f"🔍 Unlimited Access User - can make calculation: {unlimited_limit.can_make_calculation()}")
    
    # Both should have unlimited access
    if (admin_limit.get_remaining_free_calculations() == float('inf') and 
        unlimited_limit.get_remaining_free_calculations() == float('inf')):
        print("✅ Both admin and unlimited access users have unlimited calculations")
    else:
        print("❌ Both admin and unlimited access users should have unlimited calculations")
        return False
    
    if admin_limit.can_make_calculation() and unlimited_limit.can_make_calculation():
        print("✅ Both admin and unlimited access users can make calculations")
    else:
        print("❌ Both admin and unlimited access users should be able to make calculations")
        return False
    
    print("🎉 SUCCESS: Admin and unlimited access users both have unlimited calculations!")
    
    return True

if __name__ == "__main__":
    unlimited_success = test_unlimited_access()
    admin_success = test_admin_vs_unlimited_access()
    
    print("\n" + "=" * 80)
    if unlimited_success and admin_success:
        print("🎉 ALL TESTS PASSED!")
        print("   ✅ Unlimited access functionality works correctly")
        print("   ✅ Payment grants unlimited access")
        print("   ✅ Unlimited access users have infinite calculations")
        print("   ✅ Admin users still have unlimited access")
        print("   ✅ Calculation counts work correctly for all user types")
    else:
        print("❌ SOME TESTS FAILED!")
        if not unlimited_success:
            print("   ❌ Unlimited access test failed")
        if not admin_success:
            print("   ❌ Admin vs unlimited access test failed")
        sys.exit(1)
    
    sys.exit(0)
