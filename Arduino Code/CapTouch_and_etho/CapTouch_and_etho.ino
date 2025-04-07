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
  const int touchPins[3] = {5, 6, 7};
  const int ledPins[3] = {A1, A2, A4};
  String cap_touch[3] = {"0", "0", "0"};
  int EthoPin = A3;
  bool SavingData = false;

void setup() {
  //Define Baud rate and pins
    Serial.begin(BAUD_RATE);
    pinMode(ledPins[1], OUTPUT);
    pinMode(ledPins[2], OUTPUT);
    pinMode(ledPins[3], OUTPUT);
    pinMode(EthoPin, INPUT);

  //MPR121 Initialization and settings
    if (!MPR121.begin(MPR121_ADDR)) {
      Serial.println("error setting up MPR121");
      switch (MPR121.getError()) {
        case NO_ERROR:
         Serial.println("no error");
         break;
        case ADDRESS_UNKNOWN:
          Serial.println("incorrect address");
          break;
        case READBACK_FAIL:
          Serial.println("readback failure");
          break;
        case OVERCURRENT_FLAG:
          Serial.println("overcurrent on REXT pin");
          break;
        case OUT_OF_RANGE:
          Serial.println("electrode out of range");
          break;
        case NOT_INITED:
          Serial.println("not initialised");
          break;
        default:
          Serial.println("unknown error");
          break;
      }
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
    //MPR121.autoSetElectrodes();
    digitalWrite(LED_BUILTIN, LOW); 
}

void loop() {
  
  unsigned long currentMillis = millis();
  int ethopin = digitalRead(EthoPin);
  MPR121.updateAll();

  for (int i = 1; i < 3; i++) {
    if (MPR121.isNewTouch(i)) {
      cap_touch[i] = "1";
      digitalWrite(ledPins[i], HIGH);
    } else if (MPR121.isNewRelease(i)) {
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