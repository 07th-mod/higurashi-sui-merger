import os
import sys
import merge_sui
import useInformation
import conf

def debug_process_diff(path_to_diff):
    with open(path_to_diff, encoding=conf.encoding) as diff:
        all_lines = diff.readlines()

    all_lines = all_lines[5:]

    first_non_plus_line = None
    last_non_plus_line = len(all_lines)
    for i, line in enumerate(all_lines):
        linetype = line[0]

        if first_non_plus_line is None and linetype != '+':
            first_non_plus_line = i

        if linetype != '+':
            last_non_plus_line = i

    if first_non_plus_line is None:
        first_non_plus_line = 0

    cropped_diff_start = max(first_non_plus_line-100, 0)
    cropped_diff_end = min(last_non_plus_line+100, len(all_lines))

    cropped_diff = all_lines[cropped_diff_start: cropped_diff_end]
    print("Diff matched region from {} to {}".format(cropped_diff_start/len(all_lines)*100, cropped_diff_end/len(all_lines)*100))

    with open(path_to_diff + '.cropped.txt', 'w', encoding=conf.encoding) as cropped_diff_file:
        cropped_diff_file.write(""""Raw dif follows. ' ' indicates files are the same, 
        '+' indicates a line is present in the ps3 script but not in the other script, 
        '-' indicates a line is present in the other script but not the ps3 script
        the first 100 lines before and after are the matched section are included for reference""")
        cropped_diff_file.writelines(cropped_diff)



def get_input_files(folder_path_to_scan : str) -> [str]:
    file_paths_to_process = []

    for filename in os.listdir(folder_path_to_scan):
        root, ext = os.path.splitext(filename)
        if ext == '.txt':
            file_paths_to_process.append(os.path.join(folder_path_to_scan, filename))

    return file_paths_to_process

mode = None
if len(sys.argv) > 1:
    mode = int(sys.argv[1])
else:
    print('Error - mode not specified - using default mode of 1')
    print('Please specify mode as argument:\n0=search for japanese in comments\n1=search for japanese in OutputLine() functions')
    mode = 1

REGENERATE_PS3_PICKLE = False

base_folder = r'C:\temp4\base_folder\\' #''
if not os.path.exists(base_folder):
    base_folder = ''

WORKING_FOLDER = base_folder + r'output'
TEMP_FOLDER = base_folder + r'pickle'
INPUT_FOLDER = base_folder + r'input'

#ps3 xml path
ps3_script_as_xml_path = base_folder + r'data\sui_full.xml'

print('Input Folder: {}'.format(INPUT_FOLDER))
print('Temp Folder: {}'.format(TEMP_FOLDER))
print('Working Folder: {}'.format(WORKING_FOLDER))
print('PS3 XML Expected path: {}'.format(ps3_script_as_xml_path))

# merge all the scripts together to improve matching
all_input_merged_path = os.path.join(INPUT_FOLDER, 'all_input_merged.txt')

#maching sections ->
# 0,1,2,3,4,5
# 9, 9_02 10,11
# 12 13 14
# 14, 14_02
# 15
# 15_02, 15_03

files_to_join = [x.strip() for x in """
onik_000.txt
onik_001.txt
onik_002.txt
onik_003.txt
onik_004.txt
onik_005.txt
onik_009.txt
#  onik_009_02.txt
onik_010.txt
onik_011.txt
onik_012.txt
onik_013.txt
onik_014.txt
onik_014_02.txt
# onik_015.txt
onik_015_02.txt
onik_015_03.txt

""".splitlines() if x.strip() != '' and x[0] != '#']

all_script_lines = []

for script_path_filename in files_to_join:
    full_path = os.path.join(INPUT_FOLDER, script_path_filename)
    with open(full_path, encoding=conf.encoding) as f:
        all_script_lines.extend(f.readlines())

with open(all_input_merged_path, 'w', encoding=conf.encoding) as f:
    f.writelines(all_script_lines)


# files_to_process = get_input_files(INPUT_FOLDER)
files_to_process = [all_input_merged_path]

#input files folder
for script_to_patch_path in files_to_process:

    try:
        print('\n\nPatching "{}"...'.format(script_to_patch_path))

        #get list of input files from folder
        # script_to_patch_path = r'c:\temp4\sui\onik_004.txt'

        script_folder_path, script_filename = os.path.split(script_to_patch_path)

        script_with_json_path = os.path.join(WORKING_FOLDER, script_filename + '.with_json')
        final_output_path = os.path.join(WORKING_FOLDER, script_filename + '-patched.txt')

        merge_sui.merge_ps3_into_mangagamer(ps3_script_as_xml_path=ps3_script_as_xml_path,
                                            script_to_patch_path=script_to_patch_path,
                                            script_with_json_path=script_with_json_path,
                                            temp_folder=TEMP_FOLDER,
                                            forward_search_range = 150,
                                            REGEN=REGENERATE_PS3_PICKLE,
                                            mode=mode)

        useInformation.use_ps3_json_to_insert_bgm(script_with_json_path, final_output_path)

        diff_location = os.path.join(TEMP_FOLDER, script_filename + ".ps3diff.txt")
        debug_process_diff(diff_location)
        #print("expect diff at " + diff_location)

    except Exception as e:
        print('Couldnt process [{}] - Unexpected error: {}'.format(script_to_patch_path, str(e)))
