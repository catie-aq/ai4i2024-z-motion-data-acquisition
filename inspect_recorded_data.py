# -*- coding: utf-8 -*-

# Usage example : python inspect_recorded_data.py ./acquired_data/1_2.csv


import os, argparse

import pandas
import matplotlib.pyplot as plt

from tools.kinematics import normalize_acceleration_data_quat, compute_velocity_position
from tools.filtering import butter_highpass_filter, filtfilt, zero_if_under_threshold
from tools.visualization import plot_time_domain, plot_3d


def read_data_from(csv_file_path_name):
    data = pandas.read_csv(csv_file_path_name, delimiter=",", skiprows=0)
    return data

def inspect_recorded_data(
    csv_file_path_name
    ):
    csv_file_name = os.path.basename(csv_file_path_name)
    data = read_data_from(csv_file_path_name)
    t_data = data['t']
    t_ref = data['t'].iloc[0]
    data['t'] = data['t'] - t_ref

    raw_acceleration_data = data[["raw_acceleration_x", "raw_acceleration_y", "raw_acceleration_z"]]
    quaternion_data = data[["quaternion_w", "quaternion_x", "quaternion_y", "quaternion_z"]]
    normalized_acceleration_data = normalize_acceleration_data_quat(raw_acceleration_data, quaternion_data)

    plt.plot(data['t'], raw_acceleration_data)
    plt.show()

    plt.plot(data['t'], normalized_acceleration_data)
    plt.show()

    normalized_acceleration_data = filtfilt(normalized_acceleration_data, 2, 1)
    normalized_acceleration_data = zero_if_under_threshold(normalized_acceleration_data, 1.0)

    velocity_data, position_data = compute_velocity_position(raw_acceleration_data, quaternion_data, t_data)
    plot_3d(position_data, "%s / computed position" % csv_file_name)
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file_path", type=str, help="CSV file path")
    args = parser.parse_args()
    csv_file_path_name = args.csv_file_path
    inspect_recorded_data(csv_file_path_name)


if __name__ == "__main__":
    main()


