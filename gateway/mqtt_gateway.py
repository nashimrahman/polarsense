import json
import csv
import os
from datetime import datetime

import paho.mqtt.client as mqtt
import requests


# ============================================================
# POLARSENSE AI
# MQTT TELEMETRY GATEWAY
# ============================================================

BROKER = "broker.emqx.io"
PORT = 1883

TOPIC = "polarsenseai/buoy/telemetry"

CSV_FILE = "data/live_telemetry.csv"

# Local Node.js backend
BACKEND_URL = "http://localhost:3000/api/telemetry"


# ------------------------------------------------------------
# Create CSV file if it does not exist
# ------------------------------------------------------------

os.makedirs("data", exist_ok=True)

if not os.path.exists(CSV_FILE):

    with open(CSV_FILE, "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "received_at",
            "temperature_c",
            "humidity_percent",
            "wind_speed_ms",
            "wave_height_m",
            "ice_concentration_percent",
            "battery_voltage"
        ])


# ------------------------------------------------------------
# Send telemetry to Node.js backend
# ------------------------------------------------------------

def send_to_backend(data):

    payload = {

        "buoy_id": "POLAR-001",

        "water_temperature_c":
            data.get("temperature_c"),

        "air_temperature_c":
            data.get("air_temperature_c"),

        "humidity_percent":
            data.get("humidity_percent"),

        "pressure_hpa":
            data.get("pressure_hpa"),

        "accel_x_g":
            data.get("accel_x_g"),

        "accel_y_g":
            data.get("accel_y_g"),

        "accel_z_g":
            data.get("accel_z_g"),

        "gyro_x_dps":
            data.get("gyro_x_dps"),

        "gyro_y_dps":
            data.get("gyro_y_dps"),

        "gyro_z_dps":
            data.get("gyro_z_dps")
    }

    try:

        response = requests.post(
            BACKEND_URL,
            json=payload,
            timeout=5
        )

        print()
        print("[NODE.JS BACKEND]")

        print(
            "HTTP Status:",
            response.status_code
        )

        if response.ok:

            print(
                "Telemetry forwarded successfully."
            )

        else:

            print(
                "Backend rejected telemetry."
            )

            print(
                response.text
            )

    except requests.exceptions.RequestException as error:

        print()
        print("[NODE.JS BACKEND ERROR]")

        print(error)


# ------------------------------------------------------------
# MQTT connection
# ------------------------------------------------------------

def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties=None
):

    print()
    print("=" * 60)
    print("POLARSENSE AI")
    print("PYTHON MQTT GATEWAY")
    print("=" * 60)

    print()
    print("Connected to MQTT broker!")

    print(
        "Broker:",
        BROKER
    )

    print(
        "Topic:",
        TOPIC
    )

    client.subscribe(TOPIC)

    print()
    print("Waiting for buoy telemetry...")
    print("-" * 60)


# ------------------------------------------------------------
# Receive telemetry
# ------------------------------------------------------------

def on_message(
    client,
    userdata,
    message
):

    try:

        payload = (
            message
            .payload
            .decode("utf-8")
        )

        data = json.loads(payload)

        received_at = (
            datetime
            .now()
            .isoformat(
                timespec="seconds"
            )
        )

        print()
        print("[BUOY TELEMETRY]")

        print(
            "Received:",
            received_at
        )

        print(
            f"Temperature: "
            f"{data.get('temperature_c')} °C"
        )

        print(
            f"Humidity: "
            f"{data.get('humidity_percent')} %"
        )

        print(
            f"Wind: "
            f"{data.get('wind_speed_ms')} m/s"
        )

        print(
            f"Wave height: "
            f"{data.get('wave_height_m')} m"
        )

        print(
            f"Ice concentration: "
            f"{data.get('ice_concentration_percent')} %"
        )

        print(
            f"Battery: "
            f"{data.get('battery_voltage')} V"
        )

        print("-" * 60)


        # ----------------------------------------------------
        # Save MQTT telemetry
        # ----------------------------------------------------

        with open(
            CSV_FILE,
            "a",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                received_at,
                data.get("temperature_c"),
                data.get("humidity_percent"),
                data.get("wind_speed_ms"),
                data.get("wave_height_m"),
                data.get(
                    "ice_concentration_percent"
                ),
                data.get("battery_voltage")
            ])


        # ----------------------------------------------------
        # Forward telemetry to Node.js
        # ----------------------------------------------------

        send_to_backend(data)


    except json.JSONDecodeError:

        print()
        print("Invalid JSON received:")

        print(
            message.payload.decode(
                "utf-8",
                errors="ignore"
            )
        )


    except Exception as error:

        print()
        print("Gateway error:")

        print(error)


# ------------------------------------------------------------
# MQTT client
# ------------------------------------------------------------

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="polarsense-python-gateway"
)

client.on_connect = on_connect
client.on_message = on_message


# ------------------------------------------------------------
# Connect
# ------------------------------------------------------------

print()
print("Connecting to MQTT broker...")

client.connect(
    BROKER,
    PORT,
    60
)


# ------------------------------------------------------------
# Start receiving messages
# ------------------------------------------------------------

try:

    client.loop_forever()

except KeyboardInterrupt:

    print()
    print("Gateway stopped.")

    client.disconnect()