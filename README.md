Simple python script made for CTU FJFI to export selected audio waves from audacity into a pdf

#dependencies#
matplotlib
pypdf
fpdf
librosa
pynput

#setup#
enable mod-script-pipe in audacity: 
edit -> preferences -> modules -> set mod-script-pipe to 'Enabled' -> Ok -> restart

##usage##
ctrl+alt+p  SAVE currently selected clip to pdf
ctrl+alt+o  buffer currently selected clip
ctrl+alt+r  reset buffered clip
ctrl+alt+k  quit
