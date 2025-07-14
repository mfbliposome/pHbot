int pHProbe = A7; // change # to corresponding analog pin if needed
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
  pHValue1 = whatValuepH(1); // Preps first pH value, waits for user input
  pHVolts1 = readVolts();    // Measures first pH volts
  pHValue2 = whatValuepH(2); // Preps second pH value, waits for user input
  pHVolts2 = readVolts();    // Measures second pH volts
  pHSlope = calculateSlope(pHValue2, pHValue1, pHVolts2, pHVolts1);       // Calculate slope
  pHIntercept = calculateIntercept(pHValue2, pHValue1, pHVolts2, pHVolts1, pHSlope); // Calculate intercept

  Serial.println("CALIBRATION_COMPLETE");  // Exactly this to trigger host menu
}

void loop() {
  if (Serial.available() > 0) {
    String hostCommand = Serial.readStringUntil('\n');
    hostCommand.trim();
    if (hostCommand.equalsIgnoreCase("READ_PH")) {
      float pHFinal = stableReading(10, 0.05, 500, "pH");
      Serial.println("pH:" + String(pHFinal));
    }
  }
}

float whatValuepH(int bufferNumber) {
  int pHBuffer = 0;
  Serial.println("PH_BUFFER_" + String(bufferNumber) + ":");  // Must match host
  while (pHBuffer == 0) {
    if (Serial.available() > 0) {
      pHBuffer = Serial.parseInt();
    }
  }
  return pHBuffer;
}

int readVolts() {
  float voltBuffer = stableReading(10, 2, 500, "");
  return (int)voltBuffer;
}

float calculateSlope(float y2, float y1, int x2, int x1) {
  float deltay = y2 - y1;
  int deltax = x2 - x1;
  return deltay / (float)deltax;
}

float calculateIntercept(float y2, float y1, int x2, int x1, float m) {
  float b1 = y1 - (m * x1);
  float b2 = y2 - (m * x2);
  return (b1 + b2) / 2;
}

float stableReading(int count, float tolerance, int rate, String reading) {
  int counter = 0;
  float prev = 0.00;
  while (counter < count) {
    float cur = analogRead(pHProbe);
    if (reading == "pH") {
      cur = cur * pHSlope + pHIntercept;
    }
    Serial.println("Currently reading" + String(cur));
    if (cur > (prev - tolerance) && cur < (prev + tolerance)) {
      counter++;
    } else {
      counter = 0;
    }
    prev = cur;
    delay(rate);
  }
  return prev;
}
