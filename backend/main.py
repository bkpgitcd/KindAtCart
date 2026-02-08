"""
Cart Check - WhatsApp Bot for Healthy Grocery Shopping
Analyzes cart photos and provides personalized health recommendations
"""

import os
import json
import httpx
import base64
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kind At Cart", description="Healthy grocery shopping assistant")

# Environment variables
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "cartcheck-verify-token")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# In-memory user profiles (replace with database in production)
user_profiles = {}

# User states for conversation flow
user_states = {}

# ============================================
# USER PROFILE MANAGEMENT
# ============================================

class UserProfile(BaseModel):
    phone: str
    name: Optional[str] = None
    health_goals: list[str] = []
    restrictions: list[str] = []
    created_at: str = ""
    cart_checks: int = 0
    items_swapped: int = 0

def get_user_profile(phone: str) -> Optional[UserProfile]:
    return user_profiles.get(phone)

def save_user_profile(profile: UserProfile):
    user_profiles[profile.phone] = profile

def is_profile_complete(profile: UserProfile) -> bool:
    return len(profile.health_goals) > 0 and len(profile.restrictions) > 0

# ============================================
# HEALTH GOALS AND RESTRICTIONS
# ============================================

HEALTH_GOALS = {
    "1": "Lower cholesterol",
    "2": "Lose weight",
    "3": "Manage diabetes",
    "4": "Lower blood pressure",
    "5": "Improve heart health",
    "6": "General wellness"
}

RESTRICTIONS = {
    "1": "No salt",
    "2": "No oil",
    "3": "No sugar",
    "4": "No nuts",
    "5": "No dairy",
    "6": "No gluten",
    "7": "No meat",
    "8": "No eggs"
}

# ============================================
# ALTERNATIVES DATABASE
# ============================================

ALTERNATIVES_DB = [
    {
        "patterns": ["kaju katli", "kaju barfi", "cashew", "badam", "almond sweets", "pista"],
        "flags": ["has_nuts", "has_sugar"],
        "alternative": "Frozen chikoo/sapota or fresh mango",
        "reason": "Naturally sweet, no nuts, heart-healthy fiber"
    },
    {
        "patterns": ["gulab jamun", "jalebi", "rasgulla", "ladoo", "barfi", "mithai"],
        "flags": ["has_sugar", "has_oil"],
        "alternative": "Fresh fruit (mango, papaya, berries)",
        "reason": "Natural sweetness without added sugar or oil"
    },
    {
        "patterns": ["samosa", "pakora", "bhajiya", "fried"],
        "flags": ["has_oil", "has_salt"],
        "alternative": "Baked sweet potato or air-fried vegetables",
        "reason": "Satisfying without the oil, rich in nutrients"
    },
    {
        "patterns": ["bhujia", "namkeen", "mixture", "sev", "chips", "crisps"],
        "flags": ["has_oil", "has_salt", "may_have_nuts"],
        "alternative": "Air-popped popcorn (plain) or roasted chickpeas (no oil)",
        "reason": "Crunchy satisfaction without oil or excess salt"
    },
    {
        "patterns": ["ice cream", "kulfi", "frozen dessert"],
        "flags": ["has_sugar", "has_dairy"],
        "alternative": "Frozen mango or banana chunks (blend for nice cream)",
        "reason": "Creamy, sweet, whole food"
    },
    {
        "patterns": ["cheese", "paneer"],
        "flags": ["has_dairy", "saturated_fat"],
        "alternative": "Tofu or nutritional yeast",
        "reason": "Similar texture, no cholesterol"
    },
    {
        "patterns": ["ghee", "butter", "margarine"],
        "flags": ["has_oil", "saturated_fat"],
        "alternative": "Vegetable broth for cooking, or mashed avocado for spreading",
        "reason": "Flavor without saturated fat"
    },
    {
        "patterns": ["cookies", "biscuits", "cake", "pastry"],
        "flags": ["has_sugar", "has_oil"],
        "alternative": "Homemade oat bites with mashed banana",
        "reason": "Whole food sweetness, no added sugar or oil"
    },
    {
        "patterns": ["soda", "cola", "soft drink", "energy drink"],
        "flags": ["has_sugar"],
        "alternative": "Sparkling water with lemon or fresh lime soda (no sugar)",
        "reason": "Refreshing without the sugar spike"
    },
    {
        "patterns": ["white bread", "naan", "roti maida"],
        "flags": ["refined_carbs"],
        "alternative": "Whole wheat bread or whole grain roti",
        "reason": "More fiber, better for blood sugar"
    },
    {
        "patterns": ["instant noodles", "maggi", "ramen"],
        "flags": ["has_salt", "has_oil", "refined_carbs"],
        "alternative": "Rice noodles with homemade vegetable broth",
        "reason": "Lower sodium, no palm oil"
    },
    {
        "patterns": ["bacon", "sausage", "hot dog", "salami"],
        "flags": ["has_meat", "has_salt", "saturated_fat"],
        "alternative": "Grilled portobello mushrooms or tempeh",
        "reason": "Savory, satisfying, plant-based protein"
    }
]

