#!/usr/bin/python
import numpy as np
import pandas as pd
import simpledbf as dbf
import datetime as dt
import multiprocessing as mp
import shapefile as shp
from shapely.geometry import Polygon, Point, MultiPolygon

"""This module will merge cleaned data about copper service customers 
   (deduplicated, with maximally possible completeness of info) with their spacial details and links to splitter and
   gated / non-gated community
"""

#!/usr/bin/python
import numpy as np
import pandas as pd
import simpledbf as dbf
import datetime as dt
import multiprocessing as mp
import shapefile as shp
from shapely.geometry import Polygon, Point, MultiPolygon



################################################
# Main execution loop
################################################
if __name__ == '__main__':

    start_time = dt.datetime.now()
    print("Started at ", start_time)

    # paths to the input data files
    fname_copper_customers_geo = "output/copper_customers_gated.csv"
    fname_copper_customers_clean = "output/copper_customers_clean.csv"


    # paths to output data files
    fname_out_copper_customers_final = "output/copper_customers_gated_final.csv"

    # read input data into Pandas DFs
    copper_customers_clean_df = pd.read_csv(fname_copper_customers_clean, encoding='ISO-8859-1', low_memory=True)
    copper_customers_geo_df = pd.read_csv(fname_copper_customers_geo, encoding='ISO-8859-1', low_memory=True)

    # merging cleaned copper customers and their splitter/gated community relations datasets
    copper_customer_output = copper_customers_clean_df.copy()

    # get clean service details merged with the splitter and gated community references
    copper_customer_output = copper_customer_output.merge(copper_customers_geo_df, how='left')

    copper_customer_output.to_csv(fname_out_copper_customers_final, index=False)

    end_time = dt.datetime.now()
    elapsed_time = end_time - start_time
    print ("Finished preprocessing.py ... ")
    print("Elapsed time: ", elapsed_time)
