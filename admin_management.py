#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roi_calculator.settings')
django.setup()

from django.contrib.auth.models import User
from calculator.models import ROIResult, Payment, UserCalculationLimit

class AdminManager:
    """Admin management class for ROI Calculator"""
    
    def __init__(self):
        self.admin_user = None
        self.setup_admin()
    
    def setup_admin(self):
        """Setup or verify admin user exists"""
        try:
            self.admin_user = User.objects.get(username='admin')
            print(f"✅ Admin user found: {self.admin_user.username}")
        except User.DoesNotExist:
            print("❌ Admin user not found. Creating...")
            self.admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@roicalculator.com',
                password='admin123'
            )
            print(f"✅ Admin user created: {self.admin_user.username}")
    
    def get_all_users(self):
        """Get all registered users with their details"""
        users = User.objects.all().order_by('date_joined')
        return users
    
    def get_user_calculations(self, user):
        """Get all calculations for a specific user"""
        return ROIResult.objects.filter(user=user).order_by('-timestamp')
    
    def get_user_payments(self, user):
        """Get all payments for a specific user"""
        return Payment.objects.filter(user=user).order_by('-created_at')
    
    def get_user_limits(self, user):
        """Get calculation limits for a specific user"""
        try:
            return UserCalculationLimit.objects.get(user=user)
        except UserCalculationLimit.DoesNotExist:
            return None
    
    def grant_unlimited_access(self, username):
        """Grant unlimited access to a user"""
        try:
            user = User.objects.get(username=username)
            user_limit, created = UserCalculationLimit.objects.get_or_create(user=user)
            user_limit.unlimited_access = True
            user_limit.unlimited_access_purchased_at = datetime.now()
            user_limit.save()
            print(f"✅ Granted unlimited access to {username}")
            return True
        except User.DoesNotExist:
            print(f"❌ User {username} not found")
            return False
    
    def reset_user_calculations(self, username):
        """Reset calculation count for a user"""
        try:
            user = User.objects.get(username=username)
            user_limit, created = UserCalculationLimit.objects.get_or_create(user=user)
            user_limit.full_calculations_used = 0
            user_limit.save()
            print(f"✅ Reset calculation count for {username}")
            return True
        except User.DoesNotExist:
            print(f"❌ User {username} not found")
            return False
    
    def create_test_user(self, username, email, password='test123'):
        """Create a test user for demonstration"""
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            print(f"✅ Test user created: {username} ({email})")
            return user
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return None
    
    def display_user_details(self, username):
        """Display detailed information about a specific user"""
        try:
            user = User.objects.get(username=username)
            print(f"\n👤 USER DETAILS: {username}")
            print("-" * 50)
            print(f"📧 Email: {user.email}")
            print(f"📅 Joined: {user.date_joined}")
            print(f"🔑 Is Admin: {user.is_superuser}")
            print(f"🟢 Is Active: {user.is_active}")
            
            # Calculations
            calculations = self.get_user_calculations(user)
            print(f"\n📈 ROI CALCULATIONS ({calculations.count()}):")
            for calc in calculations:
                print(f"   - {calc.mode.title()} | ROI: {calc.roi_percent:.1f}% | Date: {calc.timestamp}")
            
            # Payments
            payments = self.get_user_payments(user)
            print(f"\n💳 PAYMENTS ({payments.count()}):")
            for payment in payments:
                print(f"   - ₹{payment.amount} | Status: {payment.status} | Date: {payment.created_at}")
            
            # Limits
            limits = self.get_user_limits(user)
            if limits:
                print(f"\n🎯 CALCULATION LIMITS:")
                print(f"   - Full Calculations Used: {limits.full_calculations_used}")
                print(f"   - Unlimited Access: {limits.unlimited_access}")
                if limits.unlimited_access_purchased_at:
                    print(f"   - Unlimited Access Date: {limits.unlimited_access_purchased_at}")
            
        except User.DoesNotExist:
            print(f"❌ User {username} not found")
    
    def display_all_users_summary(self):
        """Display summary of all users"""
        users = self.get_all_users()
        print(f"\n📊 ALL USERS SUMMARY ({users.count()} total)")
        print("-" * 60)
        
        for user in users:
            calculations = self.get_user_calculations(user).count()
            payments = self.get_user_payments(user).count()
            limits = self.get_user_limits(user)
            unlimited = limits.unlimited_access if limits else False
            
            print(f"👤 {user.username} ({user.email})")
            print(f"   📈 Calculations: {calculations} | 💳 Payments: {payments} | 🎯 Unlimited: {unlimited}")
    
    def run_interactive_menu(self):
        """Run interactive admin menu"""
        while True:
            print(f"\n🔐 ADMIN MANAGEMENT MENU")
            print("=" * 40)
            print("1. View all users summary")
            print("2. View user details")
            print("3. Grant unlimited access")
            print("4. Reset user calculations")
            print("5. Create test user")
            print("6. Run admin dashboard")
            print("0. Exit")
            
            choice = input("\nEnter your choice (0-6): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                self.display_all_users_summary()
            elif choice == '2':
                username = input("Enter username: ").strip()
                self.display_user_details(username)
            elif choice == '3':
                username = input("Enter username to grant unlimited access: ").strip()
                self.grant_unlimited_access(username)
            elif choice == '4':
                username = input("Enter username to reset calculations: ").strip()
                self.reset_user_calculations(username)
            elif choice == '5':
                username = input("Enter test username: ").strip()
                email = input("Enter test email: ").strip()
                self.create_test_user(username, email)
            elif choice == '6':
                from admin_dashboard import display_admin_dashboard
                display_admin_dashboard()
            else:
                print("❌ Invalid choice. Please try again.")

def main():
    """Main function"""
    print("🚀 Starting ROI Calculator Admin Management...")
    admin_manager = AdminManager()
    
    # Display initial summary
    admin_manager.display_all_users_summary()
    
    # Run interactive menu
    admin_manager.run_interactive_menu()

if __name__ == '__main__':
    main()
