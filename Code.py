import http.client
import urllib.parse
import json


class DhlApi:
    def __init__(self, dhl_api_key, tracking_num):
        self.dhl_api_key = dhl_api_key
        self.tracking_num = tracking_num
        self.type = 'express'
        self.parameters = {'service': self.type, 'trackingNumber': self.tracking_num}
        self.head = {'Accept': 'application/json', 'DHL-API-Key': self.dhl_api_key}
        self.track = None
        self.discover = None
        self.data = None
        self.fetched_data = None
        self.country_code = None
        self.city = None
        self.radius = None

    def tracker(self):
        self.track = urllib.parse.urlencode(self.parameters)

    def take_data(self):
        connection = http.client.HTTPSConnection("api-eu.dhl.com")
        try:
            connection.request("GET", "/track/shipments?" + self.track, "", self.head)
            self.data = json.loads(connection.getresponse().read())
            return self.data
        finally:
            connection.close()

    def fetch_last_event(self):
        self.tracker()
        self.fetched_data = self.take_data()
        if "shipments" in self.fetched_data and self.fetched_data["shipments"]:
            events = self.fetched_data["shipments"][0].get("events", [])
            if events:
                return events[-1]
        return None

        # I do not know if this works due to lack of access

    def get_service_point_by_parameters(self, country_code_track, city_track, radius_track=None):
        service_loc = {'countryCode': country_code_track, 'cityName': city_track}
        if radius_track:
            service_loc['radius'] = radius_track
        query_params = urllib.parse.urlencode(service_loc)
        connection = http.client.HTTPSConnection("api-eu.dhl.com")

        try:
            connection.request("GET", f"/location-finder/v1/find-by-address?{query_params}", "", self.head)
            response = connection.getresponse()
            status_code = response.status
            data = json.loads(response.read())
            # Debug
            print(f"Status Code: {status_code}")
            print("Service points response:", json.dumps(data, indent=2))
            if "locationDetails" in data:
                service_points = [location.get("name") for location in data["locationDetails"] if "name" in location]
                return service_points
            else:
                return []
        finally:
            connection.close()


if __name__ == '__main__':
    api_key = input("Insert the API key : ")
    parcel = input("Insert your parcel number : ")

    dhl = DhlApi(api_key, parcel)
    last_event = dhl.fetch_last_event()
    print("Last Tracking Event:")
    print(json.dumps(last_event, indent=2))

    # Tied to  get_service_point_by_parameters method so it does not work
    country_code = "IT"
    city = "Milan"
    radius = 10
    p_and_p = dhl.get_service_point_by_parameters(country_code, city, radius)
    if p_and_p:
        print(f"DHL Service Points in {city}, {country_code} within {radius} km:")
        for services in p_and_p:
            print(f"- {services}")
    else:
        print(f"No DHL Service Points found in {city}, {country_code} within {radius} km.")
