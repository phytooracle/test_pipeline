#!/usr/bin/env python3
"""
Author : Emmanuel Gonzalez
Date   : 2021-12-08
Purpose: Test pipeline automation
"""

import argparse
import os
import sys 
import subprocess as sp
import yaml
import glob
import multiprocessing


# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Test pipeline automation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-hpc',
                        '--hpc',
                        help='Add flag if running on an HPC system.',
                        action='store_true')

    parser.add_argument('-date',
                        '--date',
                        help='Scan date to process.',
                        metavar='scan_date',
                        type=str,
                        required=False)

    return parser.parse_args()


# --------------------------------------------------
def download_raw_data(irods_path):
    """Download raw dataset from CyVerse DataStore"""

    args = get_args()
    file_name = os.path.basename(irods_path)
    dir_name = file_name.split('.')[0]

    if not os.path.isdir(dir_name):
        cmd1 = f'iget -fKPVT {irods_path}'
        print(cmd1)
        cwd = os.getcwd()

        if '.gz' in file_name: 
            cmd2 = f'tar -xzvf {file_name}'
            cmd3 = f'rm {file_name}'

        else: 
            cmd2 = f'tar -xvf {file_name}'
            cmd3 = f'rm {file_name}'
        
        if args.hpc: 
            print('>>>>>>Using data transfer node.')
            sp.call(f"ssh filexfer 'cd {cwd}' '&& {cmd1}' '&& {cmd2}' '&& {cmd3}' '&& exit'", shell=True)
            
        else: 
            sp.call(cmd1, shell=True)
            sp.call(cmd2, shell=True)
            sp.call(cmd3, shell=True)

    return dir_name


# --------------------------------------------------
def build_containers(dictionary):
    """Get command-line arguments"""

    for k, v in dictionary['modules'].items():
        container = v['container']
        if not os.path.isfile(container["simg_name"]):
            print(f'Building {container["simg_name"]}.')
            sp.call(f'singularity build {container["simg_name"]} {container["dockerhub_path"]}', shell=True)


# --------------------------------------------------
def get_model_files(model_path):
    
    if not os.path.isfile(os.path.basename(model_path)):
        cmd1 = f'iget -fKPVT {model_path}'
        sp.call(cmd1, shell=True)
    return os.path.basename(model_path)


# --------------------------------------------------
def run_plant_volume(scan_date, input_dir):

    if not os.path.isdir('3d_entropy_merge.simg'):
        print('Building 3d_entropy_merge.simg.')
        sp.call('singularity build 3d_entropy_merge.simg docker://phytooracle/3d_entropy_merge:latest')
        
    sp.call(f'singularity run 3d_entropy_merge.simg -d {scan_date} -ie {input_dir}', shell=True)


def process_plant(plant):

    plant_name = os.path.basename(plant)

    for k, v in dictionary['modules'].items():
        command = v['command'].replace('${PLANT_PATH}', plant).replace('${MODEL_PATH}', model_name).replace('${PLANT_NAME}', plant_name)
        print(command)
        sp.call(command, shell=True)
# --------------------------------------------------
def main():
    """Make a jazz noise here"""

    args = get_args()

    with open("./config.yaml", 'r') as stream:
        try:
            global dictionary
            dictionary = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

        cyverse_path = os.path.join(dictionary['paths']['cyverse']['input']['basename'], 
                                    args.date,
                                    dictionary['paths']['cyverse']['input']['subdir'], 
                                    ''.join([str(args.date), str(dictionary['paths']['cyverse']['input']['suffix'])]))

        # Build necessary containers outlined in YAML file.
        build_containers(dictionary)
        
        # Download raw test dataset and GGCNN model weights.
        dir_name = download_raw_data(cyverse_path)
        global model_name
        model_name = get_model_files('/iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/dgcnn_3d_model.pth')

        # Iterate through each plant and run commands outlined in YAML file.
        plant_list = glob.glob(os.path.join(dir_name, '*'))

        with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
            p.map(process_plant, plant_list)


        input_dir = ''.join([args.date, '_test_set'])
        run_plant_volume(args.date, input_dir)



# --------------------------------------------------
if __name__ == '__main__':
    main()