# ============================================
# WHATSAPP API FUNCTIONS
# ============================================

async def send_whatsapp_message(to: str, message: str):
    """Send a text message via WhatsApp Cloud API"""
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logger.error(f"Failed to send message: {response.text}")
        return response

async def download_whatsapp_media(media_id: str) -> bytes:
    """Download media from WhatsApp"""
    # First, get the media URL
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        media_url = response.json().get("url")
        
        # Download the actual media
        media_response = await client.get(media_url, headers=headers)
        return media_response.content

# ============================================
# CLAUDE VISION ANALYSIS
# ============================================

async def analyze_cart_with_claude(image_base64: str, profile: UserProfile) -> dict:
    """Analyze cart image using Claude Vision API"""
    
    # Build the restriction context
    goals_str = ", ".join(profile.health_goals) if profile.health_goals else "general health"
    restrictions_str = ", ".join(profile.restrictions) if profile.restrictions else "none specified"
    
    prompt = f"""You are a friendly health-conscious grocery shopping assistant called "Cart Check".

Analyze this shopping cart image and identify the food items visible.

USER'S HEALTH PROFILE:
- Health Goals: {goals_str}
- Dietary Restrictions: {restrictions_str}

For each item you can identify, categorize it as:
1. GOOD - Supports their health goals
2. OKAY - Neutral, fine in moderation  
3. RECONSIDER - Conflicts with their goals or restrictions

For RECONSIDER items, suggest a specific healthier alternative they could swap it for.

Respond in this exact JSON format:
{{
    "items_found": [
        {{
            "name": "item name",
            "category": "GOOD" or "OKAY" or "RECONSIDER",
            "reason": "brief reason (only for RECONSIDER items)",
            "alternative": "suggested swap (only for RECONSIDER items)"
        }}
    ],
    "health_score": 7,  // 1-10 based on overall cart healthiness for this user
    "encouragement": "A brief, friendly encouraging message"
}}

Be warm, supportive, and non-judgmental. Focus on empowering healthier choices, not shaming.
If you can't identify items clearly, mention that and provide general guidance."""

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1500,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"Claude API error: {response.text}")
            return None
            
        result = response.json()
        content = result["content"][0]["text"]
        
        # Parse the JSON from Claude's response
        try:
            # Find JSON in the response
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Claude response: {e}")
            return {"error": "Could not analyze cart", "raw": content}

def format_cart_analysis(analysis: dict) -> str:
    """Format the cart analysis into a friendly WhatsApp message"""
    
    if "error" in analysis:
        return "🤔 I had trouble analyzing that image. Could you try taking another photo with better lighting? Make sure the items in your cart are clearly visible!"
    
    items = analysis.get("items_found", [])
    score = analysis.get("health_score", 5)
    encouragement = analysis.get("encouragement", "Keep making healthy choices!")
    
    # Group items by category
    good_items = [i for i in items if i.get("category") == "GOOD"]
    okay_items = [i for i in items if i.get("category") == "OKAY"]
    reconsider_items = [i for i in items if i.get("category") == "RECONSIDER"]
    
    # Build the message
    lines = []
    lines.append(f"🛒 *Your Cart Health Report*")
    lines.append(f"━━━━━━━━━━━━━━━━━")
    lines.append(f"Health Score: {'⭐' * score}{'☆' * (10-score)} ({score}/10)")
    lines.append("")
    
    if good_items:
        lines.append("✅ *GREAT CHOICES:*")
        for item in good_items:
            lines.append(f"  • {item['name']}")
        lines.append("")
    
    if okay_items:
        lines.append("👍 *OKAY IN MODERATION:*")
        for item in okay_items:
            lines.append(f"  • {item['name']}")
        lines.append("")
    
    if reconsider_items:
        lines.append("🔄 *CONSIDER SWAPPING:*")
        for item in reconsider_items:
            lines.append(f"  • *{item['name']}*")
            if item.get("reason"):
                lines.append(f"    _{item['reason']}_")
            if item.get("alternative"):
                lines.append(f"    → Try: {item['alternative']}")
        lines.append("")
    
    lines.append(f"💚 {encouragement}")
    lines.append("")
    lines.append("_Send another photo anytime!_")
    
    return "\n".join(lines)

