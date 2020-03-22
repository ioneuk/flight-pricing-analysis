import os
from datetime import datetime
from typing import Dict, List

import joblib
import pandas as pd
from dateutil.relativedelta import relativedelta
from sklearn.pipeline import Pipeline

from src.persistence import FlightHistory

COLUMN_NAMES = [
    "date_time",
    "departure_city",
    "departure_iata_code",
    "arrival_city",
    "destination_iata_code",
    "departure_date_time",
    "arrival_date_time",
    "flight_duration",
    "carrier_name",
    "agent_name",
    "flight_number",
    "prev_price_1",
    "prev_price_2",
    "prev_price_3",
]


def get_previous_prices_for_flight(
    flights_count: int, departure_city: str, arrival_city: str, carrier_name: str, flight_number: str
) -> List[FlightHistory]:
    return (
        FlightHistory.query.order_by(FlightHistory.date_time.desc())
        .filter_by(departure_city=departure_city)
        .filter_by(arrival_city=arrival_city)
        .filter_by(carrier_name=carrier_name)
        .filter_by(flight_number=flight_number)
        .limit(flights_count)
        .all()
    )


class FlightsPredictor:
    def __init__(self, model: Pipeline) -> None:
        self._model = model

    @classmethod
    def load(cls, model_folder: str) -> "FlightsPredictor":
        model = joblib.load(os.path.join(model_folder, "model.pkl"))
        return cls(model=model)

    def predict(
        self,
        departure_city: str,
        arrival_city: str,
        departure_date_time: datetime,
        arrival_date_time: datetime,
        carrier_name: str,
        agent_name: str,
        flight_duration_minutes: int,
        flight_number: str,
    ) -> Dict[str, float]:
        current_date_time = datetime.now()
        if current_date_time > departure_date_time:
            raise RuntimeError("This flight has already occurred")
        prev_flights = get_previous_prices_for_flight(3, departure_city, arrival_city, carrier_name, flight_number)
        if len(prev_flights) < 3:
            raise RuntimeError("Not enough data for this flight")

        prev_prices = [flight.price for flight in prev_flights]
        first_date_to_forecast = prev_flights[0].date_time + relativedelta(days=3)
        second_date_to_forecast = first_date_to_forecast + relativedelta(days=3)
        third_date_to_forecast = first_date_to_forecast + relativedelta(days=6)
        data_to_predict = [
            [
                first_date_to_forecast,
                departure_city,
                None,
                arrival_city,
                None,
                departure_date_time,
                arrival_date_time,
                flight_duration_minutes,
                carrier_name,
                agent_name,
                flight_number,
                prev_prices[0],
                prev_prices[1],
                prev_prices[2],
            ],
            [
                second_date_to_forecast,
                departure_city,
                None,
                arrival_city,
                None,
                departure_date_time,
                arrival_date_time,
                flight_duration_minutes,
                carrier_name,
                agent_name,
                flight_number,
                0,
                prev_prices[0],
                prev_prices[1],
            ],
            [
                third_date_to_forecast,
                departure_city,
                None,
                arrival_city,
                None,
                departure_date_time,
                arrival_date_time,
                flight_duration_minutes,
                carrier_name,
                agent_name,
                flight_number,
                0,
                0,
                prev_prices[0],
            ],
        ]
        data_frame = pd.DataFrame(data_to_predict, columns=COLUMN_NAMES)
        price_predictions = self._model.predict(data_frame)
        return {
            first_date_to_forecast.strftime("%m/%d/%Y"): price_predictions[0],
            second_date_to_forecast.strftime("%m/%d/%Y"): price_predictions[1],
            third_date_to_forecast.strftime("%m/%d/%Y"): price_predictions[2],
        }
