"""This module will pre-process the intial data in the files below


    Its ultimate reulst will be to generate new csv files where geospacial matching of individual clients
    and houses to the polygons of gated / non-gated communities and splitters performed
"""

#!/usr/bin/python
import numpy as np
import pandas as pd
import simpledbf as dbf
import datetime as dt
import multiprocessing as mp
import shapefile as shp
from shapely.geometry import Polygon, Point, MultiPolygon

def get_clean_string(str_value1, str_value2):
    value = ""
    str_value1 = str(str_value1)
    str_value2 = str(str_value2)

    if str_value1 == str_value2:
        value = str_value1
    else:
        if str_value1 == 'NULL':
            value = str_value2
        else:
            if str_value2 == 'NULL':
                value = str_value1
            else:
                l1 = len(str_value1)
                l2 = len(str_value2)
                if l1 > l2:
                    value = str_value1
                else:
                    value = str_value2
    return value

def get_clean_speed_string(str_value1, str_value2):
    value = ""
    if str_value1 == str_value2:
        value = str_value1
    else:
        if str_value1 == 'NULL':
            value = str_value2
        else:
            if str_value2 == 'NULL':
                value = str_value1
            else:
                l1 = get_speed_in_mbits(str_value1)
                l2 = get_speed_in_mbits(str_value2)
                if l1 > l2:
                    value = str_value1
                else:
                    value = str_value2
    return value

def get_speed_in_mbits(speed_description):
    speed_value = 0
    if speed_description == "-":
        speed_value = 0
    if speed_description == "Up to 2048 Kb/s":
        speed_value = 2
    if speed_description == "2MB":
        speed_value = 2
    if speed_description == "Up to 4096 Kb/s":
        speed_value = 4
    if speed_description == "Up to 8Mb/s":
        speed_value = 8
    if speed_description == "Up to 10MB":
        speed_value = 10
    if speed_description == "Up to 20MB":
        speed_value = 20
    if speed_description == "40MB":
        speed_value = 40
    if speed_description == "Up to 40MB":
        speed_value = 40
    if speed_description == "Up to 100mbps":
        speed_value = 100
    return speed_value

def clean_up_fibre_customer_details(df_duplicates):
    total_duplicate_records = df_duplicates.shape[0]
    col_names = list(df_duplicates)

    if total_duplicate_records > 1:
        # ['service_no', 'latitude', 'longitude', 'service_type', 'service_desc', 'speed_desc']
        service_no = df_duplicates.iloc[0]['service_no']
        latitude = df_duplicates.iloc[0]['latitude']
        longitude = df_duplicates.iloc[0]['longitude']
        service_type = df_duplicates.iloc[0]['service_type']
        service_desc = df_duplicates.iloc[0]['service_desc']
        speed_desc = df_duplicates.iloc[0]['speed_desc']

        for i in range(df_duplicates.shape[0]):
            if i < df_duplicates.shape[0] - 1:
                service_type = get_clean_string(service_type,
                                        df_duplicates.iloc[i+1]['service_type'])
                service_desc = get_clean_string(service_desc,
                                        df_duplicates.iloc[i+1]['service_desc'])
                speed_desc = get_clean_speed_string(speed_desc,
                                        df_duplicates.iloc[i+1]['speed_desc'])

        clean_df = pd.DataFrame(columns = col_names)
        clean_df.loc[0] = [service_no, latitude, longitude, service_type, service_desc, speed_desc]
        return clean_df
    else:
        return df_duplicates

