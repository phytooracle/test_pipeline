import sys
import argparse

class Config(object):

    MIN_OBS = 5
    BASE_URL = "https://data.cyverse.org/dav-anon/iplant/projects/phytooracle/season_10_lettuce_yr_2020/level_1/scanner3DTop/dashboard"

    data_category_strings = {
            'good_data' : "Valid useable data",
            'double_lettuce' : "Double lettuces",
            'low_observations' : "Low frequency plants*",
    }

    def __init__(self, season=10):
        self.handle_command_line_aruments()
    


    def handle_command_line_aruments(self):
        parser = argparse.ArgumentParser(
            description='GUI for 3d manual goecorrection.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument('-d',
                            '--date',
                            help='The 3D scan date for processing',
                            required=True,
        )

        parser.add_argument('-np',
                            '--n_plants_per_page',
                            help='How many plants to display per page.',
                            default=50,
                            type=int,
                            required=False,
        )

        parser.add_argument('-t',
                            '--output_process_tag',
                            help='Which pipeline output to use (i.e. polynomial_cropping_dev)',
                            required=True,
        )

        self.args = parser.parse_args()
