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
import shutil
import tarfile


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

    parser.add_argument('-d',
                        '--date',
                        help='Scan date to process. (psst, try: 2020-01-22, 2020-02-16 or 2020-03-02)',
                        metavar='scan_date',
                        type=str,
                        required=True)

    parser.add_argument('-y',
                        '--yaml',
                        help='YAML file to use for processing.',
                        metavar='yaml',
                        type=str,
                        required=True)
    
    parser.add_argument('-np',
                        '--n_plants',
                        help='Number of plants to process (useful for dev) NOT IMPLEMENTED',
                        type=int,
                        required=False)
    
    parser.add_argument('-m',
                        '--model',
                        help='Model weights to use for containers',
                        metavar='model',
                        type=str,
                        default='/iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/dgcnn_3d_model.pth')

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
    """Build module containers outlined in YAML file"""

    for k, v in dictionary['modules'].items():
        container = v['container']
        if not os.path.isfile(container["simg_name"]):
            print(f'Building {container["simg_name"]}.')
            sp.call(f'singularity build {container["simg_name"]} {container["dockerhub_path"]}', shell=True)


# --------------------------------------------------
def get_model_files(model_path):
    """Download model weights from CyVerse DataStore"""
    
    if not os.path.isfile(os.path.basename(model_path)):
        cmd1 = f'iget -fKPVT {model_path}'
        sp.call(cmd1, shell=True)
    return os.path.basename(model_path)


# --------------------------------------------------
def run_plant_volume(scan_date, input_dir):
    """Run plant volume and TDA feature extraction on each individual plant point cloud"""

    if not os.path.isdir('3d_entropy_merge.simg'):
        print('Building 3d_entropy_merge.simg.')
        sp.call('singularity build 3d_entropy_merge.simg docker://phytooracle/3d_entropy_merge:latest', shell=True)
    
    if not os.path.isfile(os.path.join(scan_date, f'{scan_date}_tda.csv')):
        sp.call(f'singularity run 3d_entropy_merge.simg -d {scan_date} -ie {input_dir}', shell=True)


# --------------------------------------------------
def tar_outputs(scan_date, dictionary):
    
    cwd = os.getcwd()
    outdir = '_'.join([dictionary['tags']['pipeline'], dictionary['tags']['description']])

    for k, v in dictionary['paths']['pipeline_outpath'].items():

        if not os.path.isdir(os.path.join(cwd, scan_date, outdir)):
            os.makedirs(os.path.join(cwd, scan_date, outdir))

        file_path = os.path.join(cwd, scan_date, outdir, f'{scan_date}_{v}_plants.tar') 
        print(f'Creating {file_path}.')
        if not os.path.isfile(file_path):
            with tarfile.open(file_path, 'w') as tar:
                tar.add(v, recursive=True)
        shutil.move(v, os.path.join(scan_date, outdir))


# --------------------------------------------------
def process_plant(plant):
    """Process each input datum through the modules outlined in YAML file"""

    plant_name = os.path.basename(plant)

    for k, v in dictionary['modules'].items():
        command = v['command'].replace('${PLANT_PATH}', plant).replace('${MODEL_PATH}', model_name).replace('${PLANT_NAME}', plant_name)
        print(command)
        sp.call(command, shell=True)


# --------------------------------------------------
def main():
    """Run processing here"""

    args = get_args()


    with open(args.yaml, 'r') as stream:
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
        model_name = get_model_files(args.model)

        # Process each plant by running commands outlined in YAML file.
        plant_list = glob.glob(os.path.join(dir_name, '*'))

        with multiprocessing.Pool(multiprocessing.cpu_count()//4) as p:
            p.map(process_plant, plant_list)

    tar_outputs(args.date, dictionary)

    # input_dir = ''.join([args.date, '_test_set'])
    # run_plant_volume(args.date, input_dir)

    # if os.path.isdir(args.date):
    #     shutil.move(dir_name, args.date)


# --------------------------------------------------
if __name__ == '__main__':
    main()
