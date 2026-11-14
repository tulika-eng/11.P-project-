
import requests
from telegram_config import BOT_TOKEN, CHAT_ID

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": "Trusted Door connected successfully!"
    },
    timeout=15
)

if response.ok and response.json().get("ok"):
    print("Message sent successfully!")
else:
    print("Telegram error:", response.status_code)
    print(response.json().get("description", "Unknown error"))
