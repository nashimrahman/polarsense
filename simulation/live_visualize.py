import os
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# POLARSENSE AI - LIVE TELEMETRY VISUALIZER
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CSV_FILE = os.path.join(
    BASE_DIR,
    "data",
    "live_telemetry.csv"
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "data",
    "plots"
)


# ============================================================
# CREATE OUTPUT FOLDER
# ============================================================

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# CHECK INPUT DATA
# ============================================================

if not os.path.exists(CSV_FILE):

    print()
    print("ERROR: live_telemetry.csv not found.")
    print(f"Expected location: {CSV_FILE}")
    print()

    raise SystemExit(1)


# ============================================================
# READ LIVE TELEMETRY
# ============================================================

print()
print("==========================================")
print("   POLARSENSE AI - LIVE VISUALIZER")
print("==========================================")
print()

print("Reading:")
print(CSV_FILE)
print()

data = pd.read_csv(
    CSV_FILE,
    on_bad_lines="skip"
)

if data.empty:

    print("ERROR: No telemetry records found.")
    raise SystemExit(1)

print(
    f"Telemetry records: {len(data)}"
)


# ============================================================
# TIME AXIS
# ============================================================

if "received_at" in data.columns:

    data["received_at"] = pd.to_datetime(
        data["received_at"],
        errors="coerce"
    )

    data = data.dropna(
        subset=["received_at"]
    )

    data = data.sort_values(
        "received_at"
    )

    time_axis = data["received_at"]

else:

    time_axis = range(
        len(data)
    )


# ============================================================
# HELPER FUNCTION
# ============================================================

def save_plot(
    filename,
    title,
    xlabel,
    ylabel,
    x,
    y,
    label
):

    plt.figure(
        figsize=(10, 5)
    )

    plt.plot(
        x,
        y,
        linewidth=2,
        label=label
    )

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    plt.grid(
        True,
        alpha=0.3
    )

    plt.legend()

    plt.tight_layout()

    output_path = os.path.join(
        OUTPUT_FOLDER,
        filename
    )

    plt.savefig(
        output_path,
        dpi=150
    )

    plt.close()

    print(
        f"Generated: {filename}"
    )


# ============================================================
# 1. TEMPERATURE HISTORY
# ============================================================

if "water_temperature_c" in data.columns:

    temperature = pd.to_numeric(
        data["water_temperature_c"],
        errors="coerce"
    )

    valid_temperature = (
        temperature >= -10
    ) & (
        temperature <= 20
    )

    temperature_data = data.loc[
        valid_temperature
    ].copy()

    temperature_data[
        "water_temperature_c"
    ] = pd.to_numeric(
        temperature_data[
            "water_temperature_c"
        ],
        errors="coerce"
    )

    if not temperature_data.empty:

        if "received_at" in temperature_data.columns:

            temperature_time = (
                temperature_data["received_at"]
            )

        else:

            temperature_time = range(
                len(temperature_data)
            )

        save_plot(
            "temperature_history.png",
            "PolarSense AI - Water Temperature History",
            "Time",
            "Water Temperature (°C)",
            temperature_time,
            temperature_data[
                "water_temperature_c"
            ],
            "Water Temperature"
        )

    else:

        print(
            "Skipped temperature_history.png: "
            "no valid temperature values."
        )


# ============================================================
# 2. PRESSURE HISTORY
# ============================================================

if "pressure_hpa" in data.columns:

    pressure = pd.to_numeric(
        data["pressure_hpa"],
        errors="coerce"
    )

    valid_pressure = pressure.notna()

    pressure_data = data.loc[
        valid_pressure
    ].copy()

    if not pressure_data.empty:

        pressure_time = (
            pressure_data["received_at"]
            if "received_at" in pressure_data.columns
            else range(len(pressure_data))
        )

        save_plot(
            "pressure_history.png",
            "PolarSense AI - Atmospheric Pressure History",
            "Time",
            "Pressure (hPa)",
            pressure_time,
            pressure_data["pressure_hpa"],
            "Pressure"
        )


# ============================================================
# 3. WIND + WAVE HISTORY
# ============================================================

