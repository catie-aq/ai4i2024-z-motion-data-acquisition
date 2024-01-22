# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import scipy


from skinematics import quat, vector, rotmat



def normalize_acceleration_data_quat(
    raw_acceleration_data,
    quaternion_data,
    ):

    """
    Computes normalized acceleration data from raw acceleration data
    (including gravity) and quaternion data.

    * Based on code available on :
    https://github.com/thomas-haslwanter/scikit-kinematics/blob/master/skinematics/imus.py

    Parameters
    ----------

    raw_acceleration_data: ndarray(N,3)
        Raw acceleration (including gravity), in [m/s^2]

    quaternion_data: ndarray(N,4)
        Four point quaternion data

    sampling_rate: float
        sampling rate, in [Hz]

    Returns
    ---------

    Vecolity and position data : (ndarray(N,3), ndarray(N,3))
    Raises an exception otherwise.

    """
    # g = scipy.constants.g   # 9.80665
    g = 9.81

    g_v = np.r_[0, 0, g]

    linear_acceleration_data = raw_acceleration_data - vector.rotate_vector(g_v, quat.q_inv(quaternion_data))
    normalized_acceleration_data = vector.rotate_vector(linear_acceleration_data, quaternion_data)

    return normalized_acceleration_data


SAMPLING_RATE = 50



def compute_velocity_position(
    raw_acceleration_data,
    quaternion_data,
    timestamp_data
    ):
    """
    Computes velocity and position from normalized acceleration data and quaternion data

    * Based on code available on :
    https://github.com/thomas-haslwanter/scikit-kinematics/blob/master/skinematics/imus.py

    Parameters
    ----------

    raw_acceleration_data: ndarray(N,3)
        Raw acceleration (including gravity), in [m/s^2]

    quaternion_data: ndarray(N,4)
        Four point quaternion data

    timestamps: ndarray(N,1)
        timestamp


    Returns
    ---------

    Normalized acceleration data : ndarray(N,3)
    Raises an exception otherwise.

    """
    initial_position = np.zeros(3)
    mean_timestamp_delta = timestamp_data.diff().dropna().mean()


    normalized_acc_data = normalize_acceleration_data_quat(raw_acceleration_data, quaternion_data)

    velocity_data = np.nan*np.ones_like(normalized_acc_data)
    position_data = np.nan*np.ones_like(normalized_acc_data)

    for ii in range(normalized_acc_data.shape[1]):
        dt = timestamp_data.diff().fillna(0)
        # velocity_data[:,ii] = (raw_acceleration_data.iloc[:, ii] * dt).cumsum()
        # position_data[:,ii] = (velocity_data[:, ii] * dt).cumsum()
        velocity_data[:,ii] = scipy.integrate.cumtrapz(normalized_acc_data[:,ii], timestamp_data, initial=0)
        position_data[:,ii] = scipy.integrate.cumtrapz(velocity_data[:,ii], timestamp_data, initial=initial_position[ii])
    return (velocity_data, position_data)


