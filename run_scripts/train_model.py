import joblib
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.pipeline import Pipeline

from src.predictor.utils import ColumnSelector, DateTransformer, MultiColumnLabelEncoder

RESOURCE_FOLDER = "/Users/ioneuk/Documents/flight-price-predictor/data/"


def main() -> None:
    df = pd.read_csv("processed_dataset.csv", parse_dates=["date_time", "departure_date_time", "arrival_date_time"])
    categorical_features = ["departure_city", "arrival_city", "carrier_name"]
    all_columns_to_use = [
        "departure_city",
        "arrival_city",
        "flight_duration",
        "carrier_name",
        "flight_number",
        "departure_hour",
        "departure_minute",
        "arrival_hour",
        "arrival_minute",
        "days_left_to_departure",
        "is_holiday",
        "prev_price_1",
        "prev_price_2",
        "prev_price_3",
    ]
    parameters = {
        "loss_function": "RMSE",
        "eval_metric": "R2",
        "iterations": 1000,
        "learning_rate": 0.03,
        "random_seed": 42,
        "od_wait": 30,
        "od_type": "Iter",
        "thread_count": 10,
        "silent": True,
        "cat_features": categorical_features,
    }
    price_regressor = CatBoostRegressor(**parameters)
    pipeline = Pipeline(
        steps=[
            ("date_transformer", DateTransformer()),
            ("label_encoder", MultiColumnLabelEncoder(columns=categorical_features)),
            ("column_selector", ColumnSelector(all_columns_to_use)),
            ("price_regressor", price_regressor),
        ]
    )

    pipeline.fit(df, df["price"])
    joblib.dump(pipeline, "model.pkl")


if __name__ == "__main__":
    main()
