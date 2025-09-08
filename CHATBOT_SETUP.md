# AI Chatbot Setup Instructions

## Overview
This Django application now includes an AI-powered chatbot that appears as a floating icon for authenticated users. The chatbot uses OpenAI's GPT-3.5-turbo model to provide assistance with ROI calculations, cloud optimization, and general questions about the calculator.

## Features
- **Floating Chatbot Icon**: Appears in the bottom-right corner for logged-in users
- **AI-Powered Responses**: Uses OpenAI's GPT-3.5-turbo model
- **Context-Aware**: Specialized for ROI calculator assistance
- **Real-time Chat**: Smooth typing indicators and message animations
- **Mobile Responsive**: Works on all device sizes
- **Secure**: Only available to authenticated users

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure OpenAI API Key

#### Option A: Environment Variable (Recommended)
Create a `.env` file in your project root:
```bash
# .env file
OPENAI_API_KEY=your_openai_api_key_here
```

#### Option B: Direct Configuration
Add your API key directly to `roi_calculator/settings.py`:
```python
OPENAI_API_KEY = 'your_openai_api_key_here'
```

### 3. Get OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in to your account
3. Create a new API key
4. Copy the key and add it to your configuration

### 4. Run the Application
```bash
python manage.py runserver
```

## Usage

### For Users
1. **Login** to the application
2. **Look for the floating robot icon** in the bottom-right corner
3. **Click the icon** to open the chatbot
4. **Type your questions** about ROI calculations, cloud optimization, etc.
5. **Get AI-powered responses** tailored to your needs

### For Developers

#### Chatbot API Endpoint
- **URL**: `/dashboard/chatbot/api/`
- **Method**: POST
- **Authentication**: Required (login_required)
- **Request Body**: `{"message": "your question here"}`
- **Response**: `{"success": true, "response": "AI response", "timestamp": "..."}`

#### Customization
You can customize the chatbot by modifying:
- **System Prompt**: In `calculator/views.py` (chatbot_api function)
- **Styling**: In `templates/base.html` (chatbot CSS)
- **Behavior**: In `templates/base.html` (JavaScript functions)

## Security Notes
- The chatbot is only available to authenticated users
- API calls are made server-side to protect your OpenAI API key
- CSRF protection is enabled for all requests
- Input validation is performed on all messages

## Troubleshooting

### Common Issues

1. **"OpenAI API key not configured" error**
   - Ensure your API key is properly set in the environment or settings
   - Check that the `.env` file is in the correct location

2. **Chatbot not appearing**
   - Make sure you're logged in
   - Check browser console for JavaScript errors
   - Verify the chatbot HTML is being rendered

3. **API calls failing**
   - Check your OpenAI API key is valid
   - Ensure you have sufficient API credits
   - Check network connectivity

### Debug Mode
To debug chatbot issues, check the browser console and Django logs for error messages.

## Cost Considerations
- OpenAI API calls are charged per token
- GPT-3.5-turbo is cost-effective for most use cases
- Consider implementing rate limiting for production use
- Monitor your OpenAI usage dashboard

## Future Enhancements
- Conversation history storage
- Multiple language support
- Custom training for domain-specific responses
- Integration with user's calculation history
- Voice input/output capabilities
