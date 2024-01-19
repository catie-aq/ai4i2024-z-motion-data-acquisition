# -*- coding: utf-8 -*-

# Usage example : python inspect_recorded_data.py ./acquired_data/1_2.csv


import os, argparse

import pandas
import matplotlib.pyplot as plt

from tools.kinematics import normalize_acceleration_data_quat, compute_velocity_position
from tools.filtering import butter_highpass_filter, filtfilt, zero_if_under_threshold
from tools.visualization import plot_time_domain, plot_3d

from conf import SAMPLING_RATE, CSV_COLS_INDEX


def read_data_from(csv_file_path_name):
    data = pandas.read_csv(csv_file_path_name, delimiter=",", skiprows=0)
    raw_acceleration_data = data.values[:,CSV_COLS_INDEX["raw_acceleration_x"]:CSV_COLS_INDEX["raw_acceleration_z"]+1]
    quaternion_data = data.values[:,CSV_COLS_INDEX["quaternion_w"]:CSV_COLS_INDEX["quaternion_z"]+1]
    return raw_acceleration_data, quaternion_data


def inspect_recorded_data(
    csv_file_path_name,
    sampling_rate
    ):
    csv_file_name = os.path.basename(csv_file_path_name)
    raw_acceleration_data, quaternion_data = read_data_from(csv_file_path_name)
    normalized_acceleration_data = normalize_acceleration_data_quat(raw_acceleration_data, quaternion_data)

    print(quaternion_data)


    plot_time_domain(raw_acceleration_data, sampling_rate, "%s / raw acceleration" % csv_file_name)
    plot_time_domain(normalized_acceleration_data, sampling_rate, "%s / normalized acceleration" % csv_file_name)
    plt.show()

    # We may apply here some filters in order to enhance trajectory integration

    # normalized_acceleration_data = filtfilt(normalized_acceleration_data, 2, 1)
    # normalized_acceleration_data = butter_highpass_filter(normalized_acceleration_data, 0.15 ,SAMPLING_RATE)
    # normalized_acceleration_data = zero_if_under_threshold(normalized_acceleration_data, 1.0)

    velocity_data, position_data = compute_velocity_position(raw_acceleration_data, quaternion_data, sampling_rate)
    plot_3d(position_data, "%s / computed position" % csv_file_name)
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file_path", type=str, help="CSV file path")
    args = parser.parse_args()
    csv_file_path_name = args.csv_file_path
    inspect_recorded_data(csv_file_path_name, SAMPLING_RATE)


if __name__ == "__main__":
    main()


