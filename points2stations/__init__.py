# -*- coding: utf-8 -*-
"""
/***************************************************************************
 points to bus
								 A python workflow
 derives bus stations from point data
							  -------------------
		begin				: 2016-03-01
		git sha			  : $Format:%H$
		copyright			: (C) 2016 by Riccardo Klinger
		email				: riccardo.klinger@geolicious.de
 ***************************************************************************/

/***************************************************************************
 *																		 *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or	 *
 *   (at your option) any later version.								   *
 *																		 *
 ***************************************************************************/
"""
import json
def filterPoints(fileIn,fileOut):
	#this will filter the geojson so we will only use points with a speed of 0
	with open(fileIn) as file:
		data = json.load(file)
	dataF = {}
	index = 0
	dataF['type']= 'FeatureCollection'
	dataF["crs"] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } }
	dataF['features']= []
	for feature in data['features']:
		index += 1
		if feature['properties']['speed']==0:
			dataF['features'].append(feature)
	#writing the filtered data to a file:
	with open(fileOut, 'w') as f:
		json.dump(dataF, f)
	print str(index)+" objects written to file"
def simplifyPoints(fileIn,eps,min): #this creates a clustered result and a simple plot of results of clustering for a precheck
	# this is taken from: http://geoffboeing.com/2014/08/clustering-to-reduce-spatial-data-set-size/
	import pandas as pd, numpy as np, matplotlib.pyplot as plt
	from sklearn.cluster import DBSCAN
	from geopy.distance import great_circle
	with open(fileIn) as file:	# loading the data
		data = json.load(file) 
	#let's work with DBSCAN
	#create arrays for lat and lon
	lat2=[]
	lon2=[]
	index=[]
	#we build the pandas dataframe from the json ... I fcuking love to iterate
	for feature in data["features"]:
		lat2.append(feature["geometry"]["coordinates"][1])
		lon2.append(feature["geometry"]["coordinates"][0])
		index.append(feature["properties"]["id"])
	coord = {"lat": lat2, "lon":lon2}
	df = pd.DataFrame(coord, index=index, columns=["lat","lon"])
	coordinates = df.as_matrix(columns=['lon', 'lat'])
	#this will call the DBSCAN algroithm:
	db = DBSCAN(eps=eps, min_samples=min).fit(coordinates)
	labels = db.labels_
	num_clusters = len(set(labels)) - (1 if -1 in labels else 0)
	clusters = pd.Series([coordinates[labels == i] for i in xrange(num_clusters)])
	print('Number of clusters: %d' % num_clusters)
	lon = []
	lat = []
	for i, cluster in clusters.iteritems():
		if len(cluster) < 3:
			representative_point = (cluster[0][0], cluster[0][1])
		else:
			representative_point = getNearestPoint(cluster, getCentroid(cluster))
		lon.append(representative_point[0])
		lat.append(representative_point[1])
	print cluster
	rs = pd.DataFrame({'lon':lon, 'lat':lat})
	#the following code will only show the results for checking. This is not the map
	plt.figure(figsize=(10, 10), dpi=100)
	rs_scatter = plt.scatter(rs['lon'], rs['lat'], c='g', alpha=.4, s=150)
	df_scatter = plt.scatter(df['lon'], df['lat'], c='k', alpha=.5, s=5)
	plt.title('Reduced Dataset for Ally')
	plt.legend((df_scatter, rs_scatter), ('Activity Points', 'Reduced Set'), loc='upper left')
	plt.xlabel('Longitude')
	plt.ylabel('Latitude')
	plt.show()
	return rs
def collectWays(fileIn,fileOut): #get ways for a bounding box imported with a geoJSON file and store them as a list of points
	import json, urllib
	with open(fileIn) as file: #needs to be a geoJSON
		data = json.load(file)
	# let's create a bounding box by getting min and max values of the geojson geometries
	lon = []
	lat = []
	for feature in data["features"]:
		lat.append(feature["geometry"]["coordinates"][1])
		lon.append(feature["geometry"]["coordinates"][0])
	bb = [min(lat), min(lon), max(lat), max(lon)]
	# here comes the api call 
	url = 'http://overpass-api.de/api/interpreter?data=[out:json][bbox:' + str(bb).strip('[]') +'];way["highway"~"secondary|primary|tertiary"];(._;>;);out geom;' #this will only fetch ways from overpass api with a higher order as we suspect busses to drive only on ways >= tertiary
	response = urllib.urlopen(url)
	data2 = json.loads(response.read())
	with open(fileOut, 'w') as outfile:
		json.dump(data2, outfile) # store them in a JSON file
