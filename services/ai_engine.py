import os
import json
from google import genai
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Load API key securely
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Prompt Template for classification
CLASSIFICATION_PROMPT = """
You are an expert AI Support Assistant for the National Pension System (NPS) in India.
Your task is to analyze support tickets and extract metadata AND generate the conversational response UI in JSON format.

## Classifications Guidelines
1. 'department': Select exactly one:
   - "CRA Operations" (PRAN activation, generic updates)
   - "Contribution Processing" (Delayed or missing contributions)
   - "Banking & Settlement" (Bank account issues, auto debit failures)
   - "KYC & Identity" (Aadhaar/PAN mismatch, name changes)
   - "Pension Fund Manager" (Investment changes, NAV queries)
   - "Grievance Cell" (Withdrawal delays, complaints)
   - "IT Support" (Login failure, portal errors)

2. 'urgency': Select exactly one:
   - "Low" (General queries, informational)
   - "Medium" (Updates, normal process delays)
   - "High" (Login issues, withdrawal delays)
   - "Critical" (Payment failures, account blocks)
   - "Risk" (Suspicious activity, fraud)

3. 'auto_resolve': boolean (true/false)
   - Set true if the issue is a standard query.
   - Set false if human intervention is required.

4. 'risk': boolean (true/false)
   - Set true ONLY if there is suspicion of fraud (panic language, unauthorized access).

5. 'sentiment_score': float (0.0 angry to 1.0 happy)

## UI Output Formatting Rules
You MUST also generate the Agentic Chat UI payload.
1. "answer": <your conversational response to the user>
2. "isResolved": <boolean — true when providing an FAQ answer that may resolve the issue>
3. "shouldFile": <boolean — true ONLY when the user explicitly confirms they want to file>

ACTION BUTTONS — "actions" array (optional):
Each action is: {{ "label": "<button text>", "type": "<reply|navigate|overlay>", "value": "<text to send / route>", "variant": "<default|outline|destructive>" }}
- When asking "Shall I file this grievance?", include "Yes, file it" and "No, add more" buttons.

SUGGESTIONS — "suggestions" array (optional):
- 2-4 short phrases the user might want to ask next

RICH CONTENT — "richContent" object (optional):
Use this to show structured data inline. Types: "fund-card", "comparison-table", "status-tracker", "info-card", "faq-list", "form-collector".

OVERLAY — "overlay" object (optional):
Same structure as richContent, shown as a modal.

Respond ONLY with valid JSON, structured exactly as follows:
{{
  "department": "IT Support",
  "urgency": "High",
  "auto_resolve": true,
  "risk": false,
  "sentiment_score": 0.4,
  "answer": "Here is how to download your receipt...",
  "isResolved": true,
  "shouldFile": false,
  "actions": [
    {{ "label": "Yes, resolved", "type": "reply", "value": "Yes, that resolved my issue", "variant": "outline" }},
    {{ "label": "No, file grievance", "type": "reply", "value": "No, I want to file a formal grievance", "variant": "default" }}
  ],
  "suggestions": ["Check contribution status", "Update nominee details"],
  "richContent": null,
  "overlay": null
}}

Ticket Description:
"{description}"
"""

def classify_ticket(description: str) -> Dict[str, Any]:
    """
    Calls the Gemini API to classify a ticket and returns a structured JSON dictionary.
    Includes basic retry logic via SDK configuration.
    """
    prompt = CLASSIFICATION_PROMPT.format(description=description)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
                system_instruction="You are a helpful JSON data extraction bot."
            )
        )
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Error calling AI classification: {e}")
        # Safe default fallback in case of AI outage
        return {
            "department": "IT Support",
            "urgency": "Medium",
            "auto_resolve": False,
            "risk": False,
            "sentiment_score": 0.5,
            "answer": "Sorry, I am currently facing technical difficulties parsing this ticket. We have routed it to human support.",
            "isResolved": False,
            "shouldFile": True,
            "actions": [],
            "suggestions": [],
            "richContent": None,
            "overlay": None
        }

def generate_auto_resolve_message(ticket_description: str) -> str:
    """
    Generates step-by-step guidance for auto-resolvable tickets.
    """
    prompt = f"""
    The user submitted this query to NPS: "{ticket_description}".
    Generate a friendly, step-by-step guide to resolve this issue automatically.
    Keep the message concise and formatted for WhatsApp.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=300,
                system_instruction="You are an NPS Auto-Resolution Assistant."
            )
        )
        return response.text.strip()
    except Exception as e:
        return "We received your request. Please visit the eNPS portal to proceed."
