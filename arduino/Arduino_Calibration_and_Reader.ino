// === Arduino Sketch: pH Reader with G-code Compatibility ===

int pHProbe = A7;
int pHVolts = 0;
float pHConverter = -0.0273;  // Your calibrated slope
float pHAdjuster = 15.546;    // Your calibrated intercept
float pHValue = 0.00;

void setup() {
  Serial.begin(9600);
  pinMode(pHProbe, INPUT);
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd.equalsIgnoreCase("READ_PH")) {
      // --- Stabilize pH reading ---
      int stableCounter = 0;
      float prevValue = 0;

      while (stableCounter < 10) {
        pHVolts = analogRead(pHProbe);
        pHValue = pHConverter * pHVolts + pHAdjuster;

        if (abs(pHValue - prevValue) < 0.05) {
          stableCounter++;
        } else {
          stableCounter = 0;
        }

        prevValue = pHValue;
        delay(500);  // wait between samples
      }

      Serial.print("pH:");
      Serial.println(pHValue, 2);  // send value with 2 decimal places
    } else {
      // --- Default response for G-code-style commands ---
      // You can optionally parse actual movement commands here
      Serial.println("ok");
    }
  }
}