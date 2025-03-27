from flask import Flask, render_template, request, redirect, url_for
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Twilio Client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
test_phone_number = "+17778889999"

# OpenAI Client
openai.api_key = OPENAI_API_KEY

# DATA STORE
meals = []
posts = []

# --- AI / GPT-4 --- 
def generate_nudge(user_context):
    prompt = f"""
    You are a behavioral science-based AI coach for healthy eating. The user context is:
    {user_context}

    Write a short, engaging SMS that nudges the user toward a healthy decision. Keep it 1 sentence, friendly, and no longer than 160 characters.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a behavioral science-based health coach."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=60
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"AI generation failed: {e}")
        return "Remember: one small healthy choice makes a big difference! 💪"

# --- PAGE ROUTES --- 
@app.route('/')
def landing_page():
    return render_template('index.html')

@app.route('/sms-setup')
def sms_setup():
    return render_template('sms_setup.html')

@app.route('/meal-tracking')
def meal_tracking():
    return render_template('meal_tracking.html', meals=meals)

@app.route('/community')
def community():
    return render_template('community.html', posts=posts)

# --- API ---
# Web App
@app.route('/signup', methods=['POST'])
def signup():
    phone = request.form.get('phone')
    try:
        message = twilio_client.messages.create(
            body="Welcome to Eatopia! You'll start receiving healthy eating nudges soon.",
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        print(f"Sent SMS to {phone}: {message.sid}")
    except Exception as e:
        print(f"Error sending SMS: {e}")
    return redirect(url_for('sms_setup'))

@app.route('/save-sms-preferences', methods=['POST'])
def save_sms_preferences():
    preferences = request.form.to_dict()
    print(f"User SMS preferences: {preferences}")
    return redirect(url_for('meal_tracking'))

@app.route('/post-community', methods=['POST'])
def post_community():
    title = request.form.get('title')
    content = request.form.get('content')
    posts.append({'title': title, 'content': content, 'author': 'Anonymous'})
    return redirect(url_for('community'))

@app.route('/request-review', methods=['POST'])
def request_review():
    print("AI review requested for meal history")
    return redirect(url_for('meal_tracking'))

# SMS / Twilio
@app.route("/sms", methods=['POST'])
def sms_reply():
    incoming_msg = request.form.get('Body')
    media_url = request.form.get('MediaUrl0')
    response = MessagingResponse()

    if media_url:
        meals.append({
            'image_url': media_url,
            'timestamp': 'Just now',
            'ai_insight': 'Thanks for sharing! We\'ll analyze your meal soon.'
        })
        response.message("📸 Meal photo received! We'll send insights soon.")
    elif incoming_msg.lower() == "review":
        response.message("🧠 Reviewing your meals... We'll text you insights shortly.")
    else:
        user_context = {
            "habit": "general health",
            "goal": "nudge user toward a better choice",
            "time": "now",
        }
        # nudge = generate_nudge(user_context)
        nudge = "Hello from Eatopia. Let's meet your weekly goal."
        response.message(nudge)

    return str(response)

@app.route("/send-test", methods=["GET"])
def send_test_sms():
    message = twilio_client.messages.create(
        body="👋 Hello from Eatopia test route!",
        from_=TWILIO_PHONE_NUMBER,
        to=test_phone_number
    )
    return f"Sent message with SID: {message.sid}"

if __name__ == '__main__':
    app.run(debug=True)
