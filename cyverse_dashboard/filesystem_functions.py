import sys, os, glob, pdb
import subprocess

date_dir_wildcard = "????-??-??/"
tag_dir_wildcard  = "*_*/"
plant_dir_wildcard = "*_[0-9]*/"

def get_plant_paths(path="."):
    return glob.glob(os.path.join(path, "plant_reports", plant_dir_wildcard))

def convert_paths_to_names(list_of_paths):
    return list(set([os.path.basename(x[:-1]) for x in list_of_paths]))


# to cyverse dates

def find_available_date_paths(de_path):
    # de_path = "/iplant/home/travis_simmons/season_11_clustering/"

    command = ['ils', de_path ]

    lines = str(subprocess.check_output(command))
    no_new_line = lines.replace('\\n', '')

    separated = no_new_line.split('  ')[1:]
    
    # print(separated)
    return separated

# --------------------replaces------------------------------
def get_all_dates_cyverse(de_path):
    date_paths = find_available_date_paths(de_path)
    date_paths = [os.path.basename(i.split(' ')[-1]) for i in date_paths if i[-1].isnumeric()]
    # print(date_paths)
    return date_paths
    
def get_all_dates(root_path="."):
    date_paths = glob.glob(os.path.join(root_path, date_dir_wildcard))
    return convert_paths_to_names(date_paths)
# -----------------replaces-----------------------------------


def get_tag_paths(path="."):
    return glob.glob(os.path.join(path, tag))

def get_all_tags(root_path="."):
    tag_paths = get_tag_paths(os.path.join(root_path, date_dir_wildcard))
    return convert_paths_to_names(tag_paths)


# make cyverse

def find_plant_paths_cyverse(date_paths, tag):
    plant_paths = []
    for i in date_paths:
        
        try:
            i = i.split(' ')[-1]
            command = ['ils', i + f'/{tag}/plant_reports' ]

            lines = str(subprocess.check_output(command))
            # print(lines)
            no_new_line = lines.replace('\\n', '')

            separated = no_new_line.split('  ')[1:]
            plant_paths += separated

            
            print(i, ' contains ' , len(separated), ' plants')

        except:
            print('No plants found in:' ,i )

    print(len(plant_paths), 'plants found.')
            
    return plant_paths


# ---------------replace---------------------------
def find_all_plant_names_cyverse(de_path, tag):
    date_paths = find_available_date_paths(de_path)
    plant_paths = find_plant_paths_cyverse(date_paths, tag)
    plant_names = [os.path.basename(i) for i in plant_paths]
    # print(plant_names)
    return plant_names

def get_all_plants(root_path="."):
    plant_paths = get_plant_paths(os.path.join(root_path, date_dir_wildcard, tag_dir_wildcard))
    return convert_paths_to_names(plant_paths)
# ---------------------------------------------------

def get_tags_in_dir(path="."):
    return convert_paths_to_names(get_tag_paths(path))


# ------------------------replace----------------------------------
def find_plant_names_in_dir_cyverse(de_path, tag_path):
    try:
        command = ['ils', os.path.join(de_path , tag_path, 'plant_reports')]
        print(command)
        lines = str(subprocess.check_output(command))
        # print(lines)
        no_new_line = lines.replace('\\n', '')

        separated = [i.split('/')[-1] for i in no_new_line.split('  ')[1:]]
        print(separated)

        return separated
    except:
        print('No plants found in ' , tag_path)
        return 'foo'

def get_plants_in_dir(path="."):
    return convert_paths_to_names(get_plant_paths(os.path.join(path)))

# -------------------------------------------------------------------

def longest_common_prefix(strs):
	"""
	From: https://www.tutorialspoint.com/longest-common-prefix-in-python
	:type strs: List[str]
	:rtype: str
	"""
	if len(strs) == 0:
		return ""
	current = strs[0]
	for i in range(1,len(strs)):
		temp = ""
		if len(current) == 0:
			break
		for j in range(len(strs[i])):
			if j<len(current) and current[j] == strs[i][j]:
				temp+=current[j]
			else:
				break
		current = temp
	return current
