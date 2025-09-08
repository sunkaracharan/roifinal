#!/usr/bin/env python
"""
Test script to verify verify button functionality
Run this to test that the verify button works correctly when clicked
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

def test_verify_button_functionality():
    """Test that verify button works correctly when clicked"""
    
    print("🧪 Testing Verify Button Functionality...")
    print("=" * 60)
    
    # Create a fresh test user
    unique_username = f'verify_button_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'verify_button_{uuid.uuid4().hex[:8]}@example.com',
        first_name='VerifyButton',
        last_name='Test'
    )
    
    print(f"✅ Created test user: {test_user.username}")
    
    # Use up all free calculations
    user_limit = get_or_create_user_limit(test_user)
    for i in range(5):
        user_limit.increment_calculation_count()
        user_limit.refresh_from_db()
    
    print(f"📊 User has used all free calculations: {user_limit.full_calculations_used}")
    
    # Test payment required page loads with verify button
    client = Client()
    client.force_login(test_user)
    
    print(f"\n🔄 Testing payment required page with verify button...")
    response = client.get('/dashboard/payment-required/')
    
    if response.status_code == 200:
        print("✅ Payment required page loads successfully")
        
        content = response.content.decode()
        
        # Check if verify button is present
        if 'I have completed the payment - Verify Now' in content:
            print("✅ Verify button is present in HTML")
        else:
            print("❌ Verify button is not present in HTML")
            return False
        
        # Check if simulation button is present
        if 'Simulate Successful Payment (Test Mode)' in content:
            print("✅ Simulation button is present in HTML")
        else:
            print("❌ Simulation button is not present in HTML")
            return False
        
        # Check if JavaScript functions are present
        if 'handlePaymentSuccess' in content:
            print("✅ handlePaymentSuccess function is present in JavaScript")
        else:
            print("❌ handlePaymentSuccess function is not present in JavaScript")
            return False
        
        if 'verifyPayment' in content:
            print("✅ verifyPayment function is present in JavaScript")
        else:
            print("❌ verifyPayment function is not present in JavaScript")
            return False
            
    else:
        print("❌ Payment required page does not load")
        return False
    
    # Create payment and test verify functionality
    print(f"\n🔄 Testing payment creation and verify functionality...")
    response = client.post('/dashboard/payment/create/')
    
    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        payment_id = data.get('payment_id')
        
        if payment_id:
            print(f"✅ Payment created for verification: {payment_id}")
            
            # Test manual verification (simulating verify button click)
            print(f"\n🔄 Testing manual verification (simulating verify button click)...")
            mock_razorpay_data = {
                'payment_id': payment_id,
                'razorpay_payment_id': f'verify_test_{uuid.uuid4().hex[:8]}',
                'razorpay_signature': f'verify_signature_{uuid.uuid4().hex[:8]}'
            }
            
            response = client.post(
                '/dashboard/payment/verify/',
                data=mock_razorpay_data,
                content_type='application/json'
            )
            
            if response.status_code == 200:
                print("✅ Manual verification successful (verify button would work)")
                
                # Check payment status
                payment = Payment.objects.get(payment_id=payment_id)
                if payment.status == 'completed':
                    print("✅ Payment status updated to completed via verification")
                else:
                    print("❌ Payment status not updated via verification")
                    return False
                
                # Check unlimited access
                user_limit.refresh_from_db()
                if user_limit.unlimited_access:
                    print("✅ Unlimited access granted via verification")
                else:
                    print("❌ Unlimited access not granted via verification")
                    return False
                
                # Test that user can access full calculator
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
                print("❌ Manual verification failed")
                return False
        else:
            print("❌ Payment ID not generated for verification")
            return False
    else:
        print("❌ Payment creation failed for verification")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Verify button functionality is working correctly!")
    print("   ✅ Verify button is present in HTML")
    print("   ✅ JavaScript functions are properly defined")
    print("   ✅ Manual verification works (simulating button click)")
    print("   ✅ Payment status updates via verification")
    print("   ✅ Unlimited access granted via verification")
    print("   ✅ User can access full calculator after verification")
    
    return True

def test_simulation_button_functionality():
    """Test that simulation button works correctly when clicked"""
    
    print("\n🧪 Testing Simulation Button Functionality...")
    print("=" * 60)
    
    # Create a fresh test user
    unique_username = f'simulation_button_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'simulation_button_{uuid.uuid4().hex[:8]}@example.com',
        first_name='SimulationButton',
        last_name='Test'
    )
    
    print(f"✅ Created test user: {test_user.username}")
    
    # Use up all free calculations
    user_limit = get_or_create_user_limit(test_user)
    for i in range(5):
        user_limit.increment_calculation_count()
        user_limit.refresh_from_db()
    
    print(f"📊 User has used all free calculations: {user_limit.full_calculations_used}")
    
    # Test payment required page loads with simulation button
    client = Client()
    client.force_login(test_user)
    
    print(f"\n🔄 Testing payment required page with simulation button...")
    response = client.get('/dashboard/payment-required/')
    
    if response.status_code == 200:
        print("✅ Payment required page loads successfully")
        
        content = response.content.decode()
        
        # Check if simulation button is present
        if 'Simulate Successful Payment (Test Mode)' in content:
            print("✅ Simulation button is present in HTML")
        else:
            print("❌ Simulation button is not present in HTML")
            return False
            
    else:
        print("❌ Payment required page does not load")
        return False
    
    # Create payment and test simulation functionality
    print(f"\n🔄 Testing payment creation and simulation functionality...")
    response = client.post('/dashboard/payment/create/')
    
    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        payment_id = data.get('payment_id')
        
        if payment_id:
            print(f"✅ Payment created for simulation: {payment_id}")
            
            # Test simulation (simulating simulation button click)
            print(f"\n🔄 Testing simulation (simulating simulation button click)...")
            mock_razorpay_data = {
                'payment_id': payment_id,
                'razorpay_payment_id': f'simulation_test_{uuid.uuid4().hex[:8]}',
                'razorpay_signature': f'simulation_signature_{uuid.uuid4().hex[:8]}'
            }
            
            response = client.post(
                '/dashboard/payment/verify/',
                data=mock_razorpay_data,
                content_type='application/json'
            )
            
            if response.status_code == 200:
                print("✅ Simulation successful (simulation button would work)")
                
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
                print("❌ Simulation failed")
                return False
        else:
            print("❌ Payment ID not generated for simulation")
            return False
    else:
        print("❌ Payment creation failed for simulation")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Simulation button functionality is working correctly!")
    print("   ✅ Simulation button is present in HTML")
    print("   ✅ Simulation works correctly")
    print("   ✅ Payment status updates via simulation")
    print("   ✅ Unlimited access granted via simulation")
    
    return True

if __name__ == "__main__":
    verify_button_success = test_verify_button_functionality()
    simulation_button_success = test_simulation_button_functionality()
    
    print("\n" + "=" * 80)
    if verify_button_success and simulation_button_success:
        print("🎉 ALL VERIFY BUTTON TESTS PASSED!")
        print("   ✅ Verify button is present and functional")
        print("   ✅ Simulation button is present and functional")
        print("   ✅ JavaScript functions are properly defined")
        print("   ✅ Payment verification works correctly")
        print("   ✅ Users can verify payments after completing them")
        print("   ✅ Unlimited access is granted after verification")
    else:
        print("❌ SOME VERIFY BUTTON TESTS FAILED!")
        if not verify_button_success:
            print("   ❌ Verify button functionality test failed")
        if not simulation_button_success:
            print("   ❌ Simulation button functionality test failed")
        sys.exit(1)
    
    sys.exit(0)
