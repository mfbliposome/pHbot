import serial
import time
import re
import csv
import os

# Serial settings
ROBOT_PORT = 'COM3'
ARDUINO_PORT = 'COM5'
ROBOT_BAUD = 115200
ARDUINO_BAUD = 9600

robot_ser = serial.Serial(ROBOT_PORT, ROBOT_BAUD, timeout=2)
time.sleep(2)
arduino_ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=10)
time.sleep(2)

def get_well_coordinates_from_string(well: str):
    """
    Returns XY (in mm) for a given 96-well plate location using A1 and H12 as reference points.
    """
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    columns = list(range(1, 13))

    A1_X, A1_Y = 118.0, 142.0
    H12_X, H12_Y = 217.0, 80.0
    spacing_x = (H12_X - A1_X) / 11
    spacing_y = (A1_Y - H12_Y) / 7

    match = re.fullmatch(r'([A-Ha-h])(\d{1,2})', well.strip())
    if not match:
        raise ValueError(f"Invalid well format: '{well}'")
    row = match.group(1).upper()
    col = int(match.group(2))
    if row not in rows or col not in columns:
        raise ValueError("Invalid row or column.")

    col_idx = col - 1
    row_idx = rows.index(row)
    dist_to_A1 = col_idx + row_idx
    dist_to_H12 = (11 - col_idx) + (7 - row_idx)

    if dist_to_A1 <= dist_to_H12:
        x = A1_X + col_idx * spacing_x
        y = A1_Y - row_idx * spacing_y
    else:
        x = H12_X - (11 - col_idx) * spacing_x
        y = H12_Y + (7 - row_idx) * spacing_y

    return round(x, 3), round(y, 3)

def send_robot_command(cmd, wait=0.05):
    if not cmd.strip():
        return
    robot_ser.write((cmd + '\r\n').encode())
    print(f"Robot >>> {cmd}")
    start = time.time()
    while True:
        if robot_ser.in_waiting:
            line = robot_ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Robot <<< {line}")
            if line.startswith("ok"):
                return
        if time.time() - start > 10:
            print(f"Timeout on robot for '{cmd}' — continuing anyway.")
            return

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
                    print("Error parsing pH — retrying...")

def wait_for_calibration():
    print("Calibrating Arduino...")
    while True:
        if arduino_ser.in_waiting:
            line = arduino_ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Arduino <<< {line}")
            if "PH_BUFFER_1:" in line:
                val1 = input("Enter pH Buffer 1 (e.g. 4.00): ").strip()
                arduino_ser.write((val1 + "\n").encode())
            elif "PH_BUFFER_2:" in line:
                val2 = input("Enter pH Buffer 2 (e.g. 7.00): ").strip()
                arduino_ser.write((val2 + "\n").encode())
            elif "CALIBRATION_COMPLETE" in line:
                print("Calibration complete.")
                break

def expand_well_ranges(well_input):
    def parse(well):
        m = re.fullmatch(r'([A-Ha-h])(\d{1,2})', well.strip())
        if not m:
            raise ValueError(f"Bad format: '{well}'")
        return m.group(1).upper(), int(m.group(2))

    rows = ['A','B','C','D','E','F','G','H']
    wells = []
    entries = [w.strip() for w in well_input.split(',') if w.strip()]
    for entry in entries:
        if '-' in entry:
            start, end = entry.split('-')
            sr, sc = parse(start)
            er, ec = parse(end)
            for r_idx in range(rows.index(sr), rows.index(er)+1):
                r = rows[r_idx]
                c_start = sc if r == sr else 1
                c_end = ec if r == er else 12
                for c in range(c_start, c_end+1):
                    wells.append(f"{r}{c}")
        else:
            r, c = parse(entry)
            wells.append(f"{r}{c}")
    return wells

def dip_and_read_ph(well, x, y, dip_z, safe_z=180, settle_sec=3):
    # Move XY to well
    send_robot_command(f"G00 X{x} Y{y}")
    send_robot_command("M400")  # wait for move to complete physically

    # Dip probe down into well
    send_robot_command(f"G01 Z{dip_z}")
    send_robot_command("M400")  # wait for dip move to complete physically

    print(f"Settling probe in well {well} for {settle_sec} seconds...")
    time.sleep(settle_sec)

    ph = read_ph_from_arduino()

    # Retract probe to safe height
    send_robot_command(f"G00 Z{safe_z}")
    send_robot_command("M400")  # wait for retraction move to finish

    return ph

def perform_wash_cycle(wash_x, wash_y, dip_z, safe_z=180, swirl_radius=1.0):
    send_robot_command(f"G00 X{wash_x} Y{wash_y}")
    send_robot_command("M400")

    send_robot_command(f"G01 Z{dip_z}")
    send_robot_command("M400")

    for x, y, i, j in [
        (wash_x + swirl_radius, wash_y, swirl_radius, 0),
        (wash_x, wash_y - swirl_radius, 0, -swirl_radius),
        (wash_x - swirl_radius, wash_y, -swirl_radius, 0),
        (wash_x, wash_y + swirl_radius, 0, swirl_radius),
    ]:
        send_robot_command(f"G2 X{x:.2f} Y{y:.2f} I{i:.2f} J{j:.2f}")

def main():
    wait_for_calibration()
    well_input = input("Enter well ranges (e.g. A1-B4, C6): ").strip()
    if not well_input:
        print("No wells given.")
        return
    try:
        wells = expand_well_ranges(well_input)
    except ValueError as e:
        print(e)
        return

    print("Starting robot and pH workflow...\n")

    send_robot_command("M17 ; Enable motors")
    send_robot_command("G21 ; mm units")
    send_robot_command("G90 ; Absolute")
    send_robot_command("G00 Z180 ; Start height")
    send_robot_command("M400")

    readings = {}
    wash_x, wash_y = 73, 151
    dip_z_sample = 165
    dip_z_wash = 140
    safe_z = 180
    swirl_radius = 1.0

    for well in wells:
        print(f"\nProcessing {well} ...")
        try:
            x, y = get_well_coordinates_from_string(well)
            ph_sample = dip_and_read_ph(well, x, y, dip_z_sample, safe_z)
            readings[well] = ph_sample

            perform_wash_cycle(wash_x, wash_y, dip_z_wash, safe_z, swirl_radius)
            time.sleep(3)

            ph_wash = read_ph_from_arduino()
            while ph_wash is None:
                send_robot_command(f"G00 Z{safe_z}")
                send_robot_command("M400")
                time.sleep(1)
                send_robot_command(f"G01 Z{dip_z_wash}")
                send_robot_command("M400")
                time.sleep(3)
                ph_wash = read_ph_from_arduino()
            readings[f"{well}_wash"] = ph_wash
            send_robot_command(f"G00 Z{safe_z}")
            send_robot_command("M400")

        except ValueError as e:
            print(f"Skipping {well}: {e}")

    downloads = os.path.join(os.path.expanduser("~"), "Downloads", "pH_Readings")
    os.makedirs(downloads, exist_ok=True)
    csv_file = os.path.join(downloads, "ph_readings.csv")

    print(f"\nSaving readings to {csv_file} ...")
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Well', 'pH_Sample', 'pH_Wash'])
        writer.writeheader()
        for well in wells:
            writer.writerow({
                'Well': well,
                'pH_Sample': readings.get(well),
                'pH_Wash': readings.get(f"{well}_wash")
            })

    print("\nDone! pH summary:")
    for well in wells:
        print(f"{well}: Sample = {readings.get(well)}, Wash = {readings.get(f'{well}_wash')}")

if __name__ == "__main__":
    main()
