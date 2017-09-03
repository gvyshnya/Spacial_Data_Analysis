"""
    This script provides take-up ratio calculation for gated communities
"""

#!/usr/bin/python
import pandas as pd
import datetime as dt
import simpledbf as dbf

################################################
# Main execution loop
################################################
if __name__ == '__main__':

    start_time = dt.datetime.now()
    print("Started at ", start_time)

    # gated community-to-splitter-to-exchange area mapping file
    fname_gated_community_to_splitter_map = "output/gated_community_to_splitter_map.csv"
    fname_Gated_Communities = "input/Gated_Communities.dbf"

    fname_out_gated_community_take_up = "output/gated_community_take_up_ratios.csv"

    # read mapping file - the csv file with fields as follows
    # - gated_community_id (equals to GIS_ID in Gated Commmunities.dbf)
    # - total_units (equals to TOTAL_UNIT in Gated Commmunities.dbf)
    # - splitter_code (equals to CBS_SPLITT in Fibre_Splitter_Boundary.dbf)
    # - splitter_actual_homes (equals to ACTUAL_HOM in Fibre_Splitter_Boundary.dbf)
    # - ea_dssu (this will map it to an Exchange Area; this is equal to EA field in Fibre_Splitter_Boundary.dbf;
    #          EA itself is equal to DSSU field in Exchange_Boundary.dbf)
    # - gated_community_area - the square (area) of a gated community
    # - splitter_area - the square (area) of the gated community
    # - intersect_area - the square (area) of intersect between the gated community and splitter
    # - intersect_ratio - (intersect_area/gated_community_area) * 100%
    mapping_df = pd.read_csv(fname_gated_community_to_splitter_map, low_memory=True)

    # calculate take-up ratio per a gated community - splitter pair
    mapping_df['take_up_ratio'] = mapping_df['splitter_actual_homes']/mapping_df['total_units']

    # create an empty output df with take-up ratios for gated communities
    col_list = ['gated_community_id', 'take_up_ratio']
    output_df = pd.DataFrame(columns=col_list)
    row_count = 0

    g = mapping_df.groupby(['gated_community_id'])['take_up_ratio'].agg('sum')

    for i, row in g.iteritems():
        gated_community_id = int(i)
        if row > 1:
            take_up_ratio = 1.0
        else:
            take_up_ratio = row
        output_df.loc[row_count] = [gated_community_id, take_up_ratio]
        row_count += 1

    gated_communities_dbf = dbf.Dbf5(fname_Gated_Communities)
    gated_communities_df = gated_communities_dbf.to_dataframe()
    all_gated_communities_df = pd.DataFrame(columns=['gated_community_id', 'total_unit'])
    all_gated_communities_df['gated_community_id'] = gated_communities_df['GIS_ID']
    all_gated_communities_df['total_unit'] = gated_communities_df['TOTAL_UNIT']

    all_gated_communities_df = all_gated_communities_df.merge(output_df, how='left')
    all_gated_communities_df.fillna(0, inplace=True)

    all_gated_communities_df.to_csv(fname_out_gated_community_take_up, index=False)

    end_time = dt.datetime.now()
    elapsed_time = end_time - start_time
    print ("Finished take_up_calculation.py ... ")
    print("Elapsed time: ", elapsed_time)