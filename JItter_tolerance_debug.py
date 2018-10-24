import pandas as pd
import re
import sys
import os
import time
import logging
import traceback
from time import sleep
import itertools
import numpy as np
import math

import GenericVISAPythonWrapper
import vivado_wrapper
import ScopeVISAPythonWrapper

bertIPAddress = r'GPIB0::20::INSTR'
instJbert = GenericVISAPythonWrapper.GenericVISAPythonWrapper(bertIPAddress)
vivado = vivado_wrapper.vivado_wrapper()

def dRange(start,stop,step):
    retList=[]
    while start <= stop:
        retList.append(start)
        start=start+step
    return retList

def bringup():
    powerOnSupplies()
    #  TachyonDefinitions.TachyonInitialization(instQuickUSB)
    measureCurrent = float(queryPS1Current())
    if measureCurrent < 0.6e-3:
        logging.critical(
            "Device is measuring less current than expected ... Something Wrong. Measured Current :" + str(measureCurrent))
        raise Exception(
            "Device is measuring less current than expected ... Something Wrong. Measured Current :" + str(measureCurrent))
    else:
        logging.critical("Device is measuring expected current .. Starting test. Measured Current :" + str(measureCurrent))

def instJbertGlobalJitterState(state=0):
    command = r':OUTJ:OUTP ' + str(state)  #:OUTJ:OUTP 1
    instJbert.Visa_Send(command)

def instJbertLFJitterState(state=0):
    command = r':OUTJ:JITT:PER ' + str(state)
    instJbert.Visa_Send(command)

def instJbertHFPj1JitterState(state=0):
    command = r':OUTJ:JITT:SIN1 ' + str(state)
    instJbert.Visa_Send(command)

def instJbertLFJitterAmplitude(instJbert_JITTER_AMPLITUDE):
    command = r':OUTJ:JITT:PER:AMPL ' + str(instJbert_JITTER_AMPLITUDE/2)
    instJbert.Visa_Send(command)

def instJbertLFJitterFrequency(instJbert_JITTER_FREQUENCY):
    command = r':OUTJ:JITT:PER:FREQ ' + str(instJbert_JITTER_FREQUENCY/2)
    instJbert.Visa_Send(command)

def instJbertHFPj1JitterAmplitude(instJbert_JITTER_AMPLITUDE):
    command = r':OUTJ:JITT:SIN1:AMPL ' + str(instJbert_JITTER_AMPLITUDE/2)
    instJbert.Visa_Send(command)

def instJbertHFPj1JitterFrequency(instJbert_JITTER_FREQUENCY):
    command = r':OUTJ:JITT:SIN1:FREQ ' + str(instJbert_JITTER_FREQUENCY/2)
    instJbert.Visa_Send(command)

def instJbertJitterFrequencyMaxJitterAmplitudeQuery(instJbert_JITTER_FREQUENCY):
    maxJitterAmplitude = 0
    if instJbert_JITTER_FREQUENCY < 0.625e+6:
        maxJitterAmplitude = 100
    else:
        maxJitterAmplitude = 1
    return maxJitterAmplitude

def BERTime(Datarate,BER,confidence):
    delay_time = -(math.log(1-confidence))/(BER*Datarate)
    return delay_time

def instJbertJitterFrequencyAmplitude(instJbert_JITTER_FREQUENCY, instJbert_JITTER_AMPLITUDE):
    # print "#instJbertJitterFrequencyAmplitude : Jitter_Frequency : "+str(instJbert_JITTER_FREQUENCY)+ " Jitter_Amplitude: "+str(instJbert_JITTER_AMPLITUDE)
    if instJbert_JITTER_FREQUENCY < 0.625e+6:
        instJbertHFPj1JitterAmplitude(0)
        instJbertLFJitterAmplitude(instJbert_JITTER_AMPLITUDE)
        instJbertLFJitterFrequency(instJbert_JITTER_FREQUENCY)
    else:
        instJbertLFJitterAmplitude(0)
        instJbertHFPj1JitterAmplitude(instJbert_JITTER_AMPLITUDE)
        instJbertHFPj1JitterFrequency(instJbert_JITTER_FREQUENCY)

