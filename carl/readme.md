config.ini 

~/.bashrc  
export HDMI2USB=/dev/video0
# For slave, replace this with hostname of box running vocto core\n" >> .bashrc
export VOC_CORE=localhost



# to runn all the things:
screen -c screenrc-ts


hu2file.sh - Hdmi2Usb to file - simple gstreamer to save to disk

vcore.sh - runs core with config.ini
vui.sh - runs gui 
v123test.sh - runs 3 avsync-test loops
source-avsync-test-clip-looped-as-cam-x.sh 

generate-cut-list.sh - displays times to screen and logs to cut-list.txt 

# to save to disk
~/lca/video-scripts/ryan/lca/record-timestamp.sh 
~/lca/voctomix/example-scripts/ffmpeg/record-mixed-ffmpeg-segmented.sh

