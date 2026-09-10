const express = require("express");
const fs = require("fs");
const path = require("path");
const mqtt = require("mqtt");

const app = express();

const PORT = process.env.PORT || 3000;

const MQTT_BROKER =
    process.env.MQTT_BROKER ||
    "mqtt://test.mosquitto.org:1883";

const MQTT_TOPIC =
    process.env.MQTT_TOPIC ||
    "polarsenseai/buoy/telemetry";

const MQTT_COMMAND_TOPIC =
    process.env.MQTT_COMMAND_TOPIC ||
    "polarsenseai/buoy/command";

const MQTT_CLIENT_ID =
    process.env.MQTT_CLIENT_ID ||
    "POLARSENSE-NODE-" +
    Math.random()
        .toString(16)
        .slice(2, 10);

const AI_SERVICE_URL =
    process.env.AI_SERVICE_URL ||
    "http://127.0.0.1:5001/api/anomaly";

app.use(
    express.json({
        limit: "1mb"
    })
);

app.use(
    express.static(
        path.join(__dirname, "dashboard")
    )
);

const dataDir =
    path.join(
        __dirname,
        "data"
    );

const csvFile =
    path.join(
        dataDir,
        "live_telemetry.csv"
    );

if (!fs.existsSync(dataDir)) {

    fs.mkdirSync(
        dataDir,
        {
            recursive: true
        }
    );
}

const CSV_HEADER = [

    "received_at",
    "buoy_id",
    "timestamp",
    "mode",

    // REAL CIRCUIT

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

    // POLAR ENVIRONMENT

    "wind_speed_ms",
    "wave_height_m",
    "salinity_psu",
    "ice_concentration_percent",
    "current_speed_ms",

    // TRAJECTORY

    "latitude",
    "longitude",
    "drift_km",
    "heading_deg",

    // AUTONOMOUS SYSTEM

    "battery_percent",
    "sampling_mode",
    "energy_mode",
    "risk",
    "buoy_motion_level",

    // COUPLING

    "motion_index",
    "pressure_stress",
    "thermal_index",

    // AI

    "ai_anomaly_status",
    "ai_anomaly",
    "ai_anomaly_score",
    "ai_anomaly_confidence"

].join(",") + "\n";


if (!fs.existsSync(csvFile)) {

    fs.writeFileSync(
        csvFile,
        CSV_HEADER
    );
}

let latestTelemetry = null;

let telemetryHistory = [];

const MAX_HISTORY = 300;

let environment = {

    mode: "NORMAL",

    water_temperature_c: -0.5,

    air_temperature_c: -8.0,

    humidity_percent: 80.0,

    pressure_hpa: 1010.0,

    wind_speed_ms: 10.0,

    wave_height_m: 2.0,

    salinity_psu: 33.5,

    ice_concentration_percent: 60.0,

    current_speed_ms: 0.8,

    current_direction_deg: 180.0,

    buoy_motion_level: "LOW",

    sampling_mode: "NORMAL",

    energy_mode: "POWER_SAVING",

    risk: "LOW"

};

let buoy = {

    id: "POLAR-001",

    latitude: -60.000000,

    longitude: 20.000000,

    startLatitude: -60.000000,

    startLongitude: 20.000000,

    driftKm: 0.0,

    headingDeg: 180.0

};

let batteryPercent = 95.0;

let circuit = {

    water_temperature_c: -0.5,

    air_temperature_c: -8.0,

    humidity_percent: 80.0,

    pressure_hpa: 1010.0,

    accel_x_g: 0.0,

    accel_y_g: 0.0,

    accel_z_g: 1.0,

    gyro_x_dps: 0.0,

    gyro_y_dps: 0.0,

    gyro_z_dps: 0.0

};

let latestAiResult = {

    status: "UNAVAILABLE",

    anomaly: false,

    anomaly_score: null,

    anomaly_confidence: null,

    model: "Isolation Forest",

    processed_at: null,

    message: "Waiting for live telemetry"

};

let coupling = {

    motionIndex: 0.0,

    pressureStress: 0.0,

    thermalIndex: 0.0,

    currentHeading: 180.0

};

function clamp(
    value,
    min,
    max
) {

    return Math.max(
        min,
        Math.min(
            max,
            value
        )
    );
}


