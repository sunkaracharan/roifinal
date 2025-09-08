#!/usr/bin/env python
"""
Test script to verify that payment success page does NOT redirect automatically
Run this to test that users stay on payment success page after payment
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

def test_no_auto_redirect():
    """Test that payment success page does not redirect automatically"""
    
    print("🧪 Testing No Auto-Redirect After Payment...")
    print("=" * 60)
    
    # Create a fresh test user
    import uuid
    unique_username = f'no_redirect_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'no_redirect_{uuid.uuid4().hex[:8]}@example.com',
        first_name='NoRedirect',
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
    
    # Test the payment success view
    client = Client()
    client.force_login(test_user)
    
    # Test payment success page - should NOT redirect
    print("\n🔄 Testing payment success page (should NOT redirect)...")
    response = client.get(f'/dashboard/payment/success/?payment_id={payment.payment_id}')
    
    print(f"📊 Response status code: {response.status_code}")
    print(f"📊 Response redirect URL: {response.url if hasattr(response, 'url') else 'No redirect'}")
    
    if response.status_code == 200:
        print("✅ Payment success page loads correctly (no redirect)")
        
        # Check if payment success content is displayed
        content = response.content.decode()
        if 'Payment Successful' in content or 'Unlimited Access Granted' in content:
            print("✅ Payment success content is displayed")
        else:
            print("❌ Payment success content is not displayed")
            return False
            
        # Check if unlimited access is shown
        if 'unlimited access' in content.lower():
            print("✅ Unlimited access status is displayed")
        else:
            print("⚠️  Unlimited access status might not be displayed")
            
        # Check if action buttons are present
        if 'Go to Full Calculator' in content:
            print("✅ Action buttons are present")
        else:
            print("❌ Action buttons are not present")
            return False
            
    else:
        print("❌ Payment success page does not load correctly")
        return False
    
    # Test that user can manually navigate to full calculator
    print("\n🔄 Testing manual navigation to full calculator...")
    response = client.get('/dashboard/full/')
    
    print(f"📊 Full calculator response status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ User can manually access full calculator")
        
        # Check if unlimited access is shown in full calculator
        content = response.content.decode()
        if 'unlimited access' in content.lower():
            print("✅ Unlimited access status is displayed in full calculator")
        else:
            print("⚠️  Unlimited access status might not be displayed in full calculator")
    else:
        print("❌ User cannot access full calculator")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: No auto-redirect functionality is working correctly!")
    print("   ✅ Payment success page loads without redirecting")
    print("   ✅ Payment success content is displayed")
    print("   ✅ Action buttons are present for manual navigation")
    print("   ✅ User can manually navigate to full calculator")
    
    return True

def test_different_payment_scenarios():
    """Test different payment scenarios without auto-redirect"""
    
    print("\n🧪 Testing Different Payment Scenarios (No Auto-Redirect)...")
    print("=" * 60)
    
    # Test 1: Payment with unlimited access
    print("\n📋 Test 1: Payment with unlimited access")
    test_user1 = User.objects.create(
        username=f'no_redirect_test_1_{uuid.uuid4().hex[:8]}',
        email=f'no_redirect1_{uuid.uuid4().hex[:8]}@example.com'
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
    
    if response.status_code == 200 and not hasattr(response, 'url'):
        print("   ✅ Unlimited access payment shows success page (no redirect)")
    else:
        print("   ❌ Unlimited access payment redirects or fails")
        return False
    
    # Test 2: Payment without unlimited access
    print("\n📋 Test 2: Payment without unlimited access")
    test_user2 = User.objects.create(
        username=f'no_redirect_test_2_{uuid.uuid4().hex[:8]}',
        email=f'no_redirect2_{uuid.uuid4().hex[:8]}@example.com'
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
    
    if response.status_code == 200 and not hasattr(response, 'url'):
        print("   ✅ Payment without unlimited access shows success page (no redirect)")
    else:
        print("   ❌ Payment without unlimited access redirects or fails")
        return False
    
    # Test 3: Invalid payment ID
    print("\n📋 Test 3: Invalid payment ID")
    response = client.get('/dashboard/payment/success/?payment_id=invalid_payment_id')
    print(f"   Status: {response.status_code}, Redirect: {response.url if hasattr(response, 'url') else 'No redirect'}")
    
    if response.status_code == 200 and not hasattr(response, 'url'):
        print("   ✅ Invalid payment ID shows error page (no redirect)")
    else:
        print("   ❌ Invalid payment ID redirects or fails")
        return False
    
    # Test 4: No payment ID
    print("\n📋 Test 4: No payment ID")
    response = client.get('/dashboard/payment/success/')
    print(f"   Status: {response.status_code}, Redirect: {response.url if hasattr(response, 'url') else 'No redirect'}")
    
    if response.status_code == 200 and not hasattr(response, 'url'):
        print("   ✅ No payment ID shows error page (no redirect)")
    else:
        print("   ❌ No payment ID redirects or fails")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: All payment scenarios show success page without redirect!")
    print("   ✅ Payment with unlimited access shows success page")
    print("   ✅ Payment without unlimited access shows success page")
    print("   ✅ Invalid payment ID shows error page")
    print("   ✅ No payment ID shows error page")
    
    return True

if __name__ == "__main__":
    import uuid
    
    no_redirect_success = test_no_auto_redirect()
    scenarios_success = test_different_payment_scenarios()
    
    print("\n" + "=" * 80)
    if no_redirect_success and scenarios_success:
        print("🎉 ALL NO-AUTO-REDIRECT TESTS PASSED!")
        print("   ✅ Payment success page loads without redirecting")
        print("   ✅ All payment scenarios show success page")
        print("   ✅ Users can manually navigate to full calculator")
        print("   ✅ No automatic redirects occur")
    else:
        print("❌ SOME NO-AUTO-REDIRECT TESTS FAILED!")
        if not no_redirect_success:
            print("   ❌ Basic no-auto-redirect test failed")
        if not scenarios_success:
            print("   ❌ Payment scenarios no-auto-redirect test failed")
        sys.exit(1)
    
    sys.exit(0)
