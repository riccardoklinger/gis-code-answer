# gis-code-challenge

## Task
Imagine you are a Software Developer at ally and you are presented that data. Your task is to derive bus stop locations from the data.

* 1. Develop an algorithm in Python that processes the data.
* 2. Visualise your results in a web map.

## Asumptions
To create a minimum data quality check we select only data points within a region around a street and with a speed equals 0. As the source of the data is unknown, even this filtering is "hogus" as we pretend to have a knowledge of the data. Yet the dataset is only reduced a little. In a in-depth analysis a more advanced approach needs to be considered. An increase in data size would also enhance QA.

## Steps 
* First we will filter the data (as mentioned above!) 
* Get OSM data for the bounding box of filtered data and store it as JSON 
* Create a [DBSCAN](http://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html) result dataset 
* Project resulting cluster centers to street points from OSM
* Export points to leaflet webmap with folium

## Needed Modules
For full functoionality different modules needs to get installed on the client side:
```
sudo pip install pandas geopy sklearn folium
```
## Algorithm Description
The points will be filtered by a very broad filter to consider only points with speed equals "0". Another option would be to select only points with a change of "previous_dominating_activity" to "current_dominating_activity" and a speed infomation. Yet using this option on the data would decrease the number of data points way to much!

After the first filtering we will use the DBSCAN algorithm to find centers of the points using a defined region (epsilon of 0.001 in this output) and a minimum number of points for a cluster center of two in the given radius. A higher radius will decrease the number of potential centers as well as a higher number of points within a cluster.

Seperately we will need an OSM extract of the bounding box of the input points. Therefore we use the overpass API to fetch only ways and their nodes in the bounding box.

As the projection function from shapely works on (Multi)LineString objects we will parse the OSM extract (JSON) to a MultiLineString. 

In the end we project the cluster centers to the nearest point of the street-structure and use those projected points as potential bus stop locations.

The webmap itself is produced from within python using a basic folium export without any further processing. The popups and the design of the webmap can be improved afterwards by reading and enhancing the osm.html file using python or a simple editor and manual editing. At the moment the map looks quite ugly. As the main framework should have been Python the main result was produced in Python only. A more improved webmap is also shipped as a result using qgis2leaf. It is stored in /map/index.html
## Reproducing The Map
```
os.chdir(path) #path needs to be the git folder
import points2stations as p2s
p2s.filterPoints("data/activity_points.geojson", "data/filtered_points.geojson")
p2s.simplifyPoints("data/filtered_points.geojson", 0.001, 2) # actual not needed but as a first preview of clustern
p2s.collectWays("data/filtered_points.geojson","data/osm_waypoints.json") # downloads the major street network and stores it in a distinct file.
p2s.createStations("data/filtered_points.geojson","data/osm_waypoints.json", 0.001,2, "data/potential_bus_stops.geojson") # this is the main function which calles the simplifyPoints as well as getLineStrings
p2s.createMap("data/potential_bus_stops.geojson","data/activity_points.geojson") # this will create a very simple webmap with the results. There are better ways to create a visualization within leaflet by adopting the html and js by hand. Unfortunately the possibilities with folium are limited but it gives a first overview of the results. 
```