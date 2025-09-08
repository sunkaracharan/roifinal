#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roi_calculator.settings')
django.setup()

from django.contrib.auth.models import User
from calculator.models import ROIResult, Payment, UserCalculationLimit

def display_admin_dashboard():
    """Display comprehensive admin dashboard with all user data and calculations"""
    
    print("=" * 80)
    print("🔐 ROI CALCULATOR - ADMIN DASHBOARD")
    print("=" * 80)
    
    # Get all users
    users = User.objects.all().order_by('date_joined')
    total_users = users.count()
    
    print(f"\n📊 DATABASE OVERVIEW")
    print(f"   Total Registered Users: {total_users}")
    print(f"   Total ROI Calculations: {ROIResult.objects.count()}")
    print(f"   Total Payments: {Payment.objects.count()}")
    print(f"   Total Calculation Limits: {UserCalculationLimit.objects.count()}")
    
    print(f"\n👥 ALL REGISTERED USERS & THEIR DATA")
    print("-" * 80)
    
    for i, user in enumerate(users, 1):
        print(f"\n{i}. 👤 USER: {user.username}")
        print(f"   📧 Email: {user.email}")
        print(f"   📅 Joined: {user.date_joined.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   🔑 Is Admin: {'Yes' if user.is_superuser else 'No'}")
        print(f"   🟢 Is Active: {'Yes' if user.is_active else 'No'}")
        
        # Get user's ROI calculations
        roi_calculations = ROIResult.objects.filter(user=user).order_by('-timestamp')
        calculation_count = roi_calculations.count()
        
        print(f"   📈 ROI Calculations: {calculation_count}")
        
        if calculation_count > 0:
            print(f"   📊 Recent Calculations:")
            for calc in roi_calculations[:3]:  # Show last 3 calculations
                print(f"      - {calc.mode.title()} | ROI: {calc.roi_percent:.1f}% | Date: {calc.timestamp.strftime('%Y-%m-%d %H:%M')}")
        
        # Get user's payments
        payments = Payment.objects.filter(user=user).order_by('-created_at')
        payment_count = payments.count()
        
        print(f"   💳 Payments: {payment_count}")
        
        if payment_count > 0:
            total_paid = sum(p.amount for p in payments if p.status == 'completed')
            print(f"   💰 Total Paid: ₹{total_paid}")
            print(f"   📋 Recent Payments:")
            for payment in payments[:2]:  # Show last 2 payments
                print(f"      - ₹{payment.amount} | Status: {payment.status} | Date: {payment.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        # Get user's calculation limits
        try:
            user_limit = UserCalculationLimit.objects.get(user=user)
            print(f"   🎯 Calculation Limits:")
            print(f"      - Full Calculations Used: {user_limit.full_calculations_used}")
            print(f"      - Unlimited Access: {'Yes' if user_limit.unlimited_access else 'No'}")
            if user_limit.unlimited_access_purchased_at:
                print(f"      - Unlimited Access Purchased: {user_limit.unlimited_access_purchased_at.strftime('%Y-%m-%d %H:%M')}")
        except UserCalculationLimit.DoesNotExist:
            print(f"   🎯 Calculation Limits: Not set")
        
        print("-" * 40)
    
    # Summary statistics
    print(f"\n📈 SUMMARY STATISTICS")
    print("-" * 40)
    
    # ROI calculation statistics
    all_calculations = ROIResult.objects.all()
    if all_calculations.exists():
        avg_roi = sum(calc.roi_percent for calc in all_calculations) / all_calculations.count()
        max_roi = max(calc.roi_percent for calc in all_calculations)
        min_roi = min(calc.roi_percent for calc in all_calculations)
        
        print(f"   📊 ROI Statistics:")
        print(f"      - Average ROI: {avg_roi:.1f}%")
        print(f"      - Highest ROI: {max_roi:.1f}%")
        print(f"      - Lowest ROI: {min_roi:.1f}%")
    
    # Payment statistics
    completed_payments = Payment.objects.filter(status='completed')
    if completed_payments.exists():
        total_revenue = sum(p.amount for p in completed_payments)
        print(f"   💰 Revenue Statistics:")
        print(f"      - Total Revenue: ₹{total_revenue}")
        print(f"      - Completed Payments: {completed_payments.count()}")
    
    # User activity statistics
    active_users = User.objects.filter(is_active=True).count()
    admin_users = User.objects.filter(is_superuser=True).count()
    
    print(f"   👥 User Statistics:")
    print(f"      - Active Users: {active_users}")
    print(f"      - Admin Users: {admin_users}")
    print(f"      - Regular Users: {total_users - admin_users}")
    
    print(f"\n🔗 ADMIN ACCESS")
    print("-" * 40)
    print(f"   🌐 Django Admin URL: http://127.0.0.1:8000/admin/")
    print(f"   👤 Admin Username: admin")
    print(f"   🔑 Admin Password: admin123")
    print(f"   📱 Application URL: http://127.0.0.1:8000/")
    
    print(f"\n✅ Admin dashboard complete! All user data and calculations are accessible.")
    print("=" * 80)

if __name__ == '__main__':
    display_admin_dashboard()
