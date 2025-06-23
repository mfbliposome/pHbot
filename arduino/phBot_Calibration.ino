int pHProbe = A7; //change # to corresponding analog pin if needed
int pHVolts1 = 0;
int pHVolts2 = 0;
int pHValue1 = 0.00;
int pHValue2 = 0.00;
float pHSlope = 0.0000;
float pHIntercept = 0.0000;

void setup() {
  Serial.begin(9600);
  pinMode(pHProbe, INPUT);
}

void loop() {
  pHValue1 = whatValuepH(1); //Preps the first pH value for reading, requires the user to input the first known pH value.
  pHVolts1 = readVolts(); //Measures the first pH value as milivolts.
  Serial.println("The reading of pH " + String(pHValue1) + " in milivolts is: " + String(pHVolts1)); //Placeholder print line to verify first reading.
  pHValue2 = whatValuepH(2); //Preps the second pH value for reading, requires the user to input the second known pH value.
  pHVolts2 = readVolts(); //Measures the second pH value as milivolts.
  Serial.println("The reading of pH " + String(pHValue2) + " in milivolts is: " + String(pHVolts2)); //Placeholder print line to verify second reading.
  delay(100); //Small delay to not interfere with the print lines, possibly not needed
  pHSlope = calculateSlope(pHValue2, pHValue1, pHVolts2, pHVolts1); //Calculates the slope using the two data points.
  Serial.println("The calibration slope is " + String(pHSlope)); //Placeholder print line to verify the slope value, displayed with two decimal points.
  pHIntercept = calculateIntercept(pHValue2, pHValue1, pHVolts2, pHVolts1, pHSlope); //Calculates the y-intercepts using the two data points and slope.
  Serial.println("The calibration intercept is " + String(pHIntercept)); //Placeholder print line verify the y-intercept, displayed with two decimal points.
  Serial.println("The calibration formula is now y = " + String(pHSlope) + "x + " + String(pHIntercept)); //Placeholder print to demonstate the formula, , displayed with two decimal points.
  while(true) {
    //Placeholder loop to prevent the program from looping.
  }
}

int whatValuepH (int bufferNumber) {
  int pHBuffer = 0; //Local variable used to hold the value of the input pH.
  Serial.println("Whole  number pH Value of buffer " + String(bufferNumber) + " :");
  while(pHBuffer == 0) {
    if(Serial.available() > 0) {
      pHBuffer = Serial.parseInt(); //Waits for a user to input the pH value, and will not continue until a non-trivial value is entered.
    }
  }
  return pHBuffer; //This will return the value back to the central program for later use.
}

int readVolts () {
  int voltBuffer = 0; //Local variable used to hold the value of the stabilized input.
  int stableCounter = 0; //Local variable used to count the amount of successive readings within tolerance
  int previousVolt = 0; //Local variable used to store the voltage value of the previous cycle of the while loop for comparison.
  while(stableCounter < 10) { //Number of consecutive similar comparisons for a reading.
    int currentVolt = 0; //Internal local variable used to compare with previousVolt.
    currentVolt = analogRead(pHProbe); //Assign the current value to currentVolt.
    if(currentVolt > (previousVolt - 2) && currentVolt < (previousVolt + 2)) { //Tolerance of comparison (Number to use = tolerance + 1)
      stableCounter++; //If the previous and current values are within tolerance, increment the stability counter.
    }
    else {
      stableCounter = 0; //Otherwise (in other words, outside of tolerance), reset the stability counter.
    }
    previousVolt = currentVolt; //Set the current value to be the previous value for the next cycle.
    delay(500); //Frequency of measurements
  }
  voltBuffer = previousVolt; //Once stable, sets the last stable value as the reading for the buffer.
  return voltBuffer;//This will return the value back to the central program for later use.
}

float calculateSlope (int y2, int y1, int x2, int x1) {
  float slope = 0.000;
  int deltay = 0;
  int deltax = 0;
  deltay = y2 - y1;
  deltax = x2 - x1;
  slope = (float)deltay / (float)deltax; //Slope calculations to find the slope.
  return slope; //This will return the value back to the central program for later use.
}

float calculateIntercept (int y2, int y1, int x2, int x1, float m) {
  float b = 0.000;
  float b1 = 0.000;
  float b2 = 0.000;
  b1 = y1 - (m * x1); //Intercept calculation for first pH value.
  b2 = y2 - (m * x2); //Intercept calculation for second pH value.
  b = (b1 + b2) / 2; //In the event where b1 and b2 are different (for whatever reason), this will use the average of the two.
  return b; //Intercept calculation for first pH value.
}
