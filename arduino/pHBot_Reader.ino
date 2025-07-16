int pHProbe = A7; //change # to corresponding analog pin if needed
int pHVolts = 0;
float pHValue = 0.00;
int pHVolts1 = 0;
int pHVolts2 = 0;
float pHValue1 = 0.00;
float pHValue2 = 0.00;
float pHSlope = 0.000;
float pHIntercept = 0.000;

void setup() {
  Serial.begin(9600);
  pinMode(pHProbe, INPUT);
  pHValue1 = whatValuepH(1); //Preps the first pH value for reading, requires the user to input the first known pH value.
  pHVolts1 = readVolts(); //Measures the first pH value as milivolts.
  pHValue2 = whatValuepH(2); //Preps the second pH value for reading, requires the user to input the second known pH value.
  pHVolts2 = readVolts(); //Measures the second pH value as milivolts.
  pHSlope = calculateSlope(pHValue2, pHValue1, pHVolts2, pHVolts1); //Calculates the slope using the two data points.
  pHIntercept = calculateIntercept(pHValue2, pHValue1, pHVolts2, pHVolts1, pHSlope); //Calculates the y-intercepts using the two data points and slope.
  Serial.println("Calibration complete."); //Lets the host code know that calibration is over
}

void loop() {
  if (Serial.available() > 0) { //Waits for the host code to write something to the arduino
    String hostCommand = Serial.readStringUntil('\n'); //Saves the string up to the '\n' portion.
    hostCommand.trim(); //Trims the string for clarity
    if(hostCommand.equalsIgnoreCase("READ_PH")) { //Begins reading the pH if the message is "READ_PH"
      float pHFinal = stableReading(10, 0.05, 500, "pH"); //Saves the stable pH value, which is found with the following consecutive measurements, tolerance, and time rate
      Serial.println("pH: " + String(pHFinal)); //Prints the value back to the host code, to be saved into a csv. file
    }
  }
}

float whatValuepH (int bufferNumber) {
  int pHBuffer = 0; //Local variable used to hold the value of the input pH.
  Serial.println("PH_BUFFER_" + String(bufferNumber) + ":");
  while(pHBuffer == 0) {
    if(Serial.available() > 0) {
      pHBuffer = Serial.parseInt(); //Waits for a user to input the pH value, and will not continue until a non-trivial value is entered.
    }
  }
  return pHBuffer; //This will return the value back to the central program for later use.
}

int readVolts () {
  float voltBuffer = stableReading(10, 2, 500, ""); //Saves the stable milivolt value, which is found with the following consecutive measurements, tolerance, and time rate
  return (int) voltBuffer; //Returns the voltage as an integer
}

float calculateSlope (float y2, float y1, int x2, int x1) {
  float slope = 0.000;
  float deltay = 0;
  int deltax = 0;
  deltay = y2 - y1;
  deltax = x2 - x1;
  slope = deltay / (float)deltax; //Slope calculations to find the slope.
  return slope; //This will return the value back to the central program for later use.
}

float calculateIntercept (float y2, float y1, int x2, int x1, float m) {
  float b = 0.000;
  float b1 = 0.000;
  float b2 = 0.000;
  b1 = y1 - (m * x1); //Intercept calculation for first pH value.
  b2 = y2 - (m * x2); //Intercept calculation for second pH value.
  b = (b1 + b2) / 2; //In the event where b1 and b2 are different (for whatever reason), this will use the average of the two.
  return b; //Intercept calculation for first pH value.
}

float stableReading(int count, float tolerance, int rate, String reading) {
  int counter = 0; //Integer variable to count the number of consecutive readings
  float prev = 0.00; //Decimal variable to hold the previous cycle's value
  while(counter < count) { //Keeps looping until count consecutiv readings have been reached.
    float cur = analogRead(pHProbe); //Reads the current milivolt value from the pH probe.
    if(reading == "pH") { 
      cur = cur * pHSlope + pHIntercept; //Converts the milivolt value into a pH value if we are reading for pH
    }
    Serial.println("Currently reading" + String(cur)); //Prints the value to let the user know
    if(cur > (prev - tolerance) &&  cur < (prev + tolerance)) {
      counter++; //Increments the counter if the value is within tolerance
    }
    else {
      counter = 0; //Resets the counter if we are not within tolerance
    }
    prev = cur; //Saves the current value to the previous value
    delay(rate); //Delays the program to for a time rate between measurements. Quickest run time = count * time rate
  }
  return prev; //Returns the last value of the iteration, since the nine ones before it were within tolerance
}
