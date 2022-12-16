import heapq as heap
import json
import os
import requests
import numpy as np
import webbrowser

from collections import defaultdict
from geopy import distance
from typing import Tuple

def getAdjMatrix(cacheFname):
    if os.path.exists(cacheFname):
        with open(cacheFname, 'r') as openfile:
            json_object = json.load(openfile)
        return np.array(json_object['adjacency_matrix']), json_object['station_map'], json_object['totalStations']

if __name__ == '__main__':
    print(getAdjMatrix('cache.json'))
