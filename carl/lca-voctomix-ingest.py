#!/usr/bin/env python3
"""
Ryan Verner <ryan.verner@gmail.com>
Voctomix ingest streams used for LCA2016, hacked up on the fly.
FIXME: This works, but it really needs rewriting.

PIPELINES:
 * dv
 * dvpulse
 * hdvpulse
 * hdmi2usb
 * blackmagichdmi
 * test

Example intended uses (NOTE expected environment variables):
 * lca-videomix-ingest.py dvpulse 0
 * lca-videomix-ingest.py hdmi2usb 1
""" 

import sys
import gi
import signal
import os
import socket

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GstNet, GObject

# init GObject & Co. before importing local classes
GObject.threads_init()
Gst.init([])

class Source(object):
    def __init__(self, pipeline_name, pulse_device, voc_port, voc_core_hostname, hdmi2usb_device):

        voc_core_ip = socket.gethostbyname(voc_core_hostname)
        print(pipeline_name, voc_core_ip, voc_port)


        if pipeline_name == 'dv': # untested, added for Carl 13-FEB-16
            pipeline = """
            dv1394src name=videosrc !
        dvdemux name=dv
        dv. !
            dvdec !
                tee name=t ! queue !
                videoconvert ! fpsdisplaysink sync=false t. ! queue !
		deinterlace mode=1 !
            videoconvert !
                videorate !
                videoscale !
                video/x-raw,format=I420,width=1280,height=720,framerate=30000/1001,pixel-aspect-ratio=1/1 !
                queue !
                mux.
        dv. !
            audioconvert !
            audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !
            queue !
            mux.
        matroskamux name=mux !
            tcpclientsink port=1000%s host=%s
            """ % (voc_port, voc_core_ip)

        elif pipeline_name == 'dvpulse':
            pipeline = """
            dv1394src name=videosrc !
		dvdemux !
		queue !
		dvdec !
		tee name=t ! queue !
		    videoconvert ! fpsdisplaysink sync=false t. ! queue !
		deinterlace mode=1 !
		videoconvert !
                videorate !
                videoscale !
                video/x-raw,format=I420,width=1280,height=720,framerate=30/1,pixel-aspect-ratio=1/1 !
                queue !
            mux. 
                pulsesrc device=%s name=audiosrc !
		audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !
                queue !
            mux.
                matroskamux name=mux !
                    tcpclientsink port=1000%s host=%s
                """ % (pulse_device, voc_port, voc_core_ip)
           
        elif pipeline_name == 'hdvpulse':
            pipeline = """
            hdv1394src do-timestamp=true name=videosrc !
		tsdemux !
		queue !
		decodebin !
		tee name=t ! queue !
		    videoconvert ! fpsdisplaysink sync=false t. ! queue !
		deinterlace mode=1 !
		videorate !
                videoscale !
		videoconvert !
		video/x-raw,format=I420,width=1280,height=720,framerate=30/1,pixel-aspect-ratio=1/1 !
                queue !
            mux. 
                pulsesrc device=%s name=audiosrc !
		audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !
                queue !
            mux.
                matroskamux name=mux !
                    tcpclientsink port=1000%s host=%s
                """ % (pulse_device, voc_port, voc_core_ip)

        elif pipeline_name == 'blackmagichdmi':
            pipeline = """
            decklinkvideosrc mode=17 connection=2 !
		tee name=t ! queue !
		    videoconvert ! fpsdisplaysink sync=false t. ! queue !
		videoconvert !
                videorate !
                videoscale !
                video/x-raw,format=I420,width=1280,height=720,framerate=30/1,pixel-aspect-ratio=1/1 !
                queue !
		mux. 
            decklinkaudiosrc !
		audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !
                queue !
		mux. 
            matroskamux name=mux !\
                tcpclientsink port=1000%s host=%s
                """ % (voc_port, voc_core_ip)
 
        elif pipeline_name == 'hdmi2usb':
            pipeline = """
            v4l2src device=%s name=videosrc !
            queue !
		image/jpeg,width=1280,height=720 !
                jpegdec !
                videoconvert !
                tee name=t ! queue ! 
                    videoconvert ! fpsdisplaysink sync=false t. ! queue !
                videorate !
                video/x-raw,format=I420,width=1280,height=720,framerate=30/1,pixel-aspect-ratio=1/1 !
                queue !
                mux. 
            audiotestsrc name=audiosrc !
                audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !
                queue !
                mux. 
            matroskamux name=mux !\
                tcpclientsink port=1000%s host=%s
                """ % (hdmi2usb_device, voc_port, voc_core_ip)

        else: #test
            pipeline = """
            videotestsrc name=videosrc pattern=ball foreground-color=0x00ff0000 background-color=0x00440000 !
                 timeoverlay !
                 video/x-raw,format=I420,width=1280,height=720,framerate=30/1,pixel-aspect-ratio=1/1 !
                 mux.
            audiotestsrc name=audiosrc freq=330 !
                 audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !
                 mux.
            matroskamux name=mux !
                 tcpclientsink port=1000%s host=%s
                 """ % (voc_port, voc_core_ip)

        print(pipeline)

        self.clock = GstNet.NetClientClock.new('voctocore', voc_core_ip, 9998, 0)
        print('obtained NetClientClock from host', self.clock)

        print('waiting for NetClientClock to sync…')
        self.clock.wait_for_sync(Gst.CLOCK_TIME_NONE)

        print('starting pipeline')
        self.senderPipeline = Gst.parse_launch(pipeline)
        self.senderPipeline.use_clock(self.clock)
        self.src = self.senderPipeline.get_by_name('src')

        # Adjust audio/video sources with different latency
        if pipeline_name == 'hdvpulse':
            video_delay = int(0 * 1000000000) # in ns, override env for testing
            audio_delay = int(0.25 * 1000000000) 
            print('Adjusting AV sync: [video: {}] [audio: {}]'.format(video_delay, audio_delay))
            if video_delay > 0:
                self.videosrc = self.senderPipeline.get_by_name('videosrc')
                self.videosrc.get_static_pad('src').set_offset(video_delay)
            if audio_delay > 0:
                self.videosrc = self.senderPipeline.get_by_name('audiosrc')
                self.videosrc.get_static_pad('src').set_offset(audio_delay)

        # Binding End-of-Stream-Signal on Source-Pipeline
        self.senderPipeline.bus.add_signal_watch()
        self.senderPipeline.bus.connect("message::eos", self.on_eos)
        self.senderPipeline.bus.connect("message::error", self.on_error)

        print("playing")
        self.senderPipeline.set_state(Gst.State.PLAYING)


    def on_eos(self, bus, message):
        print('Received EOS-Signal')
        sys.exit(1)

    def on_error(self, bus, message):
        print('Received Error-Signal')
        (error, debug) = message.parse_error()
        print('Error-Details: #%u: %s' % (error.code, debug))
        sys.exit(1)

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
  
    # populate machine-specific things
    voc_core_hostname = os.environ.get('VOC_CORE', 'localhost')
    hdmi2usb_device = os.environ.get('HDMI2USB', '/dev/video0')
    pulse_device = os.environ.get('VOC_PULSE_DEV', 'alsa_input.usb-Burr-Brown_from_TI_USB_Audio_CODEC-00.analog-stereo')
    avsync_delay = os.environ.get('AVSYNC_DELAY', '10')

    # get parameters (pipeline_name, vocto port ending digit in 1000x)
    try:
        voc_pipeline = sys.argv[1]
        voc_port = sys.argv[2]
    except (NameError, IndexError):
        print("Requires parameters: pipeline_name, vocto_port_ending_digit")
        sys.exit()
    
    src = Source(pipeline_name=voc_pipeline,
                 pulse_device=pulse_device,
                 voc_port=voc_port,
                 voc_core_hostname=voc_core_hostname,
                 hdmi2usb_device=hdmi2usb_device)
    
    mainloop = GObject.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print('Terminated via Ctrl-C')


if __name__ == '__main__':
    main()
