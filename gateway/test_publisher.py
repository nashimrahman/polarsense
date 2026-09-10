import json
import time

import paho.mqtt.client as mqtt


# ============================================================
# POLARSENSE AI
# CONTINUOUS MQTT TEST PUBLISHER
# ============================================================

BROKER = "broker.emqx.io"
PORT = 1883

TOPIC = "polarsenseai/buoy/telemetry"

PUBLISH_INTERVAL = 5


# ============================================================
# Simulated complete ESP32 telemetry
# ============================================================

payload = {

    "buoy_id": "POLAR-001",

    # --------------------------------------------------------
    # Water temperature - NTC
    # --------------------------------------------------------

    "temperature_c": -1.2,

    # --------------------------------------------------------
    # BME280
    # --------------------------------------------------------

    "air_temperature_c": -6.4,
    "humidity_percent": 84.0,
    "pressure_hpa": 1018.2,

    # --------------------------------------------------------
    # MPU6050
    # --------------------------------------------------------

    "accel_x_g": 0.05,
    "accel_y_g": -0.03,
    "accel_z_g": 1.02,

    "gyro_x_dps": 1.4,
    "gyro_y_dps": 0.7,
    "gyro_z_dps": 1.8,

    # --------------------------------------------------------
    # Polar environment
    # --------------------------------------------------------

    "wind_speed_ms": 10.0,
    "wave_height_m": 2.0,

    "salinity_psu": 33.0,

    "ice_concentration_percent": 60.0,

    "current_speed_ms": 0.8,

    # --------------------------------------------------------
    # Battery
    # --------------------------------------------------------

    "battery_voltage": 12.2

}


# ============================================================
# MQTT callbacks
# ============================================================

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
    print("CONTINUOUS MQTT TEST PUBLISHER")
    print("=" * 60)

    print()

    print(
        "Connected to MQTT broker!"
    )

    print(
        "Broker:",
        BROKER
    )

    print(
        "Topic:",
        TOPIC
    )

    print()

    print(
        "Publishing every",
        PUBLISH_INTERVAL,
        "seconds..."
    )

    print(
        "Press Ctrl+C to stop."
    )

    print("-" * 60)


def on_disconnect(
    client,
    userdata,
    disconnect_flags,
    reason_code,
    properties=None
):

    print()
    print(
        "MQTT disconnected."
    )


# ============================================================
# Create MQTT client
# ============================================================

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="polarsense-continuous-publisher"
)

client.on_connect = on_connect
client.on_disconnect = on_disconnect


# ============================================================
# Connect to broker
# ============================================================

print()
print(
    "Connecting to MQTT broker..."
)

client.connect(
    BROKER,
    PORT,
    60
)

client.loop_start()


# ============================================================
# Continuous publishing
# ============================================================

try:

    while True:

        message = json.dumps(
            payload
        )

        print()
        print(
            "[PUBLISHING TELEMETRY]"
        )

        print(
            message
        )

        result = client.publish(
            TOPIC,
            message
        )

        result.wait_for_publish()

        if result.rc == mqtt.MQTT_ERR_SUCCESS:

            print(
                "Telemetry sent successfully."
            )

        else:

            print(
                "MQTT publish failed."
            )

        print("-" * 60)

        time.sleep(
            PUBLISH_INTERVAL
        )


except KeyboardInterrupt:

    print()
    print(
        "Stopping publisher..."
    )

finally:

    client.loop_stop()

    client.disconnect()

    print(
        "Publisher disconnected."
    )