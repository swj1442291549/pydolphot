import numpy as np
import pandas as pd
from astropy.table import Table
import argparse


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


def generate_complete(df, filter1, filter2, point_num, duplicate):
    mag_bin = histogram_equal(df['{0}_VEGA'.format(filter1)], point_num)
    f1_list = list()
    f2_list = list()
    for i in range(point_num):
        df_sel = df[df['{0}_VEGA'.format(filter1)] > mag_bin[i]]
        df_sel = df_sel[df_sel['{0}_VEGA'.format(filter1)] < mag_bin[i + 1]]
        f1_list.append(np.mean(df_sel['{0}_VEGA'.format(filter1)]))
        f2_list.append(np.mean(df_sel['{0}_VEGA'.format(filter2)]))
    f1_array = np.array(f1_list * duplicate)
    f2_array = np.array(f2_list * duplicate)
    df_fake = pd.DataFrame({
        '{0}_VEGA'.format(filter1): f1_array,
        '{0}_VEGA'.format(filter2): f2_array
    })
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
            filter_list.append(key)
    if len(filter_list) == 2:
        if int(filter_list[1][1:-6]) > int(filter_list[0][1:-6]):
            filter1 = filter_list[0][:-5]
            filter2 = filter_list[1][:-5]
        else:
            filter1 = filter_list[1][:-5]
            filter2 = filter_list[0][:-5]
    else:
        for i in range(len(filter_list)):
            print('{0}: {1}'.format(i, filter_list[i]))
        index_1 = input('First filter: ')
        index_2 = input('Second filter: ')
        filter1 = filter_list[int(index_1)][:-5]
        filter2 = filter_list[int(index_2)][:-5]
    return filter1, filter2



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d',
        '--dup',
        type=int,
        default=3000,
        help='Number of duplicate (3000)')
    parser.add_argument(
        '-n', '--num', type=int, default=20, help='Number of points (20)')
    args = parser.parse_args()
    duplicate = args.dup
    point_num = args.num
    df = get_data('final/o.gst.fits')
    filter1, filter2 = get_filters(df)

    df_fake = generate_complete(df, filter1, filter2, point_num, duplicate)
    df_fake = add_xy(df_fake, df)
    t = Table.from_pandas(df_fake)
    t.write('complete.fits', overwrite=True)
