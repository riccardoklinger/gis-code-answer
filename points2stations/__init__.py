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
	index = 0
	dataF['type']= 'FeatureCollection'
	dataF["crs"] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } }
	dataF['features']= []
	for feature in data['features']:
		if feature['properties']['speed']==0:
			dataF['features'].append(feature)
			index += 1
	#writing the filtered data to a file:
	with open('data_filtered.geojson', 'w') as f:
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
def collect_ways(f): #get ways for a bounding box imported with a GeoJSON file
	import overpy
	api = overpy.Overpass()
	with open(f) as file:
		data = json.load(file)
	N = []
	E = []
	S = []
	W = []
	lon = []
	lat = []
	for feature in data["features"]:
		lat.append(feature["geometry"]["coordinates"][1])
		lon.append(feature["geometry"]["coordinates"][0])
	bb = [min(lat), min(lon), max(lat), max(lon)]
	print "[out:json];node("+str(bb).strip('[]')+");out;"
	result = api.query("[out:json];way("+str(bb).strip('[]')+");out;")
	print len(result.ways)
	print result.ways[0].get_nodes(resolve_missing=True)
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