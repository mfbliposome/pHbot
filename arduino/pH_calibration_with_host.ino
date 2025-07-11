const int pHProbe = A7;

float pHValue1 = 0.0;
float pHValue2 = 0.0;
int pHVolts1 = 0;
int pHVolts2 = 0;
float pHSlope = 0.0;
float pHIntercept = 0.0;
bool isCalibrated = false;

void setup() {
  Serial.begin(9600);
  pinMode(pHProbe, INPUT);

  // Prompt for buffer 1
  Serial.println("REQUEST_BUFFER_1");
  pHValue1 = waitForFloatFromSerial();  // Wait for host to respond with e.g., 4.00
  delay(10000); // Allow user time to dip into buffer 1
  pHVolts1 = analogRead(pHProbe);       // Record voltage

  // Prompt for buffer 2
  Serial.println("REQUEST_BUFFER_2");
  pHValue2 = waitForFloatFromSerial();  // Wait for host to respond with e.g., 7.00
  delay(10000); // Allow user time to dip into buffer 2
  pHVolts2 = analogRead(pHProbe);       // Record voltage

  // Perform calibration
  pHSlope = (pHValue2 - pHValue1) / float(pHVolts2 - pHVolts1);
  pHIntercept = pHValue1 - pHSlope * pHVolts1;

  Serial.print("CALIBRATION_COMPLETE Slope:");
  Serial.print(pHSlope, 6);
  Serial.print(" Intercept:");
  Serial.println(pHIntercept, 6);

  isCalibrated = true;
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.equalsIgnoreCase("READ_PH") && isCalibrated) {
      float stablePH = readStablePH();
      Serial.print("pH:");
      Serial.println(stablePH, 3);
    }
  }
}

float waitForFloatFromSerial() {
  while (true) {
    if (Serial.available()) {
      float val = Serial.parseFloat();
      if (val > 0 && val < 14) {
        // Flush any trailing characters
        while (Serial.available()) Serial.read();
        return val;
      }
    }
    delay(100);
  }
}

float readStablePH() {
  const int requiredStableReads = 10;
  const float tolerance = 0.05;
  int stableCount = 0;
  float lastPH = 0.0;
  float currentPH = 0.0;

  while (stableCount < requiredStableReads) {
    int raw = analogRead(pHProbe);
    currentPH = raw * pHSlope + pHIntercept;

    if (abs(currentPH - lastPH) < tolerance) {
      stableCount++;
    } else {
      stableCount = 0;
    }
    lastPH = currentPH;
    delay(500);
  }
  return currentPH;
}
