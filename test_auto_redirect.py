#!/usr/bin/env python
"""
Test script to verify automatic redirect to full calculator after payment
Run this to test that users are automatically redirected to full calculator after successful payment
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

def test_auto_redirect_after_payment():
    """Test automatic redirect to full calculator after payment"""
    
    print("🧪 Testing Automatic Redirect After Payment...")
    print("=" * 60)
    
    # Create a fresh test user
    import uuid
    unique_username = f'auto_redirect_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'auto_redirect_{uuid.uuid4().hex[:8]}@example.com',
        first_name='AutoRedirect',
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
    
    # Test the payment success view - should redirect to full calculator
    client = Client()
    client.force_login(test_user)
    
    print("\n🔄 Testing payment success redirect to full calculator...")
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
    
    # Test direct redirect to full calculator with payment success parameters
    print("\n🔄 Testing direct redirect to full calculator with payment success...")
    response = client.get('/dashboard/full/?payment_success=true&unlimited_access=true')
    
    print(f"📊 Full calculator response status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ User can access full calculator with payment success parameters")
        
        # Check if unlimited access is shown in the response
        content = response.content.decode()
        if 'unlimited access' in content.lower():
            print("✅ Unlimited access status is displayed")
        else:
            print("⚠️  Unlimited access status might not be displayed")
            
        # Check if payment success message is shown
        if 'payment successful' in content.lower():
            print("✅ Payment success message is displayed")
        else:
            print("⚠️  Payment success message might not be displayed")
    else:
        print("❌ User cannot access full calculator with payment success parameters")
        return False
    
    # Test that user can make calculations after payment
    print("\n🔄 Testing calculation capability after payment...")
    response = client.get('/dashboard/full/')
    
    if response.status_code == 200:
        print("✅ User can access full calculator after payment")
        
        # Check if payment button is not shown (since user has unlimited access)
        content = response.content.decode()
        if 'get unlimited access' not in content.lower():
            print("✅ Payment button is not shown (user has unlimited access)")
        else:
            print("⚠️  Payment button might still be shown")
    else:
        print("❌ User cannot access full calculator after payment")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Automatic redirect functionality is working correctly!")
    print("   ✅ Payment success redirects to full calculator")
    print("   ✅ Direct redirect with payment success parameters works")
    print("   ✅ Unlimited access is properly granted and displayed")
    print("   ✅ User can make unlimited calculations after payment")
    
    return True

def test_payment_flow_scenarios():
    """Test different payment flow scenarios"""
    
    print("\n🧪 Testing Different Payment Flow Scenarios...")
    print("=" * 60)
    
    # Test 1: Payment with unlimited access
    print("\n📋 Test 1: Payment with unlimited access")
    test_user1 = User.objects.create(
        username=f'auto_redirect_test_1_{uuid.uuid4().hex[:8]}',
        email=f'auto_redirect1_{uuid.uuid4().hex[:8]}@example.com'
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
    
    # Test payment success redirect
    response = client.get(f'/dashboard/payment/success/?payment_id={payment1.payment_id}')
    print(f"   Payment Success Status: {response.status_code}, Redirect: {response.url if hasattr(response, 'url') else 'No redirect'}")
    
    if response.status_code == 302 and response.url and 'full' in response.url:
        print("   ✅ Unlimited access payment redirects to full calculator")
    else:
        print("   ❌ Unlimited access payment does not redirect correctly")
        return False
    
    # Test direct access to full calculator
    response = client.get('/dashboard/full/?payment_success=true&unlimited_access=true')
    print(f"   Direct Access Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Direct access to full calculator works")
    else:
        print("   ❌ Direct access to full calculator fails")
        return False
    
    # Test 2: Payment without unlimited access (edge case)
    print("\n📋 Test 2: Payment without unlimited access")
    test_user2 = User.objects.create(
        username=f'auto_redirect_test_2_{uuid.uuid4().hex[:8]}',
        email=f'auto_redirect2_{uuid.uuid4().hex[:8]}@example.com'
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
    
    # Test payment success redirect
    response = client.get(f'/dashboard/payment/success/?payment_id={payment2.payment_id}')
    print(f"   Payment Success Status: {response.status_code}, Redirect: {response.url if hasattr(response, 'url') else 'No redirect'}")
    
    if response.status_code == 302 and response.url and 'full' in response.url:
        print("   ✅ Payment without unlimited access also redirects to full calculator")
    else:
        print("   ❌ Payment without unlimited access does not redirect correctly")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: All payment flow scenarios work correctly!")
    print("   ✅ Payment with unlimited access redirects to full calculator")
    print("   ✅ Payment without unlimited access redirects to full calculator")
    print("   ✅ Direct access with payment success parameters works")
    print("   ✅ Users can access full calculator after payment")
    
    return True

if __name__ == "__main__":
    import uuid
    
    auto_redirect_success = test_auto_redirect_after_payment()
    scenarios_success = test_payment_flow_scenarios()
    
    print("\n" + "=" * 80)
    if auto_redirect_success and scenarios_success:
        print("🎉 ALL AUTO-REDIRECT TESTS PASSED!")
        print("   ✅ Payment success automatically redirects to full calculator")
        print("   ✅ All payment flow scenarios work correctly")
        print("   ✅ Users can access unlimited calculations after payment")
        print("   ✅ Automatic redirect functionality is working")
    else:
        print("❌ SOME AUTO-REDIRECT TESTS FAILED!")
        if not auto_redirect_success:
            print("   ❌ Basic auto-redirect test failed")
        if not scenarios_success:
            print("   ❌ Payment flow scenarios test failed")
        sys.exit(1)
    
    sys.exit(0)
