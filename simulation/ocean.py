import random
import os
import math
from datetime import datetime, timedelta

from openpyxl import Workbook, load_workbook


# ============================================================
# POLAR OCEAN SIMULATOR - VERSION 2
# ============================================================


class PolarOcean:

    def __init__(self):

        # ----------------------------------------------------
        # Initial buoy location
        # Southern Ocean
        # ----------------------------------------------------

        self.latitude = -60.0
        self.longitude = 20.0

        # ----------------------------------------------------
        # Ocean conditions
        # ----------------------------------------------------

        self.temperature = -0.5
        self.salinity = 33.8
        self.pressure = 1005.0
        self.wind_speed = 10.0
        self.humidity = 85.0
        self.wave_height = 2.0

        # ----------------------------------------------------
        # Ocean current
        # ----------------------------------------------------

        self.current_speed = 0.30
        self.current_direction = 180.0

        # ----------------------------------------------------
        # Sea ice
        # ----------------------------------------------------

        self.ice_concentration = 20.0
        self.ice_thickness = 0.20

        # ----------------------------------------------------
        # Buoy movement
        # ----------------------------------------------------

        self.total_drift_km = 0.0

        # ----------------------------------------------------
        # Simulation time
        # ----------------------------------------------------

        self.time = datetime.now()


    # ========================================================
    # GENERATE ONE OCEAN OBSERVATION
    # ========================================================

    def generate_conditions(self):

        # ====================================================
        # 1. TEMPERATURE
        # ====================================================

        self.temperature += random.uniform(
            -0.08,
            0.08
        )

        self.temperature = max(
            -2.0,
            min(3.0, self.temperature)
        )


        # ====================================================
        # 2. SALINITY
        # ====================================================

        self.salinity += random.uniform(
            -0.03,
            0.03
        )

        self.salinity = max(
            32.5,
            min(35.5, self.salinity)
        )


        # ====================================================
        # 3. ATMOSPHERIC PRESSURE
        # ====================================================

        self.pressure += random.uniform(
            -3,
            3
        )

        self.pressure = max(
            950,
            min(1030, self.pressure)
        )


        # ====================================================
        # 4. WIND
        # ====================================================

        self.wind_speed += random.uniform(
            -2,
            2
        )

        self.wind_speed = max(
            2,
            min(40, self.wind_speed)
        )


        # ====================================================
        # 5. STORM EVENT
        # ====================================================

        storm_probability = random.random()

        if storm_probability < 0.08:

            self.pressure -= random.uniform(
                10,
                25
            )

            self.wind_speed += random.uniform(
                8,
                18
            )


        self.pressure = max(
            930,
            min(1030, self.pressure)
        )

        self.wind_speed = max(
            2,
            min(40, self.wind_speed)
        )


        # ====================================================
        # 6. HUMIDITY
        # ====================================================

        self.humidity += random.uniform(
            -2,
            2
        )

        self.humidity = max(
            60,
            min(100, self.humidity)
        )


        # ====================================================
        # 7. WAVES
        #
        # Stronger wind creates larger waves.
        # ====================================================

        target_wave_height = (
            self.wind_speed * 0.15
        )

        self.wave_height += (
            target_wave_height
            - self.wave_height
        ) * 0.3

        self.wave_height += random.uniform(
            -0.2,
            0.2
        )

        self.wave_height = max(
            0.2,
            min(10, self.wave_height)
        )


        # ====================================================
        # 8. OCEAN CURRENT
        # ====================================================

        self.current_speed += random.uniform(
            -0.05,
            0.05
        )

        self.current_speed = max(
            0.05,
            min(2.5, self.current_speed)
        )


        # Current direction slowly changes

        self.current_direction += random.uniform(
            -8,
            8
        )

        self.current_direction %= 360


        # ====================================================
        # 9. SEA ICE CONCENTRATION
        #
        # Colder water → more ice.
        # Warmer water → less ice.
        # ====================================================

        if self.temperature < -0.8:

            self.ice_concentration += random.uniform(
                0,
                2
            )

        elif self.temperature > 0.5:

            self.ice_concentration -= random.uniform(
                0,
                2
            )

        else:

            self.ice_concentration += random.uniform(
                -0.5,
                0.5
            )


        self.ice_concentration = max(
            0,
            min(100, self.ice_concentration)
        )


        # ====================================================
        # 10. ICE THICKNESS
        # ====================================================

        if self.ice_concentration > 50:

            self.ice_thickness += random.uniform(
                -0.02,
                0.03
            )

        else:

            self.ice_thickness -= random.uniform(
                0,
                0.02
            )


        self.ice_thickness = max(
            0,
            min(3.0, self.ice_thickness)
        )


        # ====================================================
        # 11. BUOY DRIFT
        #
        # Ocean current moves the buoy.
        # Wind also contributes to drift.
        # ====================================================

        time_hours = 10 / 60

        current_distance = (
            self.current_speed
            * 3.6
            * time_hours
        )

        wind_distance = (
            self.wind_speed
            * 0.01
            * time_hours
        )

        drift_distance = (
            current_distance
            + wind_distance
        )


        self.total_drift_km += drift_distance


        # ====================================================
        # 12. UPDATE BUOY LOCATION
        # ====================================================

        direction_rad = math.radians(
            self.current_direction
        )

        # Approximate movement

        north_movement = (
            drift_distance
            * math.cos(direction_rad)
        )

        east_movement = (
            drift_distance
            * math.sin(direction_rad)
        )


        # Convert km → degrees

        self.latitude += (
            north_movement / 111
        )

        self.longitude += (
            east_movement
            / (
                111
                * math.cos(
                    math.radians(
                        self.latitude
                    )
                )
            )
        )


        # ====================================================
        # 13. ADVANCE SIMULATION TIME
        # ====================================================

        self.time += timedelta(
            minutes=10
        )


        # ====================================================
        # 14. CREATE OBSERVATION
        # ====================================================

        observation = {

            "timestamp":
                self.time.isoformat(),

            "latitude":
                round(
                    self.latitude,
                    5
                ),

            "longitude":
                round(
                    self.longitude,
                    5
                ),

            "temperature_c":
                round(
                    self.temperature,
                    2
                ),

            "salinity_psu":
                round(
                    self.salinity,
                    2
                ),

            "pressure_hpa":
                round(
                    self.pressure,
                    2
                ),

            "wind_speed_ms":
                round(
                    self.wind_speed,
                    2
                ),

            "humidity_percent":
                round(
                    self.humidity,
                    2
                ),

            "wave_height_m":
                round(
                    self.wave_height,
                    2
                ),

            "current_speed_ms":
                round(
                    self.current_speed,
                    2
                ),

            "current_direction_deg":
                round(
                    self.current_direction,
                    2
                ),

            "ice_concentration_percent":
                round(
                    self.ice_concentration,
                    2
                ),

            "ice_thickness_m":
                round(
                    self.ice_thickness,
                    2
                ),

            "buoy_drift_km":
                round(
                    self.total_drift_km,
                    3
                )
        }


        return observation


