# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
from scipy.fftpack import fft


def plot_time_domain(
    data,
    sampling_rate,
    title
    ):
    """
    Generates a time domain plot from sampled 3D data.

    * Based on code available on :
    https://github.com/KChen89/Accelerometer-Filtering/blob/master/util/util.py

    Parameters
    ----------

    data : ndarray(N,3)
        3D sampled data (acceleration, rotation speed, velocity...)

    sampling_rate: float
        sampling rate, in [Hz]

    title: string
        Plot legend

    Returns
    ---------
    True if success.
    Raises an exception otherwise.

    """
    num_rows, num_cols = data.shape
    if num_cols != 3:
        raise ValueError('Not 3D data')
    fig, ax=plt.subplots()
    labels=['x','y','z']
    color_map=['r', 'g', 'b']
    index=np.arange(num_rows)/sampling_rate
    for i in range(num_cols):
        ax.plot(index, data[:,i], color_map[i], label=labels[i])
    ax.set_xlim([0,num_rows/sampling_rate])
    ax.set_xlabel('Time [sec]')
    ax.set_title(title)
    ax.legend()
    return True


def plot_3d(
    data,
    title
    ):
    """
    Generates a 3D plot from 3D data.

    Parameters
    ----------

    data : ndarray(N,3)
        3D data (acceleration, rotation speed, velocity...)

    title: string
        Plot legend

    Returns
    ---------
    True if success.
    Raises an exception otherwise.

    """
    ax = plt.axes(projection='3d')
    ax.scatter3D(data[:,0] ,data[:,1], data[:,2], c=data[:,2], cmap='twilight')
    ax.set_title(title)
    return True
