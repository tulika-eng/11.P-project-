import requests
import getpass

token = getpass.getpass("Enter bot token: ")

url = f"https://api.telegram.org/bot{token}/getUpdates"

response = requests.get(url, timeout=15)
response.raise_for_status()

data = response.json()

if data.get("ok"):
    for update in data.get("result", []):
        message = update.get("message", {})

        if message:
            chat = message.get("chat", {})
            print("Chat ID:", chat.get("id"))
            print("Chat type:", chat.get("type"))
else:
    print("Telegram error:", data)