function round(
    value,
    decimals = 3
) {

    return Number(
        Number(value).toFixed(decimals)
    );
}


function moveToward(
    current,
    target,
    step
) {

    if (current < target) {

        current += step;

        if (current > target) {
            current = target;
        }

    } else if (current > target) {

        current -= step;

        if (current < target) {
            current = target;
        }
    }

    return current;
}

function calculateCoupling() {

    const accelerationMagnitude =
        Math.sqrt(
            Math.pow(circuit.accel_x_g, 2) +
            Math.pow(circuit.accel_y_g, 2) +
            Math.pow(
                circuit.accel_z_g - 1,
                2
            )
        );

    const gyroMagnitude =
        Math.sqrt(
            Math.pow(circuit.gyro_x_dps, 2) +
            Math.pow(circuit.gyro_y_dps, 2) +
            Math.pow(circuit.gyro_z_dps, 2)
        );

    const motionIndex =
        clamp(
            accelerationMagnitude * 0.7 +
            gyroMagnitude / 180,
            0,
            1
        );

    const pressureDifference =
        Math.abs(
            circuit.pressure_hpa - 1013.25
        );

    const pressureStress =
        clamp(
            pressureDifference / 60,
            0,
            1
        );

    const thermalIndex =
        clamp(
            Math.abs(
                circuit.water_temperature_c + 1.8
            ) / 8,
            0,
            1
        );

    let heading =
        Math.atan2(
            circuit.accel_y_g,
            circuit.accel_x_g
        ) *
        180 /
        Math.PI;

    if (heading < 0) {
        heading += 360;
    }

    coupling.motionIndex =
        round(
            motionIndex,
            3
        );

    coupling.pressureStress =
        round(
            pressureStress,
            3
        );

    coupling.thermalIndex =
        round(
            thermalIndex,
            3
        );

    coupling.currentHeading =
        round(
            heading,
            1
        );

    return coupling;
}

function updateEnvironment() {

    calculateCoupling();

    const motion =
        coupling.motionIndex;

    const pressureStress =
        coupling.pressureStress;

    const waterTemp =
        circuit.water_temperature_c;

    const airTemp =
        circuit.air_temperature_c;

    const humidity =
        circuit.humidity_percent;

    let targetWind =
        8 +
        pressureStress * 16 +
        motion * 8;

    if (environment.mode === "STORM") {

        targetWind =
            Math.max(
                targetWind,
                24.5
            );
    }

    let targetWave =
        0.8 +
        targetWind * 0.12 +
        motion * 3.5;

    if (environment.mode === "STORM") {

        targetWave =
            Math.max(
                targetWave,
                6
            );
    }


    let targetCurrent =
        0.3 +
        motion * 1.2 +
        pressureStress * 0.5;


    // --------------------------------------------------------
    // SALINITY
    // --------------------------------------------------------

    let targetSalinity =
        33.5 -
        (waterTemp * 0.12) +
        (environment.ice_concentration_percent * 0.005);


    // --------------------------------------------------------
    // ICE
    // --------------------------------------------------------

    let targetIce =
        55;

    if (waterTemp < -1.0) {

        targetIce +=
            Math.abs(
                waterTemp + 1
            ) * 20;
    }

    if (airTemp < -10) {

        targetIce += 8;
    }

    if (waterTemp > 1.0) {

        targetIce -= 20;
    }

    targetIce =
        clamp(
            targetIce,
            5,
            95
        );


    // --------------------------------------------------------
    // HUMIDITY EFFECT
    // --------------------------------------------------------

    targetWind +=
        Math.max(
            0,
            (humidity - 80) * 0.03
        );


    // --------------------------------------------------------
    // SMOOTH ENVIRONMENT
    // --------------------------------------------------------

    environment.wind_speed_ms =
        moveToward(
            environment.wind_speed_ms,
            targetWind,
            0.7
        );

    environment.wave_height_m =
        moveToward(
            environment.wave_height_m,
            targetWave,
            0.25
        );

    environment.current_speed_ms =
        moveToward(
            environment.current_speed_ms,
            targetCurrent,
            0.08
        );

    environment.salinity_psu =
        moveToward(
            environment.salinity_psu,
            targetSalinity,
            0.08
        );

    environment.ice_concentration_percent =
        moveToward(
            environment.ice_concentration_percent,
            targetIce,
            1.5
        );


    environment.water_temperature_c =
        circuit.water_temperature_c;

    environment.air_temperature_c =
        circuit.air_temperature_c;

    environment.humidity_percent =
        circuit.humidity_percent;

    environment.pressure_hpa =
        circuit.pressure_hpa;

    environment.current_direction_deg =
        coupling.currentHeading;


    // --------------------------------------------------------
    // MOTION LEVEL
    // --------------------------------------------------------

    if (motion >= 0.70) {

        environment.buoy_motion_level =
            "HIGH";

    } else if (motion >= 0.30) {

        environment.buoy_motion_level =
            "MEDIUM";

    } else {

        environment.buoy_motion_level =
            "LOW";
    }
}


