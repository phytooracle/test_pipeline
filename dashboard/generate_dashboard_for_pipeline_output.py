import sys, glob, os, pdb
from itertools import groupby
from operator import itemgetter
import pandas as pd
import numpy as np
import subprocess
from config import Config
import re
from operator import itemgetter
import dashboard_html

"""
For Nathan using iPython locally...
%run ~/work/repos/test_pipeline/dashboard/generate_dashboard_for_pipeline_output.py -d 2020-03-02 -t polynomial_cropping_dev
"""

def divide_list_into_chunks(a, n):
    """
    From https://stackoverflow.com/questions/2130016/
    a: list to be split
    n: number of chunks
    """
    k, m = divmod(len(a), n)
    return list((a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n)))

if __name__ == "__main__":

    conf = Config() # This contains command line arguments, and phytooracle_data classes.
    dashboard_html.__root_path__ = os.path.join(conf.args.date, conf.args.output_process_tag, "plant_reports")

    ##########################################
    # Get a list of 3D plants for this date.
    ##########################################

    plant_dirs = glob.glob(os.path.join(conf.args.date, conf.args.output_process_tag, "plant_reports", "*/"))

    ##################################################
    #        Determine how many pages we need
    #
    # We don't want 200 plants on one page, so we
    # break it up into n plants per page.
    ##################################################

    n_pages = -(-len(plant_dirs)//conf.args.n_plants_per_page)  # Round up.  3.0->3, 3.1->4
    page_list = divide_list_into_chunks(plant_dirs, n_pages)

    nav_html = f"{len(plant_dirs)} plants have been divided into {n_pages} page/s...<br>"
    for n in range(n_pages):
        nav_html += f"<li><a href='index_{n+1}.html'>Page {n+1}</a>\n"

    #####################
    # Loop through pages
    #####################

    for page_count, plant_dirs in enumerate(page_list):
        page_count += 1

        print(f"Creating page {page_count} of {n_pages}")
        
        # note: indexPage is not a string, it is a class.
        indexPage  = dashboard_html.GenericPage(f"index_{page_count}.html")
        indexPage += f"""
            <h1>{conf.args.date} : Page {page_count} of {n_pages}</h1>
            <hr>
            {nav_html}
            <hr>
            <table>
        """

        ######################
        # Loop through plants 
        ######################

        for count, plant_path in enumerate(plant_dirs):
            count += 1
            plant_name = os.path.basename(plant_path[0:-1])
            print(f"({count}/{len(plant_dirs)}) : {plant_name}")

            indexPage += dashboard_html.plant_data_row(plant_name)

        indexPage += "</table>"
        indexPage.save_page()

    
#    genotype_html += dashboard_html.plant_data_row(plant_data, BASE_URL, conf)
#
#                genotype_html += f"""
#                    </tr>
#                    </table>
#                """
#
#            genotype_html += f"""
#                </table>
#                <footnote>*{data_category_strings['low_observations']} plants are defined as plants with less than {MIN_OBS} RGB observations.</footnote>
#                </body>
#                </html>
#            """
#            with open(genotype_index_file, "w") as genotype_html_fh:
#                genotype_html_fh.write(genotype_html);
#
#index_html += f"""
#    </table>
#	<hr>
#	<p><a href="../index.html">Dashboard Home</a></p>
#    <footnote>*{data_category_strings['low_observations']} plants are defined as plants with less than {MIN_OBS} RGB observations.</footnote>
#    </body>
#    </html>
#"""
#with open("index.html", "w") as index_html_file:
#    index_html_file.write(index_html);
#
#
#dashboard_html.create_random_plants_page(all_valid_plants, conf, filename="random.html")
#dashboard_html.create_random_plants_page(all_valid_plants, conf, filename="random2.html")
#dashboard_html.create_random_plants_page(all_valid_plants, conf, filename="random3.html")
#dashboard_html.create_random_plants_page(all_valid_plants, conf, filename="random4.html")
