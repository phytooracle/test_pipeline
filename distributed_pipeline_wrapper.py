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
import shutil

# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='PhytoOracle | Scalable, modular phenomic data processing pipelines',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-if',
                        '--input_filename',
                        help='Filename of input files',
                        metavar='str',
                        type=str,
                        default='combined_multiway_registered.ply')

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

    parser.add_argument('-hpc',
                        '--hpc',
                        help='Add flag if running on an HPC system.',
                        action='store_true')

    parser.add_argument('-d',
                        '--date',
                        help='Date to process',
                        metavar='str',
                        type=str,
                        required=True)

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

    parser.add_argument('-sm',
                        '--seg_model',
                        help='Model weights to use for segmentation container.',
                        metavar='seg_model',
                        type=str,
                        default='/iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/dgcnn_3d_model.pth')
    
    parser.add_argument('-dm',
                        '--det_model',
                        help='Model weights to use for detection container.',
                        metavar='det_model',
                        type=str,
                        default='/iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/detecto_heatmap_lettuce_detection_weights.pth')

    return parser.parse_args()


# --------------------------------------------------
def build_containers(dictionary):
    """Build module containers outlined in YAML file
    
    Input: 
        - dictionary: Dictionary generated from the YAML file
    
    Output: 
        - Singularity images (SIMG files)
    """

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
        cmd1 = f'cd {home} && wget {cctools_url}.tar.gz && tar -xzvf {cctools_file}.tar.gz && rm {cctools_file}.tar.gz'
        sp.call(cmd1, shell=True)
        # sp.call(f'rm {cctools_url}.tar.gz', shell=True)
        print(f'Download complete. CCTools version {cctools_version} is ready!')

    else:
        print('Required CCTools version already exists.')

    return '-'.join(['cctools', cctools_version, architecture, sys_os])


# --------------------------------------------------
def download_raw_data(irods_path):
    """Download raw dataset from CyVerse DataStore
    
        Input:
            - irods_path: CyVerse path to the raw data
            
        Output: 
            - Extracted files from the tarball.
    """

    args = get_args()
    file_name = os.path.basename(irods_path)
    dir_name = file_name.split('.')[0]

    if not os.path.isdir(dir_name):
        cmd1 = f'iget -fKPVT {irods_path}'
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
def download_level_1_data(irods_path):
    args = get_args()
    file_name = os.path.basename(irods_path)
    direc = irods_path.split('/')[-1]

    cmd1 = f'iget -rfPVT {irods_path}'
    # cmd1 = f'iget -fKPVT {irods_path}'
    cwd = os.getcwd()

    if '.gz' in file_name: 
        cmd2 = 'ls *.tar.gz | xargs -I {} tar -xzvf {}'
        cmd3 = f'rm *.tar.gz'

    else: 
        cmd2 = 'ls *.tar | xargs -I {} tar -xvf {}'
        cmd3 = f'rm *.tar'
    
    if args.hpc: 
        print('>>>>>>Using data transfer node.')
        sp.call(f"ssh filexfer 'cd {cwd}' '&& {cmd1}' '&& cd {os.path.join(cwd, direc)}' '&& {cmd2}' '&& {cmd3}' '&& exit'", shell=True)
    else: 
        sp.call(cmd1, shell=True)
        sp.call(f"cd {os.path.join(cwd, direc)}")
        sp.call(cmd2, shell=True)
        sp.call(cmd3, shell=True)


# --------------------------------------------------
def get_transformation_file(irods_path, cwd):

    cmd1 = f'iget -KPVT {os.path.join(irods_path, "preprocessing", "transfromation.json")}'
    sp.call(cmd1, shell=True)
    
    if not os.path.isfile(os.path.join(cwd, 'transfromation.json')):
        cmd2 = f'iget -KPVT {os.path.join(irods_path, "alignment", "transfromation.json")}'
        sp.call(cmd2, shell=True)


# --------------------------------------------------
def get_bundle_dir(irods_path):

    cmd1 = f'iget -rKPVT {os.path.join(irods_path, "logs", "bundle")}'

    sp.call(cmd1, shell=True)


# --------------------------------------------------
def get_bundle_json(irods_path):

    cmd1 = f'iget -KPVT {os.path.join(irods_path, "logs", "bundle_list.json")}'

    sp.call(cmd1, shell=True)


# --------------------------------------------------
def get_model_files(seg_model_path, det_model_path):
    """Download model weights from CyVerse DataStore
    
    Input:
        - seg_model_path: CyVerse path to the segmentation model (.pth file)
        - det_model_path: CyVerse path to the object detection model (.pth file)
        
    Output: 
        - Downloaded model weight files.
    """
    
    if not os.path.isfile(os.path.basename(seg_model_path)):
        cmd1 = f'iget -fKPVT {seg_model_path}'
        sp.call(cmd1, shell=True)

    if not os.path.isfile(os.path.basename(det_model_path)):
        cmd1 = f'iget -fKPVT {det_model_path}'
        sp.call(cmd1, shell=True)

    return os.path.basename(seg_model_path), os.path.basename(det_model_path) 


