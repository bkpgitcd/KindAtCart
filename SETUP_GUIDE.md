# Cart Check - WhatsApp Setup Guide
## Step-by-Step Instructions for Meta WhatsApp Business API

---

## PART 1: META DEVELOPER SETUP (30 minutes)

### Step 1.1: Create Meta Developer Account

1. Go to: https://developers.facebook.com/
2. Click "Get Started" or "Log In"
3. Log in with your Facebook account
4. Accept the developer terms

### Step 1.2: Create a New App

1. Click "My Apps" in the top right
2. Click "Create App"
3. Select app type: **"Business"**
4. Click "Next"
5. Enter app details:
   - **App Name**: Cart Check
   - **App Contact Email**: your email
   - **Business Account**: Create one if needed or select existing
6. Click "Create App"

### Step 1.3: Add WhatsApp Product

1. In your app dashboard, scroll to "Add products to your app"
2. Find **"WhatsApp"** and click **"Set Up"**
3. You'll be taken to WhatsApp Getting Started page

### Step 1.4: Get Your Credentials

On the WhatsApp > API Setup page, note down:

```
Phone Number ID: ____________________
(looks like: 123456789012345)

WhatsApp Business Account ID: ____________________
(looks like: 987654321098765)
```

### Step 1.5: Create Permanent Access Token

The default token expires in 24 hours. Create a permanent one:

1. Go to: Business Settings (business.facebook.com)
2. Click "Users" → "System Users"
3. Click "Add" to create a new system user:
   - Name: Cart Check Bot
   - Role: Admin
4. Click "Add Assets":
   - Select "Apps"
   - Find "Cart Check" and give "Full Control"
5. Click "Generate New Token":
   - Select your App (Cart Check)
   - Select permissions:
     - ✅ whatsapp_business_messaging
     - ✅ whatsapp_business_management
   - Click "Generate Token"
6. **COPY AND SAVE THIS TOKEN** - you won't see it again!

```
Access Token: ____________________
(starts with: EAA...)
```

---

## PART 2: DEPLOY TO RENDER (15 minutes)

### Step 2.1: Push Code to GitHub

1. Create a new GitHub repository named `cart-check-bot`
2. Upload the cart-check-bot folder contents to it
3. Make sure the structure is:
   ```
   cart-check-bot/
   ├── README.md
   └── backend/
       ├── main.py
       ├── requirements.txt
       └── .env.example
   ```

### Step 2.2: Create Render Web Service

1. Go to: https://dashboard.render.com/
2. Sign up / Log in (can use GitHub)
3. Click "New" → "Web Service"
4. Connect your GitHub account if needed
5. Select your `cart-check-bot` repository
6. Configure the service:

   | Setting | Value |
   |---------|-------|
   | Name | `cart-check-bot` |
   | Region | Oregon (US West) or nearest to you |
   | Branch | `main` |
   | Root Directory | `backend` |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT` |
   | Instance Type | Starter ($7/month) or Free (sleeps) |

### Step 2.3: Add Environment Variables

In Render, go to "Environment" tab and add:

| Key | Value |
|-----|-------|
| `WHATSAPP_TOKEN` | Your permanent access token (EAA...) |
| `WHATSAPP_PHONE_ID` | Your Phone Number ID |
| `VERIFY_TOKEN` | Create your own: e.g., `cartcheck-secret-2024` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

### Step 2.4: Deploy

1. Click "Create Web Service"
2. Wait for deployment (2-3 minutes)
3. Note your URL:

```
Render URL: https://cart-check-bot.onrender.com
```

4. Test it's working: Visit `https://cart-check-bot.onrender.com/` 
   - Should see: `{"status":"healthy","service":"Cart Check Bot"}`

---

## PART 3: CONFIGURE WEBHOOK (10 minutes)

### Step 3.1: Set Up Webhook in Meta

1. Go back to Meta Developer Portal
2. Navigate to: Your App → WhatsApp → Configuration
3. In the "Webhook" section, click "Edit"
4. Enter:
   - **Callback URL**: `https://cart-check-bot.onrender.com/webhook`
   - **Verify Token**: Same as your `VERIFY_TOKEN` in Render (e.g., `cartcheck-secret-2024`)
5. Click "Verify and Save"
   - If successful, you'll see a green checkmark
   - If failed, check your Render logs for errors

### Step 3.2: Subscribe to Messages

1. Still in WhatsApp → Configuration
2. Under "Webhook fields", click "Manage"
3. Subscribe to:
   - ✅ `messages`
4. Click "Done"

---

## PART 4: ADD TEST PHONE NUMBER (5 minutes)

### Step 4.1: Add Your Phone for Testing

1. In WhatsApp → API Setup
2. Find "To" field under "Send and receive messages"
3. Click "Manage phone number list"
4. Click "Add phone number"
5. Enter your phone number
6. Verify with the code sent to your phone

### Step 4.2: Test the Bot!

1. Open WhatsApp on your phone
2. Start a new chat with the test phone number shown in Meta
3. Send: **"Hi"**
4. You should receive the welcome message!

---

## PART 5: GO LIVE (Optional - For Public Use)

To use Cart Check with any phone number (not just test numbers):

### Step 5.1: Business Verification

1. Go to: Meta Business Suite → Settings → Business Verification
2. Submit your business documents
3. Wait for approval (1-3 days)

### Step 5.2: Add a Real Phone Number

1. In WhatsApp > API Setup
2. Click "Add phone number"
3. Choose to use:
   - A new number (Meta can provide)
   - Your existing number (will disconnect from personal WhatsApp)

### Step 5.3: Submit for Messaging Approval

1. Go to: WhatsApp → Overview → Insights
2. Request increased messaging limits
3. Start with 1,000 conversations/day

---

## TROUBLESHOOTING

### Webhook verification fails
- Check VERIFY_TOKEN matches exactly in both Render and Meta
- Ensure Render service is running (not sleeping)
- Check Render logs for errors

### Messages not being received
- Verify webhook is subscribed to `messages`
- Check Render logs for incoming webhooks
- Ensure phone number is added to test list

### Claude API errors
- Verify ANTHROPIC_API_KEY is correct
- Check you have API credits
- Look at Render logs for specific error

### WhatsApp API errors
- Verify WHATSAPP_TOKEN hasn't expired
- Check WHATSAPP_PHONE_ID is correct
- Ensure test number is verified

---

## YOUR CREDENTIALS CHECKLIST

Fill this in as you go:

```
[ ] Meta App ID: ____________________
[ ] Phone Number ID: ____________________
[ ] WhatsApp Business Account ID: ____________________
[ ] Permanent Access Token: ____________________
[ ] Verify Token (you create): ____________________
[ ] Render URL: ____________________
[ ] Anthropic API Key: ____________________
```

---

## COSTS SUMMARY

| Item | Cost |
|------|------|
| Meta Developer Account | Free |
| WhatsApp Cloud API | Free (1,000 conversations/month) |
| Render Starter | $7/month |
| Anthropic API | ~$0.003 per cart analysis |
| **Total to Start** | **~$7/month** |

---

## NEXT STEPS

Once everything is working:

1. ✅ Test with your own cart photos
2. ✅ Share with friends and family
3. ✅ Gather feedback
4. ✅ Add more alternatives to the database
5. ✅ Consider adding database for persistent profiles

---

**Questions?** Check the README.md or the Meta WhatsApp documentation:
https://developers.facebook.com/docs/whatsapp/cloud-api/get-started

**You've got this! 💚🛒**
