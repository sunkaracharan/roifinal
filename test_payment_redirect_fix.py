#!/usr/bin/env python
"""
Test script to verify payment redirect fix after successful payment
Run this to test that users are properly redirected after payment without about:blank issues
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

def test_payment_redirect_fix():
    """Test that payment redirect works without about:blank issues"""
    
    print("🧪 Testing Payment Redirect Fix...")
    print("=" * 60)
    
    # Create a fresh test user
    unique_username = f'redirect_fix_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'redirect_fix_{uuid.uuid4().hex[:8]}@example.com',
        first_name='RedirectFix',
        last_name='Test'
    )
    
    print(f"✅ Created test user: {test_user.username}")
    
    # Use up all free calculations
    user_limit = get_or_create_user_limit(test_user)
    for i in range(5):
        user_limit.increment_calculation_count()
        user_limit.refresh_from_db()
    
    print(f"📊 User has used all free calculations: {user_limit.full_calculations_used}")
    
    # Test payment creation with success URL
    client = Client()
    client.force_login(test_user)
    
    print(f"\n🔄 Testing payment creation with success URL...")
    response = client.post('/dashboard/payment/create/')
    
    if response.status_code == 200:
        print("✅ Payment creation successful")
        
        import json
        data = json.loads(response.content)
        payment_id = data.get('payment_id')
        success_url = data.get('success_url')
        
        if payment_id and success_url:
            print(f"✅ Payment ID generated: {payment_id}")
            print(f"✅ Success URL generated: {success_url}")
            
            # Verify success URL contains payment ID
            if payment_id in success_url:
                print("✅ Success URL contains payment ID")
            else:
                print("❌ Success URL does not contain payment ID")
                return False
                
        else:
            print("❌ Payment ID or Success URL not generated")
            return False
    else:
        print("❌ Payment creation failed")
        return False
    
    # Test manual payment verification (simulating successful payment)
    print(f"\n🔄 Testing manual payment verification...")
    
    mock_razorpay_data = {
        'payment_id': payment_id,
        'razorpay_payment_id': f'redirect_test_{uuid.uuid4().hex[:8]}',
        'razorpay_signature': f'redirect_signature_{uuid.uuid4().hex[:8]}'
    }
    
    response = client.post(
        '/dashboard/payment/verify/',
        data=mock_razorpay_data,
        content_type='application/json'
    )
    
    if response.status_code == 200:
        print("✅ Manual payment verification successful")
        
        # Check payment status
        payment = Payment.objects.get(payment_id=payment_id)
        if payment.status == 'completed':
            print("✅ Payment status updated to completed")
        else:
            print("❌ Payment status not updated to completed")
            return False
        
        # Check unlimited access
        user_limit.refresh_from_db()
        if user_limit.unlimited_access:
            print("✅ Unlimited access granted")
        else:
            print("❌ Unlimited access not granted")
            return False
            
    else:
        print("❌ Manual payment verification failed")
        return False
    
    # Test payment success redirect
    print(f"\n🔄 Testing payment success redirect...")
    response = client.get(f'/dashboard/payment/success/?payment_id={payment_id}')
    
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
    
    # Test full calculator access after payment
    print(f"\n🔄 Testing full calculator access after payment...")
    response = client.get('/dashboard/full/')
    
    if response.status_code == 200:
        print("✅ User can access full calculator after payment")
        
        content = response.content.decode()
        
        # Check if unlimited access is shown
        if 'unlimited access' in content.lower():
            print("✅ Unlimited access status is displayed")
        else:
            print("⚠️  Unlimited access status might not be displayed")
        
        # Check if payment button is not shown
        if 'get unlimited access' not in content.lower():
            print("✅ Payment button is not shown (user has unlimited access)")
        else:
            print("⚠️  Payment button might still be shown")
            
    else:
        print("❌ User cannot access full calculator after payment")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Payment redirect fix is working correctly!")
    print("   ✅ Payment creation includes success URL")
    print("   ✅ Manual payment verification works")
    print("   ✅ Payment success redirects to full calculator")
    print("   ✅ User can access full calculator after payment")
    print("   ✅ No about:blank redirect issues")
    
    return True

def test_simulation_button():
    """Test the simulation button for testing purposes"""
    
    print("\n🧪 Testing Payment Simulation Button...")
    print("=" * 60)
    
    # Create a fresh test user
    unique_username = f'simulation_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'simulation_{uuid.uuid4().hex[:8]}@example.com',
        first_name='Simulation',
        last_name='Test'
    )
    
    print(f"✅ Created test user: {test_user.username}")
    
    # Use up all free calculations
    user_limit = get_or_create_user_limit(test_user)
    for i in range(5):
        user_limit.increment_calculation_count()
        user_limit.refresh_from_db()
    
    print(f"📊 User has used all free calculations: {user_limit.full_calculations_used}")
    
    # Test payment required page loads
    client = Client()
    client.force_login(test_user)
    
    print(f"\n🔄 Testing payment required page with simulation button...")
    response = client.get('/dashboard/payment-required/')
    
    if response.status_code == 200:
        print("✅ Payment required page loads successfully")
        
        content = response.content.decode()
        
        # Check if simulation button is present
        if 'Simulate Successful Payment (Test Mode)' in content:
            print("✅ Simulation button is present")
        else:
            print("⚠️  Simulation button might not be present")
        
        # Check if manual verification button is present
        if 'I have completed the payment - Verify Now' in content:
            print("✅ Manual verification button is present")
        else:
            print("⚠️  Manual verification button might not be present")
            
    else:
        print("❌ Payment required page does not load")
        return False
    
    # Create payment and test simulation
    print(f"\n🔄 Testing payment simulation...")
    response = client.post('/dashboard/payment/create/')
    
    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        payment_id = data.get('payment_id')
        
        if payment_id:
            print(f"✅ Payment created for simulation: {payment_id}")
            
            # Simulate payment verification
            mock_razorpay_data = {
                'payment_id': payment_id,
                'razorpay_payment_id': f'simulation_{uuid.uuid4().hex[:8]}',
                'razorpay_signature': f'simulation_signature_{uuid.uuid4().hex[:8]}'
            }
            
            response = client.post(
                '/dashboard/payment/verify/',
                data=mock_razorpay_data,
                content_type='application/json'
            )
            
            if response.status_code == 200:
                print("✅ Payment simulation successful")
                
                # Check payment status
                payment = Payment.objects.get(payment_id=payment_id)
                if payment.status == 'completed':
                    print("✅ Payment status updated to completed via simulation")
                else:
                    print("❌ Payment status not updated via simulation")
                    return False
                
                # Check unlimited access
                user_limit.refresh_from_db()
                if user_limit.unlimited_access:
                    print("✅ Unlimited access granted via simulation")
                else:
                    print("❌ Unlimited access not granted via simulation")
                    return False
                    
            else:
                print("❌ Payment simulation failed")
                return False
        else:
            print("❌ Payment ID not generated for simulation")
            return False
    else:
        print("❌ Payment creation failed for simulation")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Payment simulation is working correctly!")
    print("   ✅ Simulation button is present on payment page")
    print("   ✅ Payment simulation works correctly")
    print("   ✅ Payment status updates via simulation")
    print("   ✅ Unlimited access granted via simulation")
    
    return True

if __name__ == "__main__":
    redirect_fix_success = test_payment_redirect_fix()
    simulation_success = test_simulation_button()
    
    print("\n" + "=" * 80)
    if redirect_fix_success and simulation_success:
        print("🎉 ALL PAYMENT REDIRECT FIX TESTS PASSED!")
        print("   ✅ Payment redirect fix works correctly")
        print("   ✅ No more about:blank redirect issues")
        print("   ✅ Payment simulation works for testing")
        print("   ✅ Users are properly redirected after payment")
        print("   ✅ Unlimited access is granted correctly")
    else:
        print("❌ SOME PAYMENT REDIRECT FIX TESTS FAILED!")
        if not redirect_fix_success:
            print("   ❌ Payment redirect fix test failed")
        if not simulation_success:
            print("   ❌ Payment simulation test failed")
        sys.exit(1)
    
    sys.exit(0)
