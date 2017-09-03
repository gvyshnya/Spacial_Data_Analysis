"""
    This module will identify intersepts between gated communities and splitters.
    The results will be output in a csv file with fields as follows
    - gated_community_id (equals to GIS_ID in Gated Commmunities.dbf)
    - total_units (equals to TOTAL_UNIT in Gated Commmunities.dbf)
    - splitter_code (equals to CBS_SPLITT in Fibre_Splitter_Boundary.dbf)
    - splitter_actual_homes (equals to ACTUAL_HOM in Fibre_Splitter_Boundary.dbf)
    - ea_dssu (this will map it to an Exchange Area; this is equal to EA field in Fibre_Splitter_Boundary.dbf;
              EA itself is equal to DSSU field in Exchange_Boundary.dbf)
    - gated_community_area - the square (area) of a gated community
    - splitter_area - the square (area) of the gated community
    - intersect_area - the square (area) of intersect between the gated community and splitter
    - intersect_ratio - (intersect_area/gated_community_area) * 100%
"""

#!/usr/bin/python
import pandas as pd
import datetime as dt
import geopandas as gpd
import multiprocessing as mp

# https://gis.stackexchange.com/questions/178765/intersecting-two-shapefiles-from-python-or-command-line

def do_mapping(splitters_gdf):
    fname_Gated_Communities = "input/Gated_Communities.dbf"
    fname_Gated_Communities_Shapes = "input/Gated_Communities.shp"

    col_list = ['gated_community_id', 'total_units', 'splitter_code', 'splitter_actual_homes',
                'ea_dssu', 'gated_community_area', 'splitter_area', 'intersect_area', 'intersect_ratio']
    mapping_df = pd.DataFrame(columns=col_list)
    map_record_counter = 0

    g1 = splitters_gdf
    g2 = gpd.GeoDataFrame.from_file(fname_Gated_Communities_Shapes)

    for index2, comm in g2.iterrows():
        for index, splitter in g1.iterrows():
            if (comm is not None) & (splitter is not None):
                if (splitter['STATUS'] == "WORKING"):
                    if splitter['geometry'].intersects(comm['geometry']):
                        print("Comm ID in intersect: ", comm['GIS_ID'], "; splitter ", splitter['CBS_SPLITT'])
                        # print("Intercection found - splitter:", splitter)

                        gated_community_id = int(comm['GIS_ID'])
                        total_units = comm['TOTAL_UNIT']
                        splitter_code = splitter['CBS_SPLITT']
                        splitter_actual_homes = splitter['ACTUAL_HOM']
                        ea_dssu = splitter['EA']

                        splitter_area = splitter['geometry'].area
                        gated_community_area = comm['geometry'].area  #
                        intersect_area = comm['geometry'].intersection(splitter['geometry']).area

                        if gated_community_area == 0:
                            intersect_ratio = 0
                        else:
                            intersect_ratio = intersect_area / gated_community_area * 100

                        mapping_df.loc[map_record_counter] = [gated_community_id, total_units, splitter_code,
                                                  splitter_actual_homes, ea_dssu, gated_community_area,
                                                  splitter_area, intersect_area, intersect_ratio]
                        map_record_counter += 1
    return mapping_df

################################################
# Main execution loop
################################################
if __name__ == '__main__':

    start_time = dt.datetime.now()
    print("Started at ", start_time)

    # read shapes data from ESRI .shp files
    fname_Fibre_Splitter_Boundary_Shapes = "input/Fibre_Splitter_Boundary.shp"
    fname_Fibre_Splitter_Boundary = "input/Fibre_Splitter_Boundary.dbf"

    # output mapping file
    fname_out_gated_community_to_splitter_map = "output/gated_community_to_splitter_map.csv"

    col_list = ['gated_community_id', 'total_units', 'splitter_code', 'splitter_actual_homes',
                'ea_dssu', 'gated_community_area', 'splitter_area', 'intersect_area', 'intersect_ratio']
    mapping_df = pd.DataFrame(columns = col_list)
    map_record_counter = 0

    g1 = gpd.GeoDataFrame.from_file(fname_Fibre_Splitter_Boundary_Shapes)

    # slice fibre customers data set
    slices = []
    slice_size = 20
    total_rows = g1.shape[0]

    slice_start_id = 0
    slice_end_id = slice_start_id + slice_size

    while slice_start_id < total_rows:
        print('Preparing the new splitter slice: rows [', slice_start_id, ":", slice_end_id, "]")
        df_slice = g1[slice_start_id:slice_end_id]  # row with id slice_end_id not inclusive

        slices.append(df_slice)

        slice_start_id = slice_end_id
        slice_end_id = slice_start_id + slice_size
        if slice_end_id > total_rows:
            slice_end_id = total_rows

    # processing splitter membership in multi-threaded way
    pool = mp.Pool(6)  # use 6 processes

    funclist = []

    for df in slices:
        f = pool.apply_async(do_mapping, [df])
        funclist.append(f)

    result = []
    print("Total slices: ", len(slices))
    count = 1
    for f in funclist:
        print("Processing slice # ", count)
        result.append(f.get(timeout=6000))  # timeout in 6000 seconds = 10 mins
        count += 1

    # combine chunks with splitter mapping into a single dataframe
    mapping_df = pd.concat(result)

    mapping_df.to_csv(fname_out_gated_community_to_splitter_map, index=False)

    end_time = dt.datetime.now()
    elapsed_time = end_time - start_time
    print ("Finished splitter_2_gated_community_mapper.py ... ")
    print("Elapsed time: ", elapsed_time)
