"""
API Connectors for Mannuni Chatbot
created by thexcomrade
"""

import os
import openai
from twilio.rest import Client
from dotenv import load_dotenv
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger('Mannuni.API')

class OpenAIConnector:
    def __init__(self):
        load_dotenv(Path(r"D:\MANNUNI\.env"))
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
    def generate_text(self, messages, model="gpt-4", max_tokens=1500):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI Error: {str(e)}")
            raise

class TwilioConnector:
    def __init__(self):
        load_dotenv(Path(r"D:\MANNUNI\.env"))
        self.client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
    
    def send_whatsapp(self, to, body):
        try:
            message = self.client.messages.create(
                body=body,
                from_=os.getenv('TWILIO_WHATSAPP_NUMBER'),
                to=f"whatsapp:{to}"
            )
            return message.sid
        except Exception as e:
            logger.error(f"Twilio Error: {str(e)}")
            raise