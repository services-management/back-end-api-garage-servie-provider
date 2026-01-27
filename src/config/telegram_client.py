import httpx
from src.config.database import settings
from typing import Optional
class TelegramClient:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, chat_id: int, text: str,parse_mode: str = "Markdown"):
        if not self.token:
            print("⚠️ Telegram Token is missing! Check your .env file.")
            return
            
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id, 
            "text": text, 
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"Telegram API Error: {e.response.text}")
            except Exception as e:
                print(f"Connection Error: {e}")

    async def send_document(self, chat_id: int, document_url: str, caption: Optional[str] = None):
        """Sends a PDF or file from an S3/MinIO URL to a Telegram chat."""
        if not self.token:
            return
            
        url = f"{self.base_url}/sendDocument"
        payload = {
            "chat_id": chat_id,
            "document": document_url, # Telegram fetches this link directly
            "caption": caption
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"Telegram Document Error: {e.response.text}")

# Initialize ONE instance to be used everywhere
telegram_client = TelegramClient()