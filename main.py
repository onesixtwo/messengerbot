from flask import Flask, request, Response
import requests
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

app = Flask(__name__)

# Secrets from environment``
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

# File to store opted-in users
USERS_FILE = "opted_in_users.json"

def load_opted_in_users():
    """Load the list of users who have opted in for streak reminders"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading users: {e}")
        return []

def save_opted_in_users(users):
    """Save the list of users who have opted in for streak reminders"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)
    except Exception as e:
        print(f"Error saving users: {e}")

def add_user_to_reminders(sender_id):
    """Add a user to the streak reminder list"""
    users = load_opted_in_users()
    if sender_id not in users:
        users.append(sender_id)
        save_opted_in_users(users)
        print(f"Added user {sender_id} to streak reminders")
        return True
    return False

@app.route("/", methods=["GET"])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        challenge = request.args.get("hub.challenge")
        return Response(challenge, status=200)
    return Response("Verification token mismatch", status=403)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    
    # Handle incoming messages
    if data and data.get("object") == "page":
        for entry in data.get("entry", []):
            if entry and "messaging" in entry:
                for messaging_event in entry.get("messaging", []):
                    if messaging_event and messaging_event.get("message"):
                        sender_id = messaging_event["sender"]["id"]
                        message_text = messaging_event["message"].get("text", "").lower()
                        
                        # Check for "remind streak" command
                        if "remind streak" in message_text:
                            # Add user to reminder list
                            is_new_user = add_user_to_reminders(sender_id)
                            
                            if is_new_user:
                                send_message(sender_id, "✅ Streak reminder activated! You'll receive a daily reminder at 8 PM.")
                            else:
                                send_message(sender_id, "✅ You're already signed up for streak reminders! You'll receive your daily reminder at 8 PM.")
                            
                            print(f"Streak reminder activated for user: {sender_id}")
    
    return Response("ok", status=200)

def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v18.0/me/messages"
    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    response = requests.post(url, params=params, headers=headers, json=data)
    if response.status_code != 200:
        print("Error sending message:", response.text)

# 👇 Scheduled job to send streak reminder every day at 8 PM to all opted-in users
def schedule_daily_streak_reminder():
    timezone = pytz.timezone("Asia/Manila")  # Change to your local timezone
    now = datetime.now(timezone)
    print(f"[{now}] Sending daily streak reminders to all users!")
    
    # Load all opted-in users
    users = load_opted_in_users()
    
    if not users:
        print("No users opted in for streak reminders")
        return
    
    # Send streak reminder to all opted-in users
    success_count = 0
    for user_id in users:
        try:
            send_message(user_id, "🔥 Streak reminder! Don't break your streak today!")
            success_count += 1
            print(f"Sent streak reminder to user: {user_id}")
        except Exception as e:
            print(f"Failed to send reminder to user {user_id}: {e}")
    
    print(f"✅ Sent streak reminders to {success_count}/{len(users)} users")

# Setup the daily schedule
scheduler = BackgroundScheduler()
scheduler.add_job(schedule_daily_streak_reminder, 'cron', hour=20, minute=0, timezone="Asia/Manila")
scheduler.start()

# Run the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
