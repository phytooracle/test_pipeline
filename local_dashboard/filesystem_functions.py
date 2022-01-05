import sys, os, glob, pdb

date_dir_wildcard = "????-??-??/"
tag_dir_wildcard  = "*_*/"
plant_dir_wildcard = "*_[0-9]*/"

def get_all_dates(root_path="."):
    date_paths = glob.glob(os.path.join(root_path, date_dir_wildcard))
    return convert_paths_to_names(date_paths)

def get_all_tags(root_path="."):
    tag_paths = get_tag_paths(os.path.join(root_path, date_dir_wildcard))
    return convert_paths_to_names(tag_paths)

def get_all_plants(root_path="."):
    plant_paths = get_plant_paths(os.path.join(root_path, date_dir_wildcard, tag_dir_wildcard))
    return convert_paths_to_names(plant_paths)

def get_tag_paths(path="."):
    return glob.glob(os.path.join(path, tag_dir_wildcard))

def get_plant_paths(path="."):
    return glob.glob(os.path.join(path, "plant_reports", plant_dir_wildcard))

def convert_paths_to_names(list_of_paths):
    return list(set([os.path.basename(x[:-1]) for x in list_of_paths]))

def get_tags_in_dir(path="."):
    return convert_paths_to_names(get_tag_paths(path))

def get_plants_in_dir(path="."):
    return convert_paths_to_names(get_plant_paths(os.path.join(path)))

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
