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
    if speed_description == "Up to 2048 Kb/s":
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

################################################
# Main execution loop
################################################
if __name__ == '__main__':

    start_time = dt.datetime.now()
    print("Started at ", start_time)

    # paths to the input data files
    fname_fibre_lat_lon = "input/fibre_lat_lon.csv"
    fname_copper_lat_lon = "input/copper_lat_lon.csv"

    # paths to the output data files with the client data
    fname_out_fibre_lat_lon = "output/fibre_lat_lon.csv"
    fname_out_copper_lat_lon = "output/copper_lat_lon.csv"

    # read input data into Pandas DFs
    fibre_customers_df = pd.read_csv(fname_fibre_lat_lon, encoding = 'ISO-8859-1', low_memory=True)
    copper_customers_df = pd.read_csv(fname_copper_lat_lon, encoding = 'ISO-8859-1', low_memory=True)

    # look at data frames
    print("Fibre Customer details:")
    print(fibre_customers_df.info())
    print(fibre_customers_df.tail())

    print("Copper Customer details:")
    print(copper_customers_df.info())
    print(copper_customers_df.tail())

    # drop repeatable records in both client data sets
    print("Shape of fibre_customers_df before searching for and dropping duplicates: ", fibre_customers_df.shape)
    print("Shape of copper_customers_df before searching for and dropping duplicates: ", copper_customers_df.shape)
    copper_customers_df = copper_customers_df.drop_duplicates(keep='first')
    fibre_customers_df = fibre_customers_df.drop_duplicates(keep='first')
    print("Shape of fibre_customers_df after searching for and dropping duplicates: ", fibre_customers_df.shape)
    print("Shape of copper_customers_df after searching for and dropping duplicates: ", copper_customers_df.shape)

    print("Column list:")
    col_names = list(fibre_customers_df)
    print(col_names)

    # create clean replica of fibre_customers_df
    slices = []
    unique_fibre_service_numbers = fibre_customers_df.service_no.unique()

    for i in range(len(unique_fibre_service_numbers)):
        service_no = unique_fibre_service_numbers[i]
        grouped = fibre_customers_df.groupby('service_no').get_group(service_no)
        clean_slice_df = clean_up_fibre_customer_details(grouped)
        slices.append(clean_slice_df)

    # combine chunks with clean fibre customer data into a single dataframe
    clean_fibre_customers_df = pd.concat(slices)
    clean_fibre_customers_df.to_csv(fname_out_fibre_lat_lon, index=False)

    end_time = dt.datetime.now()
    elapsed_time = end_time - start_time
    print ("Finished client_data_cleancing.py ... ")
    print("Elapsed time: ", elapsed_time)
