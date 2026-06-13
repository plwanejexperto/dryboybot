import requests

def get_rainfall_data(date=None):
    """
    Fetch 5-minute rainfall readings from NEA API.
    
    Args:
        date (str): Optional. Date or datetime string in 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:mm:ss' format.
                    If None, fetches latest reading.
    
    Returns:
        dict: JSON response from the API.
    """
    base_url = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
    params = {}
    if date:
        params['date'] = date
    
    response = requests.get(base_url, params=params)
    response.raise_for_status()  # Raise error if request failed
    
    return response.json()

# Example usage:

# Get latest rainfall data
latest_data = get_rainfall_data()
print(latest_data)

# Get rainfall data for a specific day
date_data = get_rainfall_data("2024-07-16")
print(date_data)

# Get rainfall data for a specific timestamp
datetime_data = get_rainfall_data("2024-07-16T23:59:00")
print(datetime_data)

def print_rainfall(data):
    stations = data['data']['stations']
    readings = data['data']['readings'][0]  # Assuming we want the first/latest timestamp

    # Map stationId to station name for quick lookup
    station_map = {station['id']: station['name'] for station in stations}

    print(f"Rainfall readings at {readings['timestamp']} ({data['data']['readingUnit']}):\n")

    for reading in readings['data']:
        station_id = reading['stationId']
        rainfall = reading['value']
        station_name = station_map.get(station_id, "Unknown Station")
        print(f"{station_name} ({station_id}): {rainfall} mm")

print_rainfall(latest_data)
