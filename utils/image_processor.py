"""
Image Processor for Mannuni Chatbot
created by thexcomrade
"""

from PIL import Image
import io
import base64
import requests
from pathlib import Path
import logging
from datetime import datetime  # Added missing import

logger = logging.getLogger('Mannuni.Image')

class ImageProcessor:
    def __init__(self):
        self.upload_dir = Path(r"D:\MANNUNI\static\img\uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)  # Added parents=True for full path creation

    def download_image(self, url, timeout=10):
        """Download image from URL with error handling"""
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Validate image content
            if not response.headers.get('Content-Type', '').startswith('image/'):
                raise ValueError("URL does not point to an image")
                
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Image download failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during download: {str(e)}")
            raise

    def save_image(self, image_data, filename=None):
        """Save image data to local storage"""
        try:
            # Validate image data
            if not image_data or len(image_data) == 0:
                raise ValueError("Empty image data provided")
                
            # Generate filename if not provided
            if not filename:
                timestamp = int(datetime.now().timestamp())
                filename = f"upload_{timestamp}.jpg"
            
            # Ensure valid filename
            filename = filename.replace(' ', '_').lower()
            save_path = self.upload_dir / filename
            
            # Save the image
            with open(save_path, 'wb') as f:
                f.write(image_data)
            
            # Return relative path for web access
            return str(save_path.relative_to(Path(r"D:\MANNUNI\static")))
            
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            raise

    def prepare_for_ai(self, image_data):
        """Prepare image for AI processing (base64 encoding)"""
        try:
            # Validate image data
            if not image_data or len(image_data) == 0:
                raise ValueError("Empty image data provided")
                
            # Open and validate image
            img = Image.open(io.BytesIO(image_data))
            img.verify()  # Verify image integrity
            
            # Convert to JPEG base64
            buffered = io.BytesIO()
            img = Image.open(io.BytesIO(image_data))  # Reopen after verify
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(buffered, format="JPEG", quality=85)
            
            return base64.b64encode(buffered.getvalue()).decode()
            
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            raise

    def cleanup_old_files(self, max_age_days=7):
        """Clean up files older than specified days"""
        try:
            now = datetime.now()
            for file in self.upload_dir.glob('*'):
                if file.is_file():
                    file_age = now - datetime.fromtimestamp(file.stat().st_mtime)
                    if file_age.days > max_age_days:
                        file.unlink()
                        logger.info(f"Deleted old file: {file.name}")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")