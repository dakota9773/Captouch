//Define Library
#include <MPR121.h>
#include <Wire.h>
#include <RTClib.h>

//Define Variables
const uint32_t BAUD_RATE = 115200;
const uint8_t MPR121_ADDR = 0x5C;
const uint8_t MPR121_INT = 4;
unsigned long previousMillis = 0;
const long interval = 100;
const int touchThreshold = 2; 
const int releaseThreshold = 1;
unsigned long elapsedMillis;  
unsigned long runningstartMillis = 0;
const int touchPins[4] = {0, 4, 7, 11};
const int ledPins[4] = {A0, A1, A2, A3};
String cap_touch[4] = {"0", "0", "0", "0"};
int EthoPin = A4;

void setup() {
  //Define Baud rate and pins
  Serial.begin(BAUD_RATE);
  // Fix LED pin indices (0-3) to match the array
  pinMode(ledPins[0], OUTPUT);
  pinMode(ledPins[1], OUTPUT);
  pinMode(ledPins[2], OUTPUT);
  pinMode(ledPins[3], OUTPUT);
  pinMode(EthoPin, INPUT);    

  //MPR121 Initialization and settings
  if (!MPR121.begin(MPR121_ADDR)) {
    Serial.println("Error setting up MPR121");
    while (1);
  }
  MPR121.setInterruptPin(MPR121_INT);
  MPR121.setTouchThreshold(touchThreshold);
  MPR121.setReleaseThreshold(releaseThreshold);
  MPR121.setFFI(FFI_18);
  MPR121.setSFI(SFI_18);
  MPR121.setGlobalCDT(CDT_2US);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(100);
  MPR121.autoSetElectrodes();
  MPR121.setRegister(0x2B, 0xFF);
  MPR121.setRegister(0x2F, 0xFF);
  MPR121.setRegister(0x2C, 0x00);
  MPR121.setRegister(0x30, 0x00);
  digitalWrite(LED_BUILTIN, LOW); 
}

void loop() {
  unsigned long currentMillis = millis();
  int ethopin = digitalRead(EthoPin);
  static unsigned long lastResetTime = 0;

  // Check if a serial command is available
  if (Serial.available() > 0) {
    String serialCmd = Serial.readStringUntil('\n');
    serialCmd.trim();
    if (serialCmd.equals("RESET.BASELINE") && (currentMillis - lastResetTime >= 1000)) {
      MPR121.autoSetElectrodes();
      MPR121.setRegister(0x2B, 0xFF);
      MPR121.setRegister(0x2F, 0xFF);
      MPR121.setRegister(0x2C, 0x00);
      MPR121.setRegister(0x30, 0x00);
      lastResetTime = currentMillis; 
    }
  }

  MPR121.updateAll();

  // Process up to 2 touch pins (adjust if needed)
  for (int i = 0; i < 2; i++) {
    if (MPR121.isNewTouch(touchPins[i])) {
      cap_touch[i] = "1";
      digitalWrite(ledPins[i], HIGH);
    } else if (MPR121.isNewRelease(touchPins[i])) {
      cap_touch[i] = "0";
      digitalWrite(ledPins[i], LOW);
    }
  }

  if (currentMillis - previousMillis >= interval) {
    unsigned long runningcurrentMillis = millis();
    elapsedMillis = runningcurrentMillis - runningstartMillis;
    previousMillis = currentMillis;
    
    String cap_data = "";
    for (int i = 0; i <= 11; i++) {
      String cap_base = String(MPR121.getBaselineData(i));
      String cap_filt = String(MPR121.getFilteredData(i));
      cap_data += cap_base + "," + cap_filt;
      if (i < 11) {
        cap_data += ",";
      }
    }
    cap_data += ",";
    cap_data += String(ethopin);
    Serial.println(cap_data);
  }
}

