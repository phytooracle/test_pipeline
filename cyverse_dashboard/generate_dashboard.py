import sys, glob, os, pdb
from itertools import groupby
from operator import itemgetter
import pandas as pd
import numpy as np
from config import Config
import re
from operator import itemgetter
import dashboard_html
import filesystem_functions
import argparse

"""
For Nathan using iPython locally...
%run ~/work/repos/test_pipeline/dashboard/generate_dashboard
"""




# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='PhytoOracle Dashboard',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-cp',
                        '--cyverse_path',
                        help='path to top level of cyverse data',
                        default = '/iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_2/scanner3DTop/',
                        type=str)

    parser.add_argument('-tn',
                        '--tag_name',
                        help='tag name for visualization',
                        default = 'individual_plants_out',
                        type=str)

    parser.add_argument('-p',
                        '--N_PLANTS_PER_PAGE',
                        help='Number of plants per page',
                        type=int,
                        default=50)


    return parser.parse_args()



def create_dict_of_lists_from_list(the_list):
    return_dict = {}
    for l in the_list:
        return_dict[l] = []
    return return_dict

def make_output_process_tag_pages(de_path, tag_path):

    # replace with get plants_paths
    # gets plant names per date
    date_tag_plants = filesystem_functions.find_plant_names_in_dir_cyverse(de_path, tag_path)

    # make argument
    tag_name = args.tag_name
    print(tag_name)

    ##################################################
    #        Determine how many pages we need
    #
    # We don't want 200 plants on one page, so we
    # break it up into n plants per page.
    ##################################################

    plant_dirs = date_tag_plants

    n_pages = -(-len(plant_dirs)//N_PLANTS_PER_PAGE)  # Round up.  3.0->3, 3.1->4
    page_list = dashboard_html.divide_list_into_chunks(plant_dirs, n_pages)

    nav_html = f"{len(plant_dirs)} plants have been divided into {n_pages} page/s...<br>"
    for n in range(n_pages):
        nav_html += f"<li><a href='index_{n+1}.html'>Page {n+1}</a>\n"

    #####################
    # Loop through pages
    #####################

    # use this to make the plant pages

    for page_count, plant_dirs in enumerate(page_list):
        page_count += 1

        print(f"Creating page {page_count} of {n_pages}")
        
        # note: tagPage is not a string, it is a class.

        # this needs to be changed to be local to wherever you ran it
        outpath_split = tag_path.split('/')
        date_loop = outpath_split[0]
        tag_loop = outpath_split[1]

        date_dir = os.path.join('.', date_loop)
        if not os.path.exists(date_dir):
            os.mkdir(date_dir)

        date_tag_dir = os.path.join(date_dir, tag_loop)
        if not os.path.exists(date_tag_dir):
            os.mkdir(date_tag_dir)

        reports_folder = os.path.join('.', tag_path, 'plant_reports')
        if not os.path.exists(reports_folder):
            os.mkdir(reports_folder)

        tagPage  = dashboard_html.OutputTagPage(os.path.join(reports_folder, f"index_{page_count}.html"),
                                                name=tag_path)
        tagPage += f"""
            <h2>Page {page_count} of {n_pages}</h2>
            <hr>
            {nav_html}
            <hr>
            <table>
        """

        ######################
        # Loop through plants 
        ######################

        for count, plant_name in enumerate(plant_dirs):
            count += 1
            print(f"({count}/{len(plant_dirs)}) : {plant_name}")

            # this function should be changed to point at cyverse

            cyverse_prefix = 'https://data.cyverse.org/dav-anon/iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_2/scanner3DTop/'
            
            plant_path = os.path.join(cyverse_prefix, date_loop, tag_loop, 'plant_reports', plant_name)
            tagPage += dashboard_html.plant_data_row(plant_name, plant_path)


        tagPage += dashboard_html.plant_data_row_bottom()

        tagPage += "</table>"
        tagPage.save_page()



# def make_comparison_pages(date, date_tags):
#     import itertools
#     tags = filesystem_functions.convert_paths_to_names(date_tags)
#     tags.sort()
#     tag_combinations = list(itertools.combinations(tags, 2))
#     for combination in tag_combinations:
#         combination_name = "-vs-".join(combination)

#         # find plants that they have in common
#         tag1_plants = filesystem_functions.get_plants_in_dir(os.path.join(date, combination[0]))
#         tag2_plants = filesystem_functions.get_plants_in_dir(os.path.join(date, combination[1]))
#         common_plants = list(set(tag1_plants + tag2_plants))

#         n_pages = -(-len(common_plants)//N_PLANTS_PER_PAGE)  # Round up.  3.0->3, 3.1->4
#         page_list = dashboard_html.divide_list_into_chunks(common_plants, n_pages)

#         nav_html = f"{len(common_plants)} plants have been divided into {n_pages} page/s...<br>"
#         for n in range(n_pages):
#             nav_html += f"<li><a href='{combination_name}_{n+1}.html'>Page {n+1}</a>\n"

#         #####################
#         # Loop through pages
#         #####################

#         for page_count, plant_dirs in enumerate(page_list):
#             page_count += 1

#             print(f"Creating page {page_count} of {n_pages}")
#             combinationPage  = dashboard_html.GenericPage(
#                     f"{date}/{combination_name}_{page_count}.html",
#                     name=combination_name,
#             )
            
#             # note: tagPage is not a string, it is a class.
#             combinationPage += f"""
#                 <h2>{date}</h2>
#                 <h2>Page {page_count} of {n_pages}</h2>
#                 <hr>
#                 {nav_html}
#                 <hr>
#                 <table>
#             """

#             colors = ("#332211", "#112233")
#             count = 0
#             for plant_name in plant_dirs:
#                 count += 1
#                 color = colors[ count%2 ]
#                 combinationPage += dashboard_html.comparison_row(plant_name, combination, color)

#             combinationPage += dashboard_html.combination_row_bottom(combination)
#             combinationPage += f"""
#                 </table>
#             """

#             combinationPage.save_page()



if __name__ == "__main__":

    args = get_args()
    N_PLANTS_PER_PAGE = args.N_PLANTS_PER_PAGE
    cyverse_path = args.cyverse_path
    tag_name = args.tag_name

    #dashboard_root = os.path.join(conf.args.date, conf.args.output_process_tag, "plant_reports")
    # dashboard_html.__root_path__ = "."

    page_tree_dict  = {}


    # This needs to get paths from cyverse instead
    all_dates  = filesystem_functions.get_all_dates_cyverse(cyverse_path)


    all_plants = filesystem_functions.find_all_plant_names_cyverse(cyverse_path, tag_name)
    print(all_plants)

    dates_dict  = create_dict_of_lists_from_list(all_dates)
    plants_dict = create_dict_of_lists_from_list(all_plants)

    
    metaPage = dashboard_html.GenericPage("index.html", name="Dashboard Home")
    for date in all_dates:
        print(f"{date}")
        metaPage += f"<h2>{date}</h2>\n"
        datePage = dashboard_html.GenericPage(os.path.join(date, f"index.html"))



        date_tags = [os.path.join(date, tag_name)]
        print(date_tags)
        date_tags.sort()
        for tag_path in date_tags:

            print('Date tags = ', date_tags)
            # dummyIndextagPage is wierd.  We only make it to get the path to pass
            # to metaPage.  The real tag pages get created in make_output_process_tag_pages
            # a hack because I coded myself into a corner, and dont care at the moment. [NPH]
            dummyTagPage = dashboard_html.GenericPage(
                                                  os.path.join(tag_path, 'plant_reports', 'index_1.html'),
                                                  name = tag_path,
            )
            metaPage.add_link(dummyTagPage)




            # ALl this needs to point to cyverse
            plant_paths = filesystem_functions.find_plant_names_in_dir_cyverse(cyverse_path, tag_path)

            if plant_paths == 'foo':
                print('No plants found, on to next dir')
                break
            n_plants = len(plant_paths)
            metaPage += f"({n_plants} plants processed)"


            make_output_process_tag_pages(cyverse_path, tag_path)
            # make_comparison_pages(date, date_tags)


        # note: GenericPage() is a class, not a string, it is a class, so
        #       don't be fooled by the += applied to it.

        if plant_paths != 'foo':
            datePage.save_page()

    metaPage.save_page()