# ============================================================
# START SIMULATION
# ============================================================

print()
print("================================================")
print("       POLARSENSE AI - POLAR OCEAN V2")
print("================================================")
print()


ocean = PolarOcean()

data = []


# ============================================================
# GENERATE 500 OBSERVATIONS
# ============================================================

for i in range(500):

    observation = (
        ocean.generate_conditions()
    )

    data.append(
        observation
    )

    print(
        observation
    )


# ============================================================
# CREATE DATA FOLDER
# ============================================================

os.makedirs(
    "data",
    exist_ok=True
)


# ============================================================
# EXCEL FILE
# ============================================================

file_path = (
    "data/ocean_simulations.xlsx"
)


# ============================================================
# OPEN OR CREATE EXCEL FILE
# ============================================================

if os.path.exists(
    file_path
):

    workbook = load_workbook(
        file_path
    )

else:

    workbook = Workbook()

    default_sheet = (
        workbook.active
    )

    workbook.remove(
        default_sheet
    )


# ============================================================
# FIND NEXT RUN NUMBER
# ============================================================

existing_runs = []


for sheet_name in (
    workbook.sheetnames
):

    if sheet_name.startswith(
        "Run_"
    ):

        try:

            run_number = int(
                sheet_name.split("_")[1]
            )

            existing_runs.append(
                run_number
            )

        except ValueError:

            pass


if existing_runs:

    next_run = (
        max(existing_runs)
        + 1
    )

else:

    next_run = 1


sheet_name = (
    f"Run_{next_run:03d}"
)


# ============================================================
# CREATE NEW SHEET
# ============================================================

worksheet = (
    workbook.create_sheet(
        sheet_name
    )
)


# ============================================================
# WRITE HEADERS
# ============================================================

headers = list(
    data[0].keys()
)


for column_number, header in enumerate(
    headers,
    start=1
):

    worksheet.cell(
        row=1,
        column=column_number,
        value=header
    )


# ============================================================
# WRITE DATA
# ============================================================

for row_number, observation in enumerate(
    data,
    start=2
):

    for column_number, header in enumerate(
        headers,
        start=1
    ):

        worksheet.cell(
            row=row_number,
            column=column_number,
            value=observation[header]
        )


# ============================================================
# FORMAT COLUMN WIDTHS
# ============================================================

for column in worksheet.columns:

    max_length = 0

    column_letter = (
        column[0].column_letter
    )

    for cell in column:

        if cell.value is not None:

            cell_length = len(
                str(cell.value)
            )

            max_length = max(
                max_length,
                cell_length
            )

    worksheet.column_dimensions[
        column_letter
    ].width = min(
        max_length + 2,
        30
    )


# ============================================================
# FREEZE HEADER ROW
# ============================================================

worksheet.freeze_panes = "A2"


# ============================================================
# SAVE EXCEL FILE
# ============================================================

workbook.save(
    file_path
)


# ============================================================
# FINISHED
# ============================================================

print()
print("================================================")
print("          SIMULATION COMPLETE")
print("================================================")

print(
    f"Observations generated: {len(data)}"
)

print(
    f"New Excel sheet: {sheet_name}"
)

print(
    f"Excel file: {file_path}"
)

print()
print("New variables added:")
print("  - Ocean current speed")
print("  - Ocean current direction")
print("  - Sea ice concentration")
print("  - Sea ice thickness")
print("  - Buoy latitude")
print("  - Buoy longitude")
print("  - Total buoy drift")

print("================================================")
print()