# --------------------------------------------------
def launch_workers(account, partition, job_name, nodes, number_tasks, number_tasks_per_node, time, mem_per_cpu, manager_name, min_worker, max_worker, cores, worker_timeout, outfile='worker.sh'):
    '''
    Launches workers on a SLURM workload management system.

    Input:
        - account: Account to charge compute resources
        - partition: Either standard or windfall hours
        - job_name: Name for the job 
        - nodes: Number of nodes to use per Workqueue factory
        - number_tasks: Number of tasks per node (usually 1)
        - number_tasks_per_node: Number of tasks per node (usually 1)
        - time: Time alloted for job to run 
        - mem_per_cpu: Memory per CPU (depends on HPC system, units in GB)
        - manager_name: Name of workflow manager
        - min_worker: Minimum number of workers per Workqueue factory
        - max_worker: Maximum number of workers per Workqueue factory
        - cores: Number of cores per worker
        - worker_timeout: Time to wait for worker to receive a task before timing out (units in seconds)
        - outfile: Output filename for SLURM submission script
    
    Output: 
        - Running workers on an HPC system
    '''

    with open(outfile, 'w') as fh:
        fh.writelines("#!/bin/bash -l\n")
        fh.writelines(f"#SBATCH --account={account}\n")
        fh.writelines(f"#SBATCH --partition={partition}\n")
        fh.writelines(f"#SBATCH --job-name={job_name}\n")
        fh.writelines(f"#SBATCH --nodes={nodes}\n")
        fh.writelines(f"#SBATCH --ntasks={number_tasks}\n")
        fh.writelines(f"#SBATCH --ntasks-per-node={number_tasks_per_node}\n")
        fh.writelines(f"#SBATCH --time={time}\n")
        fh.writelines("export CCTOOLS_HOME=${HOME}/cctools-7.1.12-x86_64-centos7\n")
        fh.writelines("export PATH=${CCTOOLS_HOME}/bin:$PATH\n")
        fh.writelines(f"work_queue_factory -T slurm -B '--account={account} --partition={partition} --job-name={job_name} --time={time} --mem-per-cpu={mem_per_cpu}GB' -M {manager_name} -w {min_worker} -W {max_worker} --workers-per-cycle 0 --cores={cores} -t {worker_timeout}\n")

    os.system(f"sbatch {outfile}")


# --------------------------------------------------
def kill_workers(job_name):
    '''
    Kills workers once workflow has terminated.

    Input:
        - job_name: Name of the job 
    
    Output: 
        - Kills workers on an HPC system
    '''

    os.system(f"scancel --name {job_name}")

    
