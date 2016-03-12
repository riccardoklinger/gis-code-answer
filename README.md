# gis-code-challenge

## Task
Imagine you are a Software Developer at ally and you are presented that data. Your task is to derive bus stop locations from the data.

* 1. Develop an algorithm in Python that processes the data.
* 2. Visualise your results in a web map.

## asumptions
To create a minimum data quality check we select only data points within a region around a street and with a speed equals 0. As the source of the data is unknown, even this filtering is "hogus" as we pretend to have a knowledge of the data. Yet the dataset is only reduced a little. In a in-depth analysis a more advanced approach need to be considered.

## Steps 
* First we will filter the data (as mentioned above!) 
* Get OSM data for the bounding box of filtered data and store it as JSON 
* create a [DBSCAN](http://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html) result dataset 
* project resulting cluster centers to street points from OSM
* export points to leaflet webmap with folium

## Needed modules
For full functoionality different modules needs to get installed on the client side:
```
sudo pip install pandas geopy sklearn folium
```
## algorithm description
The points will be filtered by a very broad filter to consider only points with speed equals "0". Another option would be to select only points with a change of "previous_dominating_activity" to "current_dominating_activity" and a speed infomation. Yet using this option on the data would decrease the number of data points way to much!

After the first filtering we will use the DBSCAN algorithm to find centers of the points using a defined region (epsilon of 0.001 in this output) and a minimum number of points for a cluster center of two in the given radius. A higher radius will decrease the number of potential centers as well as a higher number of points within a cluster.

Seperately we will need an OSM extract of the bounding box of the input points. Therefore we use the overpass API to fetch only ways and their nodes in the bounding box.

As the projection function from shapely works on (Multi)LineString objects we will parse the OSM extract (JSON) to a MultiLineString. 

In the end we project the cluster centers to the nearest point of the street-structure and use those projected points as potential bus stop locations.



