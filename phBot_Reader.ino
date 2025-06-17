int pHProbe = A7; //change # to corresponding analog pin if needed
int pHVolts = 0;
float pHConverter = -0.0273;
float pHAdjuster = 15.546; //Gravity Probe: 15.6(1-2)8 or 15.6(4-5)5. Plastic Probe: 15.5(3-4)6
float pHValue = 0.00;

void setup() {
  Serial.begin(9600);
  pinMode(pHProbe, INPUT);
}

void loop() {
  pHVolts = analogRead(pHProbe);
  pHValue = pHConverter * pHVolts + pHAdjuster;
  //Serial.println(pHVolts); //Commented out since it's used for verification
  Serial.println(pHValue, 2);
  //The next thing we can try is to collect a stable reading. The way we can make this work is by creating some integer type value at 0 and some conditionals to test for stability.
  //We can use two if-then statements:
  //The first if-then will be our stability counter. Here, we will check if the previous value matches the next value. This requires two parts.
  //  -We must be able to record the previous pH value and compare it to the current pH value, regardless of if it matches.
  //  -We must increase a "stability score" if the current and previous value are the same.
  //The second if-then will be our stability saver. Here, we will "lock" the value so that we have it for later.
  //  -If the stability score is at a high enough value, we consider the probe to be stable enough. For now, we will simply save the stable value to a new variable (eg. stable_value)
  //  -After we have the stable value, we shouldn't be able to save to that variable. Try to use zeros or some other method to prevent the program from trying to overwrite the value.
  delay(500); //I've cut this value in half for more accurate readings, to get an idea on the level of precision (used to be 1000 (1 sec))
}