// ============================================================
// RISK ENGINE
// ============================================================

function calculateRisk() {

    const wind =
        environment.wind_speed_ms;

    const waves =
        environment.wave_height_m;

    const pressure =
        environment.pressure_hpa;

    const motion =
        coupling.motionIndex;

    const pressureStress =
        coupling.pressureStress;

    const ice =
        environment.ice_concentration_percent;


    let score = 0;


    if (wind >= 24.5) {
        score += 3;
    } else if (wind >= 18) {
        score += 2;
    } else if (wind >= 12) {
        score += 1;
    }


    if (waves >= 6) {
        score += 3;
    } else if (waves >= 4) {
        score += 2;
    } else if (waves >= 3) {
        score += 1;
    }


    if (pressureStress >= 0.7) {
        score += 2;
    } else if (pressureStress >= 0.4) {
        score += 1;
    }


    if (motion >= 0.7) {
        score += 3;
    } else if (motion >= 0.4) {
        score += 2;
    }


    if (ice >= 85) {
        score += 2;
    }


    if (
        latestAiResult &&
        latestAiResult.anomaly === true
    ) {

        score += 2;
    }


    if (score >= 7) {

        environment.risk =
            "HIGH";

    } else if (score >= 3) {

        environment.risk =
            "MEDIUM";

    } else {

        environment.risk =
            "LOW";
    }


    // --------------------------------------------------------
    // ADAPTIVE SAMPLING
    // --------------------------------------------------------

    if (
        environment.risk === "HIGH"
    ) {

        environment.sampling_mode =
            "HIGH_FREQUENCY";

    } else if (
        environment.risk === "MEDIUM"
    ) {

        environment.sampling_mode =
            "ADAPTIVE";

    } else {

        environment.sampling_mode =
            "NORMAL";
    }


    // --------------------------------------------------------
    // ENERGY MODE
    // --------------------------------------------------------

    if (
        environment.risk === "HIGH"
    ) {

        environment.energy_mode =
            "HIGH_LOAD";

    } else if (
        environment.risk === "MEDIUM"
    ) {

        environment.energy_mode =
            "BALANCED";

    } else {

        environment.energy_mode =
            "POWER_SAVING";
    }


    return environment.risk;
}


// ============================================================
// BUOY TRAJECTORY
// ============================================================

function updateTrajectory() {

    const speed =
        environment.current_speed_ms;

    const waveFactor =
        environment.wave_height_m * 0.04;

    const motionFactor =
        1 +
        coupling.motionIndex;

    const totalSpeed =
        (
            speed +
            waveFactor
        ) *
        motionFactor;


    let heading =
        coupling.currentHeading;


    if (
        !Number.isFinite(heading)
    ) {

        heading =
            environment.current_direction_deg;
    }


    buoy.headingDeg =
        heading;


    const headingRad =
        heading *
        Math.PI /
        180;


    // Approximate conversion:
    // 1 degree latitude ≈ 111 km

    const distanceKm =
        totalSpeed *
        0.005;


    const deltaLat =
        (
            distanceKm *
            Math.cos(headingRad)
        ) /
        111;


    const latitudeRad =
        buoy.latitude *
        Math.PI /
        180;


    const kmPerDegreeLongitude =
        111 *
        Math.max(
            0.1,
            Math.cos(latitudeRad)
        );


    const deltaLon =
        (
            distanceKm *
            Math.sin(headingRad)
        ) /
        kmPerDegreeLongitude;


    buoy.latitude +=
        deltaLat;

    buoy.longitude +=
        deltaLon;

    buoy.driftKm +=
        distanceKm;


    // Keep longitude within normal range

    if (buoy.longitude > 180) {

        buoy.longitude -= 360;
    }

    if (buoy.longitude < -180) {

        buoy.longitude += 360;
    }
}


