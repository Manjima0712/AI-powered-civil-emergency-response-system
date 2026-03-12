import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twilio credentials from environment
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')
TO_NUMBER = os.getenv('TEST_TO_NUMBER')

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Send Test SMS
try:
    message = client.messages.create(
        body="This is a test notification from your Emergency Response System.",
        from_=TWILIO_FROM_NUMBER,
        to=TO_NUMBER
    )
    print(f"SMS sent successfully! Message SID: {message.sid}")
except Exception as e:
    print(f"Failed to send SMS: {str(e)}")