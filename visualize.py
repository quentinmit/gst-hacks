import gtk, gst
import OSC

Fs = 44100
N = 128

client = OSC.OSCClient()
client.connect(("18.83.4.145", 10233))

def n(F):
    return int(float(F)/(Fs/N))+1

def playerbin_message(bus, message):
    if message.type == gst.MESSAGE_ELEMENT:
        struct = message.structure
        if struct.get_name() == 'spectrum':
            # F = n * Fs / N
            # n=F / (Fs / N)
            m = struct['magnitude']
            low  = max(m[:n(125)])
            mid  = max(m[n(350):n(1500)])
            high = max(m[n(6000):])
            print "%03.1f %03.1f %03.1f %-60s %-60s %60s" % (low, mid, high,
                                                            "x"*int(low+60),
                                                            " "*int(-mid/2)+"x"*int(mid+60),
                                                            "x"*int(high+60),
                                                            )
            b = OSC.OSCBundle()
            b.append(OSC.OSCMessage("/R", (low+60)*(255/60.)))
            b.append(OSC.OSCMessage("/G", (mid+60)*(255/60.)))
            b.append(OSC.OSCMessage("/B", (high+60)*(255/60.)))
            client.send(b)
    else:
        print message
pipeline = gst.parse_launch(
    'pulsesrc device="alsa_output.pci-0000_00_1b.0.analog-surround-50.monitor" ! spectrum interval=16666667 ! fakesink')
bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect('message', playerbin_message)
pipeline.set_state(gst.STATE_PLAYING)
print "pipeline PLAYING"
gtk.main()

# Wait until error or EOS.
msg = bus.timed_pop_filtered(gst.CLOCK_TIME_NONE,
    gst.MESSAGE_ERROR | gst.MESSAGE_EOS)
print msg

# Free resources.
pipeline.set_state(gst.STATE_NULL)
