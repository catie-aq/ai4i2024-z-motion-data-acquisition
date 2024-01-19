# -*- coding: utf-8 -*-

import math

import numpy as np
from scipy.fftpack import fft
from scipy import signal


def low_pass_filter(
    data,
    f_size,
    cutoff
    ):

    lgth, num_signal=data.shape
    f_data=np.zeros([lgth, num_signal])
    lpf=signal.firwin(f_size, cutoff, window='hamming')
    for i in range(num_signal):
        f_data[:,i]=signal.convolve(data[:,i], lpf, mode='same')
    return f_data

def butter_highpass(
    cutoff,
    fs,
    order=5
    ):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def butter_highpass_filter(
    data,
    cutoff,
    fs,
    order=5
    ):
    lgth, num_signal=data.shape
    f_data=np.zeros([lgth, num_signal])
    b, a = butter_highpass(cutoff, fs, order=order)
    for i in range(num_signal):
        f_data[:,i] = signal.filtfilt(b, a, data[:,i])
    return f_data

def filtfilt(
    data,
    n,
    a
    ):
    # n : interger / the larger n is, the smoother curve will be
    b = [1.0 / n] * n
    lgth, num_signal=data.shape
    f_data=np.zeros([lgth, num_signal])
    for i in range(num_signal):
        f_data[:,i] = signal.filtfilt(b, a, data[:,i])
    return f_data

def zero_if_under_threshold(
    data,
    threshold
    ):
    lgth, num_signal=data.shape
    f_data=np.zeros([lgth, num_signal])
    for i in range(0, lgth):
        for j in range(0, num_signal):
            if math.fabs(data[i, j]) < threshold:
                f_data[i, j] = 0
            else:
                f_data[i, j] = data[i, j]
    return f_data
