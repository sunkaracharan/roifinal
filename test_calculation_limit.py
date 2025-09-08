#!/usr/bin/env python
"""
Test script to verify calculation limit fix
Run this to test if the calculation count properly decreases
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
from calculator.models import UserCalculationLimit, ROIResult
from calculator.views import get_or_create_user_limit

def test_calculation_limit():
    """Test if calculation limit works correctly"""
    
    print("🧪 Testing Calculation Limit Fix...")
    print("=" * 50)
    
    # Get or create a test user
    test_user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    if created:
        print(f"✅ Created test user: {test_user.username}")
    else:
        print(f"✅ Using existing test user: {test_user.username}")
    
    # Get user limit
    user_limit = get_or_create_user_limit(test_user)
    print(f"📊 Initial calculations used: {user_limit.full_calculations_used}")
    print(f"📊 Initial remaining calculations: {user_limit.get_remaining_free_calculations()}")
    
    # Test incrementing calculation count
    print("\n🔄 Testing calculation count increment...")
    
    for i in range(3):
        print(f"\n--- Test {i+1} ---")
        
        # Get current count
        current_used = user_limit.full_calculations_used
        current_remaining = user_limit.get_remaining_free_calculations()
        
        print(f"Before: Used={current_used}, Remaining={current_remaining}")
        
        # Increment count (simulating save_full_results)
        user_limit.increment_calculation_count()
        
        # Refresh from database
        user_limit.refresh_from_db()
        
        # Check new count
        new_used = user_limit.full_calculations_used
        new_remaining = user_limit.get_remaining_free_calculations()
        
        print(f"After:  Used={new_used}, Remaining={new_remaining}")
        
        # Verify increment worked
        if new_used == current_used + 1:
            print("✅ Calculation count incremented correctly")
        else:
            print("❌ Calculation count increment failed")
            return False
        
        # Verify remaining calculations decreased
        if new_remaining == current_remaining - 1:
            print("✅ Remaining calculations decreased correctly")
        else:
            print("❌ Remaining calculations decrease failed")
            return False
    
    # Test limit reached
    print(f"\n🎯 Final state: Used={user_limit.full_calculations_used}, Remaining={user_limit.get_remaining_free_calculations()}")
    
    # Test can_make_calculation
    can_make = user_limit.can_make_calculation()
    print(f"🔍 Can make calculation: {can_make}")
    
    if user_limit.full_calculations_used >= 5:
        if not can_make:
            print("✅ Limit enforcement working correctly")
        else:
            print("❌ Limit enforcement failed")
            return False
    else:
        if can_make:
            print("✅ Can still make calculations")
        else:
            print("❌ Should be able to make calculations")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 SUCCESS: Calculation limit fix is working correctly!")
    print("   The free calculation count now properly decreases.")
    
    return True

if __name__ == "__main__":
    success = test_calculation_limit()
    
    if not success:
        print("\n❌ FAILED: There are still issues with the calculation limit.")
        sys.exit(1)
    
    print("\n✅ All tests passed! The fix is working correctly.")
    sys.exit(0)
