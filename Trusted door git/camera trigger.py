
import os
import time
import uuid
import serial
import requests
import subprocess

from pathlib import Path
from datetime import datetime
from telegram_config import BOT_TOKEN, CHAT_ID

# Trusted Door settings
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
APPROVAL_TIMEOUT = 60

PHOTO_FOLDER = Path.home() / "TrustedDoor" / "visitors"
PHOTO_FOLDER.mkdir(parents=True, exist_ok=True)

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# The caretaker's private Telegram chat ID
AUTHORIZED_CHAT_ID = str(CHAT_ID)

arduino = serial.Serial(
    SERIAL_PORT,
    BAUD_RATE,
    timeout=0.2,
    write_timeout=2
)

session = requests.Session()

# Only one pending visitor request at a time
pending_request = None
last_update_id = 0


def telegram_request(method, **kwargs):
    response = session.post(
        f"{API}/{method}",
        timeout=kwargs.pop("timeout", 20),
        **kwargs
    )
    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            result.get("description", "Telegram error")
        )

    return result["result"]


def send_arduino(command):
    arduino.write((command + "\n").encode())
    arduino.flush()
    print("Sent to Arduino:", command)


def capture_photo():
    filename = PHOTO_FOLDER / (
        "visitor_" +
        datetime.now().strftime("%Y%m%d_%H%M%S_%f") +
        ".jpg"
    )

    result = subprocess.run(
        ["rpicam-still", "-n", "-o", str(filename)],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    print("Photo captured:", filename)
    return filename


def remove_buttons(request):
    try:
        telegram_request(
            "editMessageReplyMarkup",
            data={
                "chat_id": AUTHORIZED_CHAT_ID,
                "message_id": request["message_id"],
                "reply_markup": '{"inline_keyboard":[]}'
            }
        )
    except Exception as error:
        print("Could not remove buttons:", type(error).__name__)


def send_visitor_photo(filename):
    global pending_request

    request_id = uuid.uuid4().hex[:16]

    buttons = {
        "inline_keyboard": [[
            {
                "text": "Approve",
                "callback_data": "approve:" + request_id
            },
            {
                "text": "Reject",
                "callback_data": "reject:" + request_id
            }
        ]]
    }

    import json

    with open(filename, "rb") as photo:
        message = telegram_request(
            "sendPhoto",
            data={
                "chat_id": AUTHORIZED_CHAT_ID,
                "caption": (
                    "TRUSTED DOOR\n"
                    "Visitor at your door.\n"
                    "Approve or reject within 60 seconds."
                ),
                "reply_markup": json.dumps(buttons)
            },
            files={"photo": photo},
            timeout=40
        )

    pending_request = {
        "id": request_id,
        "message_id": message["message_id"],
        "expires": time.monotonic() + APPROVAL_TIMEOUT
    }

    print("Photo sent to caretaker on Telegram")


def expire_request():
    global pending_request

    if pending_request is None:
        return

    if time.monotonic() >= pending_request["expires"]:
        print("Approval request expired")
        remove_buttons(pending_request)
        pending_request = None


def handle_callback(callback):
    global pending_request

    callback_id = callback["id"]
    sender = str(callback["from"]["id"])
    message = callback.get("message") or {}
    chat = message.get("chat") or {}

    # Only the authorized private-chat user can approve
    authorized = (
        sender == AUTHORIZED_CHAT_ID
        and str(chat.get("id")) == AUTHORIZED_CHAT_ID
    )

    if not authorized:
        telegram_request(
            "answerCallbackQuery",
            data={
                "callback_query_id": callback_id,
                "text": "Unauthorized user",
                "show_alert": "true"
            }
        )
        return

    data = callback.get("data", "")
    action, separator, request_id = data.partition(":")

    valid = (
        separator == ":"
        and action in ("approve", "reject")
        and pending_request is not None
        and request_id == pending_request["id"]
        and message.get("message_id") ==
            pending_request["message_id"]
        and time.monotonic() < pending_request["expires"]
    )

    if not valid:
        telegram_request(
            "answerCallbackQuery",
            data={
                "callback_query_id": callback_id,
                "text": "Request expired or already handled"
            }
        )
        return

    request = pending_request
    pending_request = None

    if action == "approve":
        send_arduino("APPROVE")
        status = "Visitor APPROVED. Door unlock requested."
    else:
        send_arduino("DENY")
        status = "Visitor REJECTED. Door remains locked."

    telegram_request(
        "answerCallbackQuery",
        data={
            "callback_query_id": callback_id,
            "text": status
        }
    )

    remove_buttons(request)

    telegram_request(
        "sendMessage",
        data={
            "chat_id": AUTHORIZED_CHAT_ID,
            "text": status
        }
    )

    print(status)


def check_telegram():
    global last_update_id

    updates = telegram_request(
        "getUpdates",
        data={
            "offset": last_update_id + 1,
            "timeout": 0,
            "allowed_updates": '["callback_query"]'
        },
        timeout=10
    )

    for update in updates:
        last_update_id = max(
            last_update_id,
            update["update_id"]
        )

        if "callback_query" in update:
            handle_callback(update["callback_query"])


def start():
    global last_update_id

    print("Starting Trusted Door Telegram System")

    # Check the token without displaying it
    telegram_request("getMe")

    # This program uses polling, not a webhook
    telegram_request("deleteWebhook", data={
        "drop_pending_updates": "true"
    })

    # Ignore old Telegram events from previous runs
    old_updates = telegram_request(
        "getUpdates",
        data={"timeout": 0}
    )

    if old_updates:
        last_update_id = max(
            update["update_id"] for update in old_updates
        )

    # Arduino may reset when USB serial is opened
    time.sleep(3)
    arduino.reset_input_buffer()

    print("TRUSTED DOOR READY")
    print("Waiting for doorbell...")

    while True:
        expire_request()

        line = arduino.readline().decode(
            "utf-8", errors="ignore"
        ).strip()

        if line:
            print("Arduino:", line)

        if line == "DOORBELL_PRESSED":
            if pending_request is not None:
                print("Visitor request already pending")
            else:
                try:
                    photo = capture_photo()
                    send_visitor_photo(photo)
                except Exception as error:
                    print(
                        "Photo/Telegram error:",
                        type(error).__name__,
                        str(error)[:200]
                    )

        try:
            check_telegram()
        except requests.RequestException as error:
            print("Telegram network error:", type(error).__name__)
            time.sleep(2)


try:
    start()

except KeyboardInterrupt:
    print("\nTrusted Door stopped")

except Exception as error:
    print("System error:", type(error).__name__, str(error)[:200])

finally:
    arduino.close()
    session.close()
