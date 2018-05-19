import os
import re
import xml.etree.ElementTree as ET
import pickle
import json

import conf
import ps3hiratranslator

MAX_FAILED_MATCH = 3

#voice_match_regex = re.compile(r"[ -~]+/[ -~]+/[ -~]+")
ascii_match_regex = re.compile(r"[ -~]+")

#keep only japanese characters
#remove spaces
# is_japanese_punct = in_range(code_point, 0x3000, 0x303f) NO
# is_hiragana = in_range(code_point, 0x3040, 0x309f) YES
# is_katakana = in_range(code_point, 0x30a0, 0x30ff) YES
# is_ideograph = in_range(code_point, 0x4e00, 0x9faf) YES
#this function should also remove newlines etc.
def filter_line_for_comparison(in_line):
    # TODO: should make the script show which line was mapped to which line! (showing the diff values in addition to 'real' line content)
    # This splits the line into sentence fragments (if any) and then just takes the first one.
    # If you split the line: 魅音rvS01/03/120300039.「二人ともなぁに自信ないこと言ってんだか！kvS01/03/120300040.�二人なかよくビリにな っちゃうよ〜？」
    #          it gives you: ['魅音', '「二人ともなぁに自信ないこと言ってんだか！', '�二人なかよくビリになっちゃうよ〜？」']
    # then you take the second element of the array, and use that for line matching.
    # The following test cases can also occur:
    # r不覚にも、転んだ時に腰をひねったらしかった。k…すずりよりはマシか。 <- Note: no voice cmd but has 'r' and 'k'
    # 梨花rvS19/05/990500001.「…圭一の痛いの痛いの、飛んで行けです」
    # 圭一rvS01/01/120100064.「なに？！kvS01/01/120100065.�もう？！？！
    sentence_fragments = re.split(ascii_match_regex, in_line, maxsplit=2)

    if len(sentence_fragments) >= 2:
        in_line = sentence_fragments[1]

    ret_line = ''.join([c for c in in_line if 0x3040 < ord(c) < 0x9faf])

    return ret_line


def line_probably_is_dialogue(line):
    """
    This function attempts to figure out if a given line is Japanese Dialogue. It is only used in Mode 0 (look for
    Japanese dialogue in comments).
    :param line: The input line to test for being dialogue or not.
    :return: True if line is japanese dialogue, false otherwise
    """
    filtered = filter_line_for_comparison(line)
    if filtered:
        if '@' in line or '＠' in line or '\\' in line or '￥' in line or line[-1] == '/':
            return True

    return False


class Dialogue:
    """
    Object to store information from a Dialog instruction
    Data argument has hiragana automatically translated
    """
    def __init__(self, num, dlgtype, data, do_translate=True, do_preprocess=False):
        self.num = int(num)
        self.type = int(dlgtype)
        self.data = ps3hiratranslator.translate_and_unescape(data)
        if do_preprocess:
            self.data = filter_line_for_comparison(self.data)


def get_dialogue_and_instructions_from_ps3xml(input_xml_path, skip_blank=True):
    """
    Get a list of ps3 dialogue objects, and the entire exml file as an array of dialoge objects/ array of dictionaries

    :param input_xml_path: xml file to extract data from
    :param skip_blank: Ignore blank dialogue
    :return: ([Dialogue Objects], [xml attribute dicts])
    """
    tree = ET.parse(input_xml_path)
    root = tree.getroot()

    all_dialogue = []
    entire_xml = []

    for child in root:
        type = child.attrib['type']

        if type == 'DIALOGUE':
            d = Dialogue(child.attrib['num'], child.attrib['dlgtype'], child.attrib['data'], do_preprocess=True)
            if skip_blank and d.data:
                all_dialogue.append(d)

        for k,v in child.attrib.items():
            child.attrib[k] = ps3hiratranslator.translate_and_unescape(v)

        entire_xml.append(child.attrib)

    return all_dialogue, entire_xml


def get_original_script_japanese_lines_filtered(original_script_filepath, mode):
    """
    Extract the japanese comment lines from the modded manga gamer script? the original script.
    :param original_script_filepath:
    :return:
    """
    output_lines = []
    start_scanning = False
    with open(original_script_filepath, encoding=conf.encoding) as script_to_patch_file:
        for i,line in enumerate(script_to_patch_file):
            if mode == 0:
                if '//' in line:
                    filtered_line = filter_line_for_comparison(line)
                    #skip blank lines
                    if filtered_line and len(filtered_line) > 6:
                        if line_probably_is_dialogue(line):
                            start_scanning = True
                        if start_scanning:
                            output_lines.append((i, filter_line_for_comparison(line.strip())))
            elif mode == 1:
                if 'OutputLine' in line:
                    filtered_line = filter_line_for_comparison(line.strip())
                    if len(filtered_line) > 2: #min length to scan line in original script was 4 !
                        start_scanning = True
                        output_lines.append((i, filtered_line))
            else:
                print('ERROR - unknown mode', mode, 'EXITING')
                exit(-1)

    if not start_scanning:
        raise Exception('ERROR - Start line not found!')
        # raise Exception('ERROR - START/END PS3 INSERTION MISSING FROM SCRIPT')

    return output_lines


