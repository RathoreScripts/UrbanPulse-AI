
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# URBANPULSE AI - AI WATER DEMAND FORECASTING
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = ROOT / "data" / "synthetic" / "campus_water_demand.csv"

OUTPUT_FOLDER = ROOT / "artifacts" / "reports" / "forecasting"
MODEL_FOLDER = ROOT / "models" / "forecasting"

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
MODEL_FOLDER.mkdir(parents=True, exist_ok=True)

ZONES = [
    "hostel",
    "academic",
    "canteen",
    "medical",
    "sports",
]

FORECAST_HOURS = 24

FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "day_of_year",
    "is_weekend",
    "lag_1",
    "lag_24",
    "lag_168",
    "rolling_24_mean",
    "rolling_168_mean",
]


# ------------------------------------------------------------
# 1. LOAD AND VALIDATE DATA
# ------------------------------------------------------------

def load_data():

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    required = ["timestamp", "zone", "demand_liters"]

    for column in required:
        if column not in df.columns:
            raise ValueError(
                f"Required column missing: {column}"
            )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["demand_liters"] = pd.to_numeric(
        df["demand_liters"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp", "zone", "demand_liters"]
    )

    df = df.sort_values(
        ["zone", "timestamp"]
    ).reset_index(drop=True)

    if (df["demand_liters"] < 0).any():
        raise ValueError("Negative demand values found.")

    print("\nDATASET LOADED")
    print("-" * 45)
    print(f"Total records: {len(df)}")
    print(f"Zones: {df['zone'].nunique()}")
    print(
        f"Date range: {df['timestamp'].min()} "
        f"to {df['timestamp'].max()}"
    )

    return df


# ------------------------------------------------------------
# 2. FEATURE ENGINEERING
# ------------------------------------------------------------

def create_features(series):

    frame = pd.DataFrame({
        "timestamp": series.index,
        "demand_liters": series.values,
    })

    frame["hour"] = frame["timestamp"].dt.hour
    frame["day_of_week"] = frame["timestamp"].dt.dayofweek
    frame["day_of_year"] = frame["timestamp"].dt.dayofyear

    frame["is_weekend"] = (
        frame["day_of_week"] >= 5
    ).astype(int)

    frame["lag_1"] = frame["demand_liters"].shift(1)
    frame["lag_24"] = frame["demand_liters"].shift(24)
    frame["lag_168"] = frame["demand_liters"].shift(168)

    frame["rolling_24_mean"] = (
        frame["demand_liters"]
        .shift(1)
        .rolling(window=24)
        .mean()
    )

    frame["rolling_168_mean"] = (
        frame["demand_liters"]
        .shift(1)
        .rolling(window=168)
        .mean()
    )

    frame = frame.dropna().reset_index(drop=True)

    return frame


# ------------------------------------------------------------
# 3. MODEL DEFINITIONS
# ------------------------------------------------------------

def create_models():

    return {
        "Random Forest": RandomForestRegressor(
            n_estimators=150,
            max_depth=12,
            min_samples_split=4,
            random_state=42,
            n_jobs=1,
        ),

        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=3,
            random_state=42,
        ),
    }


# ------------------------------------------------------------
# 4. EVALUATION METRICS
# ------------------------------------------------------------

def calculate_metrics(actual, predicted):

    mae = mean_absolute_error(actual, predicted)

    rmse = np.sqrt(
        mean_squared_error(actual, predicted)
    )

    r2 = r2_score(actual, predicted)

    return {
        "MAE": round(float(mae), 3),
        "RMSE": round(float(rmse), 3),
        "R2": round(float(r2), 4),
    }


# ------------------------------------------------------------
# 5. TRAIN AND COMPARE MODELS FOR ONE ZONE
# ------------------------------------------------------------

