#this is a script to merge multiple files together (assuming there are less than 100 files)

import os
import shutil

import sys

input_pattern=sys.argv[1] #eg output.txt
output_file = sys.argv[2] #eg input_file_{}.txt - The `{}` will be replaced with the number 1,2,3,4 ...

with open(output_file,'wb') as wfd:
    for i in range(100):
        file_path = input_pattern.format(i)
        if os.path.exists(file_path):
            with open(file_path,'rb') as fd:
                shutil.copyfileobj(fd, wfd, 1024*1024*10)

            print('Merged "{}"', file_path)
