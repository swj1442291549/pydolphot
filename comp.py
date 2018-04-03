import numpy as np
import pandas as pd
from astropy.table import Table
import argparse
from random import shuffle


def histogram_equal(x, nbin):
    """Histogram objects into equal number

    Args;
        x (array): objects
        nbin (int): number of bin

    Returns:
        rad_bin (array): radius bins
    """
    npt = len(x)
    rad_bin = np.interp(
        np.linspace(0, npt, nbin + 1), np.arange(npt), np.sort(x))
    rad_bin[0] = int(rad_bin[0])
    rad_bin[-1] = rad_bin[-1] + 0.0001
    return rad_bin


def get_data(file_name):
    """Get data from o.gst.files

    Args:
        file_name (string): fielname

    Returns:
        df (DataFrame): data
    """
    df = Table.read(file_name).to_pandas()
    return df


def generate_complete(df, filter_list, bin_num, total_num):
    fake_dict = dict()
    length_list = list()
    for filter in filter_list:
        mag_list = list()
        mag_num, mag_bin = np.histogram(df['{0}_VEGA'.format(filter)], bin_num)
        for i in range(bin_num):
            df_sel = df[df['{0}_VEGA'.format(filter)] > mag_bin[i]]
            df_sel = df_sel[df_sel['{0}_VEGA'.format(filter)] < mag_bin[i + 1]]
            num = np.random.poisson(mag_num[i] * total_num / np.sum(mag_num))
            mag_list.append(np.random.random(num) * (mag_bin[i + 1] - mag_bin[i]) + mag_bin[i])
        mag_list = np.concatenate(mag_list)
        shuffle(mag_list)
        fake_dict['{0}_VEGA'.format(filter)] = mag_list
        length_list.append(len(mag_list))

    length_min = np.min(length_list)
    for key in fake_dict:
        fake_dict[key] = fake_dict[key][: length_min]
    df_fake = pd.DataFrame(fake_dict)
    return df_fake


def add_xy(df_fake, df):
    """Add fake XY to data

    Args:
        df_fake (DataFrame): fake data
        df (DataFrame): data
    """
    num_t = len(df_fake)
    chip_num = np.random.randint(1, 3, size=num_t)
    num_1 = len(chip_num[chip_num == 1])
    num_2 = len(chip_num[chip_num == 2])
    df_1 = df[df['chip'] == 1]
    X_min = min(df_1['X'])
    Y_min = min(df_1['Y'])
    X_max = max(df_1['X'])
    Y_max = max(df_1['Y'])
    X_1_fake = np.random.uniform(X_min, X_max, num_1)
    Y_1_fake = np.random.uniform(Y_min, Y_max, num_1)
    df_2 = df[df['chip'] == 2]
    X_min = min(df_2['X'])
    Y_min = min(df_2['Y'])
    X_max = max(df_2['X'])
    Y_max = max(df_2['Y'])
    X_2_fake = np.random.uniform(X_min, X_max, num_2)
    Y_2_fake = np.random.uniform(Y_min, Y_max, num_2)
    X_fake = np.zeros(num_t)
    Y_fake = np.zeros(num_t)
    chip_1_index = 0
    chip_2_index = 0
    for i in range(num_t):
        if chip_num[i] == 1:
            X_fake[i] = X_1_fake[chip_1_index]
            Y_fake[i] = Y_1_fake[chip_1_index]
            chip_1_index += 1
        else:
            X_fake[i] = X_2_fake[chip_2_index]
            Y_fake[i] = Y_2_fake[chip_2_index]
            chip_2_index += 1
    df_fake = df_fake.assign(X=X_fake)
    df_fake = df_fake.assign(Y=Y_fake)
    df_fake = df_fake.assign(chip=chip_num)
    return df_fake


def get_filters(df):
    filter_list = []
    for key in df.keys():
        if '_VEGA' in key:
            filter_list.append(key[:-5])
    filter_list.sort()
    return filter_list



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-n',
        '--num',
        type=int,
        default=50000,
        help='Num of fake stars (50000)')
    parser.add_argument(
        '-b', '--bin', type=int, default=20, help='Number of bins (20)')
    args = parser.parse_args()
    total_num = args.num
    bin_num = args.bin
    df = get_data('final/o.gst.fits')
    filter_list = get_filters(df)

    df_fake = generate_complete(df, filter_list, bin_num, total_num)
    df_fake = add_xy(df_fake, df)
    t = Table.from_pandas(df_fake)
    t.write('complete.fits', overwrite=True)
