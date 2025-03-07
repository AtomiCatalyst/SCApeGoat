import ctypes
import time
import numpy as np
import chipwhisperer as cw
from picosdk.ps2000a import ps2000a as ps
from picosdk.functions import assert_pico_ok
from WPI_SCA_LIBRARY.FileFormat import *
from WPI_SCA_LIBRARY.CWScope import *


def match_coupling(coupling):
    match(coupling):
        case 'DC':
            return ps.PS2000A_COUPLING['PS2000A_DC']
        case 'AC':
            return ps.PS2000A_COUPLING['PS2000A_AC']
        case _:
            print("Unrecognized coupling! DC it is!")
            return ps.PS2000A_COUPLING['PS2000A_DC']

def match_mV(millivolts):
    match(millivolts):
        case 10:
            return ps.PS2000A_RANGE['PS2000A_10MV']
        case 20:
            return ps.PS2000A_RANGE['PS2000A_20MV']
        case 50:
            return ps.PS2000A_RANGE['PS2000A_50MV']
        case 100:
            return ps.PS2000A_RANGE['PS2000A_100MV']
        case 200:
            return ps.PS2000A_RANGE['PS2000A_200MV']
        case 500:
            return ps.PS2000A_RANGE['PS2000A_500MV']
        case 1000:
            return ps.PS2000A_RANGE['PS2000A_1V']
        case 2000:
            return ps.PS2000A_RANGE['PS2000A_2V']
        case 5000:
            return ps.PS2000A_RANGE['PS2000A_5V']
        case 10000:
            return ps.PS2000A_RANGE['PS2000A_10V']
        case 20000:
            return ps.PS2000A_RANGE['PS2000A_20V']
        case 50000:
            return ps.PS2000A_RANGE['PS2000A_50V']
        case _:
            print("Range MUST begin with a 1, 2, or 5 and within the 10s range.")
            print("Ignoring value, setting to 10mV")
            return ps.PS2000A_RANGE['PS2000A_10MV']


