# Trusted Door – Doorstep Fraud Shield

## Project Overview

Trusted Door is a smart door security system that I developed as part of my Embedded Systems Development project (SIT210).

The main idea behind this project is to make door access safer, especially for elderly people who may be vulnerable to doorstep fraud or unknown visitors.

The system uses an Arduino Nano 33 IoT for controlling the door lock, keypad, LEDs, buzzer and push button. A Raspberry Pi 4 is connected to a 5MP camera to capture photographs of visitors.

Whenever someone presses the doorbell, the Raspberry Pi takes a photograph and sends it to a caretaker through a Telegram bot. The caretaker can then approve or reject the visitor remotely.

The prototype is built using a cardboard shoebox to demonstrate how the system works.

## Components Used

- Arduino Nano 33 IoT
- Raspberry Pi 4
- Raspberry Pi 5MP Camera Module
- 4×4 Matrix Keypad
- SG90 Servo Motor
- 0.96-inch OLED Display
- Push Button
- Red and Green LEDs
- Buzzer
- Breadboard
- Jumper Wires
- Resistors
- USB Cable
- Cardboard Shoebox

## Software and Technologies

- Arduino IDE
- Arduino C++
- Python 3
- Raspberry Pi OS
- Telegram Bot API
- Raspberry Pi Connect
- PySerial
- Python Requests Library
- Raspberry Pi Camera Tools

## How the System Works

The system has two main ways of handling door access.

### 1. Keypad Access

A user can enter a password using the 4×4 keypad.

The current password is 1234.

After entering the password, the user presses # to submit it.

If the password is correct, the green LED turns on, the buzzer gives a short beep, and the servo unlocks the door for five seconds.

After five seconds, the servo automatically returns to its locked position.

If the password is incorrect, the red LED stays on and the buzzer produces warning beeps.

After three incorrect attempts, the OLED displays a warning message.

### 2. Visitor Verification Through Telegram

When a visitor presses the push button, the Arduino sends a DOORBELL_PRESSED message to the Raspberry Pi through USB serial communication.

The Raspberry Pi then captures a photograph using the connected camera.

The photograph is saved in the visitors folder and sent to the caretaker through a Telegram bot.

The Telegram message contains two buttons:

- Approve: Sends an approval command from the Raspberry Pi to the Arduino.
- Reject: Keeps the door locked.

If no response is received within 60 seconds, the request expires.

This feature allows the caretaker to check who is at the door without being physically present.

## Hardware Connections

Component Arduino Pin

Keypad Row 1 | D2 |
Keypad Row 2 | D3 |
Keypad Row 3 | D4 |
Keypad Row 4 | D5 |
Keypad Column 1 | D6 |
Keypad Column 2 | D7 |
Keypad Column 3 | D8 |
Keypad Column 4 | D9 |
Push Button | D10 |
Buzzer | D11 |
Servo Signal | A0 |
Red LED | A1 |
Green LED | A2 |
OLED SDA | SDA |
OLED SCL | SCL |

The Raspberry Pi camera is connected through the camera ribbon connector, and the Arduino communicates with the Raspberry Pi through USB.

The servo uses a suitable external 5V power supply with a common ground connection to the Arduino.

## Servo Configuration

The servo motor is used to demonstrate the locking and unlocking mechanism.

- Locked position: 90°
- Unlocked position: 180°
- Unlock duration: 5 seconds

The servo rotates to the unlocked position when the correct password is entered or when an approved remote command is received.

## Project Files

The files used in this project are:

- **Arduino sketch (.ino):** Controls the keypad, OLED, servo, LEDs, buzzer and doorbell.
- **camera_trigger.py:** Receives Arduino messages, captures visitor photographs and handles Telegram communication.
- **telegram_config.py:** Stores the Telegram bot token and authorized caretaker Chat ID.
- **get_chat_id.py:** Helps identify the Telegram Chat ID.
- **test_telegram.py:** Tests sending a Telegram message.
- **test_photo.py:** Tests sending a visitor photograph.

The `telegram_config.py` file contains private credentials and should not be uploaded to GitHub.

## Testing

I tested the components individually before combining them into one system.

The keypad was tested by entering correct and incorrect passwords. The OLED was tested by displaying different messages, and the LEDs and buzzer were checked for access feedback.

I also tested the servo motor at different angles to find suitable positions for the cardboard door mechanism.

For the Raspberry Pi integration, I first checked whether the camera could capture photographs. After that, I connected the Arduino to the Raspberry Pi using USB and tested serial communication.

The doorbell-triggered photograph capture worked successfully.

I also tested sending messages and photographs through Telegram. The caretaker approval command was successfully sent from the Raspberry Pi, although the servo response to remote approval still needs final verification.

## Fault Tolerance

The system is designed to keep the door locked when a visitor has not been approved.

If the caretaker does not respond within the specified time, the Telegram request expires.

Old approval requests cannot be reused, and only the configured caretaker's Telegram account is allowed to approve a visitor.

If the internet connection is unavailable, remote approval cannot take place. The keypad remains available for local access.

For a real installation, a dedicated fail-secure locking mechanism and additional hardware protection would be required.

## Challenges Faced

One of the main challenges was connecting all the components to the Arduino without mixing up the pins.

I also had some difficulty with the keypad mapping because a few keys were showing different characters. I fixed this by testing the keypad and updating the mapping in the Arduino code.

Another challenge was fixing my camera it look a lot of time integratinf that and working with it.

While integrating Telegram, I faced issues with the bot token, Python files and network connection. I worked through these problems by testing the message and photograph features separately.

The servo locking mechanism also required adjustments because the prototype uses cardboard instead of a proper door frame.

## Future Improvements

In the future, I would like to improve the system by adding:

- RFID-based access.
- A stronger and more reliable locking mechanism.
- A proper enclosure instead of cardboard.
- Automatic startup of the Raspberry Pi program.
- A visitor activity log.
- Better handling of internet and power failures.
- More secure communication between the Raspberry Pi and Arduino.

## Conclusion

I learned how to connect sensors and output devices to an Arduino, use a Raspberry Pi camera, communicate between two devices using serial communication, and integrate a Telegram bot for remote notifications.

The most interesting part was making the Arduino doorbell trigger the Raspberry Pi camera and send the visitor's photograph to Telegram.

Although the prototype still needs some improvements, it demonstrates how a simple embedded system can be used to support safer door access for elderly people.
