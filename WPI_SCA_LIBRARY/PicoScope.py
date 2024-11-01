import ctypes
from picosdk.ps2000a import ps2000a as ps
import time
from picosdk.functions import assert_pico_ok
import numpy as np
import math

class PicoScope(object):
    """
    PicoScope 2000A oscilloscope interface module. Use this class when collecting traces using a PicoScope 2000A.
    """

    def __init__(self):
        """
        Initialize LecroyScope object.
        """
        self.scope = ctypes.c_int16()
        self.status = {}
        self.open()
        self.valid_trigger_states = ['AUTO', 'NORM', 'SINGLE', 'STOP']

    def __del__(self):
        """
        Close the scope on object deletion.
        :return: None
        """
        self.close()

    def open(self):
        """
        Opens a PicoScope using PythonSDK
        :return: None
        """
        self.status["openunit"] = ps.ps2000aOpenUnit(ctypes.byref(self.scope), None)
        try:
            assert_pico_ok(self.status["openunit"])

        except:
            # powerstate becomes the status number of openunit
            powerstate = self.status["openunit"]

            # If powerstate is the same as 282 then it will run this if statement
            if powerstate == 282:
                # Changes the power input to "PICO_POWER_SUPPLY_NOT_CONNECTED"
                self.status["ChangePowerSource"] = ps.ps2000aChangePowerSource(self.scope, 282)
            # If the powerstate is the same as 286 then it will run this if statement
            elif powerstate == 286:
                # Changes the power input to "PICO_USB3_0_DEVICE_NON_USB3_0_PORT"
                self.status["ChangePowerSource"] = ps.ps2000aChangePowerSource(self.scope, 286)
        else:
                raise

        assert_pico_ok(self.status["ChangePowerSource"])

    def close(self):
        """
        Closes the PicoScope
        :return: None
        """
       
        if self.scope is not None:
            self.status["close"] = ps.ps2000aCloseUnit(self.scope)
            assert_pico_ok(self.status["close"])
        

    def setup(self, v_div, timebase, samplerate, duration, v_offset, channel):
        """
        Sets up the Lecroy scope for trace capture
        :param v_div: voltage scale per division
        :param timebase: the timescale for the scope
        :param samplerate: the rate in which measurements are sampled
        :param duration: the duration of capture
        :param v_offset: the voltage offset for the measurement
        :param channel: the channel to capture the traces on
        :return: None
        """
        if self.scope:
            self.scope.write("{}:TRA ON".format(channel))
            self.scope.write(r"""vbs 'app.Acquisition.ClearSweeps' """)
            self.scope.write("TDIV " + timebase)
            self.scope.write("{}:VDIV {}".format(channel, v_div))
            self.scope.write("CFMT DEF9,WORD,BIN")
            self.scope.write(r"""vbs 'app.Acquisition.Horizontal.Maximize = "FixedSampleRate" '""")
            self.scope.write(r"""vbs 'app.Acquisition.Horizontal.SampleRate = "%s" '""" % samplerate)
            self.scope.write(r"""vbs 'app.Acquisition.Horizontal.AcquisitionDuration = "%s" '""" % duration)
            self.scope.write(r"""vbs 'app.Acquisition.%s.VerOffset = "%s" '""" % (channel, v_offset))

    def set_trigger(self, delay, level, channel='C1'):
        """
        Set the trigger for the trace capture
        :param delay: the trigger delay
        :param level: the trigger level
        :param channel: the trigger channel
        :return: None
        """
        if self.scope is None:
            self.open(self.scope_ip)
        if self.scope:
            self.scope.write("{}:TRA ON".format(channel))
            self.scope.write("{}:TRCP DC".format(channel))
            self.scope.write("TRDL " + delay)
            self.scope.write("{}:TRLV {}".format(channel, level))
            self.scope.write("{}:TRSL POS".format(channel))

    def start_trigger(self):
        """
        Tells the LecroyScope to start the trigger based on the parameters set in LecroyScope.set_trigger
        """
        if self.scope:
            self.scope.write("TRMD SINGLE")
            self.scope.write(r"""vbs 'app.acquisition.triggermode = "stopped" ' """)
            self.scope.query(r"""vbs? 'return=app.WaitUntilIdle(.01)' """)
            self.scope.write(r"""vbs 'app.acquisition.triggermode = "single" ' """)
            self.scope.query(r"""vbs? 'return=app.WaitUntilIdle(.01)' """)

    def get_trigger(self):
        """
        Returns the trigger status
        :return: A string representing the trigger status
        """
        if self.scope is None:
            self.open(self.scope_ip)
        if self.scope:
            ret = self.scope.query("TRMD?")
            return ret.split()[1]

    def wait_for_trigger(self):
        """
        Waits for the Lecroy trigger
        :return: True if successful, False if the trigger timeout
        """
        if self.scope is None:
            self.open(self.scope_ip)

        if self.scope:
            for tries in range(10):
                if self.get_trigger() == 'STOP':
                    return True
                else:
                    time.sleep(0.5)
        print("Trigger timout!")
        return False

    def get_channel(self, samples, short, channel='C3'):
        """
        Get the measurement data from the Lecroy from specified channel
        :param samples: The number of samples to record
        :param short:
        :param channel: The channel to collect data from
        :return: The data from the scope
        """
        if self.scope is None:
            self.open(self.scope_ip)
        if self.scope:
            if short:
                self.scope.write('{0}:WF? DATA1'.format(channel))
                trc = self.scope.read_raw()
                hsh = trc.find(b'#', 0)
                skp = int(trc[hsh + 1:hsh + 2])
                trc = trc[hsh + skp + 2:-1]
                ret = np.frombuffer(trc, dtype='<h', count=samples)
                return ret
            else:
                self.scope.write('{0}:INSPECT? "SIMPLE"'.format(channel))
                trc = self.scope.read_raw()
                hsh = trc.find(b'\n', 0)
                trc = trc[hsh + 2:-1]
                text = str(trc)
                float_pattern = r'-?\d+\.\d*(?:[eE][-+]?\d+)?'
                matches = re.findall(float_pattern, text)
                float_list = [float(match) for match in matches]
                return float_list
        else:
            return None

