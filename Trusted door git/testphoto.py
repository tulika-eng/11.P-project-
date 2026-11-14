
import requests
from pathlib import Path
from telegram_config import BOT_TOKEN, CHAT_ID

folder = Path.home() / "TrustedDoor" / "visitors"
photos = list(folder.glob("*.jpg"))

if not photos:
    print("No visitor photographs found.")
else:
    latest_photo = max(
        photos,
        key=lambda photo: photo.stat().st_mtime
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    with open(latest_photo, "rb") as photo:
        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": "Trusted Door: Visitor at your door"
            },
            files={"photo": photo},
            timeout=30
        )

    if response.ok and response.json().get("ok"):
        print("Visitor photograph sent successfully!")
    else:
        print("Photo sending failed:", response.status_code)
        print(response.json().get("description", "Unknown error"))
