import os
import csv
import logging
import boto3
import requests
from datetime import datetime
from itertools import islice
from itertools import product
from itertools import combinations
from dateutil.relativedelta import relativedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cities_codes_mapping = dict({
    'Kiev': 'KIEV-sky',
    'Lviv': 'LWO-sky',
    'Istanbul': 'ISTA-sky',
    'Moscow': 'MOSC-sky',
    'London': 'LOND-sky',
    'Saint Petersburg': 'LED-sky',
    'Berlin': 'BERL-sky',
    'Madrid': 'MAD-sky',
    'Rome': 'ROME-sky',
    'Paris': 'PARI-sky',
    'Bucharest': 'OTP-sky',
    'Minsk': 'MSQ-sky',
    'Hamburg': 'HAM-sky',
    'Vienna': 'VIE-sky',
    'Warsaw': 'WAW-sky',
    'Barcelona': 'BCN-sky',
    'Munich': 'MUC-sky',
    'Milan': 'MILA-sky',
    'Prague': 'PRG-sky',
    'Sofia': 'SOF-sky',
    'Brussels': 'BRUS-sky',
    'Belgrade': 'BELI-sky',
    'Venice': 'VENI-sky',
    'Florence': 'FLR-sky',
    'Amsterdam': 'AMS-sky',
    'athens': 'ATH-sky',
    'Lisbon': 'LIS-sky',
    'oslo': 'OSLO-sky',
    'kopenhagen': 'COPE-sky',
    'Edinburgh': 'EDI-sky',
    'Stockholm': 'STOC-sky',
    'Geneva': 'GVA-sky',
    'Zurich': 'ZRH-sky',
    'Budapest': 'BUD-sky'
})

rapid_api_host = os.environ["rapid_api_host"]
rapid_api_key = os.environ["rapid_api_key"]
country = os.environ["country"]
currency = os.environ["currency"]
locale = os.environ["locale"]
adults = os.environ["adults"]
s3_bucket_name = os.environ["s3_bucket_name"]
window_in_days = int(os.environ["window_in_days"])
number_of_date_iterations = int(os.environ["number_of_date_iterations"])
global_page_number = int(os.environ["global_page_number"])


class SearchResult(object):
    def __init__(self, itineraries, legs, carriers, agents, segments, places):
        self.itineraries = itineraries
        self.legs = legs
        self.carriers = carriers
        self.agents = agents
        self.segments = segments
        self.places = places

    def get_carrier_name_by_id(self, carrier_id):
        carrier = next(filter(lambda c: c["Id"] == carrier_id, self.carriers))
        return carrier["Name"]

    def get_agent_name_by_id(self, agent_id):
        agent = next(filter(lambda a: a["Id"] == agent_id, self.agents))
        return agent["Name"]

    def get_leg_by_outbound_id(self, outbound_leg_id):
        return next(filter(lambda leg: leg["Id"] == outbound_leg_id, self.legs))

    def get_segment_by_id(self, segment_id):
        return next(filter(lambda segment: segment["Id"] == segment_id, self.segments))

    def get_iata_code_by_station_id(self, station_id):
        station = next(filter(lambda s: s["Id"] == station_id, self.places))
        return station["Code"]


def create_session_for_flight_direction(departure_city, arrival_city, outbound_date, global_result,
                                        processed_flights_count, current_date_time):
    url = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/pricing/v1.0"

    origin_place_id = cities_codes_mapping[departure_city]
    destination_place_id = cities_codes_mapping[arrival_city]
    payload = f"country={country}&currency={currency}&locale={locale}&originPlace={origin_place_id}&destinationPlace={destination_place_id}&outboundDate={outbound_date}&adults={adults}"
    headers = {
        'x-rapidapi-host': rapid_api_host,
        'x-rapidapi-key': rapid_api_key,
        'content-type': "application/x-www-form-urlencoded"
    }

    response = perform_http_call("POST", url, headers, payload, None, global_result, processed_flights_count,
                                 current_date_time)
    location = response.headers['Location']
    return location.rsplit('/', 1)[-1]


def poll_for_results(session_key, global_result, processed_flights_count, current_date_time):
    url = f"https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/pricing/uk2/v1.0/{session_key}"

    querystring = {"sortType": "price", "sortOrder": "asc", "pageIndex": "0", "pageSize": "3"}

    headers = {
        'x-rapidapi-host': rapid_api_host,
        'x-rapidapi-key': rapid_api_key
    }

    response = perform_http_call("GET", url, headers, None, querystring, global_result, processed_flights_count,
                                 current_date_time).json()
    return SearchResult(response["Itineraries"], response["Legs"], response["Carriers"], response["Agents"],
                        response["Segments"], response["Places"])


