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


def dijkstra(adjacency: np.ndarray, startingNode: int, endingNode: int , NR: int) -> Tuple[dict, dict]:
    """Runs Dijkstra's Algorithm to find the shortest path from startingNode
    to endingNode.

    Parameters
    ----------
    adjacency : np.ndarray
        Adjacency matrix of size NR x NR
    startingNode : int
        Index of the starting node
    endingNode : int
        Index of the ending node
    NR: int
        Number of records or number of nodes in the graph

    Returns
    -------
    Tuple(dict, dict)
        Parent dictionary and Costs dictionary for each processed node
    """
    visited, parents, pq = set(), {}, []
    costs = defaultdict(lambda: np.inf)
    costs[startingNode] = 0.0

    # Push the source to the priority queue
    heap.heappush(pq, (0.0, startingNode, None))

    while pq:
        w, node, par = heap.heappop(pq)
        if node in visited:
            continue

        costs[node] = w
        parents[node] = par
        visited.add(node)

        # Halt function execution when we reach the final node
        if node == endingNode:
            return parents, costs

        for adjNode in range(NR):
            if adjNode in visited or adjNode == node or adjacency[node, adjNode] == np.inf:
                continue
            if w + adjacency[node, adjNode] < costs[adjNode]:
                heap.heappush(pq, (w + adjacency[node, adjNode], adjNode, node))

    return parents, costs


def getLatLongGeocoding(inputAddress: str) -> str:
    """Uses the Geocoding API to get a Lat/Long pair for a given address

    Parameters
    ----------
    inputAddress : str
        Specified input address

    Returns
    -------
    str
        Lat/Long pair as a string <lat>,<long>
    """

    baseUrl = "https://graphhopper.com/api/1/geocode?"
    params = {
        "q" : inputAddress,
        "locale" : "en",
        "key" : GEO_API_KEY
    }
    response = requests.get(baseUrl, params)
    responseData = response.json()
    pointData = responseData['hits'][0]['point']
    return (pointData['lat'], pointData['lng'])


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



def getChargingNetworkData(cacheFname: str, rawDataCacheFname: str) -> dict:
    """Gets relevant charging station data from the NREL website, and computes
    the adjacency matrix for the graph + a station_map which represents the
    lat/long coordinates of the charging stations.

    Returns
    -------
    dict
        Adjacency matrix as a np.ndarry, station_map as a dict, and 
        totalStations as an int
    """
    if os.path.exists(cacheFname):
        with open(cacheFname, 'r') as openfile:
            json_object = json.load(openfile)
        return np.array(json_object['adjacency_matrix']), json_object['station_map'], json_object['totalStations']

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

    # Dumping Cache
    json_object = json.dumps(cache)
    with open(cacheFname, "w") as outfile:
        outfile.write(json_object)

    return np.array(adjacency_matrix), station_map, totalStations


def getPointData(src: str, dest: str, EVRange: int) -> dict:
    """Returns the resulting path from source to dest which includes the
    locations of the intermediate charging stations

    Parameters
    ----------
    src : str
        Source Address as string
    dest : str
        Destination Address as string
    EVRange : int
        Range of the EV in miles

    Returns
    -------
    dict
        A dict with the URL to the graphhopper map API, a path list containing
        coordinates of the path, and a station_map for individual coordinates
        of each charging station
    """
    cacheFname = "cache.json"
    rawDataCacheFname = "raw_data.json"
    adjacency_matrix, station_map, totalStations = getChargingNetworkData(cacheFname, rawDataCacheFname)

    try:
        srcLatLong = getLatLongGeocoding(src)
        destLatLong = getLatLongGeocoding(dest)
    except:
        srcLatLong = (42.2681569, -83.7312291)
        destLatLong = (47.121872, -88.569012)


    # Subroutine fills up the distances from all stations to the source and
    # destination locations. Note that this is a geodesic disance and not a
    # road distance.
    station_map[str(totalStations)] = srcLatLong
    station_map[str(totalStations + 1)] = destLatLong

    upsizeAdj = np.zeros((totalStations + 2, totalStations + 2))
    upsizeAdj.fill(np.inf)
    upsizeAdj[0:totalStations, 0:totalStations] = adjacency_matrix
    for i in range(totalStations + 2):
        for j in range(i + 1, totalStations + 2):
            if i < totalStations and j < totalStations:
                continue
            dist = distance.geodesic(station_map[str(i)], station_map[str(j)]).miles
            upsizeAdj[i, j] = dist
            upsizeAdj[j, i] = dist

    # Filter values to incorporate EVRange
    upsizeAdj[upsizeAdj > EVRange] = np.inf

    # Call Dijkstra's using the incorrect indices
    src = totalStations
    dest = totalStations + 1
    parents, costs = dijkstra(upsizeAdj, src, dest, totalStations + 2)

    # Reconstruct path by iterating through the parents dictionary
    path = [dest]
    node = dest
    while parents[node] is not None:
        path.append(parents[node])
        node = parents[node]

    path_list = []
    for p in path:
        path_list.append(f'{station_map[str(p)][0]:.5f},{station_map[str(p)][1]:.5f}')

    # Create URL for graphhopper maps visualization
    base_url = 'https://graphhopper.com/maps/?'
    params = {
        "point": path_list,
        "profile": "car",
        "layer": "omniscale"
    }

    # Compile resulting data into a fixed dictionary
    result_data = {
        "url" : requests.get(base_url, params).url,
        "path_list" : path_list,
        "station_map" : station_map
    }

    return result_data


if __name__ == '__main__':
    result = getPointData("Detroit", "Munising", 200)
    webbrowser.open(result['url'])