def run_diff(base_filename, modified_filename, diff_output_filename):
    """
    This function is a wrapper which just calls the command line 'git diff' with some sane default arguments.
    #note: perhaps test running with '-w' and not '-w' - they give slightly different results

    :param base_filename: The 'original' file to be diffed
    :param modified_filename: The 'changed' file to be diffed
    :param diff_output_filename: The location the diff should be saved to.
    :return:
    """
    os.system(r'git diff --no-index --ignore-blank-lines -w -U1000000 {} {}  > {}'.format(base_filename, modified_filename, diff_output_filename)) #], cwd=r'c:\temp')


def get_mapping(ps3_dialogue_object_array : [Dialogue], original_script_filepath, forward_search_range, temp_folder, ps3_dialogue_as_text, japanese_line_mode, debug=False) -> []:
    """
    Create a mapping between the ps3 dialog object ids and the line numbers in the original script.

    :param ps3_dialogue_object_array:
    :param original_script_filepath:
    :param forward_search_range:
    :return:
    """
    #generate filepaths for temporary files
    original_script_folder, original_script_filename = os.path.split(original_script_filepath)
    original_script_japanese_lines_path = os.path.join(temp_folder, original_script_filename + 'japanese_lines_only.txt')
    diff_output_path = os.path.join(temp_folder, original_script_filename + 'ps3diff.txt')

    #get only japanese lines from original script, with line numbers.
    original_script =  get_original_script_japanese_lines_filtered(original_script_filepath, japanese_line_mode)

    #save line numbers to memory, save just the script lines to file for diff
    original_script_japanese_only_line_numbers = []
    original_script_japanese_only_lines = []
    for line_no, line in original_script:
        original_script_japanese_only_line_numbers.append(line_no)
        original_script_japanese_only_lines.append(line)

    with open(original_script_japanese_lines_path, 'w', encoding=conf.encoding) as original_script_japanese_lines_file:
        original_script_japanese_lines_file.writelines('\n'.join(original_script_japanese_only_lines))
        original_script_japanese_lines_file.write('\n')

    #perform diff
    run_diff(original_script_japanese_lines_path, ps3_dialogue_as_text, diff_output_path)
    print('Wrote diff to ', diff_output_path)

    #go through the diff to determine assignment of each ps3 line to japanese line (check + and - order!)
    with open(diff_output_path, encoding=conf.encoding) as diff:
        diff_all_lines = diff.readlines()
        #ignore the first 5 lines of file
        diff_all_lines = diff_all_lines[5:]

    line_association = {}

    ps3_lines_to_associate = []
    ps3_line_counter = 0
    mg_line_counter = 0

    for line_with_type in diff_all_lines:
        type = line_with_type[0]
        line = line_with_type[1:]

        if type == '+':   #ps3 line exists but no such mg line - associate it with the next MG line
            ps3_lines_to_associate.append(ps3_line_counter)
            ps3_line_counter += 1
        elif type == '-':    #MG line exists but no such line in ps3 script - note that the MG line is not associated with any ps3 line
            if debug:
                print('MG line has no corresponding PS3 line!', ps3_line_counter, line)
            mg_line_counter += 1
        elif type == ' ':  #lines are identical
            # print('lines are the same:', line.strip())
            # print('adding line_association[{}]:{} lines are the same:{}'.format(mg_line_counter,ps3_lines_to_associate, line.strip()) )

            ps3_lines_to_associate.append(ps3_line_counter)
            line_association[mg_line_counter] = ps3_lines_to_associate
            ps3_lines_to_associate = []

            ps3_line_counter += 1
            mg_line_counter += 1
        else:
            raise Exception('uknown type for line [{}]'.format(type))

    #finally, convert line based indexing into original_script_line_number : ps3_dialoge_num

    # #NOTE - should associate ps3 id rather than line number!
    returned_ps3_to_mg_mapping = {}
    for k,v in line_association.items():
        ps3_nums = [ps3_dialogue_object_array[ps3_line_number].num for ps3_line_number in v]
        mg_script_line_number = original_script_japanese_only_line_numbers[k]
        returned_ps3_to_mg_mapping[mg_script_line_number] = ps3_nums
        if debug:
            print(k,v, '->', mg_script_line_number, ps3_nums)


    return returned_ps3_to_mg_mapping