def getLinestrings(fileIn): #reads the results from OSM export and returns a MultilineString as it is needed for the projection / linear referencing of shapely.
	import json
	from shapely.geometry import Point, LineString, MultiLineString
	with open(fileIn) as file: # let's load the OSM extract
		data = json.load(file)
	# merge all lines to a singular road network:
	lines = []
	for elem in data["elements"]:
		if elem["type"]=="way":
			line = []
			for geo in elem["geometry"]:
				line.append((geo["lon"], geo["lat"]))
			lines.append(line)
	lines=MultiLineString(lines) #this is our road network in a MultiLineString
	return lines
def createStations(filteredSetFile,osmFile, eps, nr, fileOut): #this is the main implementation
	from shapely.geometry import Point
	lines=getLinestrings(osmFile)
	rs = simplifyPoints(filteredSetFile, eps, nr)
	rsProjected = []
	for index, row in rs.iterrows():
		p = Point(row.lon, row.lat)
		np = lines.interpolate(lines.project(p))
		rsProjected.append(np)
	dataF = {}
	dataF['type']= 'FeatureCollection'
	dataF["crs"] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } }
	dataF['features']= []
	for point in rsProjected:
		dataF['features'].append({"geometry": {"type": "Point", "coordinates": [point.x, point.y]}, "type": "Feature", "properties": {"type": "bus station"}})
	with open(fileOut, 'w') as outfile:
		json.dump(dataF, outfile)
def getCentroid(points): # tis will create the centroids for each cluster
	import numpy as np
	n = points.shape[0]
	sum_lon = np.sum(points[:, 0])
	sum_lat = np.sum(points[:, 1])
	return (sum_lon/n, sum_lat/n)
def getNearestPoint(set_of_points, point_of_reference): 
	from geopy.distance import great_circle
	closest_point = None
	closest_dist = None
	for point in set_of_points:
		point = (point[0], point[1])
		dist = great_circle(point_of_reference, point).meters
		if (closest_dist is None) or (dist < closest_dist):
			closest_point = point
			closest_dist = dist
	return closest_point
def createMap(fileIn, fileOrigin):
	#we will use folium to create webmaps right out of python
	import folium
	with open(fileIn) as file:
		stations = json.load(file)
	with open(fileOrigin) as file2:
		original = json.load(file2)
	map_osm = folium.Map(location=[-6.8048, 39.2865])
	for point in original["features"]:
		map_osm.circle_marker(location = [point["geometry"]["coordinates"][1],point["geometry"]["coordinates"][0]], radius=10, line_color='black', fill_color='grey', popup='previous_dominating_activity: ' + str(point["properties"]['previous_dominating_activity']) + ', bearing: ' + str(point["properties"]['bearing']) + ', previous_dominating_activity_confidence: ' + str(point["properties"]['previous_dominating_activity_confidence']) + ', current_dominating_activity: ' + str(point["properties"]['current_dominating_activity']) + ', timestamp: ' + str(point["properties"]['timestamp'])+ ', created_at: ' + str(point["properties"]['created_at']) + ', altitude: ' + str(point["properties"]['altitude']) + ', feature: ' + str(point["properties"]['feature']) + ', id: ' + str(point["properties"]['id']) + ', SPEED: ' + str(point["properties"]['speed']) + ', route: ' + str(point["properties"]['route'])+ ', current_dominating_activity_confidence: ' + str(point["properties"]['current_dominating_activity_confidence']) + ', accuracy: ' + str(point["properties"]['accuracy']))
	for station in stations["features"]:
		map_osm.circle_marker(location = [station["geometry"]["coordinates"][1],station["geometry"]["coordinates"][0]], radius=30, line_color='black', fill_color='red', popup="type: Bus Station")
	map_osm.create_map(path='osm.html')
