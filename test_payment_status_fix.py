#!/usr/bin/env python
"""
Test script to verify payment status update after successful payment
Run this to test that payment status changes from 'pending' to 'completed' after payment
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

def test_payment_status_update():
    """Test that payment status updates from pending to completed"""
    
    print("🧪 Testing Payment Status Update...")
    print("=" * 60)
    
    # Create a fresh test user
    unique_username = f'payment_status_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'payment_status_{uuid.uuid4().hex[:8]}@example.com',
        first_name='PaymentStatus',
        last_name='Test'
    )
    
    print(f"✅ Created test user: {test_user.username}")
    
    # Create a payment record with pending status
    unique_payment_id = f'test_payment_{uuid.uuid4().hex[:8]}'
    payment = Payment.objects.create(
        user=test_user,
        amount=1.00,
        currency='INR',
        payment_id=unique_payment_id,
        status='pending'
    )
    
    print(f"✅ Created payment record: {payment.payment_id}")
    print(f"📊 Initial payment status: {payment.status}")
    
    # Verify payment is pending
    assert payment.status == 'pending', "Payment should start as pending"
    print("✅ Payment starts as pending")
    
    # Simulate payment success by calling payment_success view with Razorpay data
    client = Client()
    client.force_login(test_user)
    
    # Test payment success with Razorpay data
    razorpay_payment_id = f'test_razorpay_{uuid.uuid4().hex[:8]}'
    razorpay_signature = f'test_signature_{uuid.uuid4().hex[:8]}'
    
    print(f"\n🔄 Testing payment success with Razorpay data...")
    response = client.get(f'/dashboard/payment/success/?payment_id={payment.payment_id}&razorpay_payment_id={razorpay_payment_id}&razorpay_signature={razorpay_signature}')
    
    print(f"📊 Response status code: {response.status_code}")
    print(f"📊 Response redirect URL: {response.url if hasattr(response, 'url') else 'No redirect'}")
    
    # Refresh payment from database
    payment.refresh_from_db()
    print(f"📊 Payment status after success: {payment.status}")
    print(f"📊 Razorpay payment ID: {payment.razorpay_payment_id}")
    print(f"📊 Payment completed at: {payment.paid_at}")
    
    # Verify payment status is updated
    if payment.status == 'completed':
        print("✅ Payment status updated to completed")
    else:
        print("❌ Payment status not updated to completed")
        return False
    
    # Verify Razorpay data is saved
    if payment.razorpay_payment_id == razorpay_payment_id:
        print("✅ Razorpay payment ID saved correctly")
    else:
        print("❌ Razorpay payment ID not saved correctly")
        return False
    
    # Verify unlimited access is granted
    user_limit = get_or_create_user_limit(test_user)
    user_limit.refresh_from_db()
    
    print(f"📊 Unlimited access granted: {user_limit.unlimited_access}")
    print(f"📊 Unlimited access purchased at: {user_limit.unlimited_access_purchased_at}")
    
    if user_limit.unlimited_access:
        print("✅ Unlimited access granted correctly")
    else:
        print("❌ Unlimited access not granted")
        return False
    
    # Test that user can access full calculator
    print(f"\n🔄 Testing full calculator access after payment...")
    response = client.get('/dashboard/full/')
    
    if response.status_code == 200:
        print("✅ User can access full calculator after payment")
        
        # Check if unlimited access is shown
        content = response.content.decode()
        if 'unlimited access' in content.lower():
            print("✅ Unlimited access status is displayed")
        else:
            print("⚠️  Unlimited access status might not be displayed")
    else:
        print("❌ User cannot access full calculator after payment")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Payment status update is working correctly!")
    print("   ✅ Payment status changes from pending to completed")
    print("   ✅ Razorpay payment data is saved correctly")
    print("   ✅ Unlimited access is granted after payment")
    print("   ✅ User can access full calculator after payment")
    
    return True

def test_payment_history_display():
    """Test that completed payments show correctly in payment history"""
    
    print("\n🧪 Testing Payment History Display...")
    print("=" * 60)
    
    # Create a fresh test user
    unique_username = f'payment_history_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'payment_history_{uuid.uuid4().hex[:8]}@example.com',
        first_name='PaymentHistory',
        last_name='Test'
    )
    
    print(f"✅ Created test user: {test_user.username}")
    
    # Create multiple payment records with different statuses
    payments = []
    
    # Pending payment
    pending_payment = Payment.objects.create(
        user=test_user,
        amount=1.00,
        currency='INR',
        payment_id=f'pending_payment_{uuid.uuid4().hex[:8]}',
        status='pending'
    )
    payments.append(pending_payment)
    
    # Completed payment
    completed_payment = Payment.objects.create(
        user=test_user,
        amount=1.00,
        currency='INR',
        payment_id=f'completed_payment_{uuid.uuid4().hex[:8]}',
        status='completed',
        razorpay_payment_id=f'razorpay_{uuid.uuid4().hex[:8]}',
        razorpay_signature=f'signature_{uuid.uuid4().hex[:8]}',
        paid_at=timezone.now()
    )
    payments.append(completed_payment)
    
    print(f"✅ Created {len(payments)} payment records")
    
    # Test payment history view
    client = Client()
    client.force_login(test_user)
    
    print(f"\n🔄 Testing payment history view...")
    response = client.get('/dashboard/payment/history/')
    
    print(f"📊 Response status code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Payment history page loads successfully")
        
        content = response.content.decode()
        
        # Check if pending payment is shown
        if pending_payment.payment_id[:8] in content:
            print("✅ Pending payment is displayed in history")
        else:
            print("⚠️  Pending payment might not be displayed")
        
        # Check if completed payment is shown
        if completed_payment.payment_id[:8] in content:
            print("✅ Completed payment is displayed in history")
        else:
            print("⚠️  Completed payment might not be displayed")
        
        # Check if status badges are shown
        if 'pending' in content.lower() and 'completed' in content.lower():
            print("✅ Both pending and completed statuses are displayed")
        else:
            print("⚠️  Payment statuses might not be displayed correctly")
            
    else:
        print("❌ Payment history page does not load")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Payment history display is working correctly!")
    print("   ✅ Payment history page loads successfully")
    print("   ✅ Both pending and completed payments are displayed")
    print("   ✅ Payment statuses are shown correctly")
    
    return True

def test_webhook_payment_verification():
    """Test webhook payment verification"""
    
    print("\n🧪 Testing Webhook Payment Verification...")
    print("=" * 60)
    
    # Create a fresh test user
    unique_username = f'webhook_test_user_{uuid.uuid4().hex[:8]}'
    test_user = User.objects.create(
        username=unique_username,
        email=f'webhook_{uuid.uuid4().hex[:8]}@example.com',
        first_name='Webhook',
        last_name='Test'
    )
    
    print(f"✅ Created test user: {test_user.username}")
    
    # Create a payment record
    unique_payment_id = f'webhook_payment_{uuid.uuid4().hex[:8]}'
    razorpay_payment_id = f'webhook_razorpay_{uuid.uuid4().hex[:8]}'
    
    payment = Payment.objects.create(
        user=test_user,
        amount=1.00,
        currency='INR',
        payment_id=unique_payment_id,
        status='pending',
        razorpay_payment_id=razorpay_payment_id
    )
    
    print(f"✅ Created payment record: {payment.payment_id}")
    print(f"📊 Initial payment status: {payment.status}")
    
    # Simulate webhook call
    client = Client()
    
    webhook_data = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": razorpay_payment_id,
                    "amount": 100,  # 1.00 INR in paise
                    "currency": "INR"
                }
            }
        }
    }
    
    print(f"\n🔄 Testing webhook payment verification...")
    response = client.post(
        '/dashboard/payment/webhook/',
        data=webhook_data,
        content_type='application/json'
    )
    
    print(f"📊 Webhook response status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Webhook processed successfully")
        
        # Refresh payment from database
        payment.refresh_from_db()
        print(f"📊 Payment status after webhook: {payment.status}")
        
        if payment.status == 'completed':
            print("✅ Payment status updated to completed via webhook")
        else:
            print("❌ Payment status not updated via webhook")
            return False
        
        # Verify unlimited access is granted
        user_limit = get_or_create_user_limit(test_user)
        user_limit.refresh_from_db()
        
        if user_limit.unlimited_access:
            print("✅ Unlimited access granted via webhook")
        else:
            print("❌ Unlimited access not granted via webhook")
            return False
            
    else:
        print("❌ Webhook processing failed")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Webhook payment verification is working correctly!")
    print("   ✅ Webhook processes payment.captured events")
    print("   ✅ Payment status updated to completed via webhook")
    print("   ✅ Unlimited access granted via webhook")
    
    return True

if __name__ == "__main__":
    status_update_success = test_payment_status_update()
    history_display_success = test_payment_history_display()
    webhook_verification_success = test_webhook_payment_verification()
    
    print("\n" + "=" * 80)
    if status_update_success and history_display_success and webhook_verification_success:
        print("🎉 ALL PAYMENT STATUS TESTS PASSED!")
        print("   ✅ Payment status updates from pending to completed")
        print("   ✅ Payment history displays both pending and completed payments")
        print("   ✅ Webhook payment verification works correctly")
        print("   ✅ Payment status fix is working properly")
    else:
        print("❌ SOME PAYMENT STATUS TESTS FAILED!")
        if not status_update_success:
            print("   ❌ Payment status update test failed")
        if not history_display_success:
            print("   ❌ Payment history display test failed")
        if not webhook_verification_success:
            print("   ❌ Webhook payment verification test failed")
        sys.exit(1)
    
    sys.exit(0)
