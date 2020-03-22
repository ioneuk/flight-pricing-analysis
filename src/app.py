# type: ignore
import os
from typing import Dict

import dateutil.parser
from flask import request

from src.extensions import app
from src.predictor.flights_predictor import FlightsPredictor

model_folder = os.environ["PYTHON_MODEL_FOLDER"]
model = FlightsPredictor.load(model_folder)


@app.route("/api/predict", methods=["POST"])
def predict_prices() -> Dict[str, float]:
    request_body = request.json
    departure_date_time = dateutil.parser.parse(request_body["departureDateTime"])
    arrival_date_time = dateutil.parser.parse(request_body["arrivalDateTime"])
    return model.predict(
        request_body["departureCity"],
        request_body["arrivalCity"],
        departure_date_time,
        arrival_date_time,
        request_body["carrierName"],
        request_body["agentName"],
        request_body["flightDurationMinutes"],
        request_body["flightNumber"],
    )


@app.route("/health")
def healthckech() -> Dict[str, str]:
    return {"status": "UP"}


if __name__ == "__main__":
    app.run(host="0.0.0.0")