// ============================================================
// ENERGY MODEL
// ============================================================

function updateEnergy() {

    let drain =
        0.02;


    if (
        environment.sampling_mode ===
        "ADAPTIVE"
    ) {

        drain +=
            0.015;
    }


    if (
        environment.sampling_mode ===
        "HIGH_FREQUENCY"
    ) {

        drain +=
            0.04;
    }


    if (
        environment.energy_mode ===
        "HIGH_LOAD"
    ) {

        drain +=
            0.02;
    }


    if (
        coupling.motionIndex > 0.7
    ) {

        drain +=
            0.01;
    }


    batteryPercent =
        clamp(
            batteryPercent - drain,
            0,
            100
        );
}


// ============================================================
// AI REQUEST
// ============================================================

async function runAiAnalysis(
    packet
) {

    try {

        const response =
            await fetch(
                AI_SERVICE_URL,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            packet
                        )
                }
            );


        if (!response.ok) {

            throw new Error(
                "AI service returned " +
                response.status
            );
        }


        const result =
            await response.json();


        latestAiResult = {

            status:
                result.status ||
                "UNKNOWN",

            anomaly:
                Boolean(
                    result.anomaly
                ),

            anomaly_score:
                result.anomaly_score ??
                null,

            anomaly_confidence:
                result.anomaly_confidence ??
                null,

            model:
                result.model ||
                "Isolation Forest",

            processed_at:
                new Date().toISOString(),

            message:
                result.message ||
                "AI analysis complete"
        };


    } catch (error) {

        latestAiResult = {

            status: "UNAVAILABLE",

            anomaly: false,

            anomaly_score: null,

            anomaly_confidence: null,

            model: "Isolation Forest",

            processed_at:
                new Date().toISOString(),

            message:
                "AI service unavailable"
        };

        console.log(
            "AI:",
            error.message
        );
    }
}


// ============================================================
// CSV STORAGE
// ============================================================

function saveTelemetry(
    telemetry
) {

    const values = [

        telemetry.received_at,

        telemetry.buoy_id,

        telemetry.timestamp,

        telemetry.mode,

        telemetry.water_temperature_c,

        telemetry.air_temperature_c,

        telemetry.humidity_percent,

        telemetry.pressure_hpa,

        telemetry.accel_x_g,

        telemetry.accel_y_g,

        telemetry.accel_z_g,

        telemetry.gyro_x_dps,

        telemetry.gyro_y_dps,

        telemetry.gyro_z_dps,

        telemetry.wind_speed_ms,

        telemetry.wave_height_m,

        telemetry.salinity_psu,

        telemetry.ice_concentration_percent,

        telemetry.current_speed_ms,

        telemetry.latitude,

        telemetry.longitude,

        telemetry.drift_km,

        telemetry.heading_deg,

        telemetry.battery_percent,

        telemetry.sampling_mode,

        telemetry.energy_mode,

        telemetry.risk,

        telemetry.buoy_motion_level,

        telemetry.motion_index,

        telemetry.pressure_stress,

        telemetry.thermal_index,

        telemetry.ai_anomaly_status,

        telemetry.ai_anomaly,

        telemetry.ai_anomaly_score,

        telemetry.ai_anomaly_confidence

    ];


    const csvLine =
        values
            .map(value => {

                if (
                    value === null ||
                    value === undefined
                ) {
                    return "";
                }

                return String(value)
                    .replace(/,/g, "");
            })
            .join(",") +
        "\n";


    fs.appendFileSync(
        csvFile,
        csvLine
    );
}


// ============================================================
// BUILD COMPLETE TELEMETRY
// ============================================================

