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


def send_robot_command(cmd, wait=0.05):
    if not cmd.strip():
        return None
    robot_ser.write((cmd + '\r\n').encode())
    print(f"Robot >>> {cmd}")

    start_time = time.time()
    while True:
        if robot_ser.in_waiting:
            line = robot_ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Robot <<< {line}")
            if line.startswith('ok'):
                return None
        if time.time() - start_time > 10:
            print(f"Warning: No 'ok' from robot for command '{cmd}', continuing anyway.")
            return None


def read_ph_from_arduino():
    arduino_ser.reset_input_buffer()
    arduino_ser.reset_output_buffer()
    arduino_ser.write(b'READ_PH\n')
    while True:
        if arduino_ser.in_waiting:
            line = arduino_ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Arduino <<< {line}")
            if line.startswith("pH:"):
                try:
                    return float(line.split(":")[1])
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


def expand_well_ranges(well_input):
    def well_to_index(well):
        match = re.fullmatch(r'([A-Ha-h])(\d{1,2})', well.strip())
        if not match:
            raise ValueError(f"Invalid well format: '{well}'")
        row = match.group(1).upper()
        col = int(match.group(2))
        return row, col

    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    all_wells = []

    entries = [entry.strip() for entry in well_input.split(',') if entry.strip()]
    for entry in entries:
        if '-' in entry:
            start, end = [e.strip() for e in entry.split('-')]
            start_row, start_col = well_to_index(start)
            end_row, end_col = well_to_index(end)

            start_idx = rows.index(start_row)
            end_idx = rows.index(end_row)

            if start_idx > end_idx or (start_idx == end_idx and start_col > end_col):
                raise ValueError(f"Invalid range: {entry}")

            for r_idx in range(start_idx, end_idx + 1):
                row = rows[r_idx]
                col_start = start_col if r_idx == start_idx else 1
                col_end = end_col if r_idx == end_idx else 12
                for col in range(col_start, col_end + 1):
                    all_wells.append(f"{row}{col}")
        else:
            row, col = well_to_index(entry)
            all_wells.append(f"{row}{col}")
    return all_wells


def dip_and_read_ph(well, x, y, dip_z, safe_z=180, wait_before_read=3):
    send_robot_command(f"G00 X{x} Y{y}")    # Move to XY first
    send_robot_command(f"G01 Z{dip_z}")     # Dip down - wait for move to finish (wait for 'ok')

    print(f"Waiting {wait_before_read}s for probe to settle in {well}...")
    time.sleep(wait_before_read)             # Delay only AFTER dip is done

    ph_value = read_ph_from_arduino()
    if ph_value is not None:
        print(f"pH reading at {well}: {ph_value}")
        send_robot_command(f"G00 Z{safe_z}")  # Raise probe back to safe height
        return ph_value
    else:
        print(f"Invalid pH reading at {well}, retrying...")
        send_robot_command(f"G00 Z{safe_z}")
        time.sleep(1)
        # Optional: could implement retry here


def perform_wash_cycle(wash_x, wash_y, dip_z, safe_z=180, swirl_radius=1.0):
    send_robot_command(f"G00 X{wash_x} Y{wash_y}")
    send_robot_command(f"G01 Z{dip_z}")

    swirl_path = [
        (wash_x + swirl_radius, wash_y, swirl_radius, 0),
        (wash_x, wash_y - swirl_radius, 0, -swirl_radius),
        (wash_x - swirl_radius, wash_y, -swirl_radius, 0),
        (wash_x, wash_y + swirl_radius, 0, swirl_radius),
    ]
    for x, y, i, j in swirl_path:
        send_robot_command(f"G2 X{x:.2f} Y{y:.2f} I{i:.2f} J{j:.2f}")


def main():
    wait_for_calibration()

    wells_input = input("Enter well ranges (e.g. A1-B4, B6, B8-B12): ").strip()
    if not wells_input:
        print("No wells provided, exiting.")
        return

    try:
        wells = expand_well_ranges(wells_input)
    except ValueError as e:
        print(f"Error in input: {e}")
        return

    print("Starting G-code and pH reading sequence...\n")

    send_robot_command("M17 ; Enable motors")
    send_robot_command("G21 ; Set units to mm")
    send_robot_command("G90 ; Absolute positioning")
    send_robot_command("G00 Z180 ; Safe height start")

    pH_readings = {}

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

            ph_sample = dip_and_read_ph(well, x, y, dip_sample_z, safe_z)
            pH_readings[well] = ph_sample

            perform_wash_cycle(wash_x, wash_y, dip_wash_z, safe_z, circle_radius)

            print(f"Waiting 3s for probe to settle in wash well...")
            time.sleep(3)

            ph_wash = read_ph_from_arduino()
            while ph_wash is None:
                print("Invalid pH reading at wash well, retrying dip and read...")
                send_robot_command(f"G00 Z{safe_z}")
                time.sleep(1)
                send_robot_command(f"G01 Z{dip_wash_z}")
                time.sleep(3)
                ph_wash = read_ph_from_arduino()

            print(f"pH reading at wash well: {ph_wash}")
            send_robot_command(f"G00 Z{safe_z}")

            pH_readings[f"{well}_wash"] = ph_wash

        except ValueError as e:
            print(f"Error with well {well}: {e}")

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
