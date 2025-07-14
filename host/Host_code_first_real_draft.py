import serial
import time
import re
import csv
import os

# Serial port settings
ROBOT_PORT = 'COM3'    # Change as needed
ARDUINO_PORT = 'COM5'  # Change as needed
ROBOT_BAUD = 115200
ARDUINO_BAUD = 9600

# Connect to robot controller
robot_ser = serial.Serial(ROBOT_PORT, ROBOT_BAUD, timeout=2)
time.sleep(2)

# Connect to Arduino
arduino_ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=10)
time.sleep(2)


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

    base_x = 112.3
    base_y = 143.9
    spacing = 9.0

    x_mm = base_x + (column - 1) * spacing
    y_mm = base_y - rows.index(row) * spacing

    return round(x_mm, 2), round(y_mm, 2)


def send_robot_command(cmd, wait=0.2):
    if not cmd.strip():
        return None
    robot_ser.write((cmd + '\r\n').encode())
    print(f"Robot >>> {cmd}")
    time.sleep(wait)
    # Wait for 'ok' confirmation from robot before continuing
    start_time = time.time()
    while True:
        if robot_ser.in_waiting:
            line = robot_ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Robot <<< {line}")
            if line.startswith('ok'):
                return None
        if time.time() - start_time > 5:
            print(f"Warning: No 'ok' from robot for command '{cmd}', continuing anyway.")
            return None


def read_ph_from_arduino():
    arduino_ser.reset_input_buffer()
    arduino_ser.reset_output_buffer()
    arduino_ser.write(b'READ_PH\n')
    while True:  # Keep reading until a valid pH line received
        if arduino_ser.in_waiting:
            line = arduino_ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Arduino <<< {line}")
            if line.startswith("pH:"):
                try:
                    value = float(line.split(":")[1])
                    return value
                except ValueError:
                    print("Failed to parse pH value, retrying...")


def wait_for_calibration():
    print("Starting Arduino calibration...")
    while True:
        if arduino_ser.in_waiting:
            line = arduino_ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Arduino <<< {line}")
            if "PH_BUFFER_1:" in line:
                val1 = input("Enter pH value for Buffer 1 (e.g. 4.00): ").strip()
                arduino_ser.write((val1 + "\n").encode())
            elif "PH_BUFFER_2:" in line:
                val2 = input("Enter pH value for Buffer 2 (e.g. 7.00): ").strip()
                arduino_ser.write((val2 + "\n").encode())
            elif "CALIBRATION_COMPLETE" in line:
                print("Arduino calibration finished.")
                break


def dip_and_read_ph(well, x, y, dip_z, safe_z=180, wait_before_read=3):
    """
    Dips into well, waits, reads pH; retries until successful.
    Retracts and dips again if pH reading fails.
    """
    while True:
        send_robot_command(f"G00 X{x} Y{y}")          # Move to XY
        send_robot_command(f"G01 Z{dip_z}")           # Dip to Z
        print(f"Waiting {wait_before_read}s for probe to settle in {well}...")
        time.sleep(wait_before_read)

        ph_value = read_ph_from_arduino()
        if ph_value is not None:
            print(f"pH reading at {well}: {ph_value}")
            send_robot_command(f"G00 Z{safe_z}")      # Retract
            return ph_value
        else:
            print(f"Invalid pH reading at {well}, retrying...")
            send_robot_command(f"G00 Z{safe_z}")      # Retract before retry
            time.sleep(1)  # brief pause before retry


def main():
    wait_for_calibration()

    wells_input = input("Enter wells to run (comma-separated, e.g. A1,B2,C3): ").strip()
    if not wells_input:
        print("No wells provided, exiting.")
        return

    wells = [w.strip() for w in wells_input.split(',') if w.strip()]

    print("Starting G-code and pH reading sequence...\n")

    send_robot_command("M17 ; Enable motors")
    send_robot_command("G21 ; Set units to mm")
    send_robot_command("G90 ; Absolute positioning")
    send_robot_command("G00 Z180 ; Safe height start")

    pH_readings = {}

    # Coordinates for wash well (fixed correct coords)
    wash_x = 60
    wash_y = 133
    dip_sample_z = 165
    dip_wash_z = 140
    safe_z = 180
    circle_radius = 1.0

    for well in wells:
        print(f"\nProcessing well {well} ...")

        try:
            x, y = get_well_coordinates_from_string(well)

            # Dip into sample well and read pH with retry until success
            ph_sample = dip_and_read_ph(well, x, y, dip_sample_z, safe_z)
            pH_readings[well] = ph_sample

            # After sample read, move to wash well at safe height
            send_robot_command(f"G00 X{wash_x} Y{wash_y}")

            # Dip into wash well
            send_robot_command(f"G01 Z{dip_wash_z}")

            # Circle movement at wash (relative positioning)
            send_robot_command("G91")  # relative mode
            send_robot_command(f"G2 X{circle_radius} Y0 I{circle_radius} J0")
            send_robot_command(f"G2 X0 Y{-circle_radius} I0 J{-circle_radius}")
            send_robot_command(f"G2 X{-circle_radius} Y0 I{-circle_radius} J0")
            send_robot_command(f"G2 X0 Y{circle_radius} I0 J{circle_radius}")
            send_robot_command("G90")  # back to absolute mode

            # Wait for probe to settle in wash well
            print(f"Waiting 3s for probe to settle in wash well...")
            time.sleep(3)

            # Read pH at wash with retry until success
            ph_wash = read_ph_from_arduino()
            while ph_wash is None:
                print("Invalid pH reading at wash well, retrying dip and read...")
                send_robot_command(f"G00 Z{safe_z}")   # retract
                time.sleep(1)
                send_robot_command(f"G01 Z{dip_wash_z}")  # dip again
                time.sleep(3)
                ph_wash = read_ph_from_arduino()

            print(f"pH reading at wash well: {ph_wash}")
            send_robot_command(f"G00 Z{safe_z}")  # retract from wash

            pH_readings[f"{well}_wash"] = ph_wash

        except ValueError as e:
            print(f"Error with well {well}: {e}")

    # Prepare folder path inside Downloads
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    ph_folder = os.path.join(downloads_path, "pH_Readings")
    os.makedirs(ph_folder, exist_ok=True)

    csv_filename = os.path.join(ph_folder, "ph_readings.csv")
    print(f"\nWriting pH readings to {csv_filename} ...")
    with open(csv_filename, mode='w', newline='') as csvfile:
        fieldnames = ['Well', 'pH_Sample', 'pH_Wash']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for well in wells:
            writer.writerow({
                'Well': well,
                'pH_Sample': pH_readings.get(well),
                'pH_Wash': pH_readings.get(f"{well}_wash")
            })

    print("\nAll done! Stable pH Readings saved:")
    for well in wells:
        print(f"{well}: Sample pH = {pH_readings.get(well)}, Wash pH = {pH_readings.get(f'{well}_wash')}")


if __name__ == "__main__":
    main()