function buildTelemetry() {

    return {

        received_at:
            new Date().toISOString(),

        buoy_id:
            buoy.id,

        timestamp:
            new Date().toISOString(),

        mode:
            environment.mode,


        // REAL CIRCUIT

        water_temperature_c:
            round(
                circuit.water_temperature_c,
                2
            ),

        air_temperature_c:
            round(
                circuit.air_temperature_c,
                2
            ),

        humidity_percent:
            round(
                circuit.humidity_percent,
                2
            ),

        pressure_hpa:
            round(
                circuit.pressure_hpa,
                2
            ),


        accel_x_g:
            round(
                circuit.accel_x_g,
                3
            ),

        accel_y_g:
            round(
                circuit.accel_y_g,
                3
            ),

        accel_z_g:
            round(
                circuit.accel_z_g,
                3
            ),


        gyro_x_dps:
            round(
                circuit.gyro_x_dps,
                2
            ),

        gyro_y_dps:
            round(
                circuit.gyro_y_dps,
                2
            ),

        gyro_z_dps:
            round(
                circuit.gyro_z_dps,
                2
            ),


        // POLAR ENVIRONMENT

        wind_speed_ms:
            round(
                environment.wind_speed_ms,
                2
            ),

        wave_height_m:
            round(
                environment.wave_height_m,
                2
            ),

        salinity_psu:
            round(
                environment.salinity_psu,
                2
            ),

        ice_concentration_percent:
            round(
                environment.ice_concentration_percent,
                2
            ),

        current_speed_ms:
            round(
                environment.current_speed_ms,
                2
            ),


        // TRAJECTORY

        latitude:
            round(
                buoy.latitude,
                6
            ),

        longitude:
            round(
                buoy.longitude,
                6
            ),

        drift_km:
            round(
                buoy.driftKm,
                3
            ),

        heading_deg:
            round(
                buoy.headingDeg,
                1
            ),


        // AUTONOMOUS

        battery_percent:
            round(
                batteryPercent,
                2
            ),

        sampling_mode:
            environment.sampling_mode,

        energy_mode:
            environment.energy_mode,

        risk:
            environment.risk,

        buoy_motion_level:
            environment.buoy_motion_level,


        // COUPLING

        motion_index:
            coupling.motionIndex,

        pressure_stress:
            coupling.pressureStress,

        thermal_index:
            coupling.thermalIndex,


        // AI

        ai_anomaly_status:
            latestAiResult.status,

        ai_anomaly:
            latestAiResult.anomaly,

        ai_anomaly_score:
            latestAiResult.anomaly_score,

        ai_anomaly_confidence:
            latestAiResult.anomaly_confidence
    };
}


// ============================================================
// PROCESS COMPLETE TELEMETRY
// ============================================================

async function processTelemetry(
    packet
) {

    // --------------------------------------------------------
    // UPDATE CIRCUIT
    // --------------------------------------------------------

    const numericFields = [

        "water_temperature_c",
        "air_temperature_c",
        "humidity_percent",
        "pressure_hpa",

        "accel_x_g",
        "accel_y_g",
        "accel_z_g",

        "gyro_x_dps",
        "gyro_y_dps",
        "gyro_z_dps"
    ];


    for (
        const field
        of numericFields
    ) {

        if (
            packet[field] !== undefined &&
            packet[field] !== null
        ) {

            const value =
                Number(
                    packet[field]
                );

            if (
                Number.isFinite(value)
            ) {

                circuit[field] =
                    value;
            }
        }
    }


    // --------------------------------------------------------
    // MODE
    // --------------------------------------------------------

    if (
        packet.mode === "STORM" ||
        packet.mode === "NORMAL"
    ) {

        environment.mode =
            packet.mode;
    }


    // --------------------------------------------------------
    // COUPLE CIRCUIT TO ENVIRONMENT
    // --------------------------------------------------------

    updateEnvironment();


    // --------------------------------------------------------
    // UPDATE TRAJECTORY
    // --------------------------------------------------------

    updateTrajectory();


    // --------------------------------------------------------
    // RISK BEFORE AI
    // --------------------------------------------------------

    calculateRisk();


    // --------------------------------------------------------
    // ENERGY
    // --------------------------------------------------------

    updateEnergy();


    // --------------------------------------------------------
    // BUILD PRE-AI TELEMETRY
    // --------------------------------------------------------

    let telemetry =
        buildTelemetry();


    // --------------------------------------------------------
    // AI
    // --------------------------------------------------------

    await runAiAnalysis(
        telemetry
    );


    // --------------------------------------------------------
    // RECALCULATE RISK AFTER AI
    // --------------------------------------------------------

    calculateRisk();


    // --------------------------------------------------------
    // FINAL TELEMETRY
    // --------------------------------------------------------

    telemetry =
        buildTelemetry();


    latestTelemetry =
        telemetry;


    telemetryHistory.push(
        telemetry
    );


    if (
        telemetryHistory.length >
        MAX_HISTORY
    ) {

        telemetryHistory.shift();
    }


    saveTelemetry(
        telemetry
    );


    return telemetry;
}


