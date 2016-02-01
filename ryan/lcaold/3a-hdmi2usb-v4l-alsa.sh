#!/bin/bash -e

SRC="$(dirname $(realpath ${BASH_SOURCE[@]}))"
source $SRC/A-variables.sh

PORT=10001
HOST=192.168.0.15

    gst-launch-1.0 \
        videotestsrc pattern=blank !\
            videoconvert !\
            videorate !\
            videoscale !\
            video/x-raw,format=I420,width=1280,height=720,framerate=30/1,pixel-aspect-ratio=1/1 !\
            queue !\
            mux. \
        \
        alsasrc device='hw:1,0' provide-clock=false
            audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !\
            queue !\
            mux. \
        \
        matroskamux name=mux !\
            tcpclientsink port=$PORT host=$VOCTOCOREIP

