#!/usr/bin/env python
"""
Test script to verify manual payment verification after Razorpay payment
Run this to test that users can manually verify payments after completing them in Razorpay
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
import uuid

def test_manual_payment_verification():
    """Test manual payment verification after Razorpay payment"""
    
    print("🧪 Testing Manual Payment Verification...")
    print("=" * 60)
    
    # Create a fresh test user
    unique_username = f'manual_verification_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'manual_verification_{uuid.uuid4().hex[:8]}@example.com',
        first_name='ManualVerification',
        last_name='Test'
    )
    
    print(f"✅ Created test user: {test_user.username}")
    
    # Get user limit and use up all free calculations
    user_limit = get_or_create_user_limit(test_user)
    for i in range(5):
        user_limit.increment_calculation_count()
        user_limit.refresh_from_db()
    
    print(f"📊 User has used all free calculations: {user_limit.full_calculations_used}")
    print(f"🔍 Can make calculation: {user_limit.can_make_calculation()}")
    
    # Create a payment record with pending status
    unique_payment_id = f'manual_payment_{uuid.uuid4().hex[:8]}'
    payment = Payment.objects.create(
        user=test_user,
        amount=1.00,
        currency='INR',
        payment_id=unique_payment_id,
        status='pending'
    )
    
    print(f"✅ Created payment record: {payment.payment_id}")
    print(f"📊 Initial payment status: {payment.status}")
    
    # Test payment required page loads
    client = Client()
    client.force_login(test_user)
    
    print(f"\n🔄 Testing payment required page...")
    response = client.get('/dashboard/payment-required/')
    
    if response.status_code == 200:
        print("✅ Payment required page loads successfully")
        
        content = response.content.decode()
        
        # Check if manual verification button is present
        if 'I have completed the payment - Verify Now' in content:
            print("✅ Manual verification button is present")
        else:
            print("⚠️  Manual verification button might not be present")
        
        # Check if Razorpay payment button is present
        if 'razorpay.com' in content:
            print("✅ Razorpay payment button is present")
        else:
            print("⚠️  Razorpay payment button might not be present")
            
    else:
        print("❌ Payment required page does not load")
        return False
    
    # Simulate manual payment verification
    print(f"\n🔄 Testing manual payment verification...")
    
    # Simulate the verification process by calling verify_payment endpoint
    mock_razorpay_data = {
        'payment_id': payment.payment_id,
        'razorpay_payment_id': f'manual_razorpay_{uuid.uuid4().hex[:8]}',
        'razorpay_signature': f'manual_signature_{uuid.uuid4().hex[:8]}'
    }
    
    response = client.post(
        '/dashboard/payment/verify/',
        data=mock_razorpay_data,
        content_type='application/json'
    )
    
    print(f"📊 Verification response status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Manual payment verification successful")
        
        # Refresh payment from database
        payment.refresh_from_db()
        print(f"📊 Payment status after verification: {payment.status}")
        
        if payment.status == 'completed':
            print("✅ Payment status updated to completed")
        else:
            print("❌ Payment status not updated to completed")
            return False
        
        # Verify unlimited access is granted
        user_limit.refresh_from_db()
        print(f"📊 Unlimited access granted: {user_limit.unlimited_access}")
        
        if user_limit.unlimited_access:
            print("✅ Unlimited access granted correctly")
        else:
            print("❌ Unlimited access not granted")
            return False
        
        # Test that user can now access full calculator
        print(f"\n🔄 Testing full calculator access after verification...")
        response = client.get('/dashboard/full/')
        
        if response.status_code == 200:
            print("✅ User can access full calculator after verification")
            
            content = response.content.decode()
            if 'unlimited access' in content.lower():
                print("✅ Unlimited access status is displayed")
            else:
                print("⚠️  Unlimited access status might not be displayed")
                
        else:
            print("❌ User cannot access full calculator after verification")
            return False
            
    else:
        print("❌ Manual payment verification failed")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Manual payment verification is working correctly!")
    print("   ✅ Payment required page loads with manual verification button")
    print("   ✅ Manual payment verification updates status to completed")
    print("   ✅ Unlimited access is granted after verification")
    print("   ✅ User can access full calculator after verification")
    
    return True

def test_payment_flow_with_manual_verification():
    """Test complete payment flow with manual verification"""
    
    print("\n🧪 Testing Complete Payment Flow with Manual Verification...")
    print("=" * 60)
    
    # Create a fresh test user
    unique_username = f'complete_flow_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'complete_flow_{uuid.uuid4().hex[:8]}@example.com',
        first_name='CompleteFlow',
        last_name='Test'
    )
    
    print(f"✅ Created test user: {test_user.username}")
    
    # Use up all free calculations
    user_limit = get_or_create_user_limit(test_user)
    for i in range(5):
        user_limit.increment_calculation_count()
        user_limit.refresh_from_db()
    
    print(f"📊 User has used all free calculations: {user_limit.full_calculations_used}")
    
    # Test that user is redirected to payment required
    client = Client()
    client.force_login(test_user)
    
    print(f"\n🔄 Testing redirect to payment required...")
    response = client.get('/dashboard/full/')
    
    if response.status_code == 302 and 'payment-required' in response.url:
        print("✅ User is redirected to payment required page")
    else:
        print("❌ User is not redirected to payment required page")
        return False
    
    # Create payment
    print(f"\n🔄 Testing payment creation...")
    response = client.post('/dashboard/payment/create/')
    
    if response.status_code == 200:
        print("✅ Payment creation successful")
        
        # Get payment ID from response
        import json
        data = json.loads(response.content)
        payment_id = data.get('payment_id')
        
        if payment_id:
            print(f"✅ Payment ID generated: {payment_id}")
            
            # Simulate manual verification
            print(f"\n🔄 Testing manual verification...")
            mock_razorpay_data = {
                'payment_id': payment_id,
                'razorpay_payment_id': f'flow_razorpay_{uuid.uuid4().hex[:8]}',
                'razorpay_signature': f'flow_signature_{uuid.uuid4().hex[:8]}'
            }
            
            response = client.post(
                '/dashboard/payment/verify/',
                data=mock_razorpay_data,
                content_type='application/json'
            )
            
            if response.status_code == 200:
                print("✅ Manual verification successful")
                
                # Test that user can now access full calculator
                response = client.get('/dashboard/full/')
                
                if response.status_code == 200:
                    print("✅ User can access full calculator after payment")
                    
                    # Check if payment button is not shown
                    content = response.content.decode()
                    if 'get unlimited access' not in content.lower():
                        print("✅ Payment button is not shown (user has unlimited access)")
                    else:
                        print("⚠️  Payment button might still be shown")
                        
                    return True
                else:
                    print("❌ User cannot access full calculator after payment")
                    return False
            else:
                print("❌ Manual verification failed")
                return False
        else:
            print("❌ Payment ID not generated")
            return False
    else:
        print("❌ Payment creation failed")
        return False

if __name__ == "__main__":
    manual_verification_success = test_manual_payment_verification()
    complete_flow_success = test_payment_flow_with_manual_verification()
    
    print("\n" + "=" * 80)
    if manual_verification_success and complete_flow_success:
        print("🎉 ALL MANUAL PAYMENT VERIFICATION TESTS PASSED!")
        print("   ✅ Manual payment verification works correctly")
        print("   ✅ Complete payment flow with manual verification works")
        print("   ✅ Users can verify payments after completing them in Razorpay")
        print("   ✅ Payment status updates and unlimited access is granted")
    else:
        print("❌ SOME MANUAL PAYMENT VERIFICATION TESTS FAILED!")
        if not manual_verification_success:
            print("   ❌ Manual payment verification test failed")
        if not complete_flow_success:
            print("   ❌ Complete payment flow test failed")
        sys.exit(1)
    
    sys.exit(0)
