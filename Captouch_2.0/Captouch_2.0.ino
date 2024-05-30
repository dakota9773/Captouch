/*********************************************************
This is a library for the MPR121 12-channel Capacitive touch sensor

Designed specifically to work with the MPR121 Breakout in the Adafruit shop 
  ----> https://www.adafruit.com/products/

These sensors use I2C communicate, at least 2 pins are required 
to interface

Adafruit invests time and resources providing this open source code, 
please support Adafruit and open-source hardware by purchasing 
products from Adafruit!

Written by Limor Fried/Ladyada for Adafruit Industries.  
BSD license, all text above must be included in any redistribution
**********************************************************/
/*********************************************************
The provided adafruit code was modified by Daktoa Nipper, Neurobehavioral Core, NIEHS.
Functions for troubleshooting, data logging, and other general functions were added to modify the code.
Additional comments are provided to aid in understanding the code. 
Please see the project Github at: 
**********************************************************/


//Specify which libraries are included in code
#include <Wire.h> //The library used for I2C communications
#include "Adafruit_MPR121.h" //The library for the captouch breakout board
#include <RTClib.h> //The library for the RTC breakout board
#include <SD.h> //The library for the SD card functions of the M0 Adalogger board. 

//This code is used for bit manipulation 
#ifndef _BV
#define _BV(bit) (1 << (bit)) 
#endif

//Next we define the RTC and MPR121 breakout boards. You can have more MPR121 boards attached, but we only use the one.
RTC_DS3231 rtc;
Adafruit_MPR121 cap = Adafruit_MPR121();

//Add needed for pin touch and release in loop function
uint16_t lasttouched = 0;
uint16_t currtouched = 0;

//Needed for TTL pulse in loop
const int sensorPins[] = {0, 1, 2, 3}; // Sensor indices
const int ttlPins[] = {6, 9, 10, 11};  // Corresponding TTL output pins

//This code is needed for the saving function to occur without impeding the touch-TTL part of the loop section.
unsigned long previousMillis = 0; const long interval = 33;
void setup() {
  Serial.begin(9600); //Set the baud rate. This is the bits per second the arudino can communicate at. 

  // needed to keep leonardo/micro from starting too fast!
  while (!Serial) { // while is a simple function and ! just means not, so this code says "while not the serial delay for 10 ms"
    delay(10);
  }

  //Set pinmode for inputs and outputs
  pinMode(5, OUTPUT);//This pin is attached to a red LED and is used for trobleshooting purposes. 
  for (int i = 0; i < 4; i++) {
    pinMode(ttlPins[i], OUTPUT); // Set each TTL pin as an output
  }
  
  //Introduction to the project
  Serial.println("Welcome to the");
  delay(2000);
  Serial.println("Captouch 3.0 Project"); 
  delay(5000);
  
  // Default address is 0x5A, if tied to 3.3V its 0x5B
  // If tied to SDA its 0x5C and if SCL then 0x5D
  if (!cap.begin(0x5A)) {
    Serial.println("MPR121 not found, check wiring?");
    while (1){//Locks the code in a loop and flashes the LED light. This code is used often for this purpose.
      digitalWrite(5, HIGH); delay(100); 
      digitalWrite(5, LOW); delay(2500); 
    };
  }
  Serial.println("MPR121 found!");//Print to serial
  
  delay(2000);
  
  //Next we use an if function to set SD card pin. For the M0 Adalogger this is pin 4.
  //Additionally, if(!SD.begin()) allows troubleshooting if the SD card doesn't initialize
  if(SD.begin(4)){
    Serial.print("SD Card initialized");
    Serial.println();}
    else{Serial.print("SD card fail");
    Serial.println();
    while(1){
      digitalWrite(5, HIGH); delay(100);
      digitalWrite(5, LOW); delay(100); 
      digitalWrite(5, HIGH); delay(100);
      digitalWrite(5, LOW); delay(2500);

    }}
  
  delay(2000);

  //This code initiates a file for the data logging. Additionally it adds column names
  File df = SD.open("cap_data.csv", FILE_WRITE);
  if (df){
    df.println("Time,Object 1 Baseline,Object 1 Filtered,Object 2 Baseline ,Object 2 Filtered");
    df.close();;
  } else {
    Serial.println("Couldn't access Raw data file");
    while(1){
      digitalWrite(5, HIGH); delay(100);
      digitalWrite(5, LOW); delay(100); 
      digitalWrite(5, HIGH); delay(100); 
      digitalWrite(5, LOW); delay(100); 
      digitalWrite(5, HIGH); delay(100); 
      digitalWrite(5, LOW); delay(2500);

    }} 

  //This code initiates our RTC and shoots an error code otherwise. I like to set my own time using a string so this doesnt
  //Fix the time whent he RTC dies.
if (rtc.begin()) {
    Serial.println("RTC found");
  } else{
    Serial.println("RTC not found");
    while(1){
      digitalWrite(5, HIGH); delay(50);
      digitalWrite(5, LOW); delay(50); 
      digitalWrite(5, HIGH); delay(50); 
      digitalWrite(5, LOW); delay(2500);
} }
if (rtc.lostPower()) {
  Serial.println("RTC died, need to reset time");
  while(1){
      digitalWrite(5, HIGH); delay(50);
      digitalWrite(5, LOW); delay(50); 
      digitalWrite(5, HIGH); delay(50);
      digitalWrite(5, LOW); delay(50);   
      digitalWrite(5, LOW); delay(2500);  
  }}}






  void loop() {
  //Need to assign current milliseconds passed
  unsigned long currentMillis = millis();

  // Get the current time from the RTC
  DateTime now = rtc.now();
  currtouched = cap.touched();
  
  for (uint8_t i=0; i<1; i++) {//This part of the code only checks the two sensors, 0 and 1, instead of all 12. Easy fix.
    // it if *is* touched and *wasnt* touched before, alert!
    if ((currtouched & _BV(i)) && !(lasttouched & _BV(i)) ) {
      Serial.print(i); Serial.println(" touched");
      digitalWrite(ttlPins[i], HIGH);
    }
    // if it *was* touched and now *isnt*, alert!
    if (!(currtouched & _BV(i)) && (lasttouched & _BV(i)) ) {
      Serial.print(i); Serial.println(" released");
      digitalWrite(ttlPins[i], LOW);
    }
  }
  
  // reset our state
  lasttouched = currtouched;
  
  // Format the time as a string in the format: YYYY/MM/DD HH:MM:SS
  char timeString[20];
  
  //Record current time
  sprintf(timeString, "%04d/%02d/%02d %02d:%02d:%02d", now.year(), now.month(), now.day(), now.hour(), now.minute(), now.second());
  //This function looks complicated, but we are just turning our data into a string of text and saving it as a .csv file.
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
   String cap_0_base = String(cap.baselineData(0)); String cap_0_filt = String(cap.filteredData(0));
   String cap_1_base = String(cap.baselineData(1)); String cap_1_filt = String(cap.filteredData(1)); 
    String cap_data = String(timeString) + "," + cap_0_base + "," + cap_0_filt + "," + cap_1_base + "," + cap_1_filt;
   File df = SD.open("cap_data.csv", FILE_WRITE);
  if (df) {
   df.println(cap_data);
   df.close();}
    else{
      while(1){digitalWrite(5, HIGH);}
}}
}