def map_clients_to_gated_community(df_fiber_clients):

    fname_Gated_Communities = "input/Gated_Communities.dbf"
    fname_Gated_Communities_Shapes = "input/Gated_Communities.shp"

    gated_communities_dbf = dbf.Dbf5(fname_Gated_Communities)
    gated_communities_df = gated_communities_dbf.to_dataframe()

    gated_community_sf = shp.Reader(fname_Gated_Communities_Shapes)
    gated_community_shapes = gated_community_sf.shapes()

    # match customer locations to gated communities or non-gated communities
    not_in_gated_community_id = -1   # fake code for a customer point not in a gated community

    gated_community_matches = []

    for i in (range(df_fiber_clients.shape[0])):

        y = df_fiber_clients.iloc[i]['latitude']
        x = df_fiber_clients.iloc[i]['longitude']
        customer_service_no = df_fiber_clients.iloc[i]['service_no']

        gated_community_id = not_in_gated_community_id

        a_point = Point(x, y)
        for j in range(len(gated_community_shapes)):
            # read current splitter and its shape
            gated_comm_shape = gated_community_shapes[j]
            gated_comm_id = int(gated_communities_df.iloc[j]['GIS_ID'])
            # read splitter shape geomerty
            shpfilePoints = gated_comm_shape.points
            if (len(shpfilePoints) == 0):
                print("Gated Community has zero-point geometry: ", gated_comm_id)
            else:
                poly = Polygon(shpfilePoints)

                # point in the splitter polygon test
                if poly.contains(a_point):
                    print("Customer inside the gated community: ", gated_comm_id)
                    print("Yes, we found it ++++++++++++++++++++++++++++++++++ ")
                    print("Customer service no:", gated_comm_id)
                    print("Gated Community shape boundaries: ", gated_comm_shape.bbox)
                    gated_community_id = gated_comm_id
                    print("Checked membership in Gated Community Shape #", j, ", gated community ID: ", gated_comm_id)
                    break
                else:
                    print("Customer outside the gated community: gated community ID '", gated_comm_id, "', customer: ",
                          customer_service_no)
                    print("Checked membership in Gated Community Shape #", j, ", gated community ID: ", gated_comm_id)
                    continue
        gated_community_matches.append(gated_community_id)

    mapped_df = pd.DataFrame(columns=['service_no', 'gated_community_id'])
    mapped_df['service_no'] = df_fiber_clients['service_no']
    mapped_df['gated_community_id'] = gated_community_matches
    return mapped_df

def map_clients_to_splitter(df_fiber_clients):
    # read shapes data from ESRI .shp files
    fname_Fibre_Splitter_Boundary_Shapes = "input/Fibre_Splitter_Boundary.shp"
    fname_Fibre_Splitter_Boundary = "input/Fibre_Splitter_Boundary.dbf"

    not_in_splitter = "NULL"  # fake code for a customer point not in any splitter

    fiber_splitter_dbf = dbf.Dbf5(fname_Fibre_Splitter_Boundary)
    fiber_splitter_df = fiber_splitter_dbf.to_dataframe()
    # filter only valuable fields from fiber_splitter_df

    splitter_sf = shp.Reader(fname_Fibre_Splitter_Boundary_Shapes)
    splitter_shapes = splitter_sf.shapes()

    fiber_splitter_matches = []

    for i in (range(df_fiber_clients.shape[0])):

        y = df_fiber_clients.iloc[i]['latitude']
        x = df_fiber_clients.iloc[i]['longitude']
        customer_service_no = df_fiber_clients.iloc[i]['service_no']
        splitter_reference = not_in_splitter

        a_point = Point(x, y)
        for j in range(len(splitter_shapes)):
            # check if the splitter is 'WORKING' - otherwise break and go to the next splitter
            splitter_status = fiber_splitter_df.iloc[j]['STATUS']
            # read splitter code
            splitter_code = fiber_splitter_df.iloc[j]['CBS_SPLITT']
            if (splitter_status != "WORKING"):
                print("Splitter is not working: Splitter Shape #", j, ", splitter code: ", splitter_code)
            else:

                # read current splitter and its shape
                spl_shape = splitter_shapes[j]

                # read splitter shape geomerty
                shpfilePoints = spl_shape.points
                if (len(shpfilePoints) == 0):
                    print("Splitter has zero-point geometry: ", splitter_code)
                else:
                    poly = Polygon(shpfilePoints)

                    # point in the splitter polygon test
                    if poly.contains(a_point):
                        print("Customer inside the splitter: ", splitter_code)
                        print("Yes, we found it ++++++++++++++++++++++++++++++++++ ")
                        print("Customer service no:", customer_service_no)
                        print("Splitter shape boundaries: ", spl_shape.bbox)
                        splitter_reference = splitter_code
                        print("Checked membership in Splitter Shape #", j, ", splitter code: ", splitter_code)
                        break
                    else:
                        print("Customer outside the splitter: splitter '", splitter_code, "', customer: ",
                            customer_service_no)
                        print("Checked membership in Splitter Shape #", j, ", splitter code: ", splitter_code)
                        continue

        fiber_splitter_matches.append(splitter_reference)

    mapped_df = pd.DataFrame(columns=['service_no', 'splitter'])
    mapped_df['service_no'] = df_fiber_clients['service_no']
    mapped_df['splitter'] = fiber_splitter_matches
    return mapped_df

