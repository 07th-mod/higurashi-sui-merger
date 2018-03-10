import os
import sys
import ps3hiratranslator

# This is a script to translate an arbitrary file from ps3 japanese character encoding to normal encoding.
# It is not used in the other merge scripts.

# ONLY THESE INSTRUCTIONS will be substituted.
# When scanning the script, I found that only these instructions were ever modifeid, EXCEPT
# for the first < ? 1.0 xml > header at the top of the file, because it had a question mark
# {'HIDDEN_DIALOGUE', '1.0', 'REGISTER_CONDITION', 'DIALOGUE'}
# when you run this script it will print the above set

# gets the instruction type of an xml instruction
def get_instruction_type(line):
    return line.split('"', maxsplit=2)[1]

#parse input args, determine if file is xml
if len(sys.argv) < 2:
    print('You need to specify the file to be translated as only argument')
    exit(-1)

input_file_path = sys.argv[1]
output_file_path = 'sui_translated.xml'

is_xml = False
name, ext = os.path.splitext(input_file_path)
if ext == '.xml':
    is_xml = True

#do translation
all_instructions_which_were_changed = set()
with open(input_file_path, encoding='utf-8') as infile:
    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        for line in infile:
            # do translation
            newline = ps3hiratranslator.translate(line)
            outfile.write(newline)

            # record which instructions were modified
            if is_xml and newline != line:
                all_instructions_which_were_changed.add(get_instruction_type(line))

# print instructions which were modified
if is_xml:
    print(all_instructions_which_were_changed)
