C- code for the arduino-based interface to the pH probe

Please read for context and download instructions

-The pHBot_Reader.ino file will first calibrate itself using the pHBot_Calibration library code.
It will currently do this during start up, so every time the code is uploaded to the arduino, it will calibrate.
The code is set up so that when the arduino receives a binary bit telling it to start reading, it will begin looking for a pH to send.
As placeholders, the bit is kept on and the send function is not yet written, however this system is subject to change to be compatible with the host code.

-The pHBot_Calibration.zip file is a folder and arduino library containing two files that are responsible for the calibration code.
It is important the folder is extracted into the library arduino folder, or else the code will not work.
When downloading the calibration code, do the following:
*Download the zip.file
*Extract it to Documents\Arduino\libraries
*Ensure that the two files (.cpp and .h) are in a folder that shares the same name
