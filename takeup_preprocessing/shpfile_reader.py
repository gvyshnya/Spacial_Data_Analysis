"""This module will experiment with reading ESRI shp (shape form) files

"""

#!/usr/bin/python
import numpy as np
import pandas as pd
import simpledbf as dbf
import datetime as dt
import shapefile as shp
from shapely.geometry import Polygon, Point, MultiPolygon

################################################
# Main execution loop
################################################

start_time = dt.datetime.now()
print("Started at ", start_time)

fname_Exchange_Boundary = "input/Exchange_Boundary.dbf"
fname_Exchange_Boundary_Shp = "input/Exchange_Boundary.shp"
fname_fibre_lat_lon = "input/fibre_lat_lon.csv"

exchange_boundary_dbf = dbf.Dbf5(fname_Exchange_Boundary)
exchange_boundary_df = exchange_boundary_dbf .to_dataframe()

fibre_customers_df = pd.read_csv(fname_fibre_lat_lon, encoding = 'ISO-8859-1', low_memory=True)

print("Fibre Customer details:")
print(fibre_customers_df.info())
print(fibre_customers_df.tail())

print("Exchange Boundary details:")
print(exchange_boundary_df.info())
print(exchange_boundary_df.tail())

sf = shp.Reader(fname_Exchange_Boundary_Shp)

shapes = sf.shapes()
print("Length of Shapes in Exchange Boundaries:")
print(len(shapes))

a_shape = shapes[0]
a_customer = fibre_customers_df.iloc[1000]
print("Customer A details:")
print(a_customer.tail())


y = a_customer['latitude']
x = a_customer['longitude']
customer_service_no = a_customer['service_no']

print("Customer A latitude: ", y, "; Customer A longitude: ", x)

# redefine artificially
x = 25.6792
y = -25.4438

a_point = Point(x, y)

# bbox: If the shape type contains multiple points this tuple describes the lower left (x,y) coordinate and upper
# right corner coordinate creating a complete box around the points. If the shapeType is a Null (shapeType == 0)
# then an AttributeError is raised.
print(a_shape.bbox)
# parts: Parts simply group collections of points into shapes. If the shape record has multiple parts this attribute
# contains the index of the first point of each part. If there is only one part then a list containing 0 is returned.
print(a_shape.parts)
# points: The points attribute contains a list of tuples containing an (x,y) coordinate for each point in the shape.
print(a_shape.points)
# shapeType: an integer representing the type of shape as defined by the shapefile specification.
print(a_shape.shapeType)

counter = 0

for shape in shapes:
    shpfilePoints = shape.points
    polygon = shpfilePoints
    poly = Polygon(polygon)

    # point in polygon test
    if poly.contains(a_point):
        print("Customer inside: ", customer_service_no)
        print("Yes, we found it ++++++++++++++++++++++++++++++++++ ")

    else:
        print("Customer outside: ", customer_service_no)

    print("Exchange Boundary shape details: ", shape.bbox)
    print("Checked membership in Exchange Boundary #", counter)
    counter += 1

end_time = dt.datetime.now()
elapsed_time = end_time - start_time
print ("Finished preprocessing.py ... ")
print("Elapsed time: ", elapsed_time)