################################################
# Main execution loop
################################################
if __name__ == '__main__':

    start_time = dt.datetime.now()
    print("Started at ", start_time)

    # paths to the input data files
    fname_fibre_lat_lon = "input/fibre_lat_lon.csv"
    fname_copper_lat_lon = "input/copper_lat_lon.csv"

    fname_Exchange_Boundary_Shapes = "input/Exchange_Boundary.shp"
    fname_Exchange_Boundary = "input/Exchange_Boundary.dbf"


    # paths to output data files
    fname_out_copper_customers_gated = "output/copper_customers_gated.csv"
    fname_out_fibre_customers_gated = "output/fibre_customers_gated.csv"
    fname_out_customers_non_gated = "output/customers_non_gated.csv"

    # read input data into Pandas DFs
    fibre_customers_df = pd.read_csv(fname_fibre_lat_lon, encoding = 'ISO-8859-1', low_memory=True)
    copper_customers_df = pd.read_csv(fname_copper_lat_lon, encoding = 'ISO-8859-1', low_memory=True)

    # drop repeatable records in both client data sets
    print("Shape of fibre_customers_df before searching for and dropping duplicates: ", fibre_customers_df.shape)
    print("Shape of copper_customers_df before searching for and dropping duplicates: ", copper_customers_df.shape)
    copper_customers_df = copper_customers_df.drop_duplicates(keep='first')
    fibre_customers_df = fibre_customers_df.drop_duplicates(keep='first')
    print("Shape of fibre_customers_df after searching for and dropping duplicates: ", fibre_customers_df.shape)
    print("Shape of copper_customers_df after searching for and dropping duplicates: ", copper_customers_df.shape)

    # clean up fiber_customers_df from duplicates, ambigious speed info etc.
    col_names = list(fibre_customers_df)
    # create clean replica of fibre_customers_df
    slices = []
    unique_fibre_service_numbers = fibre_customers_df.service_no.unique()

    for i in range(len(unique_fibre_service_numbers)):
        service_no = unique_fibre_service_numbers[i]
        grouped = fibre_customers_df.groupby('service_no').get_group(service_no)
        clean_slice_df = clean_up_fibre_customer_details(grouped)
        slices.append(clean_slice_df)

    # combine chunks with clean fibre customer data into a single dataframe
    fibre_customers_df = pd.concat(slices)

    # filter original customer dataframes for geospacial mapping
    fibre_customers_geo_df = fibre_customers_df.filter(items=["service_no", "latitude", "longitude"], axis = 1)
    copper_customers_geo_df = copper_customers_df.filter(items=["service_no", "latitude", "longitude"], axis = 1)

    # drop repeatable records in fibre_customers_geo_df and copper_customers_geo_df
    copper_customers_geo_df = copper_customers_geo_df.drop_duplicates(keep='first')
    fibre_customers_geo_df = fibre_customers_geo_df.drop_duplicates(keep='first')

    print("Fibre Customer geo details (after dropping duplicates):")
    print(fibre_customers_geo_df.info())
    print(fibre_customers_geo_df.tail())

    print("Copper Customer geo details (after dropping duplicates):")
    print(copper_customers_geo_df.info())
    print(copper_customers_geo_df.tail())

    # slice fibre customers data set
    slices = []
    slice_size = 10
    total_rows = fibre_customers_geo_df.shape[0]

    slice_start_id = 0
    slice_end_id = slice_start_id + slice_size


    while slice_start_id < total_rows:
        print('Preparing the new fibre customer slice: rows [', slice_start_id, ":", slice_end_id, "]")
        df_slice = fibre_customers_geo_df[slice_start_id:slice_end_id]  # row with id slice_end_id not inclusive

        slices.append(df_slice)

        slice_start_id = slice_end_id
        slice_end_id = slice_start_id + slice_size
        if slice_end_id > total_rows:
            slice_end_id = total_rows

    # processing splitter membership in multi-threaded way
    pool = mp.Pool(6)  # use 6 processes

    funclist = []

    for df in slices:
        f = pool.apply_async(map_clients_to_splitter, [df])
        funclist.append(f)

    result = []
    print("Total slices: ", len(slices))
    count = 1
    for f in funclist:
        print("Processing slice # ", count)
        result.append(f.get(timeout=6000))  # timeout in 6000 seconds = 10 mins
        count += 1

    # combine chunks with splitter mapping into a single dataframe
    fibre_customer_splitters_df = pd.concat(result)

    print("Splitter mapping results:")
    print(fibre_customer_splitters_df.info())
    print(fibre_customer_splitters_df.tail())

    # processing gated community membership in multi-threaded way
    pool = mp.Pool(6)  # use 6 processes

    funclist = []

    for df in slices:
        f = pool.apply_async(map_clients_to_gated_community, [df])
        funclist.append(f)

    result = []
    print("Total slices: ", len(slices))
    count = 1
    for f in funclist:
        print("Processing slice # ", count)
        result.append(f.get(timeout=6000))  # timeout in 6000 seconds = 10 mins
        count += 1

    # combine chunks with splitter mapping into a single dataframe
    fibre_customer_gated_community_df = pd.concat(result)

    print("Gated Community mapping results:")
    print(fibre_customer_gated_community_df.info())
    print(fibre_customer_gated_community_df.tail())

    fibre_customer_output = fibre_customers_geo_df.copy()

    # get clean service and speed descriptions for fibre service clients
    fibre_customer_output = fibre_customer_output.merge(fibre_customers_df, how='left')
    # get mapping to splitters for fibre service clients
    fibre_customer_output = fibre_customer_output.merge(fibre_customer_splitters_df, how='left')
    # get mapping to gated communities for fibre service clients
    fibre_customer_output = fibre_customer_output.merge(fibre_customer_gated_community_df, how='left')

    fibre_customer_output.to_csv(fname_out_fibre_customers_gated, index=False)

    fibre_end_time = dt.datetime.now()
    fibre_elapsed_time = fibre_end_time - start_time
    print("Time spent on fibre client mapping: ", fibre_elapsed_time)

    # slice copper customers data set
    slices = []
    slice_size = 10
    total_rows = copper_customers_geo_df.shape[0]

    slice_start_id = 0
    slice_end_id = slice_start_id + slice_size

    while slice_start_id < total_rows:
        print('Preparing the new copper customer slice: rows [', slice_start_id, ":", slice_end_id, "]")
        df_slice = copper_customers_geo_df[slice_start_id:slice_end_id]  # row with id slice_end_id not inclusive

        slices.append(df_slice)

        slice_start_id = slice_end_id
        slice_end_id = slice_start_id + slice_size
        if slice_end_id > total_rows:
            slice_end_id = total_rows

    # processing splitter membership in multi-threaded way
    pool = mp.Pool(6)  # use 6 processes

    funclist = []

    for df in slices:
        f = pool.apply_async(map_clients_to_splitter, [df])
        funclist.append(f)

    result = []
    print("Total copper slices: ", len(slices))
    count = 1
    for f in funclist:
        print("Processing slice # ", count)
        result.append(f.get(timeout=6000))  # timeout in 6000 seconds = 10 mins
        count += 1

    # combine chunks with splitter mapping into a single dataframe
    copper_customer_splitters_df = pd.concat(result)

    print("Splitter mapping results:")
    print(copper_customer_splitters_df.info())
    print(copper_customer_splitters_df.tail())

    # processing gated community membership in multi-threaded way
    pool = mp.Pool(6)  # use 6 processes

    funclist = []

    for df in slices:
        f = pool.apply_async(map_clients_to_gated_community, [df])
        funclist.append(f)

    result = []
    print("Total slices: ", len(slices))
    count = 1
    for f in funclist:
        print("Processing slice # ", count)
        result.append(f.get(timeout=6000))  # timeout in 6000 seconds = 10 mins
        count += 1

    # combine chunks with splitter mapping into a single dataframe
    copper_customer_gated_community_df = pd.concat(result)

    print("Gated Community mapping results:")
    print(copper_customer_gated_community_df.info())
    print(copper_customer_gated_community_df.tail())

    copper_customer_output = copper_customers_geo_df.copy()

    # get mapping to splitters for copper service clients
    copper_customer_output = copper_customer_output.merge(copper_customer_splitters_df, how='left')
    # get mapping to gated communities for copper service clients
    copper_customer_output = copper_customer_output.merge(copper_customer_gated_community_df, how='left')

    copper_customer_output.to_csv(fname_out_copper_customers_gated, index=False)

    end_time = dt.datetime.now()
    copper_elapsed_time = fibre_end_time - end_time
    elapsed_time = end_time - start_time
    print ("Finished preprocessing_fiber.py ... ")
    print("Elapsed time: ", elapsed_time)
    print("Time spent on fibre service customers: ", fibre_elapsed_time)
    print("Time spent on copper service customers: ", copper_elapsed_time)