def perform_http_call(http_method, url, headers, body, params, global_result, processed_flights_count,
                      current_date_time):
    response = requests.request(http_method, url, data=body, headers=headers, params=params)
    response.raise_for_status()
    return response


def process_flight_direction(departure_city, arrival_city, outbound_date, global_result, processed_flights_count,
                             current_date_time):
    session_key = create_session_for_flight_direction(departure_city, arrival_city, outbound_date, global_result,
                                                      processed_flights_count, current_date_time)
    result = poll_for_results(session_key, global_result, processed_flights_count, current_date_time)
    for itinerary in result.itineraries:
        outbound_leg_id = itinerary["OutboundLegId"]
        first_pricing_option_from_agent = next(iter(itinerary["PricingOptions"]))
        price = first_pricing_option_from_agent["Price"]

        agent_id = next(iter(first_pricing_option_from_agent["Agents"]))
        agent_name = result.get_agent_name_by_id(agent_id)

        leg = result.get_leg_by_outbound_id(outbound_leg_id)

        carrier_id = next(iter(leg["Carriers"]))
        carrier_name = result.get_carrier_name_by_id(carrier_id)

        segment_id = next(iter(leg["SegmentIds"]))
        segment = result.get_segment_by_id(segment_id)

        departure_iata_code = result.get_iata_code_by_station_id(segment["OriginStation"])
        destination_iata_code = result.get_iata_code_by_station_id(segment["DestinationStation"])

        departure_date_time = segment["DepartureDateTime"]
        arrival_date_time = segment["ArrivalDateTime"]
        flight_duration = segment["Duration"]
        flight_number = segment["FlightNumber"]
        global_result.append((current_date_time, departure_city, departure_iata_code, arrival_city,
                              destination_iata_code, departure_date_time, arrival_date_time, flight_duration,
                              carrier_name, agent_name, flight_number, price))


def persist_to_s3_bucket(global_result, processed_flights_count, current_date_time):
    logger.info(
        f"Persisting csv file with [{len(global_result)}] flight combination results to s3 bucket [{s3_bucket_name}]")
    file_name = current_date_time.strftime("%Y-%m-%d_%H:%M:%S") + '.csv'
    with open('/tmp/' + file_name, 'w') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['date_time', 'departure_city', 'departure_iata_code', 'arrival_city', 'destination_iata_code',
                          'departure_date_time', 'arrival_date_time', 'flight_duration', 'carrier_name', 'agent_name',
                          'flight_number', 'price'])
        for row in global_result:
            csv_out.writerow(row)
    s3 = boto3.client('s3')
    directory_path = current_date_time.strftime("%Y-%m-%d") + '/'
    with open('/tmp/' + file_name, "rb") as f:
        s3.upload_fileobj(f, s3_bucket_name, directory_path + file_name)


def flights_collector(event, context):
    logger.info("Starting collection process")
    processed_flights_count = int(event['iterator']['processed_flights_count'])
    global_result = []
    current_date_time = datetime.now()

    dates_to_search = []
    date_to_search = current_date_time + relativedelta(days=1)

    for i in range(0, number_of_date_iterations):
        dates_to_search.append(date_to_search)
        date_to_search += relativedelta(days=window_in_days)

    city_combinations = list(combinations(cities_codes_mapping, 2))
    city_combinations_with_dates = list(product(city_combinations, dates_to_search))

    start = processed_flights_count
    finish = min(len(city_combinations_with_dates), start + global_page_number)
    for idx, city_combination_with_date in enumerate(islice(city_combinations_with_dates, start, finish)):
        city_combination = city_combination_with_date[0]
        logger.info(
            f"Processing [{idx}] direction. Departure station [{city_combination[0]}] arrival station [{city_combination[1]}] departure date [{city_combination_with_date[1]}]")

        try:
            process_flight_direction(city_combination[0], city_combination[1],
                                     city_combination_with_date[1].strftime("%Y-%m-%d"), global_result,
                                     processed_flights_count, current_date_time)
        except requests.exceptions.HTTPError:
            logger.exception("Http error occured during request to SkyScanner API. Persisting collected results")
            persist_to_s3_bucket(global_result, processed_flights_count, current_date_time)

            processed_flights_count += len(global_result)
            logger.info(
                f"Processed [{processed_flights_count}] flight combinations out of [{len(city_combinations_with_dates)}] total")
            return {
                'processed_flights_count': processed_flights_count,
                'continue': True
            }

    persist_to_s3_bucket(global_result, processed_flights_count, current_date_time)

    processed_flights_count += len(global_result)
    logger.info(
        f"Processed [{processed_flights_count}] flight combinations out of [{len(city_combinations_with_dates)}] total")
    return {
        'processed_flights_count': processed_flights_count,
        'continue': finish < len(city_combinations_with_dates)
    }
