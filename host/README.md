Whats Done: 
- The robot listens for G-code over one serial connection. Each well location (like "A1" or "B3") gets translated into X/Y coordinates, and the robot moves there, dips into the sample, and waits for confirmation before continuing.

- At the same time, the Arduino listens over another serial line. When the robot is dipped in, the script tells the Arduino to read the pH. It waits for a stable response like pH:7.24 and grabs the number when ready.

- After each sample, the robot moves to a wash station. It performs a cleaning movement in a small swirl pattern and then reads the pH again to check for contamination or drift.

- Both readings—sample and wash—are stored in a CSV file in the Downloads folder. Each row lists the well ID, sample pH, and wash pH so everything stays organized and easy to track.

- The script starts everything off by setting up both serial ports, enabling the robot motors, and resetting both devices. After that, it handles all the coordination on its own.

- The system relies on consistent hardware response—so if the Arduino is flashed with the correct firmware and the robot accepts G-code, the whole thing runs on just a single line: main("A1, B1, C1")

- The script then writes all the data to CSV


Whats still needed: 
- The plate holder design is subject to change so place holder coordinates are still being used until changes are ready to be made.

- More calibration tests with more expensive pH probe to ensure calibration truely is being done within the code accurately (seems to with the cheap probe). 
