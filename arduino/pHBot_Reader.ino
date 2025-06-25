int pHProbe = A7; //change # to corresponding analog pin if needed
int pHVolts = 0;
float pHValue = 0.00;
int pHVolts1 = 0;
int pHVolts2 = 0;
float pHValue1 = 0.00;
float pHValue2 = 0.00;
float pHSlope = 0.000;
float pHIntercept = 0.000;
int pHCounter = 0;
float pHChecker = 0.00;
float pHFinal = 0.00;

bool hostCodeSignal = true; //To be controlled by the host code.
bool firstReset = false;

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
}

void loop() {
  if(hostCodeSignal == true) {
    firstReset = true;
    while(pHCounter < 10) {
      pHVolts = Serial.read();
      pHValue = pHVolts * pHSlope + pHIntercept;
      if(pHValue > (pHChecker - 0.1) && pHValue < (pHChecker + 0.1)) {
        pHCounter++;
      }
      else {
        pHCounter = 0;
      }
      pHChecker = pHVolts;
      delay(500);
    }
    pHFinal = pHVolts;
    //Export Final Value
  }
  else if (hostCodeSignal == false && firstReset == true) {
    firstReset = false;
    pHCounter = 0;
    pHChecker = 0.00;
    pHFinal = 0.00;
  }
}