/*********************************************************************************************************************
//Define Library
  #include <MPR121.h>
  #include <Wire.h>
  #include <RTClib.h>

//Define Variables
  const uint32_t BAUD_RATE = 115200;
  const uint8_t MPR121_ADDR = 0x5C;
  const uint8_t MPR121_INT = 4;
  unsigned long previousMillis = 0;
  const long interval = 100;
  const int touchThreshold = 2; 
  const int releaseThreshold = 1;
  unsigned long elapsedMillis;  
  unsigned long runningstartMillis = 0;
  const int touchPins[4] = {0, 4, 7, 11};
  const int ledPins[4] = {A0, A1, A2, A3};
  String cap_touch[4] = {"0", "0", "0", "0"};
  int EthoPin = A5;
  int ResetPin = A4;

void setup() {
  //Define Baud rate and pins
    Serial.begin(BAUD_RATE);
    pinMode(ledPins[1], OUTPUT);
    pinMode(ledPins[2], OUTPUT);
    pinMode(ledPins[3], OUTPUT);
    pinMode(ledPins[4], OUTPUT);
    pinMode(EthoPin, INPUT);    
    pinMode(ResetPin, INPUT);

  //MPR121 Initialization and settings
    if (!MPR121.begin(MPR121_ADDR)) {
        Serial.println("Error setting up MPR121");
        while (1);
    }
    MPR121.setInterruptPin(MPR121_INT);
    MPR121.setTouchThreshold(touchThreshold);
    MPR121.setReleaseThreshold(releaseThreshold);
    MPR121.setFFI(FFI_18);
    MPR121.setSFI(SFI_18);
    MPR121.setGlobalCDT(CDT_2US);
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    MPR121.autoSetElectrodes();
      MPR121.setRegister(0x2B, 0xFF);
      MPR121.setRegister(0x2F, 0xFF);
      MPR121.setRegister(0x2C, 0x00);
      MPR121.setRegister(0x30, 0x00);
    digitalWrite(LED_BUILTIN, LOW); 
}

void loop() {
  unsigned long currentMillis = millis();
  int ethopin = digitalRead(EthoPin);
  int resetpin = digitalRead(ResetPin);
  static unsigned long lastResetTime = 0;

  if (resetpin == HIGH && (currentMillis - lastResetTime >= 1000)) {
      MPR121.autoSetElectrodes();
      MPR121.setRegister(0x2B, 0xFF);
      MPR121.setRegister(0x2F, 0xFF);
      MPR121.setRegister(0x2C, 0x00);
      MPR121.setRegister(0x30, 0x00);
    lastResetTime = currentMillis;  // Update the last reset time
  }

  MPR121.updateAll();

  for (int i = 0; i < 2; i++) {
    if (MPR121.isNewTouch(touchPins[i])) {
      cap_touch[i] = "1";
      digitalWrite(ledPins[i], HIGH);
    } else if (MPR121.isNewRelease(touchPins[i])) {
      cap_touch[i] = "0";
      digitalWrite(ledPins[i], LOW);
    }
  }

  if (currentMillis - previousMillis >= interval) {
    unsigned long runningcurrentMillis = millis();
    elapsedMillis = runningcurrentMillis - runningstartMillis;
    previousMillis = currentMillis;
    
    String cap_data = "";
    for (int i = 0; i <= 11; i++) {
      String cap_base = String(MPR121.getBaselineData(i));
      String cap_filt = String(MPR121.getFilteredData(i));
      cap_data += cap_base + "," + cap_filt;
      if (i < 11) {
        cap_data += ",";
      }
    }
    cap_data += ",";
    cap_data += String(ethopin);
    cap_data += ",";
    cap_data += String(resetpin);
    Serial.println(cap_data);
  }
}





void loop() {
  
  unsigned long currentMillis = millis();
  int ethopin = digitalRead(EthoPin);
  MPR121.updateAll();

  for (int i = 0; i < 2; i++) {
    if (MPR121.isNewTouch(touchPins[i])) {
      cap_touch[i] = "1";
      digitalWrite(ledPins[i], HIGH);
    } else if (MPR121.isNewRelease(touchPins[i])) {
      cap_touch[i] = "0";
      digitalWrite(ledPins[i], LOW);
    }
  }

  if (currentMillis - previousMillis >= interval) {
    unsigned long runningcurrentMillis = millis();
    elapsedMillis = runningcurrentMillis - runningstartMillis;
    previousMillis = currentMillis;

    String cap_data = "";
    for (int i = 0; i <= 11; i++) {
      String cap_base = String(MPR121.getBaselineData(i));
      String cap_filt = String(MPR121.getFilteredData(i));
      cap_data += cap_base + "," + cap_filt;
      if (i < 11) {
        cap_data += ",";
      }
    }
    cap_data += ",";
    cap_data += String(ethopin);
    Serial.println(cap_data);
  }
}
*********************************************************************************************************************/