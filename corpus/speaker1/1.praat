# read in the TextGrid and the wav file, find all instances of schwa ("AH0", "AH1")
# for each of instance of schwa, get the start time, end time, duration, the corresponding word
# and the F1 and F2 values in hertz at the midpoint
# record this information to a text file

# Input: TextGrid, wav file
# Output: Text file

# where are my files?
path$ = "/Users/eleanor/Desktop/speech_corpus/"

# create the text file
outfile$ = "/Users/eleanor/Desktop/formants_schwa.txt"
appendFile: outfile$, "file", tab$, "word", tab$, "phone", tab$
appendFile: outfile$, "start", tab$, "end", tab$, "dur", tab$
appendFileLine: outfile$, "f1", tab$, "f2"

# set up the for loop
Create Strings as file list: "files", path$ + "*.TextGrid"
nFiles = Get number of strings

for i from 1 to nFiles
    selectObject: "Strings files"
    filename$ = Get string: i
    basename$ = filename$ - "_fave.TextGrid"
    # read in WAV file

    Read from file: path$ + basename$ + "_16kHz.wav"
    #pauseScript: "check sound file"

    To Formant (burg): 0, 5, 5500, 0.025, 50

    # read in TextGrid
    Read from file: path$ + filename$

    nInt = Get number of intervals: 1

    # loop through the TextGrid, and find the schwas
    for j from 1 to nInt
        selectObject: "TextGrid " + basename$ + "_fave"
        label$ = Get label of interval: 1, j

        # does the label$ contain "AH"
        if index_regex(label$, "^AH")

            # get the start time, end time, and duration
            # write the info to a text
            start = Get start time of interval: 1, j
            end = Get end time of interval: 1, j
            dur = end - start

            # get the word that it came from (this is on tier 2)
            wordInt = Get interval at time: 2, start + 0.01
            word$ = Get label of interval: 2, wordInt

            # get F1 and F2 at midpoint
            midpoint = start + (dur/2)

            # select the Formant object
            selectObject: "Formant " + basename$ + "_16kHz"
            f1 = Get value at time: 1, midpoint, "hertz", "linear"
            f2 = Get value at time: 2, midpoint, "hertz", "linear"

            appendFile: outfile$, basename$, tab$, word$, tab$, label$, tab$
            appendFileLine: outfile$, start, tab$, end, tab$, dur, tab$, f1, tab$, f2

        endif
    endfor

    # clean up 
    select all
    minusObject: "Strings files"
    Remove

endfor
