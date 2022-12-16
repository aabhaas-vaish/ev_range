# Introduction
With the recent advancements in Electric Vehicle (EV) technology, general consumers have readily started adopting EVs in the United States. However, one of the remaining challenges that is impeding the adoption of EVs is the availability of charging stations. In this context, this project would focus on creating a service that allows users to find a path from a starting location to an ending location while ensuring that the users stop at charging stations (pitstops) to recharge their range-limited EVs.

The data and code will be accessible at the following link - [https://www.github.com/](https://www.github.com/)

## Requirements
Please ensure that the following packages are installed in your environment using `pip`, before you run this project's code on your system:
    - Numpy
    - Geopy
    - Flask
## Brief Explanation
For this project, most of the work will be done by the code in the background. In order to run this, open up your terminal and activate any environments that you had created before. After this, navigate to the folder containing the project code, and run the following command: `python flask_app.py` to start the Flask server. Finally, open up your browser and type in: `http://127.0.0.1:5000/` and hit enter to open up the webpage. Finally, on the webpage, you will need to provide the following three inputs:
  1. Source City / Landmark (within Michigan)
  2. Destination City / Landmark (within Michigan)
  3. EV Range (in miles)
Finally, you can hit the `Get Route Map` or `Get Charger Coordinates` buttons to get your results!

# Data Sources
The primary data source for this project is from the Department of Energy and the auxiliary data source is the Geocoding API from Graphhopper. The following subsections describe these sources.

## Department of Energy Alternative Fuel Stations
This API provides a lot of valuable information about Alternative Fuel Stations located across the United States and is hosted by the Department of Energy at the following URL: [https://developer.nrel.gov/docs/transportation/alt-fuel-stations-v1/](https://developer.nrel.gov/docs/transportation/alt-fuel-stations-v1/). While there are a few different formats supported, I made use of the **JSON** file format. In order to access this data, I had to sign up for an API Key from the website, after which I was able to access relevant data using a GET request which returned a JSON object. Please note that the code does allow for caching, which means that if a cached JSON file exists on disk, it will directly take the information about the Alternative Fuel Stations from this file on disk. The data has been summarized as shown below:
  1. Available Records (Michigan): 1072
  2. Retrieved Records (Michigan): 1072
  3. Records
    1. **Access**: Determines if the station is private or public. For this project, I made use of only publicly available stations.
    2. **Fuel Type**: Determines the types of fuels available at stations - for instance, CNG, LPG, Electric, E85, etc. For this project, I made use of only Electric stations.
    3. **State**: Determines the state of the station. For this project, this was limited to Michigan to allow for reasonable run-times of Dijkstra's algorithm.
    4. **Latitude**: Determines the approximate latitude of the station - which is important for computing the distance between stations.
    5. **Longitude**: Determines the approximate Longitude of the station - which is important for computing the distance between stations.


## Graphhopper Geocoding API
This Geocoding API can be used to perform forward Geocoding, which is the process of obtaining a Lat/Long pair corresponding to an input street address. Note that this will be used to get the Lat/Long coordinates of the user's source and destination addresses. The documentation for this API is located at the following URL: [https://docs.graphhopper.com/#tag/Geocoding-API](https://docs.graphhopper.com/#tag/Geocoding-API). Similar to the primary data source, this data source also requires the use of an API Key form the website, which then allows you to use a GET request to get the relevant data in **JSON** format. Please note that since this address can change based on the user input (and because the results are very short JSON files), this data will not be cached. The data has been summarized as shown below:
  1. Available Records (Michigan): Greater than 1 Million (approximately)
  2. Retrieved Records (Michigan): 2 at a time
  3. Records
    1. **Query Address**: The address that we send in as a query.
    2. **Latitude**: Determines the approximate latitude of the address - which is important for computing the distance between stations and this point.
    3. **Longitude**: Determines the approximate longitude of the address - which is important for computing the distance between stations and this point.


## Graphhopper Maps API
For visualization, the source location, charger station locations, and the destination location will be passed to the Graphhopper Maps API at [https://graphhopper.com/maps/?profile=car&layer=Omniscale](https://graphhopper.com/maps/?profile=car&layer=Omniscale) which takes in a series of Lat/Long pairs to plot the path on a map. Note that this is not a data source but just a method to visualize. In addition, the project also lists down the charging station Lat/Long coordinates as texts using another button on the webpage!

![Raw](rawData.png)
![Data](data_graph.png)


# Data Structure - Graph
The primary data structure used in this project is the Graph data structure. The basic rationale of using this data structure has been highlighted below:
    - The first step of the process is to construct an **Adjacency Matrix** of the EV charger data. The idea is that the adjacency matrix will be a dense matrix representing the connections between EV charger stations. Moreover, each entry ($i,j$) in the matrix will represent the **Geodesic** distance between station $i$ and station $j$. Note here that the Geodesic distance represents an "as-the-crow-flies" distance between two points on the earth's surface instead of road distance. This is because the daily limit of the Graphhopper API for computing road distances is very low, and hence I had to use Geopy's Geodesic distance to compute pairwise distances between stations. Please note that this data can be pre-processed and saved as a cache to save time during inference.

    - The second step is to take in the source and destinations and add them as nodes to the pre-processed (or cached) Adjacency Matrix so that we have our final graph. This step is performed when the user enters their source and destination locations on the webpage, and therefore, is an on-the-fly operation that requires computing Geodesic distances again!

    - Furthermore, we can use the user-provided EV range, and filter out the connections or edges in the Adjacency Matrix that have values greater than this range. The idea here is to replace these values with $\infty$ so that Dijkstra's algorithm considers these edges unusable during its computations. Practically, this implies that our method will not generate direct paths between stations that have a pairwise distance longer than the EV range!

    - Finally, we can run Dijkstra's algorithm to find the shortest distance between the source and destination nodes in our graph!

Please note that I have also provided relevant files that interact with the cache to create the data structure (graph's adjacency matrix). First, the `makeAdjMatrix.py` file can be used to do a cache read or API call on the EV charger data and then construct the Adjacency Matrix. And finally, the `readAdjacencyMatrix.py` is a standalone file that can read and print the cached graph JSON.
[generic_graph](graph.png)

# Interaction and Presentation Options
The project is setup using a single-page Flask Web Application which can be deployed very easily using a single command: `python flask_app.py`. The main page consists of a very simple form that allows the user to input the 3 critical variables: Source Location, Destination Location, and EV Range. These three are highlighted below:
    - **Source Location**: The user can enter a city, landmark, or address within this text bar as their source location. Please note that API works really well for bigger landmarks and cities, but might return weird results for very specific street addresses once in a while.
    - **Destination Location**: The user can enter a city, landmark, or address within this text bar as their destination location. Please note that API works really well for bigger landmarks and cities, but might return weird results for very specific street addresses once in a while.
    - **EV Range**: The user can enter a numeric value for the EV Range in miles.

A screenshot of the main page is attached below for reference.
[main](CaptureProj.png)

## Get Route Map
This button can be used to generate a visualization of the shortest path from the source to the destination with pitstops in between for charging the EV. Please note that this project gets a path from Dijkstra's algorithm and saves the result as a list of Lat/Long coordinates. This result is passed to Graphhopper's Maps API to display the plotted path on their website!

[RouteMap](CaptureProj2.png)

## Get Charger Coordinates}
This button redirects to a results webpage that displays the EV charger locations that are pitstops for the user to charge their vehicle during the trip. These are represented in the form of an ordered list of the Lat/Long coordinates for each intermediate charging station!
[Charger](CaptureProj3.png)

# Demo Video of the Project
The project demo video can be accessed at the following link: [https://youtu.be/ruoM-9wWnN0](https://youtu.be/ruoM-9wWnN0)