# ============================================
# CONVERSATION HANDLERS
# ============================================

async def handle_new_user(phone: str, name: str):
    """Handle a new user starting the conversation"""
    profile = UserProfile(
        phone=phone,
        name=name,
        created_at=datetime.now().isoformat()
    )
    save_user_profile(profile)
    user_states[phone] = "awaiting_goals"
    
    welcome_msg = f"""👋 *Welcome to Cart Check, {name}!*

I help you make healthier grocery choices by checking your cart before checkout.

Let's set up your profile (takes 30 seconds):

*What are your health goals?*
Reply with the numbers (e.g., "1, 2"):

1️⃣ Lower cholesterol
2️⃣ Lose weight
3️⃣ Manage diabetes
4️⃣ Lower blood pressure
5️⃣ Improve heart health
6️⃣ General wellness"""
    
    await send_whatsapp_message(phone, welcome_msg)

async def handle_goals_response(phone: str, message: str):
    """Handle user's health goals selection"""
    profile = get_user_profile(phone)
    
    # Parse numbers from message
    numbers = [n.strip() for n in message.replace(",", " ").split() if n.strip().isdigit()]
    selected_goals = [HEALTH_GOALS[n] for n in numbers if n in HEALTH_GOALS]
    
    if not selected_goals:
        await send_whatsapp_message(phone, "Please reply with numbers (e.g., '1, 2') to select your health goals.")
        return
    
    profile.health_goals = selected_goals
    save_user_profile(profile)
    user_states[phone] = "awaiting_restrictions"
    
    restrictions_msg = f"""Great! You selected: {', '.join(selected_goals)}

*Now, any foods you need to avoid?*
Reply with numbers (e.g., "1, 2, 3"):

1️⃣ No salt
2️⃣ No oil
3️⃣ No sugar
4️⃣ No nuts
5️⃣ No dairy
6️⃣ No gluten
7️⃣ No meat
8️⃣ No eggs

Or reply "none" if no restrictions."""
    
    await send_whatsapp_message(phone, restrictions_msg)

async def handle_restrictions_response(phone: str, message: str):
    """Handle user's dietary restrictions selection"""
    profile = get_user_profile(phone)
    
    if message.lower().strip() == "none":
        selected_restrictions = []
    else:
        numbers = [n.strip() for n in message.replace(",", " ").split() if n.strip().isdigit()]
        selected_restrictions = [RESTRICTIONS[n] for n in numbers if n in RESTRICTIONS]
    
    profile.restrictions = selected_restrictions
    save_user_profile(profile)
    user_states[phone] = "ready"
    
    restrictions_text = ', '.join(selected_restrictions) if selected_restrictions else "None"
    
    ready_msg = f"""✅ *You're all set!*

*Your Profile:*
📎 Goals: {', '.join(profile.health_goals)}
🚫 Avoid: {restrictions_text}

━━━━━━━━━━━━━━━━━

*How to use Cart Check:*
📸 Take a photo of your grocery cart
📤 Send it to me
📋 Get instant health feedback + swap suggestions

Next time you're at the store, just send me a cart photo!

🛒 Happy healthy shopping! 💚"""
    
    await send_whatsapp_message(phone, ready_msg)

async def handle_cart_photo(phone: str, media_id: str):
    """Handle a cart photo submission"""
    profile = get_user_profile(phone)
    
    if not profile or not is_profile_complete(profile):
        await send_whatsapp_message(phone, "Let's set up your profile first! What are your health goals?\n\nReply with numbers:\n1. Lower cholesterol\n2. Lose weight\n3. Manage diabetes\n4. Lower blood pressure\n5. Improve heart health\n6. General wellness")
        user_states[phone] = "awaiting_goals"
        return
    
    # Send acknowledgment
    await send_whatsapp_message(phone, "🔍 Analyzing your cart... This takes about 10 seconds.")
    
    try:
        # Download the image
        image_bytes = await download_whatsapp_media(media_id)
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        
        # Analyze with Claude
        analysis = await analyze_cart_with_claude(image_base64, profile)
        
        # Format and send response
        response_msg = format_cart_analysis(analysis)
        await send_whatsapp_message(phone, response_msg)
        
        # Update profile stats
        profile.cart_checks += 1
        reconsider_count = len([i for i in analysis.get("items_found", []) if i.get("category") == "RECONSIDER"])
        profile.items_swapped += reconsider_count
        save_user_profile(profile)
        
    except Exception as e:
        logger.error(f"Error processing cart photo: {e}")
        await send_whatsapp_message(phone, "😅 Something went wrong analyzing your cart. Please try again!")

