#!/bin/sh
wget -nc -O /tmp/avsync.ts http://c3voc.mazdermind.de/testfiles/avsync.ts
(while true; do cat /tmp/avsync.ts || exit; done) | ffmpeg -y \
	-i - \
	-vf scale=1280x720 \
	-c:v rawvideo \
	-c:a pcm_s16le \
	-pix_fmt yuv420p \
	-f matroska \
	tcp://localhost:1000$1

