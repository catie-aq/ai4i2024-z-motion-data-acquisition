# -*- coding: utf-8 -*-

# Usage example : python inspect_recorded_data.py ./acquired_data/1_2.csv


import os, argparse

import numpy as np

import pandas as pd

import scipy

from skinematics import quat, vector

import matplotlib.pyplot as plt



def inspect_recorded_data(csv_file_path_name):
    csv_file_name = os.path.basename(csv_file_path_name)
    data = pd.read_csv(csv_file_path_name, delimiter=",", skiprows=0)

    timestamp_data = data['t']
    t_ref = timestamp_data.iloc[0]
    timestamp_data = timestamp_data - t_ref

    raw_acceleration_data = data[["raw_acceleration_x", "raw_acceleration_y", "raw_acceleration_z"]]
    quaternion_data = data[["quaternion_w", "quaternion_x", "quaternion_y", "quaternion_z"]]

    # g = scipy.constants.g   # 9.80665
    g = 9.81   # to be ajusted / recomputed

    g_v = np.r_[0, 0, g]

    linear_acceleration_data = raw_acceleration_data - vector.rotate_vector(g_v, quat.q_inv(quaternion_data))
    normalized_acceleration_data = vector.rotate_vector(linear_acceleration_data, quaternion_data)

    plt.plot(timestamp_data, raw_acceleration_data)
    plt.title("%s / raw acceleration data" % csv_file_name)
    plt.show()

    plt.plot(timestamp_data, normalized_acceleration_data)
    plt.title("%s / normalized acceleration data" % csv_file_name)
    plt.show()

    initial_position = np.zeros(3)
    velocity_data = np.nan*np.ones_like(normalized_acceleration_data)
    position_data = np.nan*np.ones_like(normalized_acceleration_data)

    for ii in range(normalized_acceleration_data.shape[1]):
        velocity_data[:,ii] = scipy.integrate.cumtrapz(normalized_acceleration_data[:,ii], timestamp_data, initial=0)
        position_data[:,ii] = scipy.integrate.cumtrapz(velocity_data[:,ii], timestamp_data, initial=initial_position[ii])

    ax = plt.axes(projection='3d')
    ax.scatter3D(position_data[:,0] ,position_data[:,1], position_data[:,2], c=position_data[:,2], cmap='twilight')
    ax.set_title("%s / computed position" % csv_file_name)

    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file_path", type=str, help="CSV file path")
    args = parser.parse_args()
    csv_file_path_name = args.csv_file_path
    inspect_recorded_data(csv_file_path_name)


if __name__ == "__main__":
    main()


