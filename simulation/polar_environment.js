// ============================================================
// POLARSENSE AI
// POLAR ENVIRONMENT SIMULATION ENGINE
// ============================================================
//
// This is a software simulation of a polar / Southern Ocean
// environment.
//
// NORMAL and STORM are controlled scenarios.
// Values are simulation ranges informed by NOAA / NSIDC
// polar-ocean and sea-ice references.
//
// This is NOT measured scientific field data.
// ============================================================

let currentMode = "NORMAL";

// ------------------------------------------------------------
// Utility
// ------------------------------------------------------------

function randomBetween(min, max) {
    return min + Math.random() * (max - min);
}

function round(value, decimals = 2) {
    return Number(value.toFixed(decimals));
}

// ------------------------------------------------------------
// NORMAL POLAR CONDITIONS
// ------------------------------------------------------------

function generateNormalEnvironment() {

    return {
        mode: "NORMAL",

        water_temperature_c:
            round(randomBetween(-1.8, 4.0)),

        air_temperature_c:
            round(randomBetween(-15, 5.0)),

        humidity_percent:
            round(randomBetween(65, 95)),

        pressure_hpa:
            round(randomBetween(995, 1030)),

        wind_speed_ms:
            round(randomBetween(5, 15)),

        wave_height_m:
            round(randomBetween(0.5, 3.0)),

        salinity_psu:
            round(randomBetween(30, 35)),

        ice_concentration_percent:
            round(randomBetween(15, 80)),

        current_speed_ms:
            round(randomBetween(0.2, 1.2)),

        buoy_motion_level:
            "LOW",

        sampling_mode:
            "NORMAL",

        energy_mode:
            "POWER_SAVING"
    };
}

// ------------------------------------------------------------
// STORM CONDITIONS
// ------------------------------------------------------------

function generateStormEnvironment() {

    return {
        mode: "STORM",

        water_temperature_c:
            round(randomBetween(-1.8, 3.0)),

        air_temperature_c:
            round(randomBetween(-15, 2.0)),

        humidity_percent:
            round(randomBetween(85, 100)),

        pressure_hpa:
            round(randomBetween(960, 990)),

        // NOAA Beaufort storm regime begins at 24.5 m/s.
        wind_speed_ms:
            round(randomBetween(24.5, 32.0)),

        wave_height_m:
            round(randomBetween(6.0, 12.0)),

        salinity_psu:
            round(randomBetween(30, 35)),

        // Storm does NOT automatically change ice concentration.
        ice_concentration_percent:
            round(randomBetween(15, 90)),

        current_speed_ms:
            round(randomBetween(0.5, 2.0)),

        buoy_motion_level:
            "HIGH",

        sampling_mode:
            "HIGH_FREQUENCY",

        energy_mode:
            "HIGH_LOAD"
    };
}

// ------------------------------------------------------------
// MODE CONTROL
// ------------------------------------------------------------

function setMode(mode) {

    if (mode !== "NORMAL" && mode !== "STORM") {
        throw new Error("Mode must be NORMAL or STORM");
    }

    currentMode = mode;
}

// ------------------------------------------------------------
// GENERATE CURRENT ENVIRONMENT
// ------------------------------------------------------------

function generateEnvironment() {

    if (currentMode === "STORM") {
        return generateStormEnvironment();
    }

    return generateNormalEnvironment();
}

// ------------------------------------------------------------
// EXPORTS
// ------------------------------------------------------------

module.exports = {
    setMode,
    generateEnvironment
};

// ------------------------------------------------------------
// TEST MODE
// ------------------------------------------------------------

if (require.main === module) {

    console.log("");
    console.log("==========================================");
    console.log("      POLARSENSE AI ENVIRONMENT");
    console.log("==========================================");

    console.log("");
    console.log("NORMAL WEATHER");
    console.log("------------------------------------------");

    setMode("NORMAL");
    console.table(generateEnvironment());

    console.log("");
    console.log("STORM WEATHER");
    console.log("------------------------------------------");

    setMode("STORM");
    console.table(generateEnvironment());

    console.log("");
    console.log("Environment engine test complete.");
}