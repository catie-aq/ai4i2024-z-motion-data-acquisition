# -*- coding: utf-8 -*-

import numpy as np
import scipy

from skinematics import quat, vector, rotmat


def normalize_acceleration_data_irs(
    initial_orientation_rotation_matrix,
    raw_acceleration_data,
    rotation_speed_data,
    sampling_rate
    ):
    """
    Computes normalized acceleration data from raw acceleration data
    (including gravity) and rotation speed data.

    * Based on code available on :
    https://github.com/thomas-haslwanter/scikit-kinematics/blob/master/skinematics/imus.py

    Parameters
    ----------

    initial_orientation_rotation_matrix : ndarray(3,3)
        Rotation matrix describing the initial orientation of the sensor

    raw_acceleration_data: ndarray(N,3)
        Raw acceleration (including gravity), in [m/s^2]

    rotation_speed_data: ndarray(N,3)
        Angular velocity, in [rad/s]

    sampling_rate: float
        sampling rate, in [Hz]


    Returns
    ---------
    Normalized acceleration data : ndarray(N,3)
    Raises an exception otherwise.

    """


    # From :

    # Transform recordings to angVel/acceleration in space --------------

    # Orientation of \vec{g} with the sensor in the "initial_orientation_rotation_matrix"
    # g = scipy.constants.g   # 9.80665
    g = 9.81

    g0 = np.linalg.inv(initial_orientation_rotation_matrix).dot(np.r_[0,0,g])

    # for the remaining deviation, assume the shortest rotation to there
    q0 = vector.q_shortest_rotation(raw_acceleration_data[0], g0)

    q_initial = rotmat.convert(initial_orientation_rotation_matrix, to='quat')

    # combine the two, to form a reference orientation. Note that the sequence
    # is very important!
    q_ref = quat.q_mult(q_initial, q0)

    # Calculate orientation q by "integrating" rotation_speed_data -----------------
    q = quat.calc_quat(rotation_speed_data, q_ref, sampling_rate, 'bf')

    # Acceleration, velocity, and position ----------------------------
    # From q and the measured acceleration, get the \frac{d^2x}{dt^2}
    g_v = np.r_[0, 0, g]

    linear_acceleration_data = raw_acceleration_data - vector.rotate_vector(g_v, quat.q_inv(q))
    normalized_acceleration_data = vector.rotate_vector(linear_acceleration_data, q)

    return normalized_acceleration_data



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



def compute_velocity_position(
    raw_acceleration_data,
    quaternion_data,
    sampling_rate
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

    Returns
    ---------

    Normalized acceleration data : ndarray(N,3)
    Raises an exception otherwise.

    """

    normalized_acc_data = normalize_acceleration_data_quat(raw_acceleration_data, quaternion_data)

    velocity_data = np.nan*np.ones_like(normalized_acc_data)
    position_data = np.nan*np.ones_like(normalized_acc_data)

    initial_position = np.zeros(3)

    for ii in range(normalized_acc_data.shape[1]):
        velocity_data[:,ii] = scipy.integrate.cumtrapz(normalized_acc_data[:,ii], dx=1./sampling_rate, initial=0)
        position_data[:,ii] = scipy.integrate.cumtrapz(velocity_data[:,ii], dx=1./sampling_rate, initial=initial_position[ii])

    return (velocity_data, position_data)
