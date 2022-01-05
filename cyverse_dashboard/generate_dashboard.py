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

"""
For Nathan using iPython locally...
%run ~/work/repos/test_pipeline/dashboard/generate_dashboard
"""

N_PLANTS_PER_PAGE = 50

def create_dict_of_lists_from_list(the_list):
    return_dict = {}
    for l in the_list:
        return_dict[l] = []
    return return_dict

def make_output_process_tag_pages(tag_path):

    date_tag_plants = filesystem_functions.get_plants_in_dir(tag_path)
    tag_name = filesystem_functions.convert_paths_to_names([tag_path])[0]

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

    for page_count, plant_dirs in enumerate(page_list):
        page_count += 1

        print(f"Creating page {page_count} of {n_pages}")
        
        # note: tagPage is not a string, it is a class.
        tagPage  = dashboard_html.OutputTagPage(f"{tag_path}plant_reports/index_{page_count}.html",
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

            tagPage += dashboard_html.plant_data_row(plant_name)
        tagPage += dashboard_html.plant_data_row_bottom()

        tagPage += "</table>"
        tagPage.save_page()



def make_comparison_pages(date, date_tags):
    import itertools
    tags = filesystem_functions.convert_paths_to_names(date_tags)
    tags.sort()
    tag_combinations = list(itertools.combinations(tags, 2))
    for combination in tag_combinations:
        combination_name = "-vs-".join(combination)

        # find plants that they have in common
        tag1_plants = filesystem_functions.get_plants_in_dir(os.path.join(date, combination[0]))
        tag2_plants = filesystem_functions.get_plants_in_dir(os.path.join(date, combination[1]))
        common_plants = list(set(tag1_plants + tag2_plants))

        n_pages = -(-len(common_plants)//N_PLANTS_PER_PAGE)  # Round up.  3.0->3, 3.1->4
        page_list = dashboard_html.divide_list_into_chunks(common_plants, n_pages)

        nav_html = f"{len(common_plants)} plants have been divided into {n_pages} page/s...<br>"
        for n in range(n_pages):
            nav_html += f"<li><a href='{combination_name}_{n+1}.html'>Page {n+1}</a>\n"

        #####################
        # Loop through pages
        #####################

        for page_count, plant_dirs in enumerate(page_list):
            page_count += 1

            print(f"Creating page {page_count} of {n_pages}")
            combinationPage  = dashboard_html.GenericPage(
                    f"{date}/{combination_name}_{page_count}.html",
                    name=combination_name,
            )
            
            # note: tagPage is not a string, it is a class.
            combinationPage += f"""
                <h2>{date}</h2>
                <h2>Page {page_count} of {n_pages}</h2>
                <hr>
                {nav_html}
                <hr>
                <table>
            """

            colors = ("#332211", "#112233")
            count = 0
            for plant_name in plant_dirs:
                count += 1
                color = colors[ count%2 ]
                combinationPage += dashboard_html.comparison_row(plant_name, combination, color)

            combinationPage += dashboard_html.combination_row_bottom(combination)
            combinationPage += f"""
                </table>
            """

            combinationPage.save_page()



if __name__ == "__main__":

    #dashboard_root = os.path.join(conf.args.date, conf.args.output_process_tag, "plant_reports")
    dashboard_html.__root_path__ = "."

    page_tree_dict  = {}


    # This needs to get paths from cyverse instead
    all_dates  = filesystem_functions.get_all_dates()
    all_tags   = filesystem_functions.get_all_tags()
    all_plants = filesystem_functions.get_all_plants()

    dates_dict  = create_dict_of_lists_from_list(all_dates)
    tags_dict   = create_dict_of_lists_from_list(all_tags)
    plants_dict = create_dict_of_lists_from_list(all_plants)

    
    metaPage = dashboard_html.GenericPage("index.html", name="Dashboard Home")
    for date in all_dates:
        print(f"{date}")
        metaPage += f"<h2>{date}</h2>\n"
        datePage = dashboard_html.GenericPage(os.path.join(date, f"index.html"))
        date_tags = filesystem_functions.get_tag_paths(date)
        date_tags.sort()
        for tag_path in date_tags:
            # dummyIndextagPage is wierd.  We only make it to get the path to pass
            # to metaPage.  The real tag pages get created in make_output_process_tag_pages
            # a hack because I coded myself into a corner, and dont care at the moment. [NPH]
            dummyTagPage = dashboard_html.GenericPage(
                                                  os.path.join(tag_path, f"plant_reports/index_1.html"),
                                                  name = tag_path,
            )
            metaPage.add_link(dummyTagPage)
            n_plants = len(filesystem_functions.get_plants_in_dir(tag_path))
            metaPage += f"({n_plants} plants processed)"
            make_output_process_tag_pages(tag_path)
            make_comparison_pages(date, date_tags)


        # note: GenericPage() is a class, not a string, it is a class, so
        #       don't be fooled by the += applied to it.
        datePage.save_page()

    metaPage.save_page()
    
#    ##################################################
#    #        Determine how many pages we need
#    #
#    # We don't want 200 plants on one page, so we
#    # break it up into n plants per page.
#    ##################################################
#
#    n_pages = -(-len(plant_dirs)//conf.args.n_plants_per_page)  # Round up.  3.0->3, 3.1->4
#    page_list = divide_list_into_chunks(plant_dirs, n_pages)
#
#    nav_html = f"{len(plant_dirs)} plants have been divided into {n_pages} page/s...<br>"
#    for n in range(n_pages):
#        nav_html += f"<li><a href='index_{n+1}.html'>Page {n+1}</a>\n"
#
#    #####################
#    # Loop through pages
#    #####################
#
#    for page_count, plant_dirs in enumerate(page_list):
#        page_count += 1
#
#        print(f"Creating page {page_count} of {n_pages}")
#        
#        # note: indexPage is not a string, it is a class.
#        indexPage  = dashboard_html.GenericPage(f"index_{page_count}.html")
#        indexPage += f"""
#            <h1>{conf.args.date} : Page {page_count} of {n_pages}</h1>
#            <hr>
#            {nav_html}
#            <hr>
#            <table>
#        """
#
#        ######################
#        # Loop through plants 
#        ######################
#
#        for count, plant_path in enumerate(plant_dirs):
#            count += 1
#            plant_name = os.path.basename(plant_path[0:-1])
#            print(f"({count}/{len(plant_dirs)}) : {plant_name}")
#
#            indexPage += dashboard_html.plant_data_row(plant_name)
#
#        indexPage += "</table>"
#        indexPage.save_page()
#
#    
##    genotype_html += dashboard_html.plant_data_row(plant_data, BASE_URL, conf)
##
##                genotype_html += f"""
##                    </tr>
##                    </table>
##                """
##
##            genotype_html += f"""
##                </table>
##                <footnote>*{data_category_strings['low_observations']} plants are defined as plants with less than {MIN_OBS} RGB observations.</footnote>
##                </body>
##                </html>
##            """
##            with open(genotype_index_file, "w") as genotype_html_fh:
##                genotype_html_fh.write(genotype_html);
##
##index_html += f"""
##    </table>
##	<hr>
##	<p><a href="../index.html">Dashboard Home</a></p>
##    <footnote>*{data_category_strings['low_observations']} plants are defined as plants with less than {MIN_OBS} RGB observations.</footnote>
##    </body>
##    </html>
##"""
##with open("index.html", "w") as index_html_file:
##    index_html_file.write(index_html);
##
##
##dashboard_html.create_random_plants_page(all_valid_plants, conf, filename="random.html")
##dashboard_html.create_random_plants_page(all_valid_plants, conf, filename="random2.html")
##dashboard_html.create_random_plants_page(all_valid_plants, conf, filename="random3.html")
##dashboard_html.create_random_plants_page(all_valid_plants, conf, filename="random4.html")
