from flask import Flask, request, Response
import requests
import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

app = Flask(__name__)

# Secrets from environment``
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

# Your own Facebook ID (so it sends only to you)
# Visit: https://developers.facebook.com/tools/explorer/ to get your PSID
YOUR_FACEBOOK_ID = os.environ.get("YOUR_FACEBOOK_ID")  # Add this in Render

@app.route("/", methods=["GET"])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        challenge = request.args.get("hub.challenge")
        return Response(challenge, status=200)
    return Response("Verification token mismatch", status=403)

@app.route("/", methods=["POST"])
def webhook():
    # Optional: reply to messages (not required for daily message)
    data = request.json
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

# 👇 Scheduled job to send "Hello" every day at 8 PM
def schedule_daily_hello():
    timezone = pytz.timezone("Asia/Manila")  # Change to your local timezone
    now = datetime.now(timezone)
    print(f"[{now}] Sending daily hello!")
    send_message(YOUR_FACEBOOK_ID, "Hello! 👋 This is your daily 8PM message.")

# Setup the daily schedule
scheduler = BackgroundScheduler()
scheduler.add_job(schedule_daily_hello, 'cron', hour=20, minute=0, timezone="Asia/Manila")
scheduler.start()

# Run the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
