import os
import sys
import merge_sui
import useInformation

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

#input files folder
for script_to_patch_path in get_input_files(INPUT_FOLDER):

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

    except Exception as e:
        print('Couldnt process [{}] - Unexpected error: {}'.format(script_to_patch_path, str(e)))