def merge_ps3_into_mangagamer(ps3_script_as_xml_path, script_to_patch_path, script_with_json_path, temp_folder, forward_search_range, REGEN, mode, debug=False):
    os.makedirs(temp_folder, exist_ok=True)
    ps3_dialogue_dump_path = os.path.join(temp_folder, 'ps3_dialogue_dump_path.pickle')
    ps3_xml_dump_path = os.path.join(temp_folder, 'ps3_xml_dump_path.pickle')
    ps3_dialog_text_dump_path = os.path.join(temp_folder, 'ps3_dialogue_text_dump.txt')

    #pickle instructions loaded from the xml file so it doesn't need to be parsed multiple times
    if not os.path.exists(ps3_dialogue_dump_path) or not os.path.exists(ps3_xml_dump_path) or not os.path.exists(ps3_dialog_text_dump_path):
        dialogue_objects, entire_xml = get_dialogue_and_instructions_from_ps3xml(ps3_script_as_xml_path)
        with open(ps3_dialogue_dump_path, 'wb') as ps3_dialogue_dump_file:
            pickle.dump(dialogue_objects, ps3_dialogue_dump_file)
        with open(ps3_xml_dump_path, 'wb') as ps3_full_dump_file:
            pickle.dump(entire_xml, ps3_full_dump_file)
        #dump the ps3 lines as text
        with open(ps3_dialog_text_dump_path, 'w', encoding=conf.encoding) as ps3_dialogue_text_dump_file:
            all_dialogue_objects_as_text = '\n'.join([d.data for d in dialogue_objects])
            ps3_dialogue_text_dump_file.write(all_dialogue_objects_as_text)
            ps3_dialogue_text_dump_file.write('\n')

    #load the pickled .xml instructions and dialogue lines
    with open(ps3_dialogue_dump_path, 'rb') as ps3_dialogue_dump_file:
        ps3_dialoge_object_array = pickle.load(ps3_dialogue_dump_file)

    with open(ps3_xml_dump_path, 'rb') as ps3_full_dump_file:
        ps3_xml_full = pickle.load(ps3_full_dump_file)

    mapping = get_mapping(ps3_dialoge_object_array, script_to_patch_path, forward_search_range=forward_search_range, temp_folder=temp_folder, ps3_dialogue_as_text=ps3_dialog_text_dump_path, japanese_line_mode=mode)

    # get a table listing what instructions are before each dialogue, indexed by dialogue number
    # TODO: pickle this...
    dialogue_lookup_table = {}
    current_buffer = []
    for instruction in ps3_xml_full:
        current_buffer.append(instruction)

        if instruction['type'] == 'DIALOGUE':
            id = int(instruction['num'])
            dialogue_lookup_table[id] = current_buffer
            current_buffer = []

    with open(script_to_patch_path, encoding=conf.encoding) as script_to_patch_file:
        original_script_all_lines = script_to_patch_file.readlines()

    if debug:
        print('phase1 output')

    used_instruction_ids = []

    first_match = True
    for i, _ in enumerate(original_script_all_lines):
        # print('processing line', i)
        if i in mapping:
            ps3_dialogue_id_array = mapping[i]
            if first_match:
                num_results = len(ps3_dialogue_id_array)
                ps3_dialogue_id_array = ps3_dialogue_id_array[-10:]
                if debug:
                    print('First match - just taking {} insted of {} results'.format(ps3_dialogue_id_array, num_results))
                first_match = False

            all_instructions = []
            # print(ps3_dialogue_id_array)
            for ps3_dialogue_id in ps3_dialogue_id_array:
                ps3_instructions = dialogue_lookup_table[ps3_dialogue_id]
                all_instructions += ps3_instructions
                used_instruction_ids.append(ps3_dialogue_id) #for debugging only

            if mode == 0:
                line_to_insert_on = i
            elif mode == 1:
                line_to_insert_on = i-1
            else:
                print('Unknown mode!')
                exit(-1)

            original_script_all_lines[line_to_insert_on] = ''.join([original_script_all_lines[line_to_insert_on], '//JSON_INSTRUCTIONS: ', json.dumps(all_instructions, ensure_ascii=False), '\n'])
        # else:
        #     if '//' in line:
        #         print('ERROR - NO MATCH FOUND', line)

    with open(script_with_json_path, 'w', encoding=conf.encoding) as phase1_output:
        phase1_output.writelines(original_script_all_lines)

    print('wrote output to ', script_with_json_path)

    print('The input script maps to ps3 ids from {} to {}'.format(min(used_instruction_ids), max(used_instruction_ids)))