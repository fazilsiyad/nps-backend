import os
from twilio.rest import Client

# Load environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886") # Twilio Sandbox Number

def get_twilio_client():
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return None

def send_whatsapp_message(to_number: str, message: str) -> bool:
    """
    Sends a WhatsApp message using Twilio's WhatsApp API.
    Ensure `to_number` is formatted as "whatsapp:+91..."
    """
    client = get_twilio_client()
    
    # Prefix number with whatsapp: if not present
    if not to_number.startswith("whatsapp:"):
        # simple sanitization or logic depending on DB content
        to_number = f"whatsapp:{to_number}"

    if client:
        try:
            msg = client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=message,
                to=to_number
            )
            print(f"WhatsApp message sent! SID: {msg.sid}")
            return True
        except Exception as e:
            print(f"Failed to send WhatsApp message: {e}")
            return False
    else:
        # Mock behavior for local testing without credentials
        print("\n--- MOCK WHATSAPP MESSAGE ---")
        print(f"To: {to_number}")
        print(f"Body: {message}")
        print("-----------------------------\n")
        return True
