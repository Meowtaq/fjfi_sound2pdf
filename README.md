 ### Simple python script to export selected audio waves from audacity into a pdf


## setup
enable mod-script-pipe in audacity: 
edit -> preferences -> modules -> set mod-script-pipe to 'Enabled' -> Ok -> restart

### dependencies
matplotlib \
pypdf \
fpdf\
librosa\
pynput

## usage
Select clip to export

ctrl+alt+p  SAVE currently selected clip to pdf\
ctrl+alt+o  buffer currently selected clip\
ctrl+alt+r  reset buffered clip\
ctrl+alt+k  quit

(ctrl+cmd+" " on mac)
