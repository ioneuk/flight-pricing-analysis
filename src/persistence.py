from .extensions import db


class FlightHistory(db.Model):
    flight_entry_id = db.Column("id", db.Integer, primary_key=True)
    departure_city = db.Column(db.String(80), nullable=False)
    arrival_city = db.Column(db.String(80), nullable=False)
    date_time = db.Column(db.DATETIME(), nullable=False)
    departure_date_time = db.Column(db.DATETIME(), nullable=False)
    arrival_date_time = db.Column(db.DATETIME(), nullable=False)
    carrier_name = db.Column(db.String(80), nullable=False)
    flight_duration_minutes = db.Column(db.INTEGER(), nullable=False)
    flight_number = db.Column(db.String(80), nullable=False)
    price = db.Column(db.DECIMAL(15, 2), nullable=False)