def JitterLoop(JitterFrequency,
               BistResetScript=r'source C:\\Users\\julianp\\Desktop\\reset_script.tcl',
               BistCheckScript=r'source C:\\Users\\julianp\\Desktop\\Bist_check.tcl',
               BistCheckValue=0
               ):
    instJbert_jitter_amplitude_datalogging = 0
    max_jitterlimit = 100
    if JitterFrequency < 1.01e6:
        accuracy = 0.05
    else:
        accuracy = 0.005
    maxJitterAmplitudeSupported = instJbertJitterFrequencyMaxJitterAmplitudeQuery(JitterFrequency)
    if maxJitterAmplitudeSupported < max_jitterlimit:
        max_jitterlimit = maxJitterAmplitudeSupported
    instJbert_jitter_amplitude_datalogging = JitterLoopRecursive(0, max_jitterlimit, accuracy, JitterFrequency,BistResetScript, BistCheckScript, BistCheckValue)
    return instJbert_jitter_amplitude_datalogging

    # max_jitterlimit = 100
    # accuracy = 0.01
    # instJbert_jitter_amplitude_datalogging = 0
    # instJbert_jitter_amplitude_datalogging = JitterLoopRecursive(0, max_jitterlimit, accuracy, BistResetScript,
    #                                                        BistCheckScript, BistCheckValue)
    # instJbertHFPj1JitterAmplitude(0)
    # instJbertLFJitterAmplitude(0)
    # return instJbert_jitter_amplitude_datalogging


def JitterLoopRecursive(start, stop, accuracy, JitterFrequency, BistResetScript, BistCheckScript, BistCheckValue):
    # print "#------------ Start: "+str(start)+"Stop: "+str(stop)+"Accuracy: "+str(accuracy)
    if ((stop - start) > accuracy):
        for jitterAmplitude in dRange(start, stop, (stop - start) / 4.0):
            instJbertJitterFrequencyAmplitude(JitterFrequency, jitterAmplitude)
            vivado.query_command(BistResetScript,1,1)
            time.sleep(1)
            bistStatus = vivado.query_command(BistCheckScript,1,1)
            if (int(bistStatus, 16) == BistCheckValue):
                start = jitterAmplitude
                # print " Passed : ",jitterAmplitude
            else:
                vivado.query_command(BistResetScript,1,1)
                bistStatus = vivado.query_command(BistCheckScript,1,1)
                if (int(bistStatus, 16) == BistCheckValue):
                    pass
                else:
                    stop = jitterAmplitude
                    # print "#New Stop :"+str(stop)
                    # print "#Calling recursive Start: "+str(start)+"Stop: "+str(stop)+"Accuracy: "+str(accuracy)
                    return JitterLoopRecursive(start, stop, accuracy, JitterFrequency, BistResetScript, BistCheckScript,BistCheckValue)
        return stop
    else:
        return start


def returnJTOLSpec(freq):
    x1 = 1e6
    x2 = 10e6
    y1 = 1
    y2 = 0.1
    slope = (math.log10(y2) - math.log10(y1)) / (math.log10(x2) - math.log10(x1))
    c = math.log10(y2) - (math.log10(x2) * slope)
    returnSpec = math.pow(10, (slope * (math.log10(freq))) + c)
    if freq < 1.01e6:
        returnSpec = 1
    elif freq >= 10e6:
        returnSpec = 0.1
    else:
        pass
    return returnSpec


#vivado.query_command(r'source C:\\Users\\julianp\Desktop\Bringup.tcl',1,1)

print 'JTOL ', 'JTOL_Frequency', ',', 'JTOL_Amplitude', ',', 'JTOL_Result', ',', 'JTOL_Spec'

for jtolFreq in [0.5E5,1E5,3E5,7E5,1E6,2.5e6,5E6,10E6,20E6,30E6,50E6,80E6,100e6]:
    JTOL_Spec = returnJTOLSpec(jtolFreq)
    JTOL_Frequency = jtolFreq
    JTOL_Amplitude = JitterLoop(jtolFreq)
    if JTOL_Amplitude >= JTOL_Spec:
        JTOL_Result = 'Pass'
    else:
        JTOL_Result = 'Fail'
    print 'JTOL ', str(JTOL_Frequency), ',', str(JTOL_Amplitude), ',', JTOL_Result, ',', JTOL_Spec
