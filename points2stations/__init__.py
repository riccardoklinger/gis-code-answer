# -*- coding: utf-8 -*-
"""
/***************************************************************************
 points to bus
                                 A python workflow
 derives bus stations from point data
                              -------------------
        begin                : 2016-03-01
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Riccardo Klinger
        email                : riccardo.klinger@geolicious.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import json
class pointstation:
	def filter_points(f):
		#this will filter the geojson so we will only use points with a speed of 0
		with open(f) as file:
			data = json.load(file)
		print(data)
		print("executed")
