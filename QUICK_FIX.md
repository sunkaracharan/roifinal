# 🚨 QUICK FIX: OpenAI API Key Error

## The Problem
You're seeing "OpenAI API key not configured" because you need to add your actual API key.

## ✅ Simple Solution (2 minutes)

### Step 1: Get Your API Key
1. Go to: https://platform.openai.com/api-keys
2. Sign up/login to OpenAI
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### Step 2: Add Your Key
1. Open the file `config.py` in your project
2. Find this line:
   ```python
   OPENAI_API_KEY = "sk-your-openai-api-key-here"
   ```
3. Replace it with your actual key:
   ```python
   OPENAI_API_KEY = "sk-your-actual-key-here"
   ```
4. Save the file

### Step 3: Test It
Run this command to test:
```bash
.\venv\Scripts\python.exe test_api_key.py
```

### Step 4: Start Your Server
```bash
.\venv\Scripts\python.exe manage.py runserver
```

## 🎉 That's It!

Your chatbot will now work! The floating robot icon will appear for logged-in users.

## 💰 Cost Info
- Very cheap: ~$0.002 per 1K tokens
- A simple question costs less than $0.01
- You can set usage limits in OpenAI

## 🔒 Security
- Your API key is stored locally
- Never shared or uploaded anywhere
- Handled securely server-side

## ❓ Need Help?
If you're still having issues:
1. Make sure your API key starts with `sk-`
2. Check you have credits in your OpenAI account
3. Restart the Django server after making changes
