
#include <Wire.h>
#include <Keypad.h>
#include <Servo.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// OLED setup
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(
  SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET
);

// Keypad setup
const byte ROWS = 4;
const byte COLS = 4;

// Your corrected keypad mapping
char keys[ROWS][COLS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'*', '0', '#', 'D'},
  {'7', '8', '9', 'C'}
};

byte rowPins[ROWS] = {2, 3, 4, 5};
byte colPins[COLS] = {6, 7, 8, 9};

Keypad keypad = Keypad(
  makeKeymap(keys),
  rowPins, colPins,
  ROWS, COLS
);

// Component pins
const int buttonPin = 10;
const int buzzerPin = 11;
const int servoPin = A0;
const int redLED = A1;
const int greenLED = A2;

Servo doorServo;

// Password
const String password = "1234";
String enteredPassword = "";

// Servo angles
const int lockAngle = 180;
const int unlockAngle = 90;

// Door timer
bool doorUnlocked = false;
unsigned long unlockTime = 0;
const unsigned long unlockDuration = 7000;

// OLED message timer
unsigned long messageTime = 0;
const unsigned long messageDuration = 1500;
bool temporaryMessage = false;

// Button debounce
bool lastButtonReading = HIGH;
bool stableButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

// Wrong password attempts
int wrongAttempts = 0;

// OLED display
void showMessage(String line1, String line2) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  display.setCursor(0, 8);
  display.println("   TRUSTED DOOR");

  display.drawLine(0, 22, 127, 22, SSD1306_WHITE);

  display.setCursor(0, 32);
  display.println(line1);

  display.setCursor(0, 46);
  display.println(line2);

  display.display();
}

// Mask password
void showPassword() {
  String stars = "";

  for (unsigned int i = 0;
       i < enteredPassword.length(); i++) {
    stars += "*";
  }

  showMessage("Enter Password:", stars);
}

// Success beep
void successBeep() {
  tone(buzzerPin, 2000, 150);
  delay(200);
  noTone(buzzerPin);
}

// Error beep
void errorBeep() {
  for (int i = 0; i < 3; i++) {
    tone(buzzerPin, 1000, 150);
    delay(250);
  }
  noTone(buzzerPin);
}

// Warning beep
void warningBeep() {
  for (int i = 0; i < 6; i++) {
    tone(buzzerPin, 1500, 150);
    delay(250);
  }
  noTone(buzzerPin);
}

// Doorbell beep
void doorbellBeep() {
  tone(buzzerPin, 1200, 150);
  delay(250);
  tone(buzzerPin, 1600, 200);
  delay(220);
  noTone(buzzerPin);
}

// Unlock door
void unlockDoor() {
  Serial.println("ACCESS GRANTED");

  doorServo.write(unlockAngle);

  digitalWrite(greenLED, HIGH);
  digitalWrite(redLED, LOW);

  showMessage("ACCESS GRANTED", "Door Unlocked");

  doorUnlocked = true;
  unlockTime = millis();

  wrongAttempts = 0;
  temporaryMessage = false;

  successBeep();
}

// Lock door
void lockDoor() {
  doorServo.write(lockAngle);

  digitalWrite(greenLED, LOW);
  digitalWrite(redLED, HIGH);

  doorUnlocked = false;

  showMessage("DOOR LOCKED", "Enter Password");

  Serial.println("Door locked");
}

// Doorbell function
void ringDoorbell() {
  Serial.println("DOORBELL_PRESSED");

  // No servo movement here
  // The door remains in its current state

  showMessage("VISITOR AT DOOR", "Taking Photo...");

  doorbellBeep();

  temporaryMessage = true;
  messageTime = millis();
}

// Check password
void checkPassword() {
  if (enteredPassword == password) {
    unlockDoor();
  } else {
    Serial.println("ACCESS DENIED");

    digitalWrite(greenLED, LOW);
    digitalWrite(redLED, HIGH);

    showMessage("ACCESS DENIED", "Wrong Password");

    wrongAttempts++;

    errorBeep();

    if (wrongAttempts >= 3) {
      Serial.println("WARNING: 3 wrong attempts");

      showMessage("WARNING!", "Too Many Attempts");

      warningBeep();

      wrongAttempts = 0;
    }

    temporaryMessage = true;
    messageTime = millis();
  }

  enteredPassword = "";
}

// Receive approval or rejection from Raspberry Pi
void checkRaspberryCommands() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "APPROVE") {
      Serial.println("REMOTE APPROVAL RECEIVED");

      if (!doorUnlocked) {
        unlockDoor();
      }
    }
    else if (command == "DENY") {
      Serial.println("REMOTE REJECTION RECEIVED");

      // Do not unlock or interrupt an existing
      // valid keypad access
      if (!doorUnlocked) {
        showMessage("ACCESS REJECTED", "Door Stays Locked");
        temporaryMessage = true;
        messageTime = millis();
      }
    }
  }
}

void setup() {
  Serial.begin(9600);

  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(buzzerPin, OUTPUT);
  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);

  Wire.begin();

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED not found!");
    while (true) {
      delay(100);
    }
  }

  showMessage("Starting System", "Please Wait...");
  delay(1000);

  doorServo.attach(servoPin);
  lockDoor();

  Serial.println("TRUSTED DOOR SYSTEM READY");
  Serial.println("Press # to submit PIN");
  Serial.println("Press * to clear PIN");
  Serial.println("D10 button = Doorbell");
}

void loop() {
   checkRaspberryCommands();
  // Keypad input
  char key = keypad.getKey();

  if (key) {
    Serial.print("Key pressed: ");
    Serial.println(key);

    if (key == '#') {
      if (enteredPassword.length() > 0) {
        checkPassword();
      }
    }
    else if (key == '*') {
      enteredPassword = "";
      temporaryMessage = false;
      showPassword();

      Serial.println("Password cleared");
    }
    else if (key >= '0' && key <= '9') {
      if (enteredPassword.length() < 8) {
        enteredPassword += key;
        temporaryMessage = false;
        showPassword();
      }
    }
  }

  // Doorbell button
  bool reading = digitalRead(buttonPin);

  if (reading != lastButtonReading) {
    lastDebounceTime = millis();
  }

  if (millis() - lastDebounceTime > debounceDelay) {
    if (reading != stableButtonState) {
      stableButtonState = reading;

      if (stableButtonState == LOW) {
        ringDoorbell();
      }
    }
  }

  lastButtonReading = reading;

  // Automatically relock after 5 seconds
  if (doorUnlocked &&
      millis() - unlockTime >= unlockDuration) {
    lockDoor();
  }

  // Restore OLED screen
  if (temporaryMessage &&
      millis() - messageTime >= messageDuration) {
    temporaryMessage = false;

    if (doorUnlocked) {
      showMessage("ACCESS GRANTED", "Door Unlocked");
    } else {
      showPassword();
    }
  }
}
