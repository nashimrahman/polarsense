from flask import Flask, request, jsonify
from sklearn.ensemble import IsolationForest
import numpy as np
import time

app = Flask(__name__)

# ============================================================
# POLARSENSE AI - LIVE ANOMALY SERVICE
# ============================================================
#
# This service receives COMPLETE LIVE telemetry from the
# Node.js backend.
#
# It does NOT read the Excel simulation file.
# It does NOT read the dashboard.
# It evaluates the telemetry packet that came from:
#
# Velxio ESP32 -> MQTT -> Python gateway -> Node.js -> here
#
# Isolation Forest answers:
# "Is this telemetry unusual compared with normal operation?"
#
# It is NOT a storm predictor.
# ============================================================


FEATURES = [
    "water_temperature_c",
    "air_temperature_c",
    "humidity_percent",
    "pressure_hpa",
    "accel_x_g",
    "accel_y_g",
    "accel_z_g",
    "gyro_x_dps",
    "gyro_y_dps",
    "gyro_z_dps",
    "wind_speed_ms",
    "wave_height_m",
    "salinity_psu",
    "ice_concentration_percent",
    "current_speed_ms",
]


def build_normal_training_data(n=2500):
    """
    Create a synthetic NORMAL operating envelope for the
    digital twin.

    These are baseline values for the software demonstration,
    not field-calibrated oceanographic measurements.
    """

    rng = np.random.default_rng(42)

    data = np.column_stack([
        rng.normal(0.5, 0.9, n),          # water temperature
        rng.normal(-10.0, 4.0, n),        # air temperature
        rng.normal(75.0, 8.0, n),         # humidity
        rng.normal(1013.0, 8.0, n),       # pressure

        rng.normal(0.00, 0.08, n),        # accel X
        rng.normal(0.00, 0.08, n),        # accel Y
        rng.normal(1.00, 0.08, n),        # accel Z

        rng.normal(0.0, 3.0, n),          # gyro X
        rng.normal(0.0, 3.0, n),          # gyro Y
        rng.normal(0.0, 3.0, n),          # gyro Z

        rng.normal(10.0, 2.0, n),         # wind
        rng.normal(2.0, 0.7, n),          # waves
        rng.normal(33.0, 0.8, n),         # salinity
        rng.normal(60.0, 10.0, n),        # sea ice
        rng.normal(0.8, 0.25, n),         # current
    ])

    return data


print("==========================================")
print("       POLARSENSE AI LIVE SERVICE")
print("==========================================")
print("Building NORMAL baseline...")

training_data = build_normal_training_data()

model = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)

model.fit(training_data)

print("Isolation Forest: READY")
print("Features:", len(FEATURES))
print("Listening on: http://localhost:5001")
print("==========================================")


@app.get("/api/health")
def health():
    return jsonify({
        "service": "PolarSense AI",
        "status": "ONLINE",
        "model": "IsolationForest",
        "features": FEATURES,
        "purpose": "Live telemetry anomaly detection"
    })


@app.post("/api/anomaly")
def detect_anomaly():
    try:
        packet = request.get_json(silent=True)

        if not packet:
            return jsonify({
                "success": False,
                "message": "JSON telemetry packet required"
            }), 400

        values = []

        for feature in FEATURES:
            value = packet.get(feature)

            if value is None or value == "":
                return jsonify({
                    "success": False,
                    "message": f"Missing feature: {feature}"
                }), 400

            values.append(float(value))

        sample = np.array(values, dtype=float).reshape(1, -1)

        prediction = int(model.predict(sample)[0])
        decision_score = float(model.decision_function(sample)[0])

        if prediction == -1:
            status = "ANOMALY"
        else:
            status = "NORMAL"

        # Convert the Isolation Forest score into a simple
        # presentation-friendly anomaly confidence.
        #
        # This is a software visualization metric, not a
        # calibrated probability.
        confidence = max(
            0.0,
            min(
                1.0,
                0.5 - decision_score
            )
        )

        result = {
            "success": True,
            "buoy_id": packet.get("buoy_id", "POLAR-001"),
            "status": status,
            "anomaly": status == "ANOMALY",
            "anomaly_score": round(decision_score, 6),
            "anomaly_confidence": round(confidence, 3),
            "model": "IsolationForest",
            "processed_at": time.time()
        }

        print(
            f"[AI] {result['buoy_id']} -> "
            f"{status} | score={result['anomaly_score']}"
        )

        return jsonify(result)

    except (TypeError, ValueError) as error:
        return jsonify({
            "success": False,
            "message": f"Invalid telemetry value: {error}"
        }), 400

    except Exception as error:
        print("[AI ERROR]", error)

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5001,
        debug=False
    )
