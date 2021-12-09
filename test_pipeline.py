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
def build_containers(yaml_dict):
    
    simg_name = yaml_dict['module_1']['container']['simg_name']
    dockerhub_path = yaml_dict['module_1']['container']['dockerhub_path']

    if not os.path.isfile(simg_name):
        print(f'Building {simg_name}.')
        sp.call(f'singularity build {simg_name} {dockerhub_path}', shell=True)


# --------------------------------------------------
def download_raw_data(irods_path):
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
def main():
    """Make a jazz noise here"""

    args = get_args()

    with open("./config.yaml", 'r') as stream:
        try:
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
        model_name = get_model_files('/iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/dgcnn_3d_model.pth')

        # Iterate through each plant and run commands outlined in YAML file.
        for plant in glob.glob(os.path.join(dir_name, '*'))[:1]:
            plant_name = os.path.basename(plant)
    
            for k, v in dictionary['modules'].items():
                command = v['command'].replace('${PLANT_PATH}', plant).replace('${MODEL_PATH}', model_name).replace('${PLANT_NAME}', plant_name)
                print(command)
                sp.call(command, shell=True)


# --------------------------------------------------
if __name__ == '__main__':
    main()
