int pHProbe = A7; //change # to corresponding analog pin if needed
int pHVolts = 0;
float pHValue = 0.00;
int pHVolts1 = 0;
int pHVolts2 = 0;
float pHValue1 = 0.00;
float pHValue2 = 0.00;
float pHSlope = 0.000;
float pHIntercept = 0.000;

#include <pHBot_Calibration.h>

void setup() {
  Serial.begin(9600);
  pinMode(pHProbe, INPUT);
  pHValue1 = whatValuepH(1); //Preps the first pH value for reading, requires the user to input the first known pH value.
  pHVolts1 = readVolts(pHProbe); //Measures the first pH value as milivolts.
  pHValue2 = whatValuepH(2); //Preps the second pH value for reading, requires the user to input the second known pH value.
  pHVolts2 = readVolts(pHProbe); //Measures the second pH value as milivolts.
  pHSlope = calculateSlope(pHValue2, pHValue1, pHVolts2, pHVolts1); //Calculates the slope using the two data points.
  pHIntercept = calculateIntercept(pHValue2, pHValue1, pHVolts2, pHVolts1, pHSlope); //Calculates the y-intercepts using the two data points and slope.
  Serial.println("Calibration complete. The slope is " + String(pHSlope) + " and the intercept is " + String(pHIntercept));
}

void loop() {
  if (Serial.available() > 0) {
    String hostCommand = Serial.readStringUntil('\n');
    hostCommand.trim();
    if(hostCommand.equalsIgnoreCase("READ_PH")) {
      int pHCounter = 0;
      float pHChecker = 0.00;
      float pHFinal = 0.00;
      while(pHCounter < 10) {
        pHVolts = analogRead(pHProbe);
        pHValue = pHVolts * pHSlope + pHIntercept;
        Serial.println("Currently reading" + String(pHValue));
        if(pHValue > (pHChecker - 0.05) && pHValue < (pHChecker + 0.05)) {
          pHCounter++;
        }
        else {
          pHCounter = 0;
        }
        pHChecker = pHValue;
        delay(500);
      }
      pHFinal = pHValue;
      Serial.println("pH measurement: " + String(pHFinal));
    }
  }
}
