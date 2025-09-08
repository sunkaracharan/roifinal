# OpenAI API Key Setup Guide

## 🚨 Current Status: API Key Not Configured

You need to replace the placeholder API key with your actual OpenAI API key.

## 📋 Step-by-Step Setup

### Step 1: Get Your OpenAI API Key

1. **Go to OpenAI Platform:**
   - Visit: https://platform.openai.com/api-keys
   - Sign up or log in to your account

2. **Create a New API Key:**
   - Click "Create new secret key"
   - Give it a name (e.g., "ROI Calculator Bot")
   - Copy the key (it starts with `sk-`)

3. **Important:** Save the key immediately - you won't be able to see it again!

### Step 2: Configure the API Key

**Option A: Using .env file (Recommended)**

1. Open the `.env` file in your project root
2. Replace the placeholder with your actual key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

**Option B: Direct configuration in settings.py**

1. Open `roi_calculator/settings.py`
2. Find line 134: `OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-your-openai-api-key-here')`
3. Replace with your actual key:
   ```python
   OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-your-actual-key-here')
   ```

### Step 3: Test the Configuration

1. **Restart your Django server:**
   ```bash
   .\venv\Scripts\python.exe manage.py runserver
   ```

2. **Test the chatbot:**
   - Login to your application
   - Click the floating robot icon
   - Send a test message like "Hello, can you help me with ROI calculations?"

## 💰 Cost Information

- **GPT-3.5-turbo** is very cost-effective
- Typical cost: ~$0.002 per 1K tokens
- A simple question/answer costs less than $0.01
- You can set usage limits in your OpenAI account

## 🔒 Security Notes

- Never commit your API key to version control
- The .env file is already in .gitignore
- API keys are handled server-side for security

## 🚨 Troubleshooting

### "OpenAI API key not configured" Error
- Make sure you replaced the placeholder key
- Check that the .env file is in the project root
- Restart the Django server after making changes

### "Invalid API key" Error
- Verify your API key is correct
- Check that your OpenAI account has credits
- Ensure the key starts with `sk-`

### "Rate limit exceeded" Error
- You've hit OpenAI's rate limits
- Wait a few minutes and try again
- Consider upgrading your OpenAI plan

## 📞 Need Help?

If you're still having issues:
1. Double-check your API key is correct
2. Make sure you have credits in your OpenAI account
3. Verify the .env file is in the correct location
4. Restart the Django server

## 🎯 Quick Test

Once configured, try asking the chatbot:
- "What is ROI?"
- "How do I calculate cloud savings?"
- "Explain productivity gains in ROI calculations"

The chatbot should respond with helpful, context-aware answers!