def train_zone_model(zone, zone_data):

    print("\n" + "=" * 60)
    print(f"TRAINING ZONE: {zone.upper()}")
    print("=" * 60)

    zone_data = (
        zone_data.sort_values("timestamp")
        .drop_duplicates(subset=["timestamp"])
        .set_index("timestamp")["demand_liters"]
        .asfreq("h")
    )

    if zone_data.isna().any():
        raise ValueError(
            f"{zone}: missing hourly demand values. "
            "Check the dataset before training."
        )

    if len(zone_data) <= 250:
        raise ValueError(
            f"{zone}: insufficient hourly history for forecasting."
        )

    features = create_features(zone_data)

    if len(features) < 100:
        raise ValueError(
            f"{zone}: insufficient rows after feature engineering."
        )

    # Chronological split: first 80% for training,
    # last 20% for testing.
    split_index = int(len(features) * 0.80)

    train = features.iloc[:split_index].copy()
    test = features.iloc[split_index:].copy()

    X_train = train[FEATURE_COLUMNS]
    y_train = train["demand_liters"]

    X_test = test[FEATURE_COLUMNS]
    y_test = test["demand_liters"]

    model_results = []
    predictions = {}
    trained_models = {}

    # --------------------------------------------------------
    # MOVING AVERAGE BASELINE
    # --------------------------------------------------------

    moving_average_predictions = test["rolling_24_mean"].values

    moving_metrics = calculate_metrics(
        y_test,
        moving_average_predictions
    )

    model_results.append({
        "zone": zone,
        "model": "Moving Average",
        **moving_metrics,
    })

    predictions["Moving Average"] = moving_average_predictions

    print(
        f"Moving Average | "
        f"MAE: {moving_metrics['MAE']} | "
        f"RMSE: {moving_metrics['RMSE']} | "
        f"R2: {moving_metrics['R2']}"
    )

    # --------------------------------------------------------
    # RANDOM FOREST AND GRADIENT BOOSTING
    # --------------------------------------------------------

    models = create_models()

    for model_name, model in models.items():

        model.fit(X_train, y_train)

        predicted = model.predict(X_test)

        metrics = calculate_metrics(
            y_test,
            predicted
        )

        model_results.append({
            "zone": zone,
            "model": model_name,
            **metrics,
        })

        predictions[model_name] = predicted
        trained_models[model_name] = model

        print(
            f"{model_name} | "
            f"MAE: {metrics['MAE']} | "
            f"RMSE: {metrics['RMSE']} | "
            f"R2: {metrics['R2']}"
        )

    # Select the model with the lowest test RMSE.
    best_result = min(
        model_results,
        key=lambda item: item["RMSE"]
    )

    best_name = best_result["model"]

    print(f"\nBEST MODEL FOR {zone.upper()}: {best_name}")

    best_model = trained_models.get(best_name)

    # Save the model and its feature information.
    model_path = MODEL_FOLDER / f"{zone}_best_model.pkl"

    joblib.dump(
        {
            "zone": zone,
            "best_model_name": best_name,
            "model": best_model,
            "feature_columns": FEATURE_COLUMNS,
        },
        model_path
    )

    # Save test predictions for analysis.
    prediction_df = pd.DataFrame({
        "timestamp": test["timestamp"].values,
        "zone": zone,
        "actual_demand_liters": y_test.values,
        "moving_average_prediction": predictions["Moving Average"],
        "random_forest_prediction": predictions["Random Forest"],
        "gradient_boosting_prediction": predictions["Gradient Boosting"],
        "best_model_prediction": predictions[best_name],
    })

    prediction_df.to_csv(
        OUTPUT_FOLDER / f"{zone}_test_predictions.csv",
        index=False
    )

    # Save actual versus best model plot.
    plt.figure(figsize=(12, 5))

    plt.plot(
        prediction_df["timestamp"],
        prediction_df["actual_demand_liters"],
        label="Actual Demand",
        linewidth=1.5
    )

    plt.plot(
        prediction_df["timestamp"],
        prediction_df["best_model_prediction"],
        label=f"Best Model: {best_name}",
        linewidth=1.5
    )

    plt.title(f"{zone.title()} - Actual vs Predicted Demand")
    plt.xlabel("Timestamp")
    plt.ylabel("Water Demand (Litres)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_FOLDER / f"{zone}_actual_vs_predicted.png",
        dpi=250
    )

    plt.close()

    return (
        model_results,
        best_name,
        best_model,
        zone_data,
    )


# ------------------------------------------------------------
# 6. NEXT 24-HOUR FORECAST
# ------------------------------------------------------------

def make_future_features(timestamp, history):

    values = np.asarray(history, dtype=float)

    row = {
        "hour": timestamp.hour,
        "day_of_week": timestamp.dayofweek,
        "day_of_year": timestamp.dayofyear,
        "is_weekend": int(timestamp.dayofweek >= 5),
        "lag_1": values[-1],
        "lag_24": values[-24],
        "lag_168": values[-168],
        "rolling_24_mean": float(np.mean(values[-24:])),
        "rolling_168_mean": float(np.mean(values[-168:])),
    }

    return pd.DataFrame(
        [row],
        columns=FEATURE_COLUMNS
    )


def forecast_next_24_hours(
    zone,
    history,
    best_name,
    best_model
):

    values = history.astype(float).tolist()

    last_timestamp = history.index[-1]

    future_rows = []

    for hour in range(1, FORECAST_HOURS + 1):

        future_timestamp = (
            last_timestamp + pd.Timedelta(hours=hour)
        )

        if best_name == "Moving Average":

            predicted = float(
                np.mean(values[-24:])
            )

        else:

            future_features = make_future_features(
                future_timestamp,
                values
            )

            predicted = float(
                best_model.predict(future_features)[0]
            )

        # Demand cannot be negative.
        predicted = max(0.0, predicted)

        future_rows.append({
            "timestamp": future_timestamp,
            "zone": zone,
            "predicted_demand_liters": round(predicted, 2),
            "selected_model": best_name,
        })

        # Recursive forecasting: use each prediction
        # as history for the next forecast hour.
        values.append(predicted)

    return future_rows


