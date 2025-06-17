int pHProbe = A7; //change # to corresponding analog pin if needed
int pHVolts1 = 0;
int pHVolts2 = 0;
float pHValue1 = 0.00;
float pHValue2 = 0.00;
float pHSlope = 0.0000;
float pHIntercept = 0.0000;

void setup() {
  Serial.begin(9600);
  pinMode(pHProbe, INPUT);

}

void loop() {
  pHValue1 = whatValuepH(1);
  pHVolts1 = readVolts();
  pHValue2 = whatValuepH(2);
  pHVolts2 = readVolts();
  pHSlope = calculateSlope(pHValue2, pHValue1, pHVolts2, pHVolts1);
  pHIntercept = calculateIntercept(pHValue2, pHValue1, pHVolts2, pHVolts1, pHSlope);
  while(2 > 1) {
    Serial.println("The millivolt to pH slope is " + String(pHSlope) + " and the y-intercept is " + String(pHIntercept));
    delay(5000);
  }

}

float whatValuepH (int bufferNumber) {
  float pHBuffer = 0.00;
  Serial.println("pH Value of buffer" + String(bufferNumber) + ":");
  pHBuffer = Serial.read();
  return pHBuffer;
}

int readVolts () {
  int voltBuffer = 0;
  int stableCounter = 0;
  int previousVolt = 0;
  while(stableCounter < 10) {
    int currentVolt = 0;
    currentVolt = analogRead(pHProbe);
    if(currentVolt > (previousVolt - 2) && currentVolt < (previousVolt + 2)) {
      stableCounter++;
    }
    else {
      stableCounter = 0;
    }
    previousVolt = currentVolt;
    delay(500);
  }
  voltBuffer = previousVolt; 
  return voltBuffer;
}

float calculateSlope (float y2, float y1, int x2, int x1) {
  float slope = 0.0000;
  float deltay = 0.00;
  int deltax = 0;
  deltay = y2 - y1;
  deltax = x2 - x2;
  slope = (deltay)/(1000 * deltax);
  return slope;
}

float calculateIntercept (float y2, float y1, int x2, int x1, float m) {
  float b = 0.0000;
  float b1 = 0.0000;
  float b2 = 0.0000;
  b1 = y1 - (m)*(x1)/1000;
  b2 = y2 - (m)*(x2)/1000;
  b = (b1 + b2) / 2;
  return b;
}