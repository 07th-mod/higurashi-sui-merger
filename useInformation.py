import conf
import json
# FadeOutBGM(Channel, fadetime, TRUE)
# PlayBGM(Channel, filename, volume, loop(0=loop, 1=play once))

def use_ps3_json_to_insert_bgm(input_script_with_json_path, output_path, debug=False):

    with open(input_script_with_json_path, encoding=conf.encoding) as inputScriptWithInstructions:
        all_lines = inputScriptWithInstructions.readlines()

    already_inserted_set = set()
    
    for i, line in enumerate(all_lines):
        # print(line)

        #remove existing PlayBGM lines:
        if 'PlayBGM' in line or 'FadeOutBGM' in line:
            if debug:
                print('Removing [{}]'.format(line.strip()))
            all_lines[i] = ''

        if '//JSON_INSTRUCTIONS' in line:
            dialogue_num = None #unique reference for this block of instructions
            line_json = line.replace('//JSON_INSTRUCTIONS:','')
            # print(line_json)
            data = json.loads(line_json)
            output_instructions = []
            for instruction in data:
                if instruction['type'] == 'BGM_PLAY': #{'type': 'BGM_PLAY', 'bgm_name': 'ちょこっとCITY TIME', 'bgm_file': 'HM01_05', 'volume': '188', 'single_play': '0'}
                    # output_instructions.append(str(instruction))
                    filename = instruction['bgm_file']
                    song_name = instruction['bgm_name']
                    volume = 128 #instruction['volume']
                    single_play = instruction['single_play']
                    output_instructions.append('PlayBGM( 0, "{}", 128, 0 );'.format(filename)) #always assume channel 0 bgm for now
                elif instruction['type'] == 'BGM_FADE': #{'type': 'BGM_FADE', 'duration': '60'}
                    channel = 0
                    fade_time = int(int(instruction['duration'])/60 * 1000) #ps3 game is 60 most of the time, i'm guessing that's meant to be 1 second
                    output_instructions.append('FadeOutBGM({},{},FALSE);'.format(channel, fade_time))
                    # output_instructions.append(str(instruction))
                    # output_instructions.append(output_command)
                elif instruction['type'] == 'DIALOGUE':
                    dialogue_num = instruction['num']

            #if there is a fade immediately before a bgm play, just delete the fade instruction
            # for output_instruction_index, line in enumerate(output_instructions):
            #     if 'PlayBGM' in line and output_instruction_index != 0:
            #         if 'FadeOutBGM' in output_instructions[output_instruction_index-1]:
            #             output_instructions[output_instruction_index-1] = ''
            play_bgm_in_instructions = False
            for output_instruction_index, line in enumerate(output_instructions):
                if 'PlayBGM' in line:
                    play_bgm_in_instructions = True #and output_instruction_index != 0:
                    # if 'FadeOutBGM' in output_instructions[output_instruction_index-1]:
                    #     output_instructions[output_instruction_index-1] = ''

            if play_bgm_in_instructions:
                for output_instruction_index, line in enumerate(output_instructions):
                    if 'FadeOutBGM' in line:
                        output_instructions[output_instruction_index] = ''

            #remove blank instructions
            output_instructions = [x for x in output_instructions if x.strip()]

            if dialogue_num is None:
                print('Error - this instruction chunk is missing a valid id', line)
                exit(-1)

            #only insert if that instruction chunk not already inserted
            if output_instructions and dialogue_num not in already_inserted_set:
                all_lines[i] = '\t' + '\n\t\n\t'.join(output_instructions) + '\n\t\n' #'//INSERTED_BGM\n'
                already_inserted_set.add(dialogue_num)
            else:
                all_lines[i] = ''

    #add BGM fadeout before last line in script
    for i in reversed(range(len(all_lines))):
        line = all_lines[i]
        if line.strip() == '}':
            all_lines[i] = '\tFadeOutBGM(0,1000,FALSE);\n' + all_lines[i]
            break

    with open(output_path, 'w', encoding=conf.encoding) as outputfile:
        outputfile.writelines(all_lines)

    print('wrote to', output_path)
