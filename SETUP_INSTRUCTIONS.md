# Quick Setup Instructions

## ✅ The chatbot is now installed and ready!

### To complete the setup, you need to:

1. **Get an OpenAI API Key:**
   - Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Sign up or log in
   - Create a new API key
   - Copy the key

2. **Add your API key to the project:**
   
   **Option A: Create a .env file (Recommended)**
   - Create a file named `.env` in your project root directory
   - Add this line to the file:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```
   
   **Option B: Add directly to settings.py**
   - Open `roi_calculator/settings.py`
   - Find the line: `OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')`
   - Replace it with: `OPENAI_API_KEY = 'your_actual_api_key_here'`

3. **Run the server:**
   ```bash
   .\venv\Scripts\python.exe manage.py runserver
   ```

4. **Test the chatbot:**
   - Go to your website (usually http://127.0.0.1:8000)
   - Login to your account
   - Look for the floating robot icon in the bottom-right corner
   - Click it to open the AI assistant!

## 🎉 That's it! Your AI chatbot is ready to use!

### What the chatbot can help with:
- ROI calculation explanations
- Cloud computing cost optimization
- Business metrics and KPIs
- Productivity improvements
- Technical questions about the calculator

### Troubleshooting:
- If you see "OpenAI API key not configured" error, make sure you added your API key correctly
- The chatbot only appears for logged-in users
- Make sure you're using the virtual environment: `.\venv\Scripts\python.exe manage.py runserver`
