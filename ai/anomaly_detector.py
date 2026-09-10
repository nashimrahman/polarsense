import os

import pandas as pd

from openpyxl import load_workbook

from sklearn.ensemble import IsolationForest


# ============================================================
# POLARSENSE AI
# AI ANOMALY DETECTION
# ============================================================


FILE_PATH = "data/ocean_simulations.xlsx"


# ============================================================
# CHECK DATA FILE
# ============================================================

if not os.path.exists(FILE_PATH):

    print("ERROR: Ocean simulation file not found.")

    print(
        "Run ocean.py first."
    )

    exit()


# ============================================================
# FIND LATEST SIMULATION
# ============================================================

workbook = load_workbook(
    FILE_PATH
)

run_sheets = []


for sheet_name in workbook.sheetnames:

    if sheet_name.startswith("Run_"):

        run_sheets.append(
            sheet_name
        )


if not run_sheets:

    print("ERROR: No simulation runs found.")

    exit()


# Sort Run_001, Run_002, Run_003...

run_sheets.sort()

latest_run = run_sheets[-1]


print()
print("==============================================")
print("       POLARSENSE AI - ANOMALY DETECTOR")
print("==============================================")
print()

print(
    f"Analysing simulation: {latest_run}"
)


# ============================================================
# LOAD DATA
# ============================================================

data = pd.read_excel(
    FILE_PATH,
    sheet_name=latest_run
)


print(
    f"Observations loaded: {len(data)}"
)


# ============================================================
# FEATURES USED BY AI
# ============================================================

features = [

    "temperature_c",

    "salinity_psu",

    "pressure_hpa",

    "wind_speed_ms",

    "humidity_percent",

    "wave_height_m",

    "current_speed_ms",

    "ice_concentration_percent",

    "ice_thickness_m"

]


# ============================================================
# CHECK FEATURES
# ============================================================

missing_features = []

for feature in features:

    if feature not in data.columns:

        missing_features.append(
            feature
        )


if missing_features:

    print()
    print("ERROR: Missing columns:")

    for feature in missing_features:

        print(
            f"  - {feature}"
        )

    exit()


# ============================================================
# PREPARE AI INPUT
# ============================================================

X = data[features].copy()


# Remove missing values

X = X.fillna(
    X.median()
)


# ============================================================
# CREATE AI MODEL
# ============================================================

model = IsolationForest(

    n_estimators=200,

    contamination=0.08,

    random_state=42

)


# ============================================================
# TRAIN MODEL
# ============================================================

print()
print("Training anomaly detection model...")


model.fit(X)


print("Training complete.")


# ============================================================
# PREDICT ANOMALIES
# ============================================================

predictions = model.predict(X)


scores = model.decision_function(X)


# ============================================================
# ADD RESULTS TO DATAFRAME
# ============================================================

data["anomaly_score"] = scores


data["anomaly_status"] = [

    "ANOMALY"
    if prediction == -1
    else "NORMAL"

    for prediction in predictions

]


# ============================================================
# COUNT RESULTS
# ============================================================

anomaly_count = (
    data["anomaly_status"]
    .value_counts()
    .get("ANOMALY", 0)
)


normal_count = (
    data["anomaly_status"]
    .value_counts()
    .get("NORMAL", 0)
)


# ============================================================
# SAVE RESULTS TO EXCEL
# ============================================================

result_sheet = (
    f"{latest_run}_AI"
)


# If sheet already exists, remove it

if result_sheet in workbook.sheetnames:

    del workbook[result_sheet]


worksheet = workbook.create_sheet(
    result_sheet
)


# ============================================================
# WRITE RESULTS
# ============================================================

headers = list(
    data.columns
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


for row_number, row in enumerate(
    data.itertuples(index=False),
    start=2
):

    for column_number, value in enumerate(
        row,
        start=1
    ):

        worksheet.cell(
            row=row_number,
            column=column_number,
            value=value
        )


# Freeze header

worksheet.freeze_panes = "A2"


# ============================================================
# SAVE
# ============================================================

workbook.save(
    FILE_PATH
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()
print("==============================================")
print("             AI ANALYSIS COMPLETE")
print("==============================================")

print()

print(
    f"Normal observations : {normal_count}"
)

print(
    f"Anomalies detected   : {anomaly_count}"
)

print()

print(
    f"Results saved to: {FILE_PATH}"
)

print(
    f"New sheet created: {result_sheet}"
)

print("==============================================")
print()