// ============================================================
// MQTT
// ============================================================

const mqttClient =
    mqtt.connect(
        MQTT_BROKER,
        {

            clientId:
                MQTT_CLIENT_ID,

            reconnectPeriod:
                5000,

            connectTimeout:
                10000
        }
    );


mqttClient.on(
    "connect",
    () => {

        console.log("");
        console.log(
            "=========================================="
        );

        console.log(
            "      POLARSENSE AI MQTT ONLINE"
        );

        console.log(
            "=========================================="
        );

        console.log(
            "Broker:",
            MQTT_BROKER
        );

        console.log(
            "Telemetry topic:",
            MQTT_TOPIC
        );

        console.log(
            "Command topic:",
            MQTT_COMMAND_TOPIC
        );

        console.log(
            "=========================================="
        );


        mqttClient.subscribe(
            MQTT_TOPIC,
            error => {

                if (error) {

                    console.log(
                        "MQTT subscribe error:",
                        error.message
                    );

                } else {

                    console.log(
                        "Subscribed to telemetry"
                    );
                }
            }
        );
    }
);


mqttClient.on(
    "reconnect",
    () => {

        console.log(
            "MQTT: reconnecting..."
        );
    }
);


mqttClient.on(
    "error",
    error => {

        console.log(
            "MQTT ERROR:",
            error.message
        );
    }
);


mqttClient.on(
    "message",
    async (
        topic,
        message
    ) => {

        if (
            topic !== MQTT_TOPIC
        ) {
            return;
        }


        try {

            const packet =
                JSON.parse(
                    message.toString()
                );
                
// ========================================================
// NORMALIZE ESP32 SENSOR NAMES
// ========================================================

packet.water_temperature_c =
    packet.water_temperature_c ??
    packet.water_temp_c ??
    packet.waterTemp ??
    packet.ntc_temperature_c ??
    packet.ntc_temp_c ??
    packet.temperature_c ??
    null;

packet.air_temperature_c =
    packet.air_temperature_c ??
    packet.air_temp_c ??
    packet.airTemp ??
    null;

packet.humidity_percent =
    packet.humidity_percent ??
    packet.humidity ??
    null;

packet.pressure_hpa =
    packet.pressure_hpa ??
    packet.pressure ??
    null;


            console.log("");
            console.log(
                "------------------------------------------"
            );

            console.log(
                "LIVE BUOY TELEMETRY RECEIVED"
            );

            console.log(
                "Water:",
                packet.water_temperature_c
            );

            console.log(
                "Air:",
                packet.air_temperature_c
            );

            console.log(
                "Pressure:",
                packet.pressure_hpa
            );

            console.log(
                "Motion:",
                packet.accel_x_g,
                packet.accel_y_g,
                packet.accel_z_g
            );

            console.log(
                "------------------------------------------"
            );


            await processTelemetry(
                packet
            );


        } catch (error) {

            console.log(
                "Invalid MQTT telemetry:",
                error.message
            );
        }
    }
);


// ============================================================
// API: HEALTH
// ============================================================

app.get(
    "/api/health",
    (req, res) => {

        res.json({

            service:
                "PolarSense AI",

            status:
                "ONLINE",

            mqtt:
                mqttClient.connected
                    ? "CONNECTED"
                    : "DISCONNECTED",

            ai:
                latestAiResult.status,

            timestamp:
                new Date().toISOString()
        });
    }
);


// ============================================================
// API: COMPLETE STATE
// ============================================================

