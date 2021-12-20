#!/bin/bash 

output_tag=${1%/}

browser="firefox"
dashboard_script_path="~/test_pipeline/dashboard/generate_dashboard.py"
#output_tag=${SCAN_DATE}
cyverse_root="/iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_1/scanner3DTop/test_outputs"
dates=("2020-01-22"  "2020-02-16"  "2020-03-02")

for date in ${dates[*]}
    do
        iget -N 0 -PVTK ${cyverse_root}/${date}/${output_tag}/${date}_plant_reports_plants.tar
    done

for date in ${dates[*]}
    do 
        mkdir -p ${date}/${output_tag}
        mv ${date}*tar ${date}/${output_tag}
        cd ${date}/${output_tag}
        tar -xvf ${date}*tar
        iget -N 0 -PVTK ${cyverse_root}/${date}/${output_tag}/config.yaml
        cd ../..
    done

python ${dashboard_script_path}

eval "${browser} index.html"