async def handle_text_message(phone: str, message: str, name: str):
    """Handle incoming text messages based on user state"""
    profile = get_user_profile(phone)
    state = user_states.get(phone, "new")
    
    # Check for reset/restart commands
    if message.lower().strip() in ["reset", "restart", "start over", "new profile"]:
        if phone in user_profiles:
            del user_profiles[phone]
        if phone in user_states:
            del user_states[phone]
        await handle_new_user(phone, name)
        return
    
    # Check for help command
    if message.lower().strip() in ["help", "?"]:
        help_msg = """*Cart Check Help*

📸 *Check your cart:* Send a photo of your grocery cart

🔄 *Update profile:* Type "reset" to start over

📊 *Your stats:* Type "stats" to see your progress

💬 *Commands:*
• "reset" - Start fresh
• "stats" - Your stats
• "profile" - View your profile
• "help" - This message"""
        await send_whatsapp_message(phone, help_msg)
        return
    
    # Check for stats command
    if message.lower().strip() == "stats":
        if profile:
            stats_msg = f"""📊 *Your Cart Check Stats*

🛒 Carts checked: {profile.cart_checks}
🔄 Items reconsidered: {profile.items_swapped}
📅 Member since: {profile.created_at[:10] if profile.created_at else 'Today'}

Keep making healthy choices! 💚"""
        else:
            stats_msg = "You haven't set up your profile yet. Send 'hi' to get started!"
        await send_whatsapp_message(phone, stats_msg)
        return
    
    # Check for profile command
    if message.lower().strip() == "profile":
        if profile and is_profile_complete(profile):
            restrictions_text = ', '.join(profile.restrictions) if profile.restrictions else "None"
            profile_msg = f"""👤 *Your Profile*

📎 Goals: {', '.join(profile.health_goals)}
🚫 Avoid: {restrictions_text}

Type "reset" to update your profile."""
        else:
            profile_msg = "You haven't completed your profile yet. Send 'hi' to get started!"
        await send_whatsapp_message(phone, profile_msg)
        return
    
    # Handle based on state
    if state == "new" or not profile:
        await handle_new_user(phone, name)
    elif state == "awaiting_goals":
        await handle_goals_response(phone, message)
    elif state == "awaiting_restrictions":
        await handle_restrictions_response(phone, message)
    elif state == "ready":
        # User is set up but sent text instead of photo
        await send_whatsapp_message(phone, "📸 Send me a photo of your grocery cart and I'll check it for you!\n\nOr type 'help' for more options.")

# ============================================
# WEBHOOK ENDPOINTS
# ============================================

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Cart Check Bot"}

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Webhook verification for WhatsApp"""
    logger.info(f"Webhook verification: mode={hub_mode}, token={hub_verify_token}")
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(content=hub_challenge)
    
    logger.warning("Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Handle incoming WhatsApp messages"""
    body = await request.json()
    logger.info(f"Received webhook: {json.dumps(body, indent=2)}")
    
    try:
        # Parse the webhook payload
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        contacts = value.get("contacts", [])
        
        if not messages:
            return {"status": "ok"}
        
        message = messages[0]
        phone = message.get("from")
        msg_type = message.get("type")
        
        # Get sender name
        name = "Friend"
        if contacts:
            name = contacts[0].get("profile", {}).get("name", "Friend")
        
        logger.info(f"Message from {phone} ({name}): type={msg_type}")
        
        # Handle different message types
        if msg_type == "text":
            text = message.get("text", {}).get("body", "")
            await handle_text_message(phone, text, name)
            
        elif msg_type == "image":
            media_id = message.get("image", {}).get("id")
            if media_id:
                await handle_cart_photo(phone, media_id)
            else:
                await send_whatsapp_message(phone, "I couldn't process that image. Please try again!")
        
        else:
            await send_whatsapp_message(phone, "Please send me a text message or a photo of your grocery cart! 📸")
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
    
    return {"status": "ok"}

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
