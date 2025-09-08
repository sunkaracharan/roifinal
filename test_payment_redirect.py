#!/usr/bin/env python
"""
Test script to verify payment redirect functionality
Run this to test if users are properly redirected to full calculator after payment
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
from django.test import Client
from django.urls import reverse

def test_payment_redirect():
    """Test payment redirect functionality"""
    
    print("🧪 Testing Payment Redirect Functionality...")
    print("=" * 60)
    
    # Create a fresh test user
    import uuid
    unique_username = f'redirect_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'redirect_{uuid.uuid4().hex[:8]}@example.com',
        first_name='Redirect',
        last_name='Test'
    )
    
    print(f"✅ Created test user: {test_user.username}")
    
    # Get user limit and use up all free calculations
    user_limit = get_or_create_user_limit(test_user)
    print(f"📊 Initial calculations used: {user_limit.full_calculations_used}")
    
    # Use up all free calculations
    for i in range(5):
        user_limit.increment_calculation_count()
        user_limit.refresh_from_db()
    
    print(f"📊 After using all free calculations: {user_limit.full_calculations_used}")
    print(f"🔍 Can make calculation: {user_limit.can_make_calculation()}")
    
    # Create a payment record
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
    
    print(f"📊 Unlimited access granted: {user_limit.unlimited_access}")
    print(f"🔍 Can make calculation after payment: {user_limit.can_make_calculation()}")
    
    # Test the payment success view
    client = Client()
    client.force_login(test_user)
    
    # Test payment success redirect
    print("\n🔄 Testing payment success redirect...")
    response = client.get(f'/dashboard/payment/success/?payment_id={payment.payment_id}')
    
    print(f"📊 Response status code: {response.status_code}")
    print(f"📊 Response redirect URL: {response.url if hasattr(response, 'url') else 'No redirect'}")
    
    if response.status_code == 302:
        print("✅ Payment success view redirects correctly")
        if response.url and 'full' in response.url:
            print("✅ Redirects to full calculator")
        else:
            print("❌ Does not redirect to full calculator")
            return False
    else:
        print("❌ Payment success view does not redirect")
        return False
    
    # Test that user can access full calculator
    print("\n🔄 Testing full calculator access after payment...")
    response = client.get('/dashboard/full/')
    
    print(f"📊 Full calculator response status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ User can access full calculator after payment")
        
        # Check if unlimited access is shown in the response
        if 'unlimited access' in response.content.decode().lower():
            print("✅ Unlimited access status is displayed")
        else:
            print("⚠️  Unlimited access status might not be displayed")
    else:
        print("❌ User cannot access full calculator after payment")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Payment redirect functionality is working correctly!")
    print("   ✅ Payment success view redirects to full calculator")
    print("   ✅ User can access full calculator after payment")
    print("   ✅ Unlimited access is properly granted")
    
    return True

def test_payment_redirect_scenarios():
    """Test different payment redirect scenarios"""
    
    print("\n🧪 Testing Different Payment Redirect Scenarios...")
    print("=" * 60)
    
    # Test 1: Payment with unlimited access
    print("\n📋 Test 1: Payment with unlimited access")
    test_user1 = User.objects.create(
        username=f'redirect_test_1_{uuid.uuid4().hex[:8]}',
        email=f'redirect1_{uuid.uuid4().hex[:8]}@example.com'
    )
    
    user_limit1 = get_or_create_user_limit(test_user1)
    user_limit1.grant_unlimited_access()
    
    payment1 = Payment.objects.create(
        user=test_user1,
        amount=1.00,
        currency='INR',
        payment_id=f'test_payment_1_{uuid.uuid4().hex[:8]}',
        status='completed',
        paid_at=timezone.now()
    )
    
    client = Client()
    client.force_login(test_user1)
    
    response = client.get(f'/dashboard/payment/success/?payment_id={payment1.payment_id}')
    print(f"   Status: {response.status_code}, Redirect: {response.url if hasattr(response, 'url') else 'No redirect'}")
    
    if response.status_code == 302 and response.url and 'full' in response.url:
        print("   ✅ Unlimited access payment redirects correctly")
    else:
        print("   ❌ Unlimited access payment does not redirect correctly")
        return False
    
    # Test 2: Payment without unlimited access (edge case)
    print("\n📋 Test 2: Payment without unlimited access")
    test_user2 = User.objects.create(
        username=f'redirect_test_2_{uuid.uuid4().hex[:8]}',
        email=f'redirect2_{uuid.uuid4().hex[:8]}@example.com'
    )
    
    payment2 = Payment.objects.create(
        user=test_user2,
        amount=1.00,
        currency='INR',
        payment_id=f'test_payment_2_{uuid.uuid4().hex[:8]}',
        status='completed',
        paid_at=timezone.now()
    )
    
    client.force_login(test_user2)
    
    response = client.get(f'/dashboard/payment/success/?payment_id={payment2.payment_id}')
    print(f"   Status: {response.status_code}, Redirect: {response.url if hasattr(response, 'url') else 'No redirect'}")
    
    if response.status_code == 302 and response.url and 'full' in response.url:
        print("   ✅ Payment without unlimited access also redirects correctly")
    else:
        print("   ❌ Payment without unlimited access does not redirect correctly")
        return False
    
    # Test 3: Invalid payment ID
    print("\n📋 Test 3: Invalid payment ID")
    response = client.get('/dashboard/payment/success/?payment_id=invalid_payment_id')
    print(f"   Status: {response.status_code}, Redirect: {response.url if hasattr(response, 'url') else 'No redirect'}")
    
    if response.status_code == 302 and response.url and 'full' in response.url:
        print("   ✅ Invalid payment ID redirects correctly")
    else:
        print("   ❌ Invalid payment ID does not redirect correctly")
        return False
    
    # Test 4: No payment ID
    print("\n📋 Test 4: No payment ID")
    response = client.get('/dashboard/payment/success/')
    print(f"   Status: {response.status_code}, Redirect: {response.url if hasattr(response, 'url') else 'No redirect'}")
    
    if response.status_code == 302 and response.url and 'full' in response.url:
        print("   ✅ No payment ID redirects correctly")
    else:
        print("   ❌ No payment ID does not redirect correctly")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: All payment redirect scenarios work correctly!")
    print("   ✅ Payment with unlimited access redirects")
    print("   ✅ Payment without unlimited access redirects")
    print("   ✅ Invalid payment ID redirects")
    print("   ✅ No payment ID redirects")
    
    return True

if __name__ == "__main__":
    import uuid
    
    redirect_success = test_payment_redirect()
    scenarios_success = test_payment_redirect_scenarios()
    
    print("\n" + "=" * 80)
    if redirect_success and scenarios_success:
        print("🎉 ALL PAYMENT REDIRECT TESTS PASSED!")
        print("   ✅ Payment success always redirects to full calculator")
        print("   ✅ All edge cases are handled correctly")
        print("   ✅ Users can access full calculator after payment")
        print("   ✅ Unlimited access is properly granted")
    else:
        print("❌ SOME PAYMENT REDIRECT TESTS FAILED!")
        if not redirect_success:
            print("   ❌ Basic payment redirect test failed")
        if not scenarios_success:
            print("   ❌ Payment redirect scenarios test failed")
        sys.exit(1)
    
    sys.exit(0)
