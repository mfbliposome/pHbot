import re

def get_well_coordinates_from_string(well: str):
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    columns = list(range(1, 13))

    match = re.fullmatch(r'([A-Ha-h])(\d{1,2})', well.strip())
    if not match:
        raise ValueError(f"Invalid well format: '{well}'. Use format like 'A1' to 'H12'.")

    row = match.group(1).upper()
    column = int(match.group(2))

    if row not in rows:
        raise ValueError(f"Invalid row '{row}'. Must be A–H.")
    if column not in columns:
        raise ValueError(f"Invalid column '{column}'. Must be 1–12.")

    x0 = 14.38  # mm from left
    y0 = 74.24  # mm from bottom
    spacing = 9.0

    row_index = rows.index(row)
    x_mm = x0 + (column - 1) * spacing
    y_mm = y0 - row_index * spacing

    return round(x_mm, 2), round(y_mm, 2)

def generate_gcode_for_well(well, wash_x=0, wash_y=0, circle_radius=1.0):
    x, y = get_well_coordinates_from_string(well)
    gcode = []

    gcode.append(f"G00 X{x} Y{y} ; Move to {well.upper()}")
    gcode.append("G01 Z110 ; Dip")
    gcode.append("G00 Z130 ; Retract")

    gcode.append(f"G00 X{wash_x} Y{wash_y} ; Move to wash station")
    gcode.append("G01 Z110 ; Dip in wash")
    gcode.append(f"G2 X{circle_radius} Y0 I{circle_radius} J0 ; Quarter circle")
    gcode.append(f"G2 X0 Y{-circle_radius} I0 J{-circle_radius} ; Quarter circle")
    gcode.append(f"G2 X{-circle_radius} Y0 I{-circle_radius} J0 ; Quarter circle")
    gcode.append(f"G2 X0 Y{circle_radius} I0 J{circle_radius} ; Quarter circle (complete loop)")
    gcode.append("G00 Z130 ; Retract from wash\n")

    return gcode

def main(user_input):
    # user_input = input("Enter well positions (comma-separated, e.g., A1, B2, H12): ")
    
    wells = [w.strip() for w in user_input.split(',') if w.strip()]

    gcode_output = [
        "M17 ; enable motors",
        "G21 ; Set units to mm",
        "G90 ; set absolute positioning",
        "G00 Z130 ; Start at safe height\n"
    ]

    for well in wells:
        try:
            gcode_output.extend(generate_gcode_for_well(well))
        except ValueError as e:
            gcode_output.append(f"; Error with '{well}': {e}")

    # Print all G-code as one list
    print(gcode_output)
    return gcode_output

if __name__ == "__main__":
    main()
