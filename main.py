import requests
from datetime import datetime

def get_rainfall_data(date=None):
    base_url = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
    params = {}
    if date:
        params['date'] = date
    
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    return response.json()

def print_all_stations(data):
    stations = data['data']['stations']
    print("Available stations:")
    for station in stations:
        print(f"{station['id']}: {station['name']}")

def print_rainfall_for_station(data, station_id):
    stations = data['data']['stations']
    readings = data['data']['readings'][0]  # first/latest timestamp

    station_map = {station['id']: station['name'] for station in stations}

    if station_id not in station_map:
        print(f"Station ID '{station_id}' not found.")
        return

    # Find the rainfall reading for the chosen station
    rainfall_value = None
    for reading in readings['data']:
        if reading['stationId'] == station_id:
            rainfall_value = reading['value']
            break

    if rainfall_value is None:
        print(f"No rainfall data found for station {station_id}.")
        return

    # Parse and format the timestamp
    timestamp_str = readings['timestamp']
    dt = datetime.fromisoformat(timestamp_str)

    # Format example: Date and time: August 9, 2025, at 3:05 PM SGT
    # %-d and %-I work on Unix; on Windows, use %#d and %#I instead
    try:
        formatted_time = dt.strftime("Date and time: %B %-d, %Y, at %-I:%M %p SGT")
    except ValueError:
        # For Windows compatibility:
        formatted_time = dt.strftime("Date and time: %B %#d, %Y, at %#I:%M %p SGT")

    print(f"Rainfall reading for {station_map[station_id]} ({station_id}) at {formatted_time}: {rainfall_value} {data['data']['readingUnit']}")

# Example usage
latest_data = get_rainfall_data()

print_all_stations(latest_data)
chosen_station = input("\nEnter the station ID you want rainfall data for: ").strip()

print_rainfall_for_station(latest_data, chosen_station)
