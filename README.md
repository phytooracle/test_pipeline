# Test Pipeline
This is a test pipeline for scanner3DTop (point cloud) data. The pipeline can be run on local or HPC resources, so long as Singularity is installed. 

## YAML file 
The YAML file can be edited to run any container. Below is a list of important keys to ensure the pipeline runs correctly:
### Tags 
You can specify tags which will are used to identify distinct test outputs. 
* [tags]
  * [pipeline] | Name of test
  * [description] | Version of test
  * [notes] | General notes of test
### Modules 
You can specify any number of modules. Each module runs a single container and generates corresponding outputs. 
* [modules]
  * [container][simg_name] | Singularity image name
  * [container][dockerhub_path] | Dockerhub path to the container
  * [command] | Command used to run the container 

### Paths 
* [paths]
  * [pipeline_outpath]
    * [pointclouds] | Output path to point cloud data 
    * [dashboard] | Output path to visualizations (GIFs, etc)
  * [cyverse]
    * [input]
      * [basename] | Root directory of raw data
      * [subdir] | Subdirectory of raw data
      * [suffix] | Suffix tag of raw data
    * [output]
      * [base] | Root directory to upload data
      * [subdir] | Subdirectory in which to upload data