if (
    "wind_speed_ms" in data.columns
    and
    "wave_height_m" in data.columns
):

    wind = pd.to_numeric(
        data["wind_speed_ms"],
        errors="coerce"
    )

    wave = pd.to_numeric(
        data["wave_height_m"],
        errors="coerce"
    )

    valid_wind_wave = (
        wind.notna()
        &
        wave.notna()
    )

    wind_wave_data = data.loc[
        valid_wind_wave
    ].copy()

    if not wind_wave_data.empty:

        wind_wave_time = (
            wind_wave_data["received_at"]
            if "received_at" in wind_wave_data.columns
            else range(len(wind_wave_data))
        )

        plt.figure(
            figsize=(10, 5)
        )

        plt.plot(
            wind_wave_time,
            pd.to_numeric(
                wind_wave_data["wind_speed_ms"],
                errors="coerce"
            ),
            linewidth=2,
            label="Wind Speed (m/s)"
        )

        plt.plot(
            wind_wave_time,
            pd.to_numeric(
                wind_wave_data["wave_height_m"],
                errors="coerce"
            ),
            linewidth=2,
            label="Wave Height (m)"
        )

        plt.title(
            "PolarSense AI - Wind and Wave History"
        )

        plt.xlabel("Time")
        plt.ylabel("Value")

        plt.grid(
            True,
            alpha=0.3
        )

        plt.legend()

        plt.tight_layout()

        output_path = os.path.join(
            OUTPUT_FOLDER,
            "wind_wave_history.png"
        )

        plt.savefig(
            output_path,
            dpi=150
        )

        plt.close()

        print(
            "Generated: wind_wave_history.png"
        )


# ============================================================
# 4. BATTERY HISTORY
# ============================================================

if "battery_percent" in data.columns:

    battery = pd.to_numeric(
        data["battery_percent"],
        errors="coerce"
    )

    valid_battery = battery.notna()

    battery_data = data.loc[
        valid_battery
    ].copy()

    if not battery_data.empty:

        battery_time = (
            battery_data["received_at"]
            if "received_at" in battery_data.columns
            else range(len(battery_data))
        )

        save_plot(
            "battery_history.png",
            "PolarSense AI - Battery History",
            "Time",
            "Battery (%)",
            battery_time,
            pd.to_numeric(
                battery_data["battery_percent"],
                errors="coerce"
            ),
            "Battery"
        )


# ============================================================
# 5. BUOY TRAJECTORY
# ============================================================

if (
    "latitude" in data.columns
    and
    "longitude" in data.columns
):

    latitude = pd.to_numeric(
        data["latitude"],
        errors="coerce"
    )

    longitude = pd.to_numeric(
        data["longitude"],
        errors="coerce"
    )

    valid_position = (
        latitude.notna()
        &
        longitude.notna()
    )

    position_data = data.loc[
        valid_position
    ].copy()

    if not position_data.empty:

        position_data[
            "latitude"
        ] = pd.to_numeric(
            position_data["latitude"],
            errors="coerce"
        )

        position_data[
            "longitude"
        ] = pd.to_numeric(
            position_data["longitude"],
            errors="coerce"
        )

        plt.figure(
            figsize=(8, 6)
        )

        plt.plot(
            position_data["longitude"],
            position_data["latitude"],
            linewidth=2,
            label="Buoy Trajectory"
        )

        plt.scatter(
            position_data["longitude"].iloc[0],
            position_data["latitude"].iloc[0],
            s=60,
            label="Start"
        )

        plt.scatter(
            position_data["longitude"].iloc[-1],
            position_data["latitude"].iloc[-1],
            s=60,
            label="Latest"
        )

        plt.title(
            "PolarSense AI - Live Buoy Trajectory"
        )

        plt.xlabel(
            "Longitude"
        )

        plt.ylabel(
            "Latitude"
        )

        plt.grid(
            True,
            alpha=0.3
        )

        plt.legend()

        plt.tight_layout()

        output_path = os.path.join(
            OUTPUT_FOLDER,
            "buoy_trajectory.png"
        )

        plt.savefig(
            output_path,
            dpi=150
        )

        plt.close()

        print(
            "Generated: buoy_trajectory.png"
        )


# ============================================================
# 6. AI ANOMALY HISTORY
# ============================================================

if "ai_anomaly" in data.columns:

    anomaly_values = (
        pd.to_numeric(
            data["ai_anomaly"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    plt.figure(
        figsize=(10, 5)
    )

    plt.step(
        time_axis,
        anomaly_values,
        where="post",
        linewidth=2,
        label="AI Anomaly"
    )

    plt.yticks(
        [0, 1],
        ["NORMAL", "ANOMALY"]
    )

    plt.title(
        "PolarSense AI - AI Anomaly History"
    )

    plt.xlabel("Time")
    plt.ylabel("AI Status")

    plt.grid(
        True,
        alpha=0.3
    )

    plt.legend()

    plt.tight_layout()

    output_path = os.path.join(
        OUTPUT_FOLDER,
        "anomaly_history.png"
    )

    plt.savefig(
        output_path,
        dpi=150
    )

    plt.close()

    print(
        "Generated: anomaly_history.png"
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("==========================================")
print("       VISUALIZATION COMPLETE")
print("==========================================")
print()

print(
    "Plots saved to:"
)

print(
    OUTPUT_FOLDER
)

print()

print("Generated files:")
print("  1. temperature_history.png")
print("  2. pressure_history.png")
print("  3. wind_wave_history.png")
print("  4. battery_history.png")
print("  5. buoy_trajectory.png")
print("  6. anomaly_history.png")

print()
print("==========================================")