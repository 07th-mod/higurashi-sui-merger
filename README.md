# higurashi-sui-merger

This program merges the sui .xml instructions into MG formatted game scripts. Two merged scripts are generated - one 
which contains ALL instructions associated with each dialog, and one which has only the BGM play/stop inserted, and the 
old BGM commands removed.

## Usage

0. A Windows machine with Git installed is required for this script!
1. Place the sui .xml file in the 'data' directory
2. Place the MG Scripts you want to merge in the 'input' directory
3. Run the main.py script (`py main.py`)
4. Output files will be created in the output directory.

If you make the folder `C:\temp4\base_folder` on your computer, the script will use the files/folders from there instead.

## Extensibility

As an initial step script will merge ALL instructions into the sui script as a JSON comment. You can take the output
at that stage and process it with your own script, rather than using this script. These files are placed in the `output`
folder, called `[input_script_name].with_json`. The JSON lines start with a comment followed by the JSON
`//JSON_INSTRUCTIONS: [{json stuff is here}]`


## High Level Software Overview

The program basically carries out these steps:

1. Extract only the dialog lines from the .xml file and one input script (the program will repeat these steps for each input script).
A mapping must be kept of each dialog line to the original line number in the script it was extracted from.
2. Pre-process the dialog lines of both scripts to remove any small differences/keep only Japanese characters
3. Do a git diff of the two scripts, matching up the lines (ps3 .xml -> input script)
4. Now the lines are matched up, copy the associated ps3 .xml instructions above each Japanese line in the original script.
5. The desired instructions (like the BGM command) are are then reformatted so they work in the input script

In Step 2, the preprocessing step, is only necessary to make the git diff work better (as it won't be confused by lines
which are slightly different due to punctuation etc.)

In Step 3, the git diff only tells you which lines have been added (with a `+`), removed (with a `-`), or the same (` `).
You have to keep a counter for the scripts being diffed to keep track of where you are in each script.

In Step 4, each dialog line is associated with multiple instructions (the instructions directly before it). But because
the input script is a subset of the sui script, the very first dialog would be associated with a very large amount
of the input script. I just took the last 10 instructions as associated the first dialog with it. You could also
take instructions up until the previous dialog line.

Steps 1-4 are in `merge_sui.py`, Step 5 is in `useInformation.py`

### File Overview

- main.py - takes care of iterating over all the input files and calling the other functions/files
- merge.py - merges the sui xml instructions into the input script(s)
- ps3hiratranslator.py - utility class to fix up the the sui hiragana encoding
- conf.py - specify the encoding of text files / any other settings
- useInformation.py - Uses the information in each of the .with_json files to insert the BGM/any other required lines.

### Misc

#### Editing the Source Code

I recommend using PyCharm to edit the source files.

#### Options

The script can read Japanese lines them from comments in the input script (option 0) or read them from `OutputLine()`
functions (option 1). Option 1 is the default, but by passing the argument `0` or `1` on the command line you can change
the mode.
