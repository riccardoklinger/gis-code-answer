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
import osmapi
import overpy
def filterPoints(f):
		#this will filter the geojson so we will only use points with a speed of 0
	with open(f) as file:
		data = json.load(file)
	dataF = {}
	dataF['type']= 'FeatureCollection'
	dataF["crs"] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } }
	dataF['features']= []
	for feature in data['features']:
		if feature['properties']['speed']==0:
			dataF['features'].append(feature)
	#writing the filtered data to a file:
	with open('data/data_filtered.geojson', 'w') as f:
		json.dump(dataF, f)
	print str(index)+" objects written to file"
	print("executed")
def simplifyPoints(f,eps,min):
	with open(f) as file:
		data = json.load(file)
	#print dist 
	#let's work with DBSCAN
	import pandas as pd, numpy as np, matplotlib.pyplot as plt
	from sklearn.cluster import DBSCAN
	from geopy.distance import great_circle
	#create arrays for lat and lon
	lat2=[]
	lon2=[]
	index=[]
	for feature in data["features"]:
		lat2.append(feature["geometry"]["coordinates"][1])
		lon2.append(feature["geometry"]["coordinates"][0])
		index.append(feature["properties"]["id"])
	coord = {"lat": lat2, "lon":lon2}
	print coord
	df = pd.DataFrame(coord, index=index, columns=["lat","lon"])
	coordinates = df.as_matrix(columns=['lon', 'lat'])
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
	plt.figure(figsize=(10, 6), dpi=100)
	rs_scatter = plt.scatter(rs['lon'], rs['lat'], c='g', alpha=.4, s=150)
	df_scatter = plt.scatter(df['lon'], df['lat'], c='k', alpha=.5, s=5)
	plt.title('reduced dataset for ally')
	plt.legend((df_scatter, rs_scatter), ('activity points', 'Reduced set'), loc='upper left')
	plt.xlabel('Lon')
	plt.ylabel('Lat')
	plt.show()
	return rs
def collectWays(f, out_file): #get ways for a bounding box imported with a GeoJSON file and store them as a list of points
	import json, urllib
	with open(f) as file:
		data = json.load(file)

	lon = []
	lat = []
	for feature in data["features"]:
		lat.append(feature["geometry"]["coordinates"][1])
		lon.append(feature["geometry"]["coordinates"][0])
	bb = [min(lat), min(lon), max(lat), max(lon)]
	url = 'http://overpass-api.de/api/interpreter?data=[out:json][bbox:' + str(bb).strip('[]') +'];way["highway"~"secondary|primary|tertiary"];(._;>;);out geom;'
	response = urllib.urlopen(url)
	data2 = json.loads(response.read())
	with open(out_file, 'w') as outfile:
		json.dump(data2, outfile)
def getLinestrings(f): #reads the results from OSM export and returns a MultilineString
	import json
	from shapely.geometry import Point, LineString, MultiLineString
	with open(f) as file:
		data = json.load(file)

	lines = []

	for elem in data["elements"]:
		if elem["type"]=="way":
			line = []
			for geo in elem["geometry"]:
				line.append((geo["lon"], geo["lat"]))
			lines.append(line)
	lines=MultiLineString(lines)
	return lines
def createStation(filteredSetFile,osmFile):
	import pandas as pd, numpy as np, matplotlib.pyplot as plt	
	from shapely.geometry import Point
	lines=getLinestrings(osmFile)
	rs = simplifyPoints(filteredSetFile, 0.001, 2)
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
		dataF['features'].append({"geometry": {"type": "Point", "coordinates": [point.x, point.y]}, "type": "Feature", "properties": {"previous_dominating_activity": "still", "bearing": 0, "route": "", "previous_dominating_activity_confidence": 60, "current_dominating_activity": "in_vehicle", "current_dominating_activity_confidence": 77, "timestamp": "2015-11-11T09:03:01+0300", "created_at": "2015-11-11 06:03:12", "feature": "passive_tracking", "id": 4, "speed": 0, "altitude": 0.0, "accuracy": 23.0}})
	with open("data/potential_bus_stations.gojson", 'w') as outfile:
		json.dump(dataF, outfile)
def getCentroid(points):
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


def createMap(f):
	#we will use folium to create webmaps right out of python
	import folium
	stations_path = f
	
	map_osm = folium.Map(location=[45.5236, -122.6750])
	map_osm.geo_json(geo_path=stations_path)
	map_osm.create_map(path='osm.html')