# ------------------------------------------------------------
# 7. MAIN FORECASTING PIPELINE
# ------------------------------------------------------------

def run_forecasting():

    print("\n" + "=" * 60)
    print("              URBANPULSE AI")
    print("          AI DEMAND FORECASTING")
    print("=" * 60)

    df = load_data()

    all_metrics = []
    all_forecasts = []
    best_models = {}

    for zone in ZONES:

        zone_data = df[df["zone"] == zone].copy()

        if zone_data.empty:
            print(f"\nWARNING: No data found for {zone}.")
            continue

        results, best_name, best_model, history = (
            train_zone_model(zone, zone_data)
        )

        all_metrics.extend(results)

        best_models[zone] = best_name

        forecast_rows = forecast_next_24_hours(
            zone,
            history,
            best_name,
            best_model
        )

        all_forecasts.extend(forecast_rows)

    # --------------------------------------------------------
    # SAVE MODEL COMPARISON
    # --------------------------------------------------------

    metrics_df = pd.DataFrame(all_metrics)

    metrics_df.to_csv(
        OUTPUT_FOLDER / "model_comparison_metrics.csv",
        index=False
    )

    # --------------------------------------------------------
    # SAVE FORECASTS
    # --------------------------------------------------------

    forecast_df = pd.DataFrame(all_forecasts)

    forecast_df.to_csv(
        OUTPUT_FOLDER / "next_24_hour_forecast.csv",
        index=False
    )

    # --------------------------------------------------------
    # TOTAL CAMPUS FORECAST
    # --------------------------------------------------------

    if not forecast_df.empty:

        campus_forecast = (
            forecast_df.groupby("timestamp")[
                "predicted_demand_liters"
            ]
            .sum()
            .reset_index()
        )

        campus_forecast.to_csv(
            OUTPUT_FOLDER / "campus_total_forecast.csv",
            index=False
        )

    # --------------------------------------------------------
    # FORECAST PLOT
    # --------------------------------------------------------

    for zone in ZONES:

        zone_forecast = forecast_df[
            forecast_df["zone"] == zone
        ]

        if zone_forecast.empty:
            continue

        plt.figure(figsize=(11, 5))

        plt.plot(
            zone_forecast["timestamp"],
            zone_forecast["predicted_demand_liters"],
            marker="o",
            label="Forecast"
        )

        plt.title(f"{zone.title()} - Next 24 Hours Water Demand")
        plt.xlabel("Forecast Time")
        plt.ylabel("Predicted Demand (Litres)")
        plt.xticks(rotation=30)
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()

        plt.savefig(
            OUTPUT_FOLDER / f"{zone}_24_hour_forecast.png",
            dpi=250
        )

        plt.close()

    # --------------------------------------------------------
    # SAVE BEST MODEL INFORMATION
    # --------------------------------------------------------

    with open(
        OUTPUT_FOLDER / "best_models.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            best_models,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------

    report_path = OUTPUT_FOLDER / "forecasting_report.txt"

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write("URBANPULSE AI - FORECASTING REPORT\n")
        file.write("=" * 55 + "\n\n")

        file.write("Dataset: Synthetic campus water demand\n")
        file.write("Forecast horizon: Next 24 hours\n")
        file.write("Models: Moving Average, Random Forest, Gradient Boosting\n")
        file.write("Validation: Chronological 80/20 split\n\n")

        file.write("MODEL COMPARISON\n")
        file.write("-" * 40 + "\n")
        file.write(metrics_df.to_string(index=False))

        file.write("\n\nSELECTED MODEL PER ZONE\n")
        file.write("-" * 40 + "\n")

        for zone, model_name in best_models.items():
            file.write(f"{zone}: {model_name}\n")

        file.write("\nIMPORTANT LIMITATIONS\n")
        file.write("-" * 40 + "\n")
        file.write(
            "Forecasts are based on synthetic historical demand.\n"
        )
        file.write(
            "They are not verified predictions of actual campus consumption.\n"
        )
        file.write(
            "Recursive multi-step forecasts may accumulate prediction errors.\n"
        )

    print("\n" + "=" * 60)
    print("FORECASTING COMPLETED")
    print("=" * 60)

    print("\nMODEL COMPARISON:")
    print(metrics_df.to_string(index=False))

    print("\nSELECTED MODELS:")
    for zone, model_name in best_models.items():
        print(f"{zone}: {model_name}")

    print("\nNEXT 24-HOUR FORECAST:")
    print(forecast_df.head(10).to_string(index=False))

    print(f"\nForecast outputs: {OUTPUT_FOLDER}")
    print(f"Saved models: {MODEL_FOLDER}")


if __name__ == "__main__":
    run_forecasting()
