#!/usr/bin/env python
"""
Simple script to test OpenAI API key configuration
Run this to verify your API key is working before using the chatbot
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roi_calculator.settings')
django.setup()

from django.conf import settings
import google.generativeai as genai

def test_api_key():
    """Test if the Gemini API key is configured and working"""
    
    print("🔍 Testing Google Gemini API Key Configuration...")
    print("=" * 50)
    
    # Check if API key is configured
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    
    if not api_key:
        print("❌ ERROR: No API key found in settings")
        return False
    
    if api_key == 'your-gemini-api-key-here':
        print("❌ ERROR: You're still using the placeholder API key!")
        print("   Please replace it with your actual Gemini API key.")
        print("   See GEMINI_API_SETUP.md for instructions.")
        return False
    
    if not api_key.startswith('AIza'):
        print("❌ ERROR: API key doesn't look valid (should start with 'AIza')")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Test the API key
    try:
        print("🧪 Testing API connection...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Make a simple test request
        response = model.generate_content(
            "Say 'Hello! API key is working correctly.'",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=20,
                temperature=0.7,
            )
        )
        
        bot_response = response.text
        print(f"✅ API test successful!")
        print(f"🤖 Bot response: {bot_response}")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        if "Invalid API key" in str(e):
            print("   Your API key is invalid. Please check it.")
        elif "quota" in str(e).lower():
            print("   Quota exceeded. Check your Gemini API usage limits.")
        else:
            print("   Check your internet connection and try again.")
        return False

if __name__ == "__main__":
    success = test_api_key()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SUCCESS: Your Gemini API key is configured correctly!")
        print("   You can now use the chatbot in your Django application.")
    else:
        print("❌ FAILED: Please fix the issues above and try again.")
        print("   See GEMINI_API_SETUP.md for detailed instructions.")
    
    sys.exit(0 if success else 1)
