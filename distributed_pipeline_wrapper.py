#!/usr/bin/env python3
"""
Author : Emmanuel Gonzalez
Date   : 2021-12-17
Purpose: PhytoOracle | Scalable, modular phenomic data processing pipelines
"""

import argparse
import os
import sys
from typing_extensions import final
import json
import subprocess as sp
import yaml


# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='PhytoOracle | Scalable, modular phenomic data processing pipelines',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('positional',
                        metavar='str',
                        help='Input directory for processing')

    parser.add_argument('-if',
                        '--input_filename',
                        help='Filename of input files',
                        metavar='str',
                        type=str,
                        required=True)

    parser.add_argument('-dl',
                        '--distribution_level',
                        help='Level of distribution, either "plant" or "directory"',
                        metavar='str',
                        type=str,
                        choices=['plant', 'directory'], 
                        default='plant')

    parser.add_argument('-bt',
                        '--batch_type',
                        help='Type of batch distribution',
                        metavar='str',
                        type=str,
                        choices=['local', 'dryrun', 'condor', 'sge', 'pbs', 'torque', 'blue_waters', 'slurm', 'moab', 'cluster', 'wq', 'amazon', 'mesos'], 
                        default='wq')

    parser.add_argument('-mn',
                        '--manager_name',
                        help='Name of workflow manager',
                        metavar='str',
                        type=str,
                        default='phytooracle_manager')

    parser.add_argument('-r',
                        '--retries',
                        help='Number of retries for a failed job',
                        metavar='int',
                        type=int,
                        default=2)

    parser.add_argument('-p',
                        '--port',
                        help='Port number on which to run the pipeline',
                        metavar='int',
                        type=int,
                        default=0)

    parser.add_argument('-y',
                        '--yaml',
                        help='YAML file specifying processing tasks/arguments',
                        metavar='str',
                        type=str,
                        required=True)

    return parser.parse_args()



# --------------------------------------------------
def build_containers(dictionary):
    """Build module containers outlined in YAML file"""

    for k, v in dictionary['modules'].items():
        container = v['container']
        if not os.path.isfile(container["simg_name"]):
            print(f'Building {container["simg_name"]}.')
            sp.call(f'singularity build {container["simg_name"]} {container["dockerhub_path"]}', shell=True)


# --------------------------------------------------
def download_cctools(cctools_version = '7.1.12', architecture = 'x86_64', sys_os = 'centos7'):
    '''
    Download CCTools (https://cctools.readthedocs.io/en/latest/) and extracts the contents of the file. 

    Input:
        - cctools_version: CCTools version to install 
        - architecture:  Bit software to download
        - sys_os: Operating system on current machine
    Output: 
        - path to cctools on working machine
    '''

    cwd = os.getcwd()
    home = os.path.expanduser('~')
    
    cctools_file = '-'.join(['cctools', cctools_version, architecture, sys_os])
    
    if not os.path.isdir(os.path.join(home, cctools_file)):
        print(f'Downloading {cctools_file}.')
        cctools_url = ''.join(['http://ccl.cse.nd.edu/software/files/', cctools_file])
        cmd1 = f'cd {home} && wget {cctools_url}.tar.gz && tar -xzvf {cctools_file}.tar.gz'
        sp.call(cmd1, shell=True)
        print(os.getcwd())
        #sp.call(f'cd {cwd}')
        print(f'Download complete. CCTools version {cctools_version} is ready!')

    else:
        print('Required CCTools version already exists.')

    return '-'.join(['cctools', cctools_version, architecture, sys_os])

# --------------------------------------------------
def get_file_list(directory, match_string, level):
    '''
    Walks through a given directory and grabs all files with the given search string.

    Input: 
        - directory: Local directory to search 
        - match_string: Substring to search and add only elements with items containing 
                        this string being added to the file list. 

    Output: 
        - subdir_list: List containing all subdirectories within the raw data.
        - files_list: List containing all files within each subdirectory within the raw data.
    '''

    files_list = []
    subdir_list = []

    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            if match_string in name:
                files_list.append(os.path.join(root, name))
            
        for name in dirs:
            subdir_list.append(os.path.join(root, name))

    if level=='plant':
        files_list = files_list
    elif level=='directory':
        files_list = subdir_list

    return files_list


# --------------------------------------------------
def write_file_list(input_list, out_path='file.txt'):
    '''
    Write either files/subdir list to file.

    Input: 
        - input_list: List containing files
        - out_path: Filename of the output
    Output: 
        - TXT file.  
    '''

    textfile = open(out_path, "w")
    for element in input_list:
        textfile.write(element + "\n")
    textfile.close()


# --------------------------------------------------
def generate_makeflow_json(files_list, command, yaml, n_rules=1, json_out_path='wf_file.json'):
    '''
    Generate Makeflow JSON file to distribute tasks. 

    Input: 
        - files_list: Either files or subdirectory list
        - n_rules: Number of rules per JSON file
        - json_out_path: Path to the resulting JSON file

    Output:
        - json_out_path: Path to the resulting JSON file
    '''

    jx_dict = {
        "rules": [
                    {
                        "command" : command.replace('${PLANT_PATH}', os.path.dirname(file)),
                        # "outputs" : [ file ],
                        "inputs"  : [ file ]

                    } for file in  files_list
                ]
    } 
    
    with open(json_out_path, 'w') as convert_file:
        convert_file.write(json.dumps(jx_dict))

    return json_out_path


# --------------------------------------------------
def run_jx2json(json_out_path, cctools_path, batch_type, manager_name, retries=3, port=0, out_log=True):
    '''
    Create a JSON file for Makeflow distributed computing framework. 

    Input: 
        - json_out_path: Path to the JSON file containing inputs
        - cctools_path: Path to local installation of CCTools
    '''

    home = os.path.expanduser('~')
    cctools = os.path.join(home, cctools_path, 'bin', 'makeflow')
    cctools = os.path.join(home, cctools)

    if out_log==True:
        arguments = f'-T {batch_type} --json {json_out_path} -N {manager_name} -r {retries} -p {port} -dall -o dall.log $@'
        cmd1 = ' '.join([cctools, arguments])

    else:
        arguments = f'-T {batch_type} --json {json_out_path} -N {manager_name} -r {retries} -p {port} $@'
        cmd1 = ' '.join([cctools, arguments])

    sp.call(cmd1, shell=True)


# --------------------------------------------------
def main():
    """Run processing here"""

    args = get_args()
    cctools_path = download_cctools()
    
    with open(args.yaml, 'r') as stream:
        try:
            global dictionary
            dictionary = yaml.safe_load(stream)
            build_containers(dictionary)

        except yaml.YAMLError as exc:
            print(exc)

        for k, v in dictionary['modules'].items():
            distribution_level = v['distribution_level']
            files_list = get_file_list(args.positional, args.input_filename, level=distribution_level)
            write_file_list(files_list)
            json_out_path = generate_makeflow_json(files_list, v['command'], yaml=args.yaml)
            run_jx2json(json_out_path, cctools_path, batch_type=args.batch_type, manager_name=args.manager_name, retries=args.retries, port=args.port, out_log=True)


# --------------------------------------------------
if __name__ == '__main__':
    main()
