# 🛒 Cart Check - WhatsApp Healthy Shopping Assistant

Cart Check helps people make healthier grocery choices by analyzing their shopping cart photos via WhatsApp and providing personalized recommendations based on their health goals.

## 🌟 Features

- **Personalized Profiles**: Set health goals (lower cholesterol, lose weight, etc.) and dietary restrictions (no salt, no sugar, no nuts, etc.)
- **AI-Powered Analysis**: Claude Vision analyzes cart photos and identifies items
- **Smart Recommendations**: Suggests healthier alternatives for problematic items
- **WhatsApp Native**: No app to download - works right in WhatsApp
- **Friendly & Supportive**: Non-judgmental guidance focused on empowerment

## 📱 How It Works

```
User                          Cart Check Bot
  │                                 │
  │  "Hi"                          │
  │ ──────────────────────────────►│
  │                                 │
  │  Welcome! Set your goals...    │
  │ ◄──────────────────────────────│
  │                                 │
  │  "1, 2" (goals)                │
  │ ──────────────────────────────►│
  │                                 │
  │  Great! Any restrictions?      │
  │ ◄──────────────────────────────│
  │                                 │
  │  "1, 2, 3, 4" (restrictions)   │
  │ ──────────────────────────────►│
  │                                 │
  │  ✅ You're all set!            │
  │ ◄──────────────────────────────│
  │                                 │
  │  [Sends cart photo] 📸         │
  │ ──────────────────────────────►│
  │                                 │
  │  🛒 Your Cart Health Report    │
  │  Score: ⭐⭐⭐⭐⭐⭐⭐☆☆☆        │
  │  ✅ Great: Spinach, Lentils    │
  │  🔄 Swap: Kaju Katli → Sapota  │
  │ ◄──────────────────────────────│
```

## 🚀 Setup Instructions

### Prerequisites

1. **Meta Developer Account**: https://developers.facebook.com/
2. **WhatsApp Business Account**: Set up via Meta Business Suite
3. **Anthropic API Key**: https://console.anthropic.com/
4. **Render.com Account**: https://render.com/ (for hosting)

### Step 1: Create Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Select "Business" → "Business"
4. Name your app "Cart Check"
5. In the app dashboard, click "Add Product"
6. Find "WhatsApp" and click "Set Up"

### Step 2: Configure WhatsApp

1. In WhatsApp settings, go to "API Setup"
2. Note your:
   - **Phone Number ID** (e.g., `123456789012345`)
   - **WhatsApp Business Account ID**
3. Generate a **Permanent Access Token**:
   - Go to Business Settings → System Users
   - Create a system user with Admin access
   - Generate a token with `whatsapp_business_messaging` permission

### Step 3: Deploy to Render

1. Push this code to a GitHub repository

2. Go to [Render Dashboard](https://dashboard.render.com/)

3. Click "New" → "Web Service"

4. Connect your GitHub repo

5. Configure:
   - **Name**: `cart-check-bot`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

6. Add Environment Variables:
   ```
   WHATSAPP_TOKEN=your_permanent_access_token
   WHATSAPP_PHONE_ID=your_phone_number_id
   VERIFY_TOKEN=your_custom_verify_token
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

7. Click "Create Web Service"

8. Note your Render URL (e.g., `https://cart-check-bot.onrender.com`)

### Step 4: Configure Webhook

1. Go back to Meta Developer Portal → Your App → WhatsApp → Configuration

2. Click "Edit" next to Webhook

3. Enter:
   - **Callback URL**: `https://cart-check-bot.onrender.com/webhook`
   - **Verify Token**: Same as your `VERIFY_TOKEN` env variable

4. Click "Verify and Save"

5. Under "Webhook Fields", subscribe to:
   - `messages`

### Step 5: Test It!

1. Add the WhatsApp test number to your phone
2. Send "Hi" to start the conversation
3. Complete your profile setup
4. Send a photo of a grocery cart
5. Receive your health analysis!

## 🔧 Local Development

```bash
# Clone the repo
git clone https://github.com/yourusername/cart-check-bot.git
cd cart-check-bot/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your actual values

# Run locally
uvicorn main:app --reload --port 8000

# For webhook testing, use ngrok
ngrok http 8000
# Use the ngrok URL for webhook configuration
```

## 📝 WhatsApp Commands

| Command | Description |
|---------|-------------|
| `hi` / `hello` | Start conversation or restart |
| `reset` | Clear profile and start over |
| `profile` | View your current profile |
| `stats` | See your cart check statistics |
| `help` | Show available commands |
| `[photo]` | Send a cart photo for analysis |

## 🏗️ Architecture

```
┌─────────────────┐
│  WhatsApp User  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ WhatsApp Cloud  │
│      API        │
└────────┬────────┘
         │ webhook
         ▼
┌─────────────────┐
│   FastAPI on    │
│     Render      │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌──────────┐
│Claude │ │ In-Memory│
│Vision │ │ Profiles │
│  API  │ │ (*)      │
└───────┘ └──────────┘

(*) Replace with PostgreSQL for production
```

## 🔮 Future Improvements

- [ ] PostgreSQL database for persistent user profiles
- [ ] Store-specific product database
- [ ] Barcode scanning support
- [ ] Weekly health reports
- [ ] Multi-language support (Hindi, Tamil, etc.)
- [ ] Integration with grocery delivery apps
- [ ] Gamification (streaks, badges)

## 💰 Cost Estimates

| Service | Monthly Cost |
|---------|--------------|
| Render (Starter) | $7 |
| WhatsApp Cloud API | Free (1,000 conversations) |
| Claude API | ~$10-20 (depends on usage) |
| **Total** | **~$17-27/month** |

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## 📄 License

MIT License - feel free to use this for good!

## 🙏 Acknowledgments

- Built with [Claude](https://anthropic.com) by Anthropic
- Powered by [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- Hosted on [Render](https://render.com)

---

**Made with 💚 for healthier lives**