app.get(
    "/api/state",
    (req, res) => {

        res.json({

            success: true,

            system: {

                status:
                    "ONLINE",

                mqtt:
                    mqttClient.connected
                        ? "CONNECTED"
                        : "DISCONNECTED"
            },

            circuit,

            environment,

            buoy,

            coupling,

            battery_percent:
                batteryPercent,

            ai:
                latestAiResult,

            latestTelemetry
        });
    }
);


// ============================================================
// API: LATEST TELEMETRY
// ============================================================

app.get(
    "/api/telemetry/latest",
    (req, res) => {

        res.json(
    latestTelemetry
);
    }
);


// ============================================================
// API: TELEMETRY HISTORY
// ============================================================

app.get(
    "/api/telemetry/history",
    (req, res) => {

        res.json({

            success: true,

            count:
                telemetryHistory.length,

            telemetry:
                telemetryHistory
        });
    }
);


// ============================================================
// API: ENVIRONMENT
// ============================================================

app.get(
    "/api/environment",
    (req, res) => {

        res.json({

            success: true,

            environment,

            coupling,

            buoy
        });
    }
);


// ============================================================
// API: AI
// ============================================================

app.get(
    "/api/ai",
    (req, res) => {

        res.json({

            success: true,

            ai:
                latestAiResult
        });
    }
);


// ============================================================
// API: SET NORMAL MODE
// ============================================================

app.post(
    "/api/mode/normal",
    (req, res) => {

        environment.mode =
            "NORMAL";


        mqttClient.publish(
            MQTT_COMMAND_TOPIC,
            "NORMAL"
        );


        console.log(
            "COMMAND: NORMAL"
        );


        res.json({

            success: true,

            mode:
                "NORMAL"
        });
    }
);


// ============================================================
// API: SET STORM MODE
// ============================================================

app.post(
    "/api/mode/storm",
    (req, res) => {

        environment.mode =
            "STORM";


        mqttClient.publish(
            MQTT_COMMAND_TOPIC,
            "STORM"
        );


        console.log(
            "COMMAND: STORM"
        );


        res.json({

            success: true,

            mode:
                "STORM"
        });
    }
);


// ============================================================
// API: RESET BUOY
// ============================================================

app.post(
    "/api/reset",
    (req, res) => {

        buoy.latitude =
            buoy.startLatitude;

        buoy.longitude =
            buoy.startLongitude;

        buoy.driftKm =
            0;

        buoy.headingDeg =
            180;

        batteryPercent =
            95;


        telemetryHistory =
            [];


        environment.mode =
            "NORMAL";


        console.log(
            "SYSTEM: BUOY RESET"
        );


        res.json({

            success: true,

            message:
                "PolarSense buoy reset"
        });
    }
);


// ============================================================
// SIMULATION TICK
// ============================================================
//
// This keeps the digital twin alive even between ESP32
// packets and makes the trajectory/environment visibly live.
// ============================================================

setInterval(
    async () => {

        try {

            if (
                latestTelemetry
            ) {

                updateEnvironment();

                updateTrajectory();

                calculateRisk();

                updateEnergy();


                latestTelemetry =
                    buildTelemetry();


                telemetryHistory.push(
                    latestTelemetry
                );


                if (
                    telemetryHistory.length >
                    MAX_HISTORY
                ) {

                    telemetryHistory.shift();
                }


                saveTelemetry(
                    latestTelemetry
                );
            }

        } catch (error) {

            console.log(
                "Simulation tick error:",
                error.message
            );
        }

    },
    5000
);


// ============================================================
// SERVER START
// ============================================================

app.listen(
    PORT,
    () => {

        console.log("");
        console.log(
            "=========================================="
        );

        console.log(
            "        POLARSENSE AI BACKEND"
        );

        console.log(
            "=========================================="
        );

        console.log(
            "Server:",
            `http://localhost:${PORT}`
        );

        console.log(
            "Dashboard:",
            `http://localhost:${PORT}`
        );

        console.log(
            "MQTT:",
            MQTT_BROKER
        );

        console.log(
            "Telemetry:",
            MQTT_TOPIC
        );

        console.log(
            "AI:",
            AI_SERVICE_URL
        );

        console.log(
            "=========================================="
        );

        console.log(
            "Waiting for live buoy telemetry..."
        );

        console.log("");
    }
);