# --------------------------------------------------
def generate_makeflow_json(files_list, command, container, inputs, outputs, n_rules=1, json_out_path='wf_file.json'):
    '''
    Generate Makeflow JSON file to distribute tasks. 

    Input: 
        - files_list: Either files or subdirectory list
        - n_rules: Number of rules per JSON file
        - json_out_path: Path to the resulting JSON file

    Output:
        - json_out_path: Path to the resulting JSON file
    '''
    existing_file_list = []

    for file in files_list:
        if os.path.isfile(file):
            existing_file_list.append(file)

    if inputs:

        jx_dict = {
            "rules": [
                        {
                            "command" : command.replace('${PLANT_PATH}', os.path.dirname(file)).replace('${SEG_MODEL_PATH}', seg_model_name).replace('${PLANT_NAME}', os.path.basename(os.path.dirname(file))).replace('${DET_MODEL_PATH}', det_model_name),
                            "outputs" : [out.replace('$PLANT_NAME', os.path.basename(os.path.dirname(file))) for out in outputs],
                            "inputs"  : [file, 
                                        container, 
                                        seg_model_name, 
                                        det_model_name] + [input.replace('$PLANT_NAME', os.path.basename(os.path.dirname(file))) for input in inputs]

                        } for file in  existing_file_list
                    ]
        } 

    else: 
        
        jx_dict = {
            "rules": [
                        {
                            "command" : command.replace('${PLANT_PATH}', os.path.dirname(file)).replace('${SEG_MODEL_PATH}', seg_model_name).replace('${PLANT_NAME}', os.path.basename(os.path.dirname(file))).replace('${DET_MODEL_PATH}', det_model_name),
                            "outputs" : [out.replace('$PLANT_NAME', os.path.basename(os.path.dirname(file))) for out in outputs],
                            "inputs"  : [file, 
                                        container, 
                                        seg_model_name, 
                                        det_model_name]

                        } for file in  existing_file_list
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

    Output: 
        - Running workflow
    '''

    home = os.path.expanduser('~')
    cctools = os.path.join(home, cctools_path, 'bin', 'makeflow')
    cctools = os.path.join(home, cctools)

    if out_log==True:
        arguments = f'-T {batch_type} --skip-file-check --json {json_out_path} -a -N {manager_name} -M {manager_name} -r {retries} -p {port} -dall -o dall.log --disable-cache $@'
        cmd1 = ' '.join([cctools, arguments])

    else:
        arguments = f'-T {batch_type} --skip-file-check --json {json_out_path} -a -N {manager_name} -M {manager_name} -r {retries} -p {port} --disable-cache $@'
        cmd1 = ' '.join([cctools, arguments])

    sp.call(cmd1, shell=True)


# --------------------------------------------------
def clean_directory():
    '''
    Cleans directory from distributed pipeline output logs and files lists.

    Input:
        - NA
    
    Output: 
        - Clean working directory
    '''

    if os.path.isfile("dall.log"):
        os.remove("dall.log")
    
    if os.path.isfile("file.txt"):
        os.remove("file.txt")

    if os.path.isfile("wf_file.json"):
        os.remove("wf_file.json")

    if os.path.isfile("wf_file.json.makeflowlog"):
        os.remove("wf_file.json.makeflowlog")

    if os.path.isfile("wf_file.json.wqlog"):
        os.remove("wf_file.json.wqlog")

    if os.path.isfile("wf_file.json.wqlog.tr"):
        os.remove("wf_file.json.wqlog.tr")

    # if os.path.isdir('alignment'):
    #     shutil.rmtree('alignment')
    
    # if os.path.isfile('transfromation.json'):
    #     os.remove('transfromation.json')
    
    # if os.path.isdir('bundle'):
    #     shutil.rmtree('bundle')

    # if os.path.isfile('bundle_list.json'):
    #     os.remove('bundle_list.json')
    

# --------------------------------------------------
def main():
    """Run distributed data processing here"""

    args = get_args()
    cctools_path = download_cctools()
    clean_directory()
    
    with open(args.yaml, 'r') as stream:
        try:
            global dictionary
            dictionary = yaml.safe_load(stream)
            build_containers(dictionary)

        except yaml.YAMLError as exc:
            print(exc)
        
        kill_workers(dictionary['workload_manager']['job_name'])

        launch_workers(account=dictionary['workload_manager']['account'], 
                partition=dictionary['workload_manager']['partition'], 
                job_name=dictionary['workload_manager']['job_name'], 
                nodes=dictionary['workload_manager']['nodes'], 
                number_tasks=dictionary['workload_manager']['number_tasks'], 
                number_tasks_per_node=dictionary['workload_manager']['numer_tasks_per_node'], 
                time=dictionary['workload_manager']['time_minutes'], 

                mem_per_cpu=dictionary['workload_manager']['mem_per_cpu'], 
                manager_name=args.manager_name, 
                min_worker=dictionary['workload_manager']['min_worker'], 
                max_worker=dictionary['workload_manager']['max_worker'], 
                cores=dictionary['workload_manager']['cores_per_worker'], 
                worker_timeout=dictionary['workload_manager']['worker_timeout_seconds'])

        # cyverse_path = os.path.join(dictionary['paths']['cyverse']['input']['basename'], 
        #                                 args.date,
        #                                 dictionary['paths']['cyverse']['input']['subdir'], 
        #                                 ''.join([str(args.date), str(dictionary['paths']['cyverse']['input']['suffix'])]))
                                        
        # dir_name = download_raw_data(cyverse_path)
        global seg_model_name, det_model_name
        seg_model_name, det_model_name = get_model_files(args.seg_model, args.det_model)

        for k, v in dictionary['modules'].items():
            level_1 = dictionary['paths']['cyverse']['input']['basename']

            if dictionary['tags']['sensor']=='scanner3DTop':
                cwd = os.getcwd()
                irods_data_path = os.path.join(level_1, args.date, 'alignment')
                if not os.path.isdir('alignment'):
                    download_level_1_data(irods_data_path)
                if not os.path.isfile('transfromation.json'):
                    get_transformation_file(os.path.join(level_1, args.date), cwd)
                if not os.path.isdir('bundle'):
                    get_bundle_dir(os.path.join(level_1, args.date))
                if not os.path.isfile('bundle_list.json'):
                    get_bundle_json(os.path.join(level_1, args.date))

            files_list = get_file_list(dir_name, args.input_filename, level=v['distribution_level'])
            write_file_list(files_list)            
            # json_out_path = generate_makeflow_json(files_list=files_list, command=v['command'], container=v['container']['simg_name'], inputs=v['inputs'], outputs=v['outputs'])
            # run_jx2json(json_out_path, cctools_path, batch_type=args.batch_type, manager_name=args.manager_name, retries=args.retries, port=args.port, out_log=True)
            # clean_directory()
    
    kill_workers(dictionary['workload_manager']['job_name'])


# --------------------------------------------------
if __name__ == '__main__':
    main()
