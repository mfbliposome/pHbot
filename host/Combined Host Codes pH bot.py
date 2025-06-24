import serial
import time
import re

# Serial port settings
ROBOT_PORT = 'COM3'    # Change as needed
ARDUINO_PORT = 'COM5'  # Change as needed
ROBOT_BAUD = 115200
ARDUINO_BAUD = 9600

# Connect to robot controller (for G-code commands)
robot_ser = serial.Serial(ROBOT_PORT, ROBOT_BAUD, timeout=2)
time.sleep(2)  # Let robot initialize

# Connect to Arduino (for pH readings)
arduino_ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=10)
time.sleep(2)  # Let Arduino initialize


def get_well_coordinates_from_string(well: str):
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    columns = list(range(1, 13))
    match = re.fullmatch(r'([A-Ha-h])(\d{1,2})', well.strip())
    if not match:
        raise ValueError(f"Invalid well format: '{well}'. Use format like 'A1' to 'H12'.")
    row = match.group(1).upper()
    column = int(match.group(2))
    if row not in rows or column not in columns:
        raise ValueError("Invalid well coordinates.")
    x0 = 14.38
    y0 = 74.24
    spacing = 9.0
    x_mm = x0 + (column - 1) * spacing
    y_mm = y0 - rows.index(row) * spacing
    return round(x_mm, 2), round(y_mm, 2)


def generate_gcode_for_well(well, wash_x=0, wash_y=0, circle_radius=1.0):
    x, y = get_well_coordinates_from_string(well)
    gcode = [
        f"G00 X{x} Y{y} ; Move to {well.upper()}",
        "G01 Z110 ; Dip",
        "READ_PH ; Trigger pH read",  # Custom command to trigger pH reading
        "G00 Z130 ; Retract",
        f"G00 X{wash_x} Y{wash_y} ; Move to wash station",
        "G01 Z110 ; Dip in wash",
        f"G2 X{circle_radius} Y0 I{circle_radius} J0 ; Quarter circle",
        f"G2 X0 Y{-circle_radius} I0 J{-circle_radius} ; Quarter circle",
        f"G2 X{-circle_radius} Y0 I{-circle_radius} J0 ; Quarter circle",
        f"G2 X0 Y{circle_radius} I0 J{circle_radius} ; Quarter circle (complete loop)",
        "READ_PH ; Trigger pH read at wash",
        "G00 Z130 ; Retract from wash"
    ]
    return gcode


def send_robot_command(cmd, wait=0.2):
    """Send G-code to robot and wait for 'ok'."""
    if not cmd.strip():
        return None
    robot_ser.write((cmd + '\r\n').encode())
    print(f"Robot >>> {cmd}")
    time.sleep(wait)
    while True:
        if robot_ser.in_waiting:
            line = robot_ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Robot <<< {line}")
            if line.startswith('ok'):
                return None


def read_ph_from_arduino():
    """Send READ_PH command to Arduino and read pH line."""
    arduino_ser.reset_input_buffer()
    arduino_ser.write(b'READ_PH\n')  # You should have Arduino listen for this string if needed
    timeout = time.time() + 10  # 10 seconds timeout
    while time.time() < timeout:
        if arduino_ser.in_waiting:
            line = arduino_ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Arduino <<< {line}")
            if line.startswith("pH:"):
                try:
                    value = float(line.split(":")[1])
                    return value
                except ValueError:
                    return None
    return None


def main(wells_input):
    wells = [w.strip() for w in wells_input.split(',') if w.strip()]
    print("Starting G-code and pH reading sequence...\n")
    pH_readings = {}

    # Prepare robot
    send_robot_command("M17 ; Enable motors")
    send_robot_command("G21 ; Set units to mm")
    send_robot_command("G90 ; Absolute positioning")
    send_robot_command("G00 Z130 ; Safe height start")

    # Coordinates for wash well (example - adjust accordingly)
    wash_x, wash_y = 10, 10

    for well in wells:
        print(f"\nProcessing well {well} ...")
        try:
            gcode_commands = generate_gcode_for_well(well, wash_x=wash_x, wash_y=wash_y)
            for cmd in gcode_commands:
                base_cmd = cmd.split(';')[0].strip()
                comment = cmd.split(';')[1].strip() if ';' in cmd else ''

                if base_cmd == "READ_PH":
                    # Read pH from Arduino
                    ph_value = read_ph_from_arduino()
                    if "wash" in comment.lower():
                        pH_readings[f"{well}_wash"] = ph_value
                        print(f"pH reading at wash: {ph_value}")
                    else:
                        pH_readings[well] = ph_value
                        print(f"pH reading at sample: {ph_value}")
                else:
                    send_robot_command(base_cmd)

        except ValueError as e:
            print(f"Error with well {well}: {e}")

    print("\nAll done! Stable pH Readings:")
    for well, val in pH_readings.items():
        print(f"{well}: {val if val is not None else 'Failed to read'}")

    return pH_readings


if __name__ == "__main__":
    wells_to_run = "A1"
    main(wells_to_run)