class PicoScope(object):
    """
    PicoScope 2000a oscilloscope interface module. Use this class when collecting traces using a PicoScope 2000A.
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
        Opens a PicoScope using PythonSDK, should only be called from __init__
        :return: None
        """
        self.status["openunit"] = ps.ps2000aOpenUnit(ctypes.byref(self.scope), None)
        assert_pico_ok(self.status["openunit"])


    def close(self):
        """
        Closes the PicoScope connection
        :return: None
        """
       
        if self.scope is not None:
            self.status["close"] = ps.ps2000aCloseUnit(self.scope)
            assert_pico_ok(self.status["close"])


    def ch_setup(self, chA_coupling: str = 'AC', chA_mVrange: int = 50, chB_coupling: str = 'DC', chB_mVrange: int = 2000):
        """
        Sets up the PicoScope 2000a Channels for trace capture
        :param 
        :type 
        :param 
        :type
        :param 
        :type 
        :param 
        :type 
        :param 
        :type 
        :return: None
        :Authors: Nat Dynko (nmdynko@wpi.edu)
        """
        if self.scope is None:
            self.open()
        if self.scope is not None:
            # save these for later
            self.chA_mVrange = chA_mVrange
            self.chB_mVrange = chB_mVrange

            # Set up Channel 1
            self.status["setChA"] = ps.ps2000aSetChannel(self.scope,
                                                    ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],
                                                    1,  # channel enabled
                                                    match_coupling(chA_coupling),  # coupling
                                                    match_mV(chA_mVrange),  # mV range
                                                    0)  # no DC offset by default
            assert_pico_ok(self.status["setChA"])
            print(f"Channel A configured: {chA_coupling}, {chA_mVrange} mV range.")

            # Set up Channel 2
            self.status["setChB"] = ps.ps2000aSetChannel(self.scope,
                                                    ps.PS2000A_CHANNEL['PS2000A_CHANNEL_B'],
                                                    1,  # channel enabled
                                                    match_coupling(chB_coupling), # coupling
                                                    match_mV(chB_mVrange),  # mV range
                                                    0) # no DC offset by default
            assert_pico_ok(self.status["setChB"])
            print(f"Channel B configured: {chB_coupling}, {chB_mVrange} mV range.")
        
        return
      
    def set_trigger_simple(self, trigger_channel: str = 'B', trigger_mV: int = 1800, direction: str = "rising", delay_samples: int = 0, auto_trig: int = 0):
        """
        Set the trigger for the trace capture
        :return: None
        """
        max_adc = 32512
        
        match(trigger_channel):
            case 'A':
                trigger_ch = ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A']
                threshold = round((trigger_mV * max_adc) / self.chA_mVrange)
                self.vcc_ch = ps.PS2000A_CHANNEL['PS2000A_CHANNEL_B']
            case _: # default use B
                trigger_ch = ps.PS2000A_CHANNEL['PS2000A_CHANNEL_B']
                threshold = round((trigger_mV * max_adc) / self.chB_mVrange)
                self.vcc_ch = ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A']
        
        match(direction):
            case "above":
                trig_dir = ps.PS2000A_THRESHOLD_DIRECTION['PS2000A_ABOVE']
            case "below":
                trig_dir = ps.PS2000A_THRESHOLD_DIRECTION['PS2000A_BELOW']
            case "falling":
               trig_dir = ps.PS2000A_THRESHOLD_DIRECTION['PS2000A_FALLING']
            case _:
                trig_dir = ps.PS2000A_THRESHOLD_DIRECTION['PS2000A_RISING']


        self.status["trigger"] = ps.ps2000aSetSimpleTrigger(self.scope,
                                                1,  # enable trigger
                                                trigger_ch,  # trigger source
                                                ctypes.c_int16(threshold),  # threshold in adc
                                                trig_dir,  # trigger edge
                                                delay_samples,  # delay in samples
                                                auto_trig)  # auto trigger in ms
        assert_pico_ok(self.status["trigger"])
        print(f"Trigger configured on Channel {trigger_channel} (threshold {trigger_mV} mV, {direction} edge).")


    def cw_pico_capture(self, target: CWScope, fp: FileParent, experiment_name: str, timebase: int = 1, downsample_ratio: int = 1, ratio_mode: str = None, samples_per_run: int = 5000, num_traces: int = 2500, key: np.ndarray = None, texts: np.ndarray = None):
        """
        :param pscope: PicoScope 2000a Object
        :type pscope: PicoScope
        :param samples_per_run:
        :type samples_per_run: int
            
        :return: None
        :Authors: Nat Dynko (nmdynko@wpi.edu)
        """

        timebase = ctypes.c_uint32(timebase)
        downsample_ratio = ctypes.c_uint32(downsample_ratio)
        match(ratio_mode):
            case "aggregate":
                r_mode = ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_AGGREGATE']
            case "decimate":
                r_mode = ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_DECIMATE']
            case "average":
                r_mode = ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_AVERAGE']
            case _:
                r_mode = ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE']

        
        # Allocate a buffer
        bufferA = np.zeros(samples_per_run, dtype=np.int16)
        memory_segment = 0
        # Register the data buffer with the PicoScope
        self.status["setDataBuffer"] = ps.ps2000aSetDataBuffer(self.scope,
                                                            self.vcc_ch,
                                                            bufferA.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                                                            samples_per_run,
                                                            memory_segment,
                                                            r_mode)
        assert_pico_ok(self.status["setDataBuffer"])
                
        print(f"Data buffer allocated ({samples_per_run} samples per capture).")
        # Prepare list to collect acquired traces
        traces_array = []
        textin_array = []
        responses = []
        ktp = cw.ktp.Basic()

        if key is None:
            key = ktp.next()[0]
        if texts is None:
            text = ktp.next()[1]
        else:
            text = texts[i]
        
        target.target.set_key(key)
        
        print(f"Beginning capture loop ({num_traces} acquisitions)...")
        for trace_num in trange(num_traces):
            traces_list = np.array([])
            collected_samples = ctypes.c_uint32(samples_per_run)
            throwaway = ctypes.c_int16(0)
            block_ready = ctypes.c_int16(0)
            bufferA[:] = 0
            self.status["runBlock"] = ps.ps2000aRunBlock(self.scope,
                                                    0, # pre trigger samples
                                                    samples_per_run, # post trigger samples
                                                    timebase,
                                                    0,
                                                    None,
                                                    memory_segment,
                                                    None,
                                                    None)
            assert_pico_ok(self.status["runBlock"])
            target.target.simpleserial_write('p', text)
        
            while block_ready.value == 0:
                self.status["blockReady"] = ps.ps2000aIsReady(self.scope,
                                                    ctypes.byref(block_ready))
                time.sleep(0.01)
            responses.append(target.target.simpleserial_read('r', 16))
            textin_array.append(text)
            self.status["getValues"] = ps.ps2000aGetValues(self.scope, 
                                                    0,
                                                    ctypes.byref(collected_samples), 
                                                    downsample_ratio, 
                                                    r_mode, 
                                                    memory_segment, 
                                                    ctypes.byref(throwaway))
            assert_pico_ok(self.status["getValues"])
            traces_array.append(bufferA.copy())
            
            if key is None:
                key = ktp.next()[0]
            if texts is None:
                text = ktp.next()[1]
            else:
                text = texts[i]


        self.status["stop"] = ps.ps2000aStop(self.scope)
        assert_pico_ok(self.status["stop"])

        traces_pico = np.array(traces_array)
        textin_pico = np.array(textin_array)
        responses_pico = np.array(responses)
        print("Capture complete. Data shape: ", traces_pico.shape)

        if experiment_name not in fp.experiments:
            exp = fp.add_experiment(experiment_name)
        else:
            exp = fp.experiments[experiment_name]
        
        exp.add_dataset("Pico_Capture_Traces", traces_pico, datatype="float32")
        exp.add_dataset("Pico_Capture_Plaintexts", textin_pico, datatype="int8")
        exp.add_dataset("Pico_Capture_Ciphertexts", responses_pico, datatype="int8")

   
    
      
