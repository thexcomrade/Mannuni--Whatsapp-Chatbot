"""
Message Parser for Mannuni Chatbot
created by thexcomrade
"""

import re
from datetime import datetime
import logging

logger = logging.getLogger('Mannuni.Parser')

class MessageParser:
    @staticmethod
    def extract_style_request(text):
        """Extract response style from message"""
        try:
            if 'style:' in text.lower():
                parts = re.split(r'style:', text, flags=re.IGNORECASE)
                return parts[1].strip() if len(parts) > 1 else text
            return None
        except Exception as e:
            logger.error(f"Style extraction failed: {str(e)}")
            return None

    @staticmethod
    def format_response(text, style=None):
        """Format response based on style"""
        styles = {
            'short': lambda t: f"🔹 {t.split('.')[0]}.",  # First sentence
            'detailed': lambda t: f"📝 DETAILED ANSWER:\n\n{t}",
            'steps': lambda t: f"🔄 STEP-BY-STEP:\n\n1. {t.replace('. ', '.\n2. ')}",
            'simple': lambda t: f"👶 SIMPLE EXPLANATION:\n\n{t}",
            'tech': lambda t: f"⚙️ TECHNICAL ANSWER:\n\n{t}"
        }
        return styles.get(style, lambda t: t)(text)

    @staticmethod
    def add_timestamp(text):
        """Add timestamp to message"""
        return f"{text}\n\n[{datetime.now().strftime('%H:%M %d/%m/%Y')}]"