import ctypes
from picosdk.ps2000a import ps2000a as ps, PS2000A_DIGITAL_CHANNEL_DIRECTIONS, PS2000A_TRIGGER_CONDITIONS, PS2000A_TRIGGER_CHANNEL_PROPERTIES, PS2000A_PWQ_CONDITIONS
from picosdk.functions import assert_pico_ok
import numpy as np

class PicoScope(object):
    """
    PicoScope 2000A oscilloscope interface module. Use this class when collecting traces using a PicoScope 2000A.
    """

    def __init__(self):
        """
        Initialize PicoScope object.
        """
        self.scope = ctypes.c_int16()
        self.status = {}
        self.open()
        

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
            raise


    def close(self):
        """
        Closes the PicoScope
        :return: None
        """
       
        if self.scope is not None:
            self.status["close"] = ps.ps2000aCloseUnit(self.scope)
            assert_pico_ok(self.status["close"])
        

    def setup(self, v_div, timebase, samplerate, duration, trigger_type, capture_mode, channel):
        """
        Sets up the PicoScope for trace capture
        :return: None
        """
        if self.scope is None:
            self.open()
        if self.scope is not None:

            return

    def set_sampling_mode(self):
        """
        Sets up the PicoScope for trace capture
        :return: None
        """
        return

            
    def set_trigger_simple(self, threshold: int, delay: int, auto: int, direction: int, channel: int = 0, enable: int = 1, simple: bool = False):
        """
        Set the trigger for the trace capture
        :param threshold: 
        :param delay: set the trigger delay
        :param auto: set how long to wait for trigger
        :param direction: the trigger channel
        :param channel: the trigger channel
        :param enable: the trigger channel
        :return: None
        """
        ps.ps2000aSetSimpleTrigger(self.scope, 
                                    enable, 
                                   channel, 
                                   ctypes.c_int16(threshold), 
                                   direction,
                                   ctypes.c_int32(delay),
                                   ctypes.c_int16(auto)
                                   )

        
    
    def start_trigger(self, capture_mode: int):
        """
        Tells the PicoScope to start the trigger based on the parameters set in PicoScope
        """

       

    def get_trigger(self):
        """
        Returns the trigger status
        :return: A string representing the trigger status
        """
       

    def wait_for_trigger(self):
        """
        Waits for the Lecroy trigger
        :return: True if successful, False if the trigger timeout
        """


    def get_channel(self, samples, short, channel='C3'):
        """
        Get the measurement data from the Lecroy from specified channel
        :param samples: The number of samples to record
        :param short:
        :param channel: The channel to collect data from
        :return: The data from the scope
        """
      
