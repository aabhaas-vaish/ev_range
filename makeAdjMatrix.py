import heapq as heap
import json
import os
import requests
import numpy as np
import webbrowser

from collections import defaultdict
from geopy import distance
from typing import Tuple

from APIKeys import DATA_API_KEY, GEO_API_KEY

def getRawData(rawDataCacheFname: str):
    if os.path.exists(rawDataCacheFname):
        with open(rawDataCacheFname, 'r') as openfile:
            json_object = json.load(openfile)
        return json_object['station_map'], json_object['totalStations']

    baseUrl = 'https://developer.nrel.gov/api/alt-fuel-stations/v1.json?'
    params = {
        "status" : "E",
        "access" : "public",
        "fuel_type" : "ELEC",
        "country" : "US",
        "state" : "MI",
        "api_key" : DATA_API_KEY
    }
    response = requests.get(baseUrl, params)
    a = response.json()
    print(f"Response received with {a['total_results']} stations records.")
    totalStations = a['total_results']
    station_map = {str(i) : [] for i in range(totalStations)}
    fuel_stations = a['fuel_stations']

    for i, station in enumerate(fuel_stations):
        station_map[str(i)] = (station['latitude'], station['longitude'])

    cache = {
        'station_map' : station_map,
        'totalStations' : totalStations
    }

    # Dumping Cache
    json_object = json.dumps(cache)
    with open(rawDataCacheFname, "w") as outfile:
        outfile.write(json_object)

    return station_map, totalStations

def getChargingNetworkData(rawDataCacheFname: str) -> dict:
    """Gets relevant charging station data from the NREL website, and computes
    the adjacency matrix for the graph + a station_map which represents the
    lat/long coordinates of the charging stations.

    Returns
    -------
    dict
        Adjacency matrix as a np.ndarry, station_map as a dict, and 
        totalStations as an int
    """
    station_map, totalStations = getRawData(rawDataCacheFname)

    # Compute and fill pairwise geodesic distance. Note that we cannot use a 
    # road-wise distance because the Routing API from graphhopper allows very
    # limited number of queries per day.
    adjacency_matrix = np.zeros((totalStations, totalStations))
    adjacency_matrix.fill(np.inf)
    for i in range(totalStations):
        for j in range(i+1, totalStations):
            dist = distance.geodesic(station_map[str(i)], station_map[str(j)]).miles
            adjacency_matrix[i, j] = dist
            adjacency_matrix[j, i] = dist

    cache = {
        'adjacency_matrix' : adjacency_matrix.tolist(),
        'station_map' : station_map,
        'totalStations' : totalStations
    }

    return np.array(adjacency_matrix), station_map, totalStations

if __name__ == '__main__':
    print(getChargingNetworkData